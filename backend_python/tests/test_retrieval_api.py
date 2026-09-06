"""
retrieval_api 检索接口测试
覆盖 /retrieval/retrieve 与 /retrieval/chunks/preview。
关键回归：RagService.retrieve_by_question 是 async，路由必须 await（曾因漏 await 报
"'coroutine' object has no attribute 'docs'"），本测试用 async mock 断言响应正确展开。
"""
import pytest
from fastapi.testclient import TestClient


class _RagDoc:
    def __init__(self, doc_id, title, content, source):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.source = source
        self.score = 0.9


@pytest.fixture
def mock_rag_service(mocker):
    svc = mocker.MagicMock()
    svc.retrieve_by_question = mocker.AsyncMock()

    class _FakeMetrics:
        def model_dump(self):
            return {"recall": 1.0}

    class _FakeResult:
        question = "q"
        docs = [_RagDoc(1, "t1", "c1", "s1"), _RagDoc(2, "t2", "c2", "s2")]
        metrics = _FakeMetrics()

    svc.retrieve_by_question.return_value = _FakeResult()
    return svc


@pytest.fixture
def mock_chunking_service():
    from unittest.mock import MagicMock

    svc = MagicMock()
    svc.split.return_value = ["c1", "c2"]
    return svc


@pytest.fixture
def client(mock_rag_service, mock_chunking_service):
    from app.main import app
    from app.main import get_rag_service, get_chunking_service

    app.dependency_overrides.clear()
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    app.dependency_overrides[get_chunking_service] = lambda: mock_chunking_service
    return TestClient(app)


class TestRetrieveAPI:
    def test_retrieve_awaits_async_service(self, client):
        """回归：漏 await 时 async mock 返回 coroutine，docs 访问会 TypeError → 500"""
        resp = client.post("/retrieval/retrieve", json={"question": "JVM 内存模型"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"] == "q"
        assert len(data["docs"]) == 2
        assert data["docs"][0]["title"] == "t1"
        assert data["metrics"]["recall"] == 1.0

    def test_retrieve_uses_request_params(self, client, mock_rag_service):
        client.post("/retrieval/retrieve", json={
            "question": "q", "use_hybrid": False, "use_rerank": False,
        })
        args, _ = mock_rag_service.retrieve_by_question.call_args
        assert args[0] == "q"
        assert args[1] is False
        assert args[2] is False

    def test_chunks_preview(self, client):
        resp = client.post("/retrieval/chunks/preview", json={
            "text": "hello world", "chunk_size": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_chunks"] == 2
        assert data["avg_length"] > 0