#新增底层向量库封装
import sqlite3
import numpy as np
import math
import jieba
from collections import Counter
from app.core.config import settings
from app.core.exceptions import VectorDbInsertError, VectorDbSearchError
from app.models.schemas import RagDoc
import logging
logger = logging.getLogger(__name__)

# 尝试导入sqlite_vec，如果失败则使用备选方案
try:
    import sqlite_vec
    HAS_SQLITE_VEC = True
except ImportError:
    HAS_SQLITE_VEC = False
    logger.warning("sqlite_vec未安装，将使用备选向量检索方案")

VECTOR_DIM = 1024

class VectorDB:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path if db_path is not None else settings.sqlite_db_path
        self.conn = self._get_conn()
        self._init_table()
        jieba.initialize()
        # BM25参数
        self.k1 = 1.5
        self.b = 0.75
        self._idf_cache: dict[str, float] = {}
        self._idf_dirty = True

    def _get_conn(self):
        # 加载sqlite-vec向量扩展
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        if HAS_SQLITE_VEC:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
        return conn

    def _init_table(self):
        # 普通文档表：存储可读文本、来源（0003 文本与向量分离存储）
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS rag_docs (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            source TEXT,
            question_no TEXT DEFAULT '',
            section TEXT DEFAULT ''
        )
        """)
        # 兼容旧库：为已存在但缺列的 rag_docs 补列（T2.2 元数据落库）
        cols = [row[1] for row in self.conn.execute("PRAGMA table_info(rag_docs)").fetchall()]
        if "question_no" not in cols:
            self.conn.execute("ALTER TABLE rag_docs ADD COLUMN question_no TEXT DEFAULT ''")
        if "section" not in cols:
            self.conn.execute("ALTER TABLE rag_docs ADD COLUMN section TEXT DEFAULT ''")

        # 文件级指纹索引：幂等入库（D3）——未变更跳过、变更替换、目录对账
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS rag_file_index (
            source TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            imported_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """)
        
        if HAS_SQLITE_VEC:
            # vec虚拟向量表，存储1024维嵌入
            self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS rag_vectors USING vec0(
                doc_id INTEGER PRIMARY KEY,
                embedding FLOAT[1024]
            )
            """)
        else:
            # 备选方案：普通表存储向量
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rag_vectors (
                doc_id INTEGER PRIMARY KEY,
                embedding BLOB
            )
            """)
        
        self.conn.commit()
        logger.info("向量数据表初始化完成")

    def insert_chunk(self, title: str, content: str, source: str, embedding: list[float],
                     question_no: str = "", section: str = "") -> int:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO rag_docs(title, content, source, question_no, section) VALUES (?, ?, ?, ?, ?)",
                (title, content, source, question_no, section)
            )
            doc_id = cur.lastrowid
            vec_bin = np.array(embedding, dtype=np.float32).tobytes()
            cur.execute(
                "INSERT INTO rag_vectors(doc_id, embedding) VALUES (?, ?)",
                (doc_id, vec_bin)
            )
            self.conn.commit()
            self._idf_dirty = True
            return doc_id
        except Exception as e:
            logger.error(f"插入文档失败: {e}")
            self.conn.rollback()
            raise VectorDbInsertError(f"文档入库失败: {str(e)}")

    # ---------- 文件级指纹与幂等（P3 · 落实 ADR-0002 D3） ----------

    def file_fingerprint(self, source: str) -> str | None:
        """查询文件指纹；未入库返回 None"""
        row = self.conn.execute(
            "SELECT fingerprint FROM rag_file_index WHERE source = ?", (source,)
        ).fetchone()
        return row[0] if row else None

    def upsert_file_fingerprint(self, source: str, fingerprint: str) -> None:
        """记录/更新文件指纹"""
        self.conn.execute(
            "INSERT INTO rag_file_index(source, fingerprint, imported_at) "
            "VALUES (?, ?, datetime('now', 'localtime')) "
            "ON CONFLICT(source) DO UPDATE SET fingerprint = excluded.fingerprint, "
            "imported_at = excluded.imported_at",
            (source, fingerprint),
        )
        self.conn.commit()

    def delete_file_index(self, source: str) -> None:
        """删除文件指纹记录"""
        self.conn.execute("DELETE FROM rag_file_index WHERE source = ?", (source,))
        self.conn.commit()

    def delete_docs_by_source(self, source: str) -> int:
        """删除某来源题库的全部题目分块与向量"""
        doc_ids = self.list_doc_ids_by_source(source)
        for doc_id in doc_ids:
            self.delete_doc_by_id(doc_id)
        return len(doc_ids)

    def delete_doc_by_id(self, doc_id: int) -> None:
        """按 doc_id 删除单条文档与向量（回滚用）"""
        self.conn.execute("DELETE FROM rag_vectors WHERE doc_id = ?", (doc_id,))
        self.conn.execute("DELETE FROM rag_docs WHERE doc_id = ?", (doc_id,))
        self.conn.commit()
        self._idf_dirty = True

    def list_docs_by_source(self, source: str) -> list[dict]:
        """列出某来源文件的全部文档（回滚恢复用）"""
        rows = self.conn.execute(
            "SELECT title, content, question_no, section FROM rag_docs WHERE source = ?",
            (source,),
        ).fetchall()
        return [
            {"title": r[0], "content": r[1], "question_no": r[2], "section": r[3]}
            for r in rows
        ]

    def list_doc_ids_by_source(self, source: str) -> list[int]:
        """列出某来源题库的全部 doc_id（蓝绿替换时删除旧块用）"""
        return [r[0] for r in self.conn.execute(
            "SELECT doc_id FROM rag_docs WHERE source = ?", (source,)
        ).fetchall()]

    def count_docs_by_source(self, source: str) -> int:
        """某来源题库的题目分块数（自检对账用）"""
        return self.conn.execute(
            "SELECT COUNT(*) FROM rag_docs WHERE source = ?", (source,)
        ).fetchone()[0]

    def count_vectors_by_source(self, source: str) -> int:
        """某来源题库的向量数（自检对账用）"""
        return self.conn.execute(
            "SELECT COUNT(*) FROM rag_vectors v JOIN rag_docs d ON v.doc_id = d.doc_id "
            "WHERE d.source = ?", (source,)
        ).fetchone()[0]

    def count_questions_by_source(self, source: str) -> int:
        """某来源题库的题目数（自检对账用）"""
        return self.conn.execute(
            "SELECT COUNT(DISTINCT question_no) FROM rag_docs WHERE source = ? AND question_no != ''",
            (source,),
        ).fetchone()[0]

    def indexed_sources(self) -> list[str]:
        """已入库题库的 source 清单（目录对账用）"""
        return [row[0] for row in self.conn.execute(
            "SELECT source FROM rag_file_index"
        ).fetchall()]

    def total_docs(self) -> int:
        """全库题目分块总数（统计用）"""
        return self.conn.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0]

    def total_vectors(self) -> int:
        """全库向量总数（统计用）"""
        return self.conn.execute("SELECT COUNT(*) FROM rag_vectors").fetchone()[0]

    def source_grouping(self) -> list[tuple]:
        """按来源分组的 (source, chunk_count) 列表（统计用）"""
        return self.conn.execute(
            "SELECT source, COUNT(*) FROM rag_docs GROUP BY source"
        ).fetchall()

    def clear_all(self) -> None:
        """清空全部文档、向量与指纹索引（知识库清空）"""
        self.conn.execute("DELETE FROM rag_vectors")
        self.conn.execute("DELETE FROM rag_docs")
        self.conn.execute("DELETE FROM rag_file_index")
        self.conn.commit()
        self._idf_dirty = True

    def search_vector(self, query_emb: list[float], top_k: int, threshold: float) -> list[RagDoc]:
        """稠密向量检索｜0004密集检索"""
        try:
            if HAS_SQLITE_VEC:
                # 使用sqlite-vec进行向量检索
                vec_bin = np.array(query_emb, dtype=np.float32).tobytes()
                cur = self.conn.cursor()
                rows = cur.execute("""
                    SELECT d.doc_id, d.title, d.content, d.source, d.question_no, d.section, distance
                    FROM rag_vectors v
                    JOIN rag_docs d ON v.doc_id = d.doc_id
                    WHERE embedding MATCH ? AND k = ?
                """, (vec_bin, top_k)).fetchall()
                res = []
                for doc_id, title, content, src, q_no, sec, dist in rows:
                    sim_score = 1 - dist  # 欧式距离转相似度
                    if sim_score >= threshold:
                        res.append(RagDoc(doc_id=doc_id, title=title, content=content, source=src,
                                          question_no=q_no or "", section=sec or "", score=sim_score))
                return res
            else:
                # 备选方案：Python计算向量距离
                cur = self.conn.cursor()
                rows = cur.execute("SELECT doc_id, embedding FROM rag_vectors").fetchall()
                
                results = []
                query_vec = np.array(query_emb, dtype=np.float32)
                
                for doc_id, vec_blob in rows:
                    doc_vec = np.frombuffer(vec_blob, dtype=np.float32)
                    # 计算余弦相似度
                    similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                    if similarity >= threshold:
                        results.append((doc_id, similarity))
                
                # 按相似度排序
                results.sort(key=lambda x: x[1], reverse=True)
                
                # 获取完整的文档信息
                res = []
                for doc_id, score in results[:top_k]:
                    doc_row = self.conn.execute(
                        "SELECT title, content, source, question_no, section FROM rag_docs WHERE doc_id = ?",
                        (doc_id,)
                    ).fetchone()
                    if doc_row:
                        res.append(RagDoc(
                            doc_id=doc_id,
                            title=doc_row[0],
                            content=doc_row[1],
                            source=doc_row[2],
                            question_no=doc_row[3] or "",
                            section=doc_row[4] or "",
                            score=score
                        ))
                return res
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in jieba.lcut(text) if w.strip()]

    def _ensure_idf_ready(self):
        if self._idf_dirty:
            self._build_idf_index()

    def _build_idf_index(self):
        N = self.conn.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0]
        if N == 0:
            self._idf_cache = {}
            self._idf_dirty = False
            return

        df_counter: dict[str, int] = {}
        rows = self.conn.execute("SELECT content FROM rag_docs").fetchall()
        for (content,) in rows:
            for token in set(self._tokenize(content)):
                df_counter[token] = df_counter.get(token, 0) + 1

        new_cache = {
            token: math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            for token, df in df_counter.items()
        }
        self._idf_cache = new_cache
        self._idf_dirty = False

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str], avg_dl: float) -> float:
        doc_len = len(doc_tokens)
        doc_counter = Counter(doc_tokens)

        score = 0.0
        for token in query_tokens:
            if token in doc_counter:
                tf = doc_counter[token]
                idf = self._idf_cache.get(token, 1.0)

                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_dl)
                score += idf * numerator / denominator

        return score

    def search_bm25(self, query: str, top_k: int) -> list[RagDoc]:
        try:
            self._ensure_idf_ready()
            query_tokens = self._tokenize(query)
            
            cur = self.conn.cursor()
            # 获取所有文档
            rows = cur.execute("SELECT doc_id, title, content, source, question_no, section FROM rag_docs").fetchall()

            if not rows:
                return []

            # 计算平均文档长度
            all_doc_tokens = [self._tokenize(content) for _, _, content, _, _, _ in rows]
            avg_dl = sum(len(tokens) for tokens in all_doc_tokens) / len(all_doc_tokens) if all_doc_tokens else 1

            # 计算每个文档的BM25分数
            doc_scores = []
            for i, (doc_id, title, content, source, q_no, sec) in enumerate(rows):
                doc_tokens = all_doc_tokens[i]
                score = self._bm25_score(query_tokens, doc_tokens, avg_dl)
                doc_scores.append((doc_id, title, content, source, q_no, sec, score))

            # 按分数排序，返回top_k
            doc_scores.sort(key=lambda x: x[6], reverse=True)

            res = []
            for doc_id, title, content, source, q_no, sec, score in doc_scores[:top_k]:
                if score > 0:
                    res.append(RagDoc(
                        doc_id=doc_id,
                        title=title,
                        content=content,
                        source=source,
                        question_no=q_no or "",
                        section=sec or "",
                        score=score
                    ))

            return res
        except Exception as e:
            logger.error(f"BM25检索失败: {e}")
            return []

    def search_hybrid(self, query: str, query_emb: list[float], top_k: int, threshold: float,
                     vector_weight: float = 0.7, bm25_weight: float = 0.3) -> list[RagDoc]:
        try:
            vector_results = self.search_vector(query_emb, top_k * 2, threshold)

            bm25_results = self.search_bm25(query, top_k * 2)

            doc_scores = {}

            for doc in vector_results:
                doc_scores[doc.doc_id] = {
                    'doc': doc,
                    'vector_score': doc.score,
                    'bm25_score': 0
                }

            for doc in bm25_results:
                if doc.doc_id in doc_scores:
                    doc_scores[doc.doc_id]['bm25_score'] = doc.score
                else:
                    doc_scores[doc.doc_id] = {
                        'doc': doc,
                        'vector_score': 0,
                        'bm25_score': doc.score
                    }

            max_bm25 = max((v['bm25_score'] for v in doc_scores.values()), default=0)

            final_results = []
            for doc_id, scores in doc_scores.items():
                vector_norm = scores['vector_score']
                bm25_norm = scores['bm25_score'] / max_bm25 if max_bm25 > 0 else 0

                total_score = vector_weight * vector_norm + bm25_weight * bm25_norm

                # 阈值判定：任一路强命中即可放行，避免单一权重通道被阈值整体滤除（T4.1）
                if total_score >= threshold or vector_norm >= threshold or bm25_norm >= threshold:
                    doc = scores['doc']
                    doc.score = total_score
                    final_results.append(doc)

            final_results.sort(key=lambda x: x.score, reverse=True)

            return final_results[:top_k]
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return self.search_vector(query_emb, top_k, threshold)

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")