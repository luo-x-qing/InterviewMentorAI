"""POST /research/deep（RAG 反思深度检索，架构 §5.4 / §9.2）端点测试。

轻量装配：不走 app.lifespan（避免拉起向量/LLM 等昂贵基础服务），
仅注入 fake 检索 Agent + research 路由 + 错误契约，验证路由层与编排正确。
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.research_api import router as research_router
from app.core.exceptions import register_error_handlers
from app.models.schemas import RagAnswerResult


class _FakeCandidate:
    def __init__(self, title: str, source: str, full_answer: str):
        self.title = title
        self.source = source
        self.full_answer = full_answer


class _FakeRetrievalAgent:
    def __init__(self, answered: bool = True):
        self.answered = answered
        self.asked: list = []

    async def answer(self, question: str) -> RagAnswerResult:
        self.asked.append(question)
        candidates = []
        if self.answered:
            candidates.append(_FakeCandidate("Java 集合", "题库A", "答案是集合相关完整内容..."))
            candidates.append(_FakeCandidate("Java 集合进阶", "题库B", "补充要点..."))
        return RagAnswerResult(
            question=question,
            candidates=candidates,
            status="answered" if self.answered else "no_match",
            iterations=1,
        )


@pytest.fixture
def client():
    app = FastAPI()
    app.state.retrieval_agent = _FakeRetrievalAgent(answered=True)
    register_error_handlers(app)
    app.include_router(research_router)
    with TestClient(app) as c:
        yield c


def test_research_deep_happy_path(client):
    resp = client.post("/research/deep", json={"keywords": ["Java 集合"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["keywords"] == ["Java 集合"]
    assert body["total_keywords"] == 1
    assert len(body["results"]) == 1
    assert "关联知识点：Java 集合" in body["results"][0]
    assert "Java 集合（题库A）" in body["results"][0]
    assert "## 关联知识点扩展" in body["extension_report"]


def test_research_deep_multiple_keywords_and_max(client):
    agent = client.app.state.retrieval_agent
    resp = client.post("/research/deep", json={"keywords": ["A", "B", "C"], "max_keywords": 2})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["keywords"] == ["A", "B"]
    assert len(agent.asked) == 2


def test_research_deep_no_match_degrades(client):
    client.app.state.retrieval_agent = _FakeRetrievalAgent(answered=False)
    resp = client.post("/research/deep", json={"keywords": ["虚无问题"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["results"] == []
    assert body["extension_report"] == ""


def test_research_deep_empty_keywords_422(client):
    resp = client.post("/research/deep", json={"keywords": []})
    assert resp.status_code == 422
    resp = client.post("/research/deep", json={"keywords": ["   "]})
    assert resp.status_code == 200, resp.text
    assert resp.json()["total_keywords"] == 0