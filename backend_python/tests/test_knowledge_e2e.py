"""
知识库导入 → 检索 E2E 集成测试

使用临时 SQLite 数据库，验证完整的「文档分块 → 向量化 → 混合检索 → MCP 组装」链路。
不依赖外部 API（LLM/Embedding 调用使用 mock）。

> 待迁移：本文件基于旧版 LlmClient 构造与 batch_import_knowledge（已删除），
> 当前 6 个用例因接口不匹配报 error；新链路单测见 test_import_pipeline.py，
> 端到端演练见 rag_e2e_check.py，迁移完成后应全部改走 import_document 单入口。
"""
import os
import tempfile
import uuid

import pytest


# ── Fixtures ──

@pytest.fixture
def temp_db():
    """临时 SQLite 数据库路径，测试后自动清理"""
    path = os.path.join(tempfile.gettempdir(), f"e2e_test_{uuid.uuid4().hex}.db")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_doc_dir():
    """临时知识库文档目录，含测试用 Markdown 文件"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        # 创建测试文档
        doc1 = os.path.join(d, "Java基础面试题.md")
        with open(doc1, "w", encoding="utf-8") as f:
            f.write("# Java 基础面试题\n\n")
            f.write("## 什么是 JVM？\n\n")
            f.write("JVM（Java Virtual Machine）是运行 Java 字节码的虚拟机。")
            f.write("它是 Java 平台的核心，提供了内存管理、垃圾回收等功能。\n\n")
            f.write("## String 和 StringBuilder 的区别\n\n")
            f.write("String 是不可变对象，每次修改都会创建新对象。")
            f.write("StringBuilder 是可变的，适合频繁字符串拼接操作。\n\n")

        doc2 = os.path.join(d, "Python基础面试题.md")
        with open(doc2, "w", encoding="utf-8") as f:
            f.write("# Python 基础面试题\n\n")
            f.write("## 什么是 GIL？\n\n")
            f.write("GIL（Global Interpreter Lock）是 CPython 中的全局解释器锁。")
            f.write("它保证同一时刻只有一个线程执行 Python 字节码。\n\n")
            f.write("## 列表和元组的区别\n\n")
            f.write("列表（list）是可变的，元组（tuple）是不可变的。")
            f.write("元组可以作为字典的键，列表不可以。\n\n")

        yield d


# ── Services fixture（复用 DI 链，mock LLM/Embedding） ──

@pytest.fixture
def services(temp_db, temp_doc_dir, mocker):
    """构建完整服务链，mock 外部依赖"""
    from app.core.config import Settings

    # 临时配置
    settings = Settings(
        dashscope_api_key="test_key",
        llm_model_name="qwen-plus",
        llm_base_url="https://test.example.com/api",
        sqlite_db_path=temp_db,
        rag_doc_root=temp_doc_dir,
        embedding_model="text-embedding-v3",
        rag_top_k=3,
        rag_similar_threshold=0.01,
        chunk_size=200,
        chunk_overlap=50,
    )

    # Mock OpenAI client
    mock_openai = mocker.patch("app.services.llm_client.AsyncOpenAI")
    mock_client = mock_openai.return_value

    # Mock embedding 返回固定向量
    mocker.patch("app.services.embedding_service.EmbeddingService.get_embedding",
                 return_value=[0.1] * 1024)

    from app.core.vector_db import VectorDB
    from app.services.chunking_service import ChunkingService
    from app.services.embedding_service import EmbeddingService
    from app.services.reranker_service import RerankerService
    from app.services.rag_service import RagService
    from app.services.prompt_service import PromptService
    from app.services.rag_mcp import RagMCP
    from app.services.knowledge_service import KnowledgeService
    from app.services.llm_client import LlmClient

    llm_client = LlmClient(api_key=settings.dashscope_api_key,
                           base_url=settings.llm_base_url,
                           model=settings.llm_model_name)
    vector_db = VectorDB(db_path=temp_db)
    chunking = ChunkingService()
    embedding = EmbeddingService(llm_client=llm_client)
    reranker = RerankerService()
    prompt = PromptService(llm_client=llm_client)
    rag = RagService(vector_db=vector_db, embedding_service=embedding, reranker_service=reranker)
    rag_mcp = RagMCP(rag_service=rag, prompt_service=prompt)
    knowledge = KnowledgeService(vector_db=vector_db, chunking_service=chunking, embedding_service=embedding)

    yield {
        "vector_db": vector_db,
        "chunking": chunking,
        "embedding": embedding,
        "reranker": reranker,
        "rag": rag,
        "rag_mcp": rag_mcp,
        "knowledge": knowledge,
        "settings": settings,
    }

    # 清理
    vector_db.close()


# ── Tests ──

class TestKnowledgeE2E:
    """知识库端到端测试：导入 → 检索 → MCP 上下文组装"""

    def test_full_import_pipeline(self, services):
        """E2E-1: 文档批量导入 → 验证分块和向量化"""
        knowledge = services["knowledge"]
        vector_db = services["vector_db"]

        # 执行导入
        count = knowledge.batch_import_knowledge(chunk_method="paragraph")

        # 验证导入数量 > 0
        assert count > 0, f"应导入至少 1 个分块，实际导入 {count}"

        # 验证数据库中有记录
        doc_count = vector_db.conn.execute(
            "SELECT COUNT(*) FROM rag_docs"
        ).fetchone()[0]
        assert doc_count == count, f"rag_docs 记录数 {doc_count} 应与分块数 {count} 一致"

        # 验证向量表有对应记录
        vec_count = vector_db.conn.execute(
            "SELECT COUNT(*) FROM rag_vectors"
        ).fetchone()[0]
        assert vec_count == count, f"rag_vectors 记录数 {vec_count} 应与分块数 {count} 一致"

    def test_hybrid_retrieval(self, services):
        """E2E-2: 混合检索（向量 + BM25） → 返回相关文档"""
        knowledge = services["knowledge"]
        rag = services["rag"]

        # 先导入
        knowledge.batch_import_knowledge()

        # 检索
        results = rag.retrieve_by_question("什么是 JVM", use_hybrid=True, use_rerank=False)

        assert len(results) > 0, "混合检索应返回至少 1 个结果"
        assert results[0].score is not None, "每个结果应有 score 字段"

        # 最高分文档应包含 "JVM"
        top_content = " ".join([r.content for r in results])
        assert "JVM" in top_content, f"检索结果应包含 JVM 相关内容: {top_content[:100]}"

    def test_reranked_retrieval(self, services):
        """E2E-3: 混合检索 + 重排序 → 结果排序优化"""
        knowledge = services["knowledge"]
        rag = services["rag"]

        knowledge.batch_import_knowledge()

        # 无重排序
        results_no_rerank = rag.retrieve_by_question(
            "String 和 StringBuilder", use_hybrid=True, use_rerank=False
        )
        # 有重排序
        results_reranked = rag.retrieve_by_question(
            "String 和 StringBuilder", use_hybrid=True, use_rerank=True
        )

        assert len(results_no_rerank) > 0
        assert len(results_reranked) > 0
        # 两种模式都应返回结果（重排序改变的是排序，不改变数量）

    def test_mcp_context_assembly(self, services):
        """E2E-4: MCP 上下文组装 → 检索 + 组装 + 截断"""
        knowledge = services["knowledge"]
        rag_mcp = services["rag_mcp"]

        knowledge.batch_import_knowledge()

        # 完整 MCP 链路
        context = rag_mcp.build_rag_context(
            rag_mcp.rag_service.retrieve_by_question(
                "GIL 是什么", use_hybrid=True, use_rerank=False
            )
        )

        assert context is not None
        assert len(context) > 0, "MCP 上下文不应为空"
        assert "GIL" in context, f"上下文应包含 GIL 相关信息: {context[:200]}"

    def test_knowledge_stats(self, services):
        """E2E-5: 导入后统计信息正确"""
        knowledge = services["knowledge"]

        knowledge.batch_import_knowledge()
        stats = knowledge.get_stats()

        assert stats["total_documents"] > 0
        assert stats["total_vectors"] > 0
        assert len(stats["source_files"]) > 0, "应有来源文件统计"

        # 每个来源文件应有文件名和分块数
        for sf in stats["source_files"]:
            assert "filename" in sf
            assert "chunk_count" in sf
            assert sf["chunk_count"] > 0

    def test_clear_and_reimport(self, services):
        """E2E-6: 清空后重新导入 → 数据正确"""
        knowledge = services["knowledge"]
        vector_db = services["vector_db"]

        # 第一次导入
        count1 = knowledge.batch_import_knowledge()
        assert count1 > 0

        # 清空
        knowledge.clear_all()
        after_clear = vector_db.conn.execute(
            "SELECT COUNT(*) FROM rag_docs"
        ).fetchone()[0]
        assert after_clear == 0, "清空后 rag_docs 应为 0"

        # 重新导入
        count2 = knowledge.batch_import_knowledge()
        assert count2 == count1, f"重新导入数量 {count2} 应与首次 {count1} 一致"
