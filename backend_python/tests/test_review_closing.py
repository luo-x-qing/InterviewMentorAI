"""
复盘收尾链路测试（§10.1 归并→持久化→推送 + §7.5 画像闭环 + 复盘后一键推荐）

覆盖缺口1（状态/报告/评估明细落库）、缺口1深化（/report evaluations 从表读）、
缺口2（画像回写 + 推荐练习 REST/MCP/复盘响应）。
"""
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth_api import router as auth_router
from app.api.coach_api import router as coach_router
from app.api.interview_api import router as interview_router
from app.api.report_api import router as report_router
from app.api.user_api import router as user_router
from app.core.database import Database
from app.core.exceptions import register_error_handlers
from app.models.schemas import AnalysisResponse, AnalysisStatus, EvaluationLevel, EvaluationResult
from app.agents.orchestrator import Orchestrator
from app.services.auth_service import AuthService
from app.services.coach_service import CoachService
from app.services.profiling_service import ProfilingService


class _FakePipeline:
    """模拟 AgentPipeline.run：直接返回固定复盘结果（含一条薄弱项评估）"""

    async def run(self, request):
        return AnalysisResponse(
            status=AnalysisStatus.COMPLETED,
            interview_id=request.interview_id,
            report="# 复盘报告\n主体",
            evaluations=[
                EvaluationResult(
                    question="什么是索引？", answer="不清楚",
                    score=30, level=EvaluationLevel.WEAK,
                    strengths="", weaknesses="数据库索引原理不熟",
                    correction="补充索引B+树结构", knowledge_points="索引,数据库",
                ),
            ],
        )


@pytest.fixture
def client(tmp_path):
    """轻量 TestClient：业务路由 + Orchestrator(FakePipeline) + Coach 内存题库"""
    from app.agents.coach_workers.question_worker import QuestionWorker
    from app.models.entities import CoachQuestion

    db = Database(str(tmp_path / "closing.db"))
    auth = AuthService(database=db)
    profiling = ProfilingService(database=db)
    coach = CoachService(database=db)

    def _source(_limit):
        return [
            CoachQuestion(question_no="1", title="索引优化", question="如何优化慢查询？",
                          answer="加索引", evaluation_points="索引",
                          difficulty="MEDIUM", source="test"),
            CoachQuestion(question_no="2", title="事务 ACID", question="什么是事务？",
                          answer="原子性一致性", evaluation_points="事务",
                          difficulty="MEDIUM", source="test"),
            CoachQuestion(question_no="3", title="HTTP 状态码", question="200/404 含义？",
                          answer="成功/未找到", evaluation_points="网络",
                          difficulty="MEDIUM", source="test"),
        ]

    coach.question_worker = QuestionWorker(question_source=_source)

    class _FakeHub:
        """记录广播主题与 payload（影子 ws_hub）"""

        def __init__(self):
            self.messages = []

        async def broadcast(self, topic: str, payload: dict) -> int:
            self.messages.append((topic, payload))
            return 1

    hub = _FakeHub()

    app = FastAPI()
    app.state.database = db
    app.state.auth_service = auth
    app.state.coach_service = coach
    app.state.profiling_service = profiling
    app.state.ws_hub = hub
    app.state.orchestrator = Orchestrator(pipeline=_FakePipeline())

    register_error_handlers(app)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(interview_router)
    app.include_router(report_router)
    app.include_router(coach_router)

    with TestClient(app) as c:
        yield c
    db.close()


def _register(client, phone=None):
    r = client.post("/auth/register", json={
        "phone": phone or f"139{str(uuid.uuid4().int)[:8]}",
        "password": "secret123", "nickname": "tester",
    })
    assert r.status_code == 200, r.text
    return r.json()


