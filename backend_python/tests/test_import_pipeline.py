"""
import_document 幂等入库管道测试（P3 T3.1/T3.2/T3.3/T3.4）
使用临时 SQLite，mock Embedding，验证：全量入库 / 幂等跳过 / 变更替换 / 失败回滚 / 自检。
"""
import os
import tempfile
import uuid
import pytest


@pytest.fixture
def temp_db():
    path = os.path.join(tempfile.gettempdir(), f"import_test_{uuid.uuid4().hex}.db")
    yield path
    if os.path.exists(path):
        os.remove(path)


def _write_question_bank(path, question="什么是JVM？", answer="JVM是Java虚拟机。",
                         q_no="1", title="Java基础面试题", question2=None):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"## 题目{q_no}：{question}\n\n")
        f.write(f"**问题：** {question}\n\n")
        f.write(f"**标准答案：** {answer}\n\n")
        f.write("**评估要点：** 核心原理、应用场景。\n\n")
        if question2:
            f.write(f"## 题目{int(q_no) + 1}：{question2}\n\n")
            f.write(f"**问题：** {question2}\n\n")
            f.write("**标准答案：** 第二个问题的答案。\n\n")
            f.write("**评估要点：** 扩展知识。\n\n")


@pytest.fixture
def services(temp_db, mocker):
    """注入临时 VectorDB + mock Embedding 的 KnowledgeService"""
    from app.core.vector_db import VectorDB
    from app.services.chunking_service import ChunkingService
    from app.services.embedding_service import EmbeddingService
    from app.services.knowledge_service import KnowledgeService

    mocker.patch("app.services.embedding_service.EmbeddingService.get_embedding",
                 return_value=[0.1] * 1024)
    db = VectorDB(db_path=temp_db)
    svc = KnowledgeService(
        vector_db=db,
        chunking_service=ChunkingService(chunk_size=200, chunk_overlap=0),
        embedding_service=EmbeddingService(cache_file=os.path.join(tempfile.gettempdir(), "import_test_cache.json")),
    )
    yield svc
    svc.close()


class TestImportNewDocument:
    """T3.1 新文件全量入库 + T3.3 入库报告"""

    def test_import_new_document(self, services, tmp_path):
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))

        report = services.import_document(str(doc))

        assert report.status == "imported"
        assert report.question_count == 1
        assert report.chunk_count >= 1
        assert report.vector_count == report.chunk_count
        assert report.self_check == "passed"
        assert report.error == ""

        stats = services.get_stats()
        assert stats["total_documents"] == report.chunk_count
        assert stats["total_vectors"] == report.vector_count

    def test_import_two_questions(self, services, tmp_path):
        doc = tmp_path / "Java集合面试题.md"
        _write_question_bank(str(doc), question="HashMap原理？", q_no="1",
                             question2="ArrayList和LinkedList区别？")

        report = services.import_document(str(doc))

        assert report.question_count == 2
        assert report.chunk_count == 2
        assert services.get_stats()["total_documents"] == 2


class TestIdempotentImport:
    """T3.1 幂等：未变更跳过，变更替换，stats 不翻倍"""

    def test_unchanged_reimport_skips(self, services, tmp_path):
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))

        r1 = services.import_document(str(doc))
        r2 = services.import_document(str(doc))

        assert r2.status == "skipped"
        assert services.get_stats()["total_documents"] == r1.chunk_count

    def test_changed_file_replaces_chunks(self, services, tmp_path):
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc), question="什么是JVM？", q_no="1")
        r1 = services.import_document(str(doc))

        _write_question_bank(str(doc), question="什么是JVM？", q_no="1",
                             question2="什么是垃圾回收？")
        r2 = services.import_document(str(doc))

        assert r2.status == "updated"
        assert r2.question_count == 2
        stats = services.get_stats()
        assert stats["total_documents"] == r2.chunk_count
        titles = [row[0] for row in services.vector_db.conn.execute(
            "SELECT title FROM rag_docs WHERE source = ?", (doc.name,)
        ).fetchall()]
        assert any("题2" in t for t in titles)


class TestRollbackOnFailure:
    """T3.1 入库失败回滚"""

    def test_embedding_failure_rolls_back_new_file(self, services, tmp_path, mocker):
        from app.core.exceptions import EmbeddingError
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))

        def boom(text):
            raise EmbeddingError("embedding 服务不可用")

        mocker.patch("app.services.embedding_service.EmbeddingService.get_embedding", side_effect=boom)
        report = services.import_document(str(doc))

        assert report.status == "failed"
        assert services.get_stats()["total_documents"] == 0
        assert services.get_stats()["total_vectors"] == 0

    def test_embedding_failure_keeps_old_chunks(self, services, tmp_path, mocker):
        from app.core.exceptions import EmbeddingError
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))
        r1 = services.import_document(str(doc))

        # 修改文件后再导入，但 embedding 抛错
        _write_question_bank(str(doc), question="什么是JVM？", q_no="1",
                             question2="什么是垃圾回收？")
        mocker.patch("app.services.embedding_service.EmbeddingService.get_embedding",
                     side_effect=EmbeddingError("失败"))
        r2 = services.import_document(str(doc))

        assert r2.status == "failed"
        stats = services.get_stats()
        assert stats["total_documents"] == r1.chunk_count  # 旧分块保留
        assert stats["total_vectors"] == r1.vector_count

    def test_replace_phase_failure_restores_old_chunks(self, services, tmp_path, mocker):
        """蓝绿切换阶段失败（新块已插、旧块已删）→ 回滚恢复旧分块与旧指纹"""
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))
        r1 = services.import_document(str(doc))

        # 修改文件后再导入，指纹写入阶段抛错（首次调用抛错，回滚内的恢复调用正常）
        _write_question_bank(str(doc), question="什么是JVM？", q_no="1",
                             question2="什么是垃圾回收？")
        call_count = {"n": 0}
        def flaky_fp(source, fingerprint):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("磁盘写入失败")
        mocker.patch.object(services.vector_db, "upsert_file_fingerprint", side_effect=flaky_fp)
        r2 = services.import_document(str(doc))

        assert r2.status == "failed"
        stats = services.get_stats()
        assert stats["total_documents"] == r1.chunk_count  # 旧分块恢复
        assert stats["total_vectors"] == r1.vector_count
        assert services.vector_db.file_fingerprint("Java基础面试题.md") is not None


