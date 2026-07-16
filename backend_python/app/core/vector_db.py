#新增底层向量库封装
import sqlite3
import numpy as np
import math
from collections import Counter
from app.core.config import settings
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

class VectorDB:
    def __init__(self):
        self.db_path = settings.sqlite_db_path
        self.conn = self._get_conn()
        self._init_table()
        # BM25参数
        self.k1 = 1.5
        self.b = 0.75

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
            source TEXT
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

    def insert_chunk(self, title: str, content: str, source: str, embedding: list[float]) -> int:
        """写入分块文本+向量｜离线入库阶段 0001"""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
                (title, content, source)
            )
            doc_id = cur.lastrowid
            vec_bin = np.array(embedding, dtype=np.float32).tobytes()
            cur.execute(
                "INSERT INTO rag_vectors(doc_id, embedding) VALUES (?, ?)",
                (doc_id, vec_bin)
            )
            self.conn.commit()
            return doc_id
        except Exception as e:
            logger.error(f"插入文档失败: {e}")
            self.conn.rollback()
            raise Exception(f"文档入库失败: {str(e)}")

    def search_vector(self, query_emb: list[float], top_k: int, threshold: float) -> list[RagDoc]:
        """稠密向量检索｜0004密集检索"""
        try:
            if HAS_SQLITE_VEC:
                # 使用sqlite-vec进行向量检索
                vec_bin = np.array(query_emb, dtype=np.float32).tobytes()
                cur = self.conn.cursor()
                rows = cur.execute("""
                    SELECT d.doc_id, d.title, d.content, d.source, distance
                    FROM rag_vectors v
                    JOIN rag_docs d ON v.doc_id = d.doc_id
                    WHERE embedding MATCH ? AND k = ?
                """, (vec_bin, top_k)).fetchall()
                res = []
                for doc_id, title, content, src, dist in rows:
                    sim_score = 1 - dist  # 欧式距离转相似度
                    if sim_score >= threshold:
                        res.append(RagDoc(doc_id=doc_id, title=title, content=content, source=src, score=sim_score))
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
                        "SELECT title, content, source FROM rag_docs WHERE doc_id = ?",
                        (doc_id,)
                    ).fetchone()
                    if doc_row:
                        res.append(RagDoc(
                            doc_id=doc_id,
                            title=doc_row[0],
                            content=doc_row[1],
                            source=doc_row[2],
                            score=score
                        ))
                return res
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    def _tokenize(self, text: str) -> list[str]:
        """简单的中文分词｜按字符和常见词分割"""
        import re
        # 简单分词：按标点和空格分割，同时保留单个字符
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', text)
        return tokens

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str], avg_dl: float) -> float:
        """计算单个文档的BM25分数"""
        doc_len = len(doc_tokens)
        doc_counter = Counter(doc_tokens)
        
        score = 0.0
        for token in query_tokens:
            if token in doc_counter:
                tf = doc_counter[token]
                # IDF计算
                # 这里简化处理，实际应该从数据库统计
                idf = 1.0  # 占位，后面会优化
                
                # BM25公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_dl)
                score += idf * numerator / denominator
        
        return score

    def search_bm25(self, query: str, top_k: int) -> list[RagDoc]:
        """BM25稀疏检索｜关键词匹配"""
        try:
            query_tokens = self._tokenize(query)
            
            cur = self.conn.cursor()
            # 获取所有文档
            rows = cur.execute("SELECT doc_id, title, content, source FROM rag_docs").fetchall()
            
            if not rows:
                return []
            
            # 计算平均文档长度
            all_doc_tokens = [self._tokenize(content) for _, _, content, _ in rows]
            avg_dl = sum(len(tokens) for tokens in all_doc_tokens) / len(all_doc_tokens) if all_doc_tokens else 1
            
            # 计算每个文档的BM25分数
            doc_scores = []
            for i, (doc_id, title, content, source) in enumerate(rows):
                doc_tokens = all_doc_tokens[i]
                score = self._bm25_score(query_tokens, doc_tokens, avg_dl)
                doc_scores.append((doc_id, title, content, source, score))
            
            # 按分数排序，返回top_k
            doc_scores.sort(key=lambda x: x[4], reverse=True)
            
            res = []
            for doc_id, title, content, source, score in doc_scores[:top_k]:
                if score > 0:
                    res.append(RagDoc(
                        doc_id=doc_id,
                        title=title,
                        content=content,
                        source=source,
                        score=score
                    ))
            
            return res
        except Exception as e:
            logger.error(f"BM25检索失败: {e}")
            return []

    def search_hybrid(self, query: str, query_emb: list[float], top_k: int, threshold: float, 
                     vector_weight: float = 0.7, bm25_weight: float = 0.3) -> list[RagDoc]:
        """混合检索｜结合向量检索和BM25检索"""
        try:
            # 向量检索
            vector_results = self.search_vector(query_emb, top_k * 2, threshold)
            
            # BM25检索
            bm25_results = self.search_bm25(query, top_k * 2)
            
            # 合并结果，使用加权分数
            doc_scores = {}
            
            # 处理向量检索结果
            for doc in vector_results:
                doc_scores[doc.doc_id] = {
                    'doc': doc,
                    'vector_score': doc.score,
                    'bm25_score': 0
                }
            
            # 处理BM25结果
            for doc in bm25_results:
                if doc.doc_id in doc_scores:
                    doc_scores[doc.doc_id]['bm25_score'] = doc.score
                else:
                    doc_scores[doc.doc_id] = {
                        'doc': doc,
                        'vector_score': 0,
                        'bm25_score': doc.score
                    }
            
            # 计算加权总分
            final_results = []
            for doc_id, scores in doc_scores.items():
                # 归一化分数
                vector_norm = scores['vector_score']
                bm25_norm = scores['bm25_score'] / 10 if scores['bm25_score'] > 0 else 0  # 简单归一化
                
                total_score = vector_weight * vector_norm + bm25_weight * bm25_norm
                
                if total_score >= threshold:
                    doc = scores['doc']
                    doc.score = total_score
                    final_results.append(doc)
            
            # 按总分排序
            final_results.sort(key=lambda x: x.score, reverse=True)
            
            return final_results[:top_k]
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            # 降级到纯向量检索
            return self.search_vector(query_emb, top_k, threshold)

# 全局单例（0008连接复用优化）
vector_db = VectorDB()