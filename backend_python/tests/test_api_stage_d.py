"""
阶段 D 集成测试：JWT 认证 + 用户/面试/报告 / Coach REST 前端。

跳过知识库/向量依赖：AuthService / Database 用临时 SQLite（tmp_path），
不走 lifespan（避免拉起昂贵的基础服务）。仅验证路由层 + 业务对象装配正确。
"""
import pytest
from fastapi import FastAPI, Request, WebSocket
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketState

from app.api.auth_api import router as auth_router
from app.api.coach_api import router as coach_router
from app.api.interview_api import router as interview_router
from app.api.report_api import router as report_router
from app.api.user_api import router as user_router
from app.core.database import Database
from app.core.exceptions import register_error_handlers
from app.services.auth_service import AuthService
from app.services.coach_service import CoachService


@pytest.fixture
def client(tmp_path):
    """轻量 TestClient：仅业务路由 + 最小 app.state（database/auth_service/coach_service）"""
    from app.agents.coach_workers.question_worker import QuestionWorker
    from app.models.entities import CoachQuestion

    db = Database(str(tmp_path / "stage_d.db"))
    auth = AuthService(database=db)
    coach = CoachService(database=db)

    # 注入内存题库：避免真实知识库依赖，出题 Worker 可出题
    def _source(_limit: int):
        return [
            CoachQuestion(question_no="1", title="列表 vs 元组",
                          question="Python 列表和元组的区别？", answer="列表可变，元组不可变",
                          evaluation_points="数据结构", difficulty="MEDIUM"),
            CoachQuestion(question_no="2", title="HashMap",
                          question="HashMap 的底层结构？", answer="数组+链表/红黑树",
                          evaluation_points="集合", difficulty="EASY"),
        ]

    coach.question_worker = QuestionWorker(question_source=_source)

    app = FastAPI()
    app.state.database = db
    app.state.auth_service = auth
    app.state.coach_service = coach
    register_error_handlers(app)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(interview_router)
    app.include_router(report_router)
    app.include_router(coach_router)

    with TestClient(app) as c:
        yield c
    db.close()


def _register(client, phone="13800138000"):
    r = client.post("/auth/register", json={"phone": phone, "password": "secret123", "nickname": "tester"})
    assert r.status_code == 200, r.text
    return r.json()