def _auth_header(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_interview(client, tokens, title="一面"):
    created = client.post("/interview", json={"title": title, "audio_file_path": "/tmp/a.wav"},
                          headers=_auth_header(tokens))
    assert created.status_code == 200
    return created.json()


# ── 缺口1：复盘结果持久化 + 状态流转 ───────────────────────

def test_analyze_persists_status_report_and_evaluations(client):
    tokens = _register(client)
    iv = _create_interview(client, tokens)

    resp = client.post(f"/interview/{iv['id']}/analyze", headers=_auth_header(tokens))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"

    # interview 状态与报告已落库
    detail = client.get(f"/interview/{iv['id']}", headers=_auth_header(tokens))
    assert detail.json()["status"] == "COMPLETED"
    assert detail.json()["final_report"].startswith("# 复盘报告")

    # /report 正文来自库
    report = client.get(f"/report/interview/{iv['id']}/report", headers=_auth_header(tokens))
    assert report.json()["content"].startswith("# 复盘报告")

    # 评估明细已从表读取（缺口1深化）
    evals = client.get(f"/report/interview/{iv['id']}/evaluations", headers=_auth_header(tokens))
    rows = evals.json()
    assert len(rows) == 1
    assert rows[0]["question"] == "什么是索引？"
    assert rows[0]["score"] == 30 and rows[0]["level"] == "WEAK"


def test_analyze_marks_failed_when_pipeline_fails(client):
    class _FailPipeline:
        async def run(self, request):
            return AnalysisResponse(
                status=AnalysisStatus.FAILED, interview_id=request.interview_id,
                error="ASR 失败",
            )

    client.app.state.orchestrator = Orchestrator(pipeline=_FailPipeline())
    tokens = _register(client, "13912345678")
    iv = _create_interview(client, tokens)

    resp = client.post(f"/interview/{iv['id']}/analyze", headers=_auth_header(tokens))
    assert resp.status_code == 200 and resp.json()["status"] == "FAILED"

    detail = client.get(f"/interview/{iv['id']}", headers=_auth_header(tokens))
    assert detail.json()["status"] == "FAILED"


# ── 缺口2：画像回写 + 复盘后一键推荐 ───────────────────────

def test_analyze_ingests_profile_and_recommends(client):
    tokens = _register(client)
    iv = _create_interview(client, tokens)

    resp = client.post(f"/interview/{iv['id']}/analyze", headers=_auth_header(tokens))
    assert resp.status_code == 200
    body = resp.json()

    # 薄弱项（索引/数据库 <50）已回写画像
    profile = client.app.state.profiling_service.get_profile(_me(client, tokens))
    assert profile is not None
    assert "索引" in profile.weaknesses

    # 复盘响应与 WS complete 均带推荐练习（按弱项"索引"命中优先）
    assert body["recommendations"], "复盘响应应携带推荐练习"
    rec_top = body["recommendations"][0]
    assert rec_top["title"] == "索引优化"  # 弱项命中靠前

    complete_msgs = [p for t, p in client.app.state.ws_hub.messages if t.endswith(".complete")]
    assert complete_msgs and complete_msgs[-1]["recommendations"]


def _me(client, tokens):
    me = client.get("/auth/me", headers=_auth_header(tokens))
    return me.json()["id"]


# ── /coach/recommend REST + 归属 ─────────────────────────

def test_coach_recommend_returns_questions(client):
    tokens = _register(client)
    resp = client.get("/coach/recommend", headers=_auth_header(tokens))
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    limited = client.get("/coach/recommend?limit=2", headers=_auth_header(tokens))
    assert limited.status_code == 200 and len(limited.json()) == 2

    anon = client.get("/coach/recommend")
    assert anon.status_code == 401


def test_recommend_empty_without_question_source(client):
    from app.agents.coach_workers.question_worker import QuestionWorker
    old = client.app.state.coach_service.question_worker
    client.app.state.coach_service.question_worker = QuestionWorker(question_source=None)

    tokens = _register(client, "13987654321")
    resp = client.get("/coach/recommend", headers=_auth_header(tokens))
    assert resp.status_code == 200 and resp.json() == []

    client.app.state.coach_service.question_worker = old


# ── MCP coach.recommend 工具 ─────────────────────────────

@pytest.mark.asyncio
async def test_mcp_coach_recommend_tool(tmp_path):
    from app.agents.coach_workers.question_worker import QuestionWorker
    from app.mcp.coach_tools import CoachTools
    from app.mcp.server import ToolRegistry
    from app.models.entities import CoachQuestion

    db = Database(str(tmp_path / "mcp.db"))
    coach = CoachService(database=db)

    def _source(_limit):
        return [CoachQuestion(question_no="1", title="索引", question="慢查询？",
                              answer="加索引", evaluation_points="索引", difficulty="MEDIUM")]

    coach.question_worker = QuestionWorker(question_source=_source)

    reg = ToolRegistry()
    CoachTools(coach=coach).register(reg)
    assert "coach.recommend" in [t["name"] for t in reg.list_tools()]

    res = await reg.call_tool("coach.recommend", {"user_id": 1, "limit": 2})
    assert isinstance(res, list) and res[0]["title"] == "索引"
    db.close()


# ── QuestionWorker.recommend 弱项优先 ─────────────────────

def test_question_worker_recommend_prefers_weakness():
    from app.agents.coach_workers.question_worker import QuestionWorker
    from app.models.entities import CoachQuestion, UserProfile

    def _source(_n):
        return [
            CoachQuestion(question_no="1", title="题目A", question="QQ", answer="AA",
                          evaluation_points="索引,数据库"),
            CoachQuestion(question_no="2", title="题目B", question="QQ", answer="BB",
                          evaluation_points="排序"),
            CoachQuestion(question_no="3", title="题目C", question="QQ", answer="CC",
                          evaluation_points="数据库"),
        ]

    worker = QuestionWorker(question_source=_source)
    profile = UserProfile(user_id=1, weaknesses=["索引"])
    recs = worker.recommend(profile, limit=2)
    assert len(recs) == 2
    assert "索引" in recs[0].evaluation_points      # 弱项命中最先

    # 无题库源 → 空列表降级
    empty = QuestionWorker(question_source=None)
    assert empty.recommend(profile) == []


# ── §9.1 PUT /user/password 改密码 ───────────────────────

def test_change_password_flow(client):
    tokens = _register(client, "13911112222")
    me = client.get("/auth/me", headers=_auth_header(tokens)).json()
    user_id = me["id"]
    db = client.app.state.database

    # 旧密码错误 → 401
    bad = client.put("/user/password", json={"old_password": "wrong123", "new_password": "newpass88"},
                     headers=_auth_header(tokens))
    assert bad.status_code == 401

    # 新密码太短 → 422（Pydantic min_length=6 先拦截）
    short = client.put("/user/password", json={"old_password": "secret123", "new_password": "abc"},
                       headers=_auth_header(tokens))
    assert short.status_code == 422

    # 正常改密 → 旧密码登录失败、新密码登录成功
    ok = client.put("/user/password", json={"old_password": "secret123", "new_password": "newpass88"},
                    headers=_auth_header(tokens))
    assert ok.status_code == 200 and ok.json()["status"] == "OK"

    user = db.get_user_by_id(user_id)
    assert user.hashed_password != "secret123"  # 落库为哈希

    old_login = client.post("/auth/login", json={"phone": me["phone"], "password": "secret123"})
    assert old_login.status_code == 401
    new_login = client.post("/auth/login", json={"phone": me["phone"], "password": "newpass88"})
    assert new_login.status_code == 200


# ── §9.3 GET /coach/profile 查看画像 ─────────────────────

def test_coach_profile_returns_weakness(client):
    tokens = _register(client, "13922223333")
    _ = client.app.state.profiling_service.ingest_review(
        _me(client, tokens),
        [EvaluationResult(question="Q1", answer="A", score=30, level=EvaluationLevel.WEAK,
                          strengths="", weaknesses="不会", correction="再学", knowledge_points="索引")],
    )
    resp = client.get("/coach/profile", headers=_auth_header(tokens))
    assert resp.status_code == 200
    assert resp.json()["weaknesses"] == ["索引"]

    # 未登录 → 401
    assert client.get("/coach/profile").status_code == 401