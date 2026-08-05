"""
知识库管理服务
提供知识库统计、清空、批量导入等管理功能
"""
import os
import asyncio
import threading
import logging
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.vector_db import VectorDB
from app.models.schemas import ImportReport
from app.services.cleaning_service import CleaningService

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库管理服务"""
    
    def __init__(self, vector_db=None, chunking_service=None, embedding_service=None):
        # 依赖注入
        if vector_db is None:
            from app.core.vector_db import VectorDB
            self.vector_db = VectorDB()
        else:
            self.vector_db = vector_db
        
        if chunking_service is None:
            from app.services.chunking_service import ChunkingService
            self.chunking_service = ChunkingService()
        else:
            self.chunking_service = chunking_service
        
        if embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()
        else:
            self.embedding_service = embedding_service
    
    def import_document(self, file_path: str, max_chunk_size: Optional[int] = None) -> ImportReport:
        """单入口入库管道：清洗→解析→切面→向量化→落库→自检（ADR-0002 D2/D3/D5）

        幂等语义：指纹相同跳过、指纹变更蓝绿替换、失败/自检不过回滚。
        HTTP 与 Agent 工具共用此入口。
        """
        path = os.path.abspath(file_path)
        source = os.path.basename(path)
        if not os.path.exists(path):
            return ImportReport(path=path, status="failed", error="文件不存在")
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            return ImportReport(path=path, status="failed", error=f"读取文件失败: {e}")

        fp = CleaningService.fingerprint(raw)
        old_fp = self.vector_db.file_fingerprint(source)
        # 幂等：指纹相同则跳过（D3）
        if old_fp == fp:
            return ImportReport(path=path, status="skipped",
                                deduplicated_count=1, self_check="passed")

        # 清洗 → 解析 → 结构化切面
        cleaner = CleaningService()
        questions = cleaner.parse_questions(cleaner.clean_text(raw), source=source)
        chunks = self.chunking_service.chunk_questions(questions, max_chunk_size)

        # 记录旧分块以便失败回滚（蓝绿替换：先新后旧，只删旧 doc_id）
        old_docs = self.vector_db.list_docs_by_source(source)
        old_ids = self.vector_db.list_doc_ids_by_source(source)

        new_doc_ids = []
        switching = False
        try:
            for chunk in chunks:
                emb = self._resolve_embedding(self.embedding_service.get_embedding(chunk.content))
                doc_id = self.vector_db.insert_chunk(
                    chunk.title, chunk.content, chunk.source, emb,
                    question_no=chunk.question_no, section=chunk.section,
                )
                new_doc_ids.append(doc_id)
            # 蓝绿切换与指纹更新同样纳入失败回滚（D3）：任一失败 → 恢复旧分块与旧指纹
            switching = True
            for old_id in old_ids:
                self.vector_db.delete_doc_by_id(old_id)
            self.vector_db.upsert_file_fingerprint(source, fp)
            self.embedding_service._save_cache()
        except Exception as e:
            if switching:
                self._rollback_replace(source, old_fp, old_docs)
            else:
                self._rollback_inserted(new_doc_ids)
            logger.error(f"入库题库 {source} 失败并回滚: {e}")
            return ImportReport(path=path, status="failed",
                                question_count=len(questions),
                                chunk_count=len(chunks), error=str(e))

        status = "updated" if old_fp is not None else "imported"
        report = ImportReport(path=path, status=status,
                              question_count=len(questions),
                              chunk_count=len(chunks),
                              vector_count=len(new_doc_ids),
                              deduplicated_count=self._count_duplicated_questions(questions))

        # 自检闭环（D5）：stats 对账 + 抽样检索自测
        if not questions:
            # 0 题不入库：回滚指纹，避免空库指纹残留导致后续重导被跳过（P5 验收修复）
            if old_fp is not None:
                self.vector_db.upsert_file_fingerprint(source, old_fp)
            else:
                self.vector_db.delete_file_index(source)
            report.self_check = "empty"
            report.error = "未识别到题目，内容未入库"
            logger.warning(f"入库题库 {source} 未识别到题目，自检状态 empty")
            return report
        if not self._self_check(source, chunks):
            self._rollback_replace(source, old_fp, old_docs)
            report.status = "failed"
            report.self_check = "failed"
            report.error = "自检未通过：stats 对账或抽样检索失败"
            logger.error(f"入库题库 {source} 自检未通过，已回滚")
            return report

        report.self_check = "passed"
        logger.info(f"入库完成 {source}：{report.question_count} 题 / {report.chunk_count} 块，状态={report.status}")
        return report

    @staticmethod
    def _count_duplicated_questions(questions: list) -> int:
        """统计文件内题目级重复数（入库报告用，T3.3）"""
        seen, dup = set(), 0
        for q in questions:
            key = CleaningService.fingerprint(f"{q.title}\n{q.question}")
            if key in seen:
                dup += 1
            seen.add(key)
        return dup

    def _rollback_inserted(self, new_doc_ids: list[int]) -> None:
        """删除本次已插入的新分块（回滚）"""
        for doc_id in new_doc_ids:
            self.vector_db.delete_doc_by_id(doc_id)

    def _rollback_replace(self, source: str, old_fp: Optional[str], old_docs: list) -> None:
        """蓝绿替换/自检失败回滚：清空该题库现有块 → 恢复旧分块与旧指纹"""
        self.vector_db.delete_docs_by_source(source)
        for doc in old_docs:
            try:
                emb = self._resolve_embedding(self.embedding_service.get_embedding(doc["content"]))
            except Exception:
                emb = [0.0] * VectorDB.VECTOR_DIM
            self.vector_db.insert_chunk(doc["title"], doc["content"], source, emb,
                                        question_no=doc["question_no"],
                                        section=doc["section"])
        if old_fp is not None:
            self.vector_db.upsert_file_fingerprint(source, old_fp)
        else:
            self.vector_db.delete_file_index(source)

    @staticmethod
    def _resolve_embedding(result):
        """兼容 async embedding（真实）与同步返回（测试 mock）

        已在事件循环内调用时（FastAPI/Agent async 上下文）另起线程执行，
        避免 asyncio.run 在运行中的循环里抛 RuntimeError。
        """
        if not asyncio.iscoroutine(result):
            return result
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(result)
        box = {}
        def _run():
            box["value"] = asyncio.run(result)
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join()
        return box["value"]

    def _self_check(self, source: str, chunks: list) -> bool:
        """自检（D5）：题目数/分块数/向量数对账 + 抽样检索自测"""
        try:
            if self.vector_db.count_docs_by_source(source) != len(chunks):
                return False
            if self.vector_db.count_vectors_by_source(source) != len(chunks):
                return False
            expected_questions = len({c.question_no for c in chunks if c.question_no})
            if expected_questions and self.vector_db.count_questions_by_source(source) != expected_questions:
                return False
            for chunk in chunks[:2]:
                probe = chunk.content[:60]
                results = self.vector_db.search_bm25(probe, top_k=5)
                if not any(r.source == source for r in results):
                    return False
            return True
        except Exception as e:
            logger.error(f"自检异常: {e}")
            return False

    def delete_document(self, source: str) -> bool:
        """删除某来源题库的全部分块与指纹（T3.2 文档级生命周期）"""
        self.vector_db.delete_docs_by_source(source)
        self.vector_db.delete_file_index(source)
        logger.info(f"已删除题库 {source}")
        return True

    def reconcile_directory(self, root: Optional[str] = None) -> int:
        """目录对账（D3）：删除已从磁盘目录消失文件的旧分块与指纹

        Returns:
            清理的文档数
        """
        root = root or settings.rag_doc_root
        if not os.path.isdir(root):
            return 0
        indexed = self.vector_db.indexed_sources()
        removed = 0
        for source in indexed:
            exists = any(
                os.path.basename(p) == source
                for dirpath, _, filenames in os.walk(root)
                for p in (os.path.join(dirpath, fn) for fn in filenames)
            )
            if not exists:
                self.delete_document(source)
                removed += 1
        if removed:
            logger.info(f"目录对账完成，清理 {removed} 个已消失文件的旧分块")
        return removed

    def list_doc_files(self, root: Optional[str] = None) -> List[str]:
        """扫描知识库根目录下的题库文件（MD/TXT），供 API 与离线脚本共享（P5 验收收敛）

        Returns:
            绝对路径列表
        """
        root = root or settings.rag_doc_root
        if not os.path.isdir(root):
            return []
        return [
            os.path.join(dirpath, fn)
            for dirpath, _, filenames in os.walk(root)
            for fn in sorted(filenames)
            if fn.lower().endswith((".md", ".txt"))
        ]
    
    def get_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            包含文档数量、向量数量、来源文件统计的字典
        """
        try:
            return {
                "total_documents": self.vector_db.total_docs(),
                "total_vectors": self.vector_db.total_vectors(),
                "source_files": [
                    {"filename": row[0], "chunk_count": row[1]}
                    for row in self.vector_db.source_grouping()
                ]
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise
    
    def clear_all(self) -> None:
        """
        清空知识库
        """
        try:
            self.vector_db.clear_all()
            logger.info("知识库已清空")
        except Exception as e:
            logger.error(f"清空知识库失败: {e}")
            raise
    
    def close(self):
        """清理资源"""
        self.embedding_service.clear_cache()
        self.vector_db.close()
        logger.info("知识库管理服务资源清理完成")