def _auth_header(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ── Auth ───────────────────────────────────────────────

def test_register_and_login_tokens(client):
    tokens = _register(client)
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"] and tokens["refresh_token"]

    login = client.post("/auth/login", json={"phone": "13800138000", "password": "secret123"})
    assert login.status_code == 200
    assert login.json()["access_token"]

    wrong = client.post("/auth/login", json={"phone": "13800138000", "password": "badpass"})
    assert wrong.status_code == 401


def test_register_duplicate_rejected(client):
    _register(client)
    dup = client.post("/auth/register", json={"phone": "13800138000", "password": "secret123"})
    assert dup.status_code == 409


def test_refresh_rotates_tokens(client):
    tokens = _register(client)
    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != tokens["access_token"]


def test_me_requires_auth_and_returns_user(client):
    tokens = _register(client)
    me = client.get("/auth/me", headers=_auth_header(tokens))
    assert me.status_code == 200
    body = me.json()
    assert body["phone"] == "13800138000"

    anon = client.get("/auth/me")
    assert anon.status_code == 401


# ── 用户 → 面试 → 报告 归属链路 ─────────────────────────

def test_interview_crud_owned_by_user(client):
    alice = _register(client, "13800138001")
    bob = _register(client, "13800138002")

    created = client.post("/interview", json={"title": "后端一面", "audio_file_path": "/tmp/a.wav"},
                          headers=_auth_header(alice))
    assert created.status_code == 200
    iv = created.json()
    assert iv["id"] > 0 and iv["status"] == "PENDING"

    listed = client.get("/interview/list", headers=_auth_header(alice))
    assert listed.status_code == 200 and len(listed.json()) == 1

    my = client.get("/interview/my", headers=_auth_header(alice))
    assert my.status_code == 200 and len(my.json()) == 1

    detail = client.get(f"/interview/{iv['id']}", headers=_auth_header(alice))
    assert detail.status_code == 200 and detail.json()["title"] == "后端一面"

    # 归属校验：bob 无法读 alice 的面试
    forbidden = client.get(f"/interview/{iv['id']}", headers=_auth_header(bob))
    assert forbidden.status_code == 403


def test_report_owned_and_list(client):
    tokens = _register(client)
    created = client.post("/interview", json={"title": "一面"}, headers=_auth_header(tokens))
    iv = created.json()

    # 报告为空时返回空正文与空列表
    report = client.get(f"/report/interview/{iv['id']}/report", headers=_auth_header(tokens))
    assert report.status_code == 200 and report.json()["content"] == ""

    evals = client.get(f"/report/interview/{iv['id']}/evaluations", headers=_auth_header(tokens))
    assert evals.status_code == 200 and evals.json() == []

    lst = client.get("/report/list", headers=_auth_header(tokens))
    assert lst.status_code == 200 and lst.json() == []


# ── WebSocket（阶段 A）────────────────────────────────

class _FakeWS:
    """最小 fake：记录 accept 与收到文本，模拟已连接状态"""

    def __init__(self):
        self.sent = []
        self.accepted = False
        self.client_state = WebSocketState.CONNECTED

    async def accept(self):
        self.accepted = True

    async def send_text(self, data: str):
        self.sent.append(data)


def test_ws_requires_valid_token(tmp_path):
    """无 token / 无效 token → 握手被拒（403 关闭）"""
    from app.api.ws_api import router as ws_router
    from app.services.ws_service import WebSocketHub

    db = Database(str(tmp_path / "ws.db"))
    auth = AuthService(database=db)

    app = FastAPI()
    app.state.database = db
    app.state.auth_service = auth
    app.state.ws_hub = WebSocketHub()
    app.include_router(ws_router)

    with TestClient(app) as c:
        # 无效 token：握手应失败（连接被 403 关闭）
        with pytest.raises(Exception) as exc:
            with c.websocket_connect("/ws?token=invalid&subscribe=interview.1") as ws:
                ws.receive_text()
        assert exc.value is not None
    db.close()


@pytest.mark.asyncio
async def test_hub_subscribe_and_broadcast():
    """hub 精确投递：订阅者收到、未订阅主题不收到、断开后清理"""
    from app.services.ws_service import WebSocketHub

    hub = WebSocketHub()
    a = _FakeWS()
    b = _FakeWS()
    await hub.connect(a, ["interview.3", "user.9.notifications"])
    await hub.connect(b, ["user.9.notifications"])

    n = await hub.broadcast("interview.3.progress", {"message": "x", "step": 1, "total": 4})
    assert n == 1
    assert len(a.sent) == 1 and len(b.sent) == 0
    assert "interview.3.progress" in a.sent[0]

    n2 = await hub.broadcast("user.9.notifications", {"message": "hi"})
    assert n2 == 2
    assert len(a.sent) == 2 and len(b.sent) == 1

    await hub.disconnect(a)
    n3 = await hub.broadcast("user.9.notifications", {"message": "bye"})
    assert n3 == 1


@pytest.mark.asyncio
async def test_hub_unsubscribe_on_dead_connection():
    """已断开的连接不再收到广播"""
    from app.services.ws_service import WebSocketHub

    hub = WebSocketHub()
    a = _FakeWS()
    b = _FakeWS()
    await hub.connect(a, ["interview.7"])
    await hub.connect(b, ["interview.7"])

    a.client_state = None  # 模拟断开 → WebSocketState 判断跳过
    n = await hub.broadcast("interview.7.progress", {"message": "x"})
    assert n == 1
    assert len(b.sent) == 1


# ── Coach REST ─────────────────────────────────────────

def test_coach_session_lifecycle(client):
    tokens = _register(client)
    headers = _auth_header(tokens)

    started = client.post("/coach/session", json={"mode": "TEXT", "difficulty": "MEDIUM"}, headers=headers)
    assert started.status_code == 200
    sid = started.json()["session_id"]
    assert started.json()["status"] == "ACTIVE"

    q = client.get(f"/coach/session/{sid}/question", headers=headers)
    assert q.status_code == 200
    assert q.json()["question_no"]

    fb = client.post(f"/coach/session/{sid}/answer",
                     json={"answer": "列表是有序可变，元组不可变"}, headers=headers)
    assert fb.status_code == 200
    assert "score" in fb.json()

    ended = client.post(f"/coach/session/{sid}/end", headers=headers)
    assert ended.status_code == 200
    assert "accuracy" in ended.json()
    assert ended.json()["total_questions"] >= 1


def test_coach_session_ownership_enforced(client):
    alice = _register(client, "13800138101")
    bob = _register(client, "13800138102")

    started = client.post("/coach/session", json={}, headers=_auth_header(alice))
    sid = started.json()["session_id"]

    stolen = client.get(f"/coach/session/{sid}/question", headers=_auth_header(bob))
    assert stolen.status_code == 403


# ── Build_graph（阶段 B）────────────────────────────────

def test_build_graph_compiles_with_stageD_state():
    from app.services.agent_pipeline import AgentPipeline
    from app.agents.orchestrator import Orchestrator

    orch = Orchestrator(pipeline=AgentPipeline(prompt_service=object(), rag_mcp=object()))
    graph = orch.build_graph()
    for node in ("transcribe", "separate", "evaluate", "reflex", "report"):
        assert node in graph.nodes