class TestSelfCheck:
    """T3.4 自检：stats 对账 + 抽样检索自测"""

    def test_self_check_reports_passed(self, services, tmp_path):
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc), question="HashMap底层原理？",
                             answer="基于数组加链表和红黑树。")

        report = services.import_document(str(doc))

        assert report.self_check == "passed"

    def test_self_check_failure_rolls_back(self, services, tmp_path, mocker):
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc), question="HashMap底层原理？")

        # 使检索永远失败 → 自检不通过
        mocker.patch.object(services.vector_db, "search_bm25", return_value=[])
        report = services.import_document(str(doc))

        assert report.status == "failed"
        assert services.get_stats()["total_documents"] == 0

    def test_empty_question_bank_reports_empty(self, services, tmp_path):
        """解析出 0 题：不静默通过，自检状态为 empty"""
        doc = tmp_path / "无题目参考.md"
        with open(doc, "w", encoding="utf-8") as f:
            f.write("# 参考文档\n\n这段文本没有任何题目格式。\n")

        report = services.import_document(str(doc))

        assert report.self_check == "empty"
        assert report.chunk_count == 0
        assert report.question_count == 0


class TestP5LifecycleRegression:
    """P5 验收回归：clear 后可恢复重导、0 题文件不残留指纹"""

    def test_clear_then_reimport_is_imported(self, services, tmp_path):
        """clear_all 后重导同文件应为 imported（指纹已随清库清除）"""
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))

        assert services.import_document(str(doc)).status == "imported"
        services.clear_all()
        assert services.import_document(str(doc)).status == "imported"

    def test_empty_bank_leaves_no_fingerprint(self, services, tmp_path):
        """0 题文件：不入库且不残留指纹，内容补上题目后可重新入库"""
        doc = tmp_path / "无题目参考.md"
        with open(doc, "w", encoding="utf-8") as f:
            f.write("# 参考文档\n\n这段文本没有任何题目格式。\n")

        r1 = services.import_document(str(doc))
        assert r1.self_check == "empty"
        assert services.vector_db.file_fingerprint(doc.name) is None

        _write_question_bank(str(doc))
        assert services.import_document(str(doc)).status == "imported"


class TestAsyncCompat:
    """asyncio 兼容：已在事件循环内调用 import_document 不抛 RuntimeError"""

    def test_embedding_async_inside_running_loop(self, services, tmp_path, mocker):
        import asyncio
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))

        async def fake_embedding(text):
            return [0.1] * 1024

        mocker.patch("app.services.embedding_service.EmbeddingService.get_embedding",
                     side_effect=fake_embedding)

        async def run():
            return services.import_document(str(doc))

        report = asyncio.run(run())

        assert report.status == "imported"
        assert report.self_check == "passed"


class TestDocumentLifecycle:
    """T3.2 文档级生命周期：删除 / 目录对账"""

    def test_delete_document_removes_chunks(self, services, tmp_path):
        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))
        services.import_document(str(doc))
        assert services.get_stats()["total_documents"] >= 1

        ok = services.delete_document("Java基础面试题.md")

        assert ok is True
        assert services.get_stats()["total_documents"] == 0
        assert services.vector_db.file_fingerprint("Java基础面试题.md") is None

    def test_reconcile_removes_missing_file_chunks(self, services, tmp_path):
        doc1 = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc1))
        doc2 = tmp_path / "Python基础面试题.md"
        _write_question_bank(str(doc2), question="什么是GIL？", title="Python基础面试题")
        services.import_document(str(doc1))
        services.import_document(str(doc2))
        total_before = services.get_stats()["total_documents"]
        assert total_before >= 2

        # 磁盘上删除 doc1 后对账
        os.remove(str(doc1))
        removed = services.reconcile_directory(str(tmp_path))

        assert removed >= 1
        assert services.vector_db.file_fingerprint("Java基础面试题.md") is None
        assert services.get_stats()["total_documents"] == total_before - 1


class TestAgentTools:
    """T3.4 Agent 工具化：RagMCP 暴露入库/删除工具"""

    def test_rag_mcp_import_document(self, services, tmp_path, mocker):
        from app.services.rag_mcp import RagMCP
        mcp = RagMCP(rag_service=mocker.Mock(), prompt_service=mocker.Mock())
        mcp._knowledge_service = services

        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))
        report = mcp.import_document(str(doc))

        assert report.status == "imported"
        assert report.self_check == "passed"

    def test_rag_mcp_delete_document(self, services, tmp_path, mocker):
        from app.services.rag_mcp import RagMCP
        mcp = RagMCP(rag_service=mocker.Mock(), prompt_service=mocker.Mock())
        mcp._knowledge_service = services

        doc = tmp_path / "Java基础面试题.md"
        _write_question_bank(str(doc))
        mcp.import_document(str(doc))
        assert mcp.delete_document("Java基础面试题.md") is True
        assert services.get_stats()["total_documents"] == 0
