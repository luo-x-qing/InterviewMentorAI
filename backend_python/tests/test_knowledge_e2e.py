"""
知识库导入 → 检索 端到端集成测试

使用临时 SQLite，验证完整的「文档分块 → 向量化 → 混合检索 → 重排 → MCP 组装」跨模块链路。
不依赖外部 API：Embedding 使用 mock 固定向量，LLM 链路不参与。

> 原本基于旧版 `batch_import_knowledge` / 旧 `LlmClient` 构造（已删除）而整体 skip。
> 迁移至新单入口 `KnowledgeService.import_document`（幂等 + 自检），与
> `test_import_pipeline.py`（逐分支单测）互补：本文覆盖「多模块协作」的端到端路径。
"""
import os
import tempfile
import uuid

import pytest


@pytest.fixture
def temp_db():
    """临时 SQLite 数据库路径，测试后自动清理"""
    path = os.path.join(tempfile.gettempdir(), f"e2e_test_{uuid.uuid4().hex}.db")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_doc_dir():
    """临时知识库文档目录，含标准题目格式的 Markdown 文件"""
    with tempfile.TemporaryDirectory() as d:
        doc1 = os.path.join(d, "Java基础面试题.md")
        with open(doc1, "w", encoding="utf-8") as f:
            f.write("# Java 基础面试题\n\n")
            f.write("## 题目1：什么是JVM？\n\n")
            f.write("**问题：** 什么是JVM？\n\n")
            f.write("**标准答案：** JVM（Java Virtual Machine）是运行 Java 字节码的虚拟机，"
                    "提供内存管理、垃圾回收等功能。\n\n")
            f.write("**评估要点：** 核心原理、内存模型。\n\n")
            f.write("## 题目2：String 和 StringBuilder 的区别\n\n")
            f.write("**问题：** String 和 StringBuilder 的区别\n\n")
            f.write("**标准答案：** String 是不可变对象，每次修改都会创建新对象；"
                    "StringBuilder 是可变的，适合频繁字符串拼接。\n\n")
            f.write("**评估要点：** 不可变性、性能。\n\n")

        doc2 = os.path.join(d, "Python基础面试题.md")
        with open(doc2, "w", encoding="utf-8") as f:
            f.write("# Python 基础面试题\n\n")
            f.write("## 题目1：什么是GIL？\n\n")
            f.write("**问题：** 什么是GIL？\n\n")
            f.write("**标准答案：** GIL（Global Interpreter Lock）是 CPython 中的全局解释器锁，"
                    "保证同一时刻只有一个线程执行字节码。\n\n")
            f.write("**评估要点：** 并发模型。\n\n")

        yield d


@pytest.fixture
def services(temp_db, mocker):
    """构建完整服务链（VectorDB + Knowledge + Rag + Reranker），mock Embedding"""
    from app.core.vector_db import VectorDB
    from app.services.chunking_service import ChunkingService
    from app.services.embedding_service import EmbeddingService
    from app.services.reranker_service import RerankerService
    from app.services.rag_service import RagService
    from app.services.knowledge_service import KnowledgeService

    mocker.patch("app.services.embedding_service.EmbeddingService.get_embedding",
                 return_value=[0.1] * 1024)
    db = VectorDB(db_path=temp_db)
    embedding = EmbeddingService(cache_file=os.path.join(tempfile.gettempdir(), "e2e_embed_cache.json"))
    reranker = RerankerService()
    rag = RagService(vector_db=db, embedding_service=embedding, reranker_service=reranker)
    knowledge = KnowledgeService(
        vector_db=db,
        chunking_service=ChunkingService(chunk_size=200, chunk_overlap=50),
        embedding_service=embedding,
    )

    yield {
        "vector_db": db,
        "rag": rag,
        "knowledge": knowledge,
    }

    db.close()


class TestKnowledgeE2E:
    """知识库端到端测试：导入 → 检索 → 重排 → 统计 → 清空重导"""

    def _import_all(self, services, temp_doc_dir):
        for f in ("Java基础面试题.md", "Python基础面试题.md"):
            services["knowledge"].import_document(os.path.join(temp_doc_dir, f))

    def test_full_import_and_stats(self, services, temp_doc_dir):
        """E2E-1: import_document 全量入库 → 分块/向量/指纹一致"""
        knowledge, vector_db = services["knowledge"], services["vector_db"]
        self._import_all(services, temp_doc_dir)

        stats = knowledge.get_stats()
        assert stats["total_documents"] > 0
        assert stats["total_vectors"] == stats["total_documents"]
        assert len(stats["source_files"]) == 2
        for sf in stats["source_files"]:
            assert "filename" in sf and "chunk_count" in sf

    def test_import_is_idempotent(self, services, temp_doc_dir):
        """E2E-1b: 同文件重复导入 → skipped，数量不翻倍"""
        knowledge = services["knowledge"]
        self._import_all(services, temp_doc_dir)
        before = knowledge.get_stats()["total_documents"]

        r = services["knowledge"].import_document(
            os.path.join(temp_doc_dir, "Java基础面试题.md"))
        assert r.status == "skipped"
        assert knowledge.get_stats()["total_documents"] == before

    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, services, temp_doc_dir):
        """E2E-2: 混合检索（向量 + BM25） → 返回相关文档"""
        self._import_all(services, temp_doc_dir)
        result = await services["rag"].retrieve_by_question(
            "什么是JVM", use_hybrid=True, use_rerank=False)
        docs = result.docs

        assert len(docs) > 0
        assert all(getattr(r, "score", None) is not None for r in docs)
        top_content = " ".join(r.content for r in docs)
        assert "JVM" in top_content, f"检索结果应包含 JVM 相关内容: {top_content[:100]}"

    @pytest.mark.asyncio
    async def test_reranked_retrieval(self, services, temp_doc_dir):
        """E2E-3: 混合检索 ± 重排 → 均返回结果（重排改变排序而非数量）"""
        self._import_all(services, temp_doc_dir)
        no_rerank = (await services["rag"].retrieve_by_question(
            "String 和 StringBuilder", use_hybrid=True, use_rerank=False)).docs
        reranked = (await services["rag"].retrieve_by_question(
            "String 和 StringBuilder", use_hybrid=True, use_rerank=True)).docs

        assert len(no_rerank) > 0
        assert len(reranked) > 0
        # 注：mock 固定向量下所有块得分相同，重排不改变相对顺序，这里只保证两条路径都可用。

    def test_clear_and_reimport(self, services, temp_doc_dir):
        """E2E-4: 清空后重导同文件 → 重新入库（非 skipped），数量与首次一致"""
        knowledge, vector_db = services["knowledge"], services["vector_db"]
        self._import_all(services, temp_doc_dir)
        count1 = knowledge.get_stats()["total_documents"]

        knowledge.clear_all()
        assert vector_db.conn.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0] == 0

        self._import_all(services, temp_doc_dir)
        count2 = knowledge.get_stats()["total_documents"]
        assert count2 == count1
