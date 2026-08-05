"""
knowledge_api 文档级生命周期接口测试（P5 T5.1）
覆盖：/import 单入口导入 / DELETE {source} 文档级删除 / /reconcile 目录对账 / /stats / /clear。
全部通过 dependency_overrides 注入 mock KnowledgeService，不触碰真实文件系统。
"""
import pytest
from fastapi.testclient import TestClient

from app.models.schemas import ImportReport


@pytest.fixture
def mock_knowledge_service(mocker):
    svc = mocker.MagicMock()
    svc.import_document.return_value = ImportReport(
        path="bank.md", status="imported",
        question_count=2, chunk_count=3, vector_count=3, self_check="passed",
    )
    svc.list_doc_files.return_value = ["bank1.md", "bank2.md"]
    svc.delete_document.return_value = True
    svc.reconcile_directory.return_value = 1
    svc.get_stats.return_value = {
        "total_documents": 3, "total_vectors": 3,
        "source_files": [{"filename": "a.md", "chunk_count": 3}],
    }
    return svc


@pytest.fixture
def client(mock_knowledge_service):
    from app.main import app
    from app.main import get_knowledge_service

    app.dependency_overrides.clear()
    app.dependency_overrides[get_knowledge_service] = lambda: mock_knowledge_service
    return TestClient(app)


class TestImportAPI:
    def test_import_without_paths_scans_rag_root(self, client, mock_knowledge_service):
        resp = client.post("/knowledge/import", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["imported_count"] >= 1
        assert data["reports"][0]["status"] == "imported"
        assert mock_knowledge_service.import_document.call_count >= 1

    def test_import_with_specific_paths(self, client, mock_knowledge_service):
        resp = client.post("/knowledge/import", json={
            "file_paths": ["/data/docs/java_bank.md"],
        })
        assert resp.status_code == 200
        paths = [c.args[0] for c in mock_knowledge_service.import_document.call_args_list]
        assert "/data/docs/java_bank.md" in paths
        assert len(paths) == 1

    def test_import_reports_failure(self, client, mock_knowledge_service):
        mock_knowledge_service.import_document.return_value = ImportReport(
            path="bad.md", status="failed", error="self check failed",
        )
        resp = client.post("/knowledge/import", json={"file_paths": ["bad.md"]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["reports"][0]["status"] == "failed"


class TestDocumentLifecycleAPI:
    def test_delete_document(self, client, mock_knowledge_service):
        resp = client.delete("/knowledge/java_interview.md")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_knowledge_service.delete_document.assert_called_once_with("java_interview.md")

    def test_clear_not_shadowed_by_source_param(self, client, mock_knowledge_service):
        """路由顺序回归：/clear 必须先于 /{source} 声明，否则会被吞成删除"clear" """
        resp = client.delete("/knowledge/clear")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_knowledge_service.clear_all.assert_called_once()
        mock_knowledge_service.delete_document.assert_not_called()

    def test_reconcile_directory(self, client, mock_knowledge_service):
        resp = client.post("/knowledge/reconcile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["removed"] == 1
        mock_knowledge_service.reconcile_directory.assert_called_once()


class TestStatsAndClearAPI:
    def test_stats(self, client, mock_knowledge_service):
        resp = client.get("/knowledge/stats")
        assert resp.status_code == 200
        assert resp.json()["total_documents"] == 3

    def test_clear(self, client, mock_knowledge_service):
        resp = client.delete("/knowledge/clear")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_knowledge_service.clear_all.assert_called_once()
