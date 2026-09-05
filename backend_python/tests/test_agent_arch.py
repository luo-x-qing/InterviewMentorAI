"""
v3.1 架构骨架测试：MCP 工具层 / Coach 会话状态机 / 画像 / Workers / Orhestrator

原则：全部走公共接口（不触碰内部细节），隔离外部依赖（LLM/向量库用注入替换）。
"""
import os
import tempfile
import uuid

import pytest

from app.core.database import Database
from app.models.entities import (
    CoachAnswerRecord,
    CoachQuestion,
    CoachSessionStatus,
    Difficulty,
    UserProfile,
)
from app.mcp.server import ToolRegistry, ToolSpec, ToolError
from app.mcp import knowledge_tools, retrieval_tools, coach_tools  # noqa: F401 模块可导入
from app.mcp.coach_tools import CoachTools
from app.agents.coach_workers.question_worker import QuestionWorker
from app.agents.coach_workers.feedback_worker import FeedbackWorker
from app.agents.coach_workers.profiling_worker import ProfilingWorker
from app.services.coach_service import CoachService
from app.services.profiling_service import ProfilingService
from app.agents.orchestrator import Orchestrator


@pytest.fixture
def db():
    path = os.path.join(tempfile.gettempdir(), f"test_agent_arch_{uuid.uuid4().hex}.db")
    database = Database(db_path=path)
    yield database
    database.close()
    if os.path.exists(path):
        os.remove(path)


# ── 题目源（注入用内存题库）──────────────────────────────

def _questions(_n=None):
    return [
        CoachQuestion(question_no="1", title="HTTP 是什么", question="请解释 HTTP",
                      answer="HTTP 是超文本传输协议", evaluation_points="超文本,传输,协议",
                      difficulty=Difficulty.EASY.value, source="test"),
        CoachQuestion(question_no="2", title="数据库索引", question="为什么用索引",
                      answer="索引加速查询", evaluation_points="加速,查询",
                      difficulty=Difficulty.MEDIUM.value, source="test"),
        CoachQuestion(question_no="3", title="进程线程区别", question="区别是什么",
                      answer="资源/调度", evaluation_points="资源,调度",
                      difficulty=Difficulty.HARD.value, source="test"),
    ]


# ── MCP 工具层 ─────────────────────────────────────────

class TestToolRegistry:

    def test_register_and_list(self):
        reg = ToolRegistry()
        reg.register(ToolSpec("echo.echo", "回显", lambda text: text))
        tools = reg.list_tools()
        assert [t["name"] for t in tools] == ["echo.echo"]
        assert tools[0]["description"] == "回显"

    def test_register_duplicate_raises(self):
        reg = ToolRegistry()
        reg.register(ToolSpec("echo.echo", "x", lambda: None))
        with pytest.raises(ToolError):
            reg.register(ToolSpec("echo.echo", "y", lambda: None))

    @pytest.mark.asyncio
    async def test_call_tool_with_pydantic_validation(self):
        from pydantic import BaseModel, Field

        class Args(BaseModel):
            text: str
            size: int = Field(ge=1)

        reg = ToolRegistry()
        reg.register(ToolSpec("echo.upper", "大写", lambda text, size: (text.upper(), size), Args))
        assert await reg.call_tool("echo.upper", {"text": "hi", "size": 2}) == ["HI", 2]

    @pytest.mark.asyncio
    async def test_call_async_handler(self):
        async def handler(text: str):
            return f"async:{text}"

        reg = ToolRegistry()
        reg.register(ToolSpec("async.run", "异步", handler))
        assert await reg.call_tool("async.run", {"text": "ok"}) == "async:ok"

    @pytest.mark.asyncio
    async def test_call_unknown_raises(self):
        reg = ToolRegistry()
        with pytest.raises(ToolError):
            await reg.call_tool("nope", {})

    @pytest.mark.asyncio
    async def test_jsonable_serializes_pydantic(self):
        from pydantic import BaseModel

        class R(BaseModel):
            a: int

        reg = ToolRegistry()
        reg.register(ToolSpec("r.get", "x", lambda: R(a=1)))
        assert await reg.call_tool("r.get", {}) == {"a": 1}


# ── Coach 会话状态机 ────────────────────────────────────

class TestCoachService:

    @pytest.mark.asyncio
    async def test_full_session_flow(self, db):
        coach = CoachService(database=db)
        coach.question_worker.set_question_source(_questions)

        handle = coach.start_session(user_id=1, mode="TEXT", difficulty="MEDIUM")
        assert handle.status == CoachSessionStatus.ACTIVE.value
        session = db.get_coach_session(handle.session_id)
        assert session is not None

        # 出题 → 作答 → 推进
        q = coach.next_question(handle.session_id)
        assert q.question_no and q.question
        fb = coach.submit_answer(handle.session_id, "超文本 传输 协议")
        assert 0 <= fb.score <= 100
        session = db.get_coach_session(handle.session_id)
        assert session.total_count == 1
        assert session.question_index == 1
        assert db.list_answer_records(handle.session_id) != []

        # 错误顺序守卫
        with pytest.raises(KeyError):
            coach.submit_answer("no-such-session", "x")

        report = coach.end_session(handle.session_id)
        assert report.total_questions == 1
        assert 0.0 <= report.accuracy <= 1.0
        assert db.get_coach_session(handle.session_id).status == CoachSessionStatus.DONE.value

    def test_next_on_done_session_raises(self, db):
        coach = CoachService(database=db)
        coach.question_worker.set_question_source(_questions)
        handle = coach.start_session(user_id=1)
        report = coach.end_session(handle.session_id)
        with pytest.raises(ValueError):
            coach.next_question(handle.session_id)


# ── Coach Workers ──────────────────────────────────────

class TestWorkers:

    def test_question_worker_selects_by_difficulty(self):
        worker = QuestionWorker(question_source=lambda _n: _questions())
        q = worker.select(None, Difficulty.EASY.value)
        assert q.difficulty == Difficulty.EASY.value

    def test_question_worker_prefers_weakness(self):
        worker = QuestionWorker(question_source=lambda _n: _questions())
        profile = UserProfile(user_id=1, weaknesses=["索引"])
        q = worker.select(profile, Difficulty.MEDIUM.value)
        assert "索引" in q.title  # 弱项命中优先

    def test_question_worker_no_source_raises(self):
        worker = QuestionWorker(question_source=None)
        with pytest.raises(RuntimeError):
            worker.select(None, Difficulty.EASY.value)

    def test_feedback_worker_rule_scoring(self):
        worker = FeedbackWorker()
        q = _questions()[0]
        good = worker.evaluate(q, "HTTP 是超文本传输协议，采用传输与协议设计")
        assert good.is_correct is True
        bad = worker.evaluate(q, "我不清楚")
        assert bad.is_correct is False
        # 记录落为画像输入
        rec = worker.to_record(q, good, "sess")
        assert isinstance(rec, CoachAnswerRecord)
        assert rec.knowledge_points == "超文本,传输,协议"

    def test_feedback_worker_empty_answer(self):
        worker = FeedbackWorker()
        fb = worker.evaluate(_questions()[1], "   ")
        assert fb.is_correct is False and fb.score == 0


# ── 画像 ──────────────────────────────────────────────

class TestProfiling:

    def test_aggregate_builds_weakness(self, db):
        profiler = ProfilingService(database=db)
        records = [
            CoachAnswerRecord(session_id="s", question_no="1", title="HTTP",
                              answer="", score=30, knowledge_points="超文本,协议"),
            CoachAnswerRecord(session_id="s", question_no="1", title="HTTP",
                              answer="", score=40, knowledge_points="超文本"),
            CoachAnswerRecord(session_id="s", question_no="2", title="索引",
                              answer="", score=90, knowledge_points="索引"),
        ]
        profile = profiler.build_profile(1, records)
        assert "索引" in profile.strengths       # 90 ≥70
        assert "超文本" in profile.weaknesses     # 平均35 <50
        # 已写库
        loaded = profiler.get_profile(1)
        assert loaded is not None and loaded.user_id == 1

    def test_suggest_difficulty(self):
        profiler = ProfilingService()
        s = db_placeholder_session()
        s.correct_count, s.total_count = 4, 5
        assert profiler.suggest_difficulty(s) == Difficulty.HARD.value
        s.correct_count, s.total_count = 1, 5
        assert profiler.suggest_difficulty(s) == Difficulty.EASY.value

    def test_cosine(self):
        profiler = ProfilingService()
        assert profiler.cosine(["超文本"], ["超文本传输"]) > 0
        assert profiler.cosine(["a"], ["b"]) == 0.0
        assert profiler.cosine(["索引", "数据库"], ["索引"]) > 0

    def test_rank_questions_by_profile(self):
        profiler = ProfilingService()
        profile = UserProfile(user_id=1, weaknesses=["索引"])
        ranked = profiler.rank_questions_by_profile(
            [("1", "HTTP"), ("2", "索引加速")], profile)
        assert ranked[0][0] == "2"


def db_placeholder_session():
    from app.models.entities import CoachSession
    return CoachSession(id="x", user_id=1)


# ── Orchestrator ───────────────────────────────────────

class TestOrchestrator:

    @pytest.mark.asyncio
    async def test_subscribe_and_default_step_count(self):
        """骨架：Orchestrator.run 委托默认执行器；进度回调前后触发"""
        cbs = []

        class _FakePipeline:
            async def run(self, request):
                return None

        class _FakeRequest:
            interview_id = "fake-id"

        orch = Orchestrator(pipeline=_FakePipeline())
        orch.subscribe(lambda s, t, m, st: cbs.append((s, t)))
        await orch.run(_FakeRequest())
        assert cbs[0] == (0, 4)      # 初始化
        assert cbs[-1] == (4, 4)     # 完成

    def test_build_graph_compiles(self):
        """阶段 B：build_graph() 落地为可编译 LangGraph 状态图"""
        from app.services.agent_pipeline import AgentPipeline

        pipeline = AgentPipeline(prompt_service=object(), rag_mcp=object())
        orch = Orchestrator(pipeline=pipeline)
        graph = orch.build_graph()
        # 图已编译：存在可调用的 5 个节点
        for node in ("transcribe", "separate", "evaluate", "reflex", "report"):
            assert node in graph.nodes
        assert orch.__repr__() is not None

    @pytest.mark.asyncio
    async def test_build_graph_ainvoke_runs_full_flow(self, mocker):
        """阶段 B：图 ainvoke 走完整 ASR→分离→评估→反思→报告 链路"""
        from app.models.schemas import (
            AgentState,
            AnalysisRequest,
            DialogueItem,
            EvaluationLevel,
            EvaluationResult,
            Speaker,
        )
        from app.services.agent_pipeline import AgentPipeline

        pipeline = AgentPipeline(prompt_service=mocker.MagicMock(), rag_mcp=mocker.MagicMock())
        pipeline.prompt_service.transcribe_interview = mocker.AsyncMock(return_value="面试官：Q1\n候选人：A1")
        pipeline._parse_dialogue = mocker.AsyncMock(return_value=[
            DialogueItem(speaker=Speaker.INTERVIEWER, content="Q1"),
            DialogueItem(speaker=Speaker.CANDIDATE, content="A1"),
        ])
        pipeline._evaluate_answers = mocker.AsyncMock(return_value=[
            EvaluationResult(question="Q1", answer="A1", score=60,
                             level=EvaluationLevel.WEAK, strengths="s", weaknesses="w1, w2",
                             correction="c", knowledge_points="kp1"),
        ])
        pipeline._generate_report = mocker.AsyncMock(return_value="# 复盘报告\n主体")
        pipeline.prompt_service.evaluate_answer = mocker.AsyncMock(return_value="{}")

        # 反思回路：有薄弱项 → 深度检索出扩展 → 追加进报告
        class FakeRetrievalAgent:
            async def answer(self, q):
                from app.models.schemas import RagAnswerResult
                return RagAnswerResult(question=q, candidates=[], status="no_match", iterations=1)

        orch = Orchestrator(pipeline=pipeline, retrieval_agent=FakeRetrievalAgent())
        graph = orch.build_graph()
        result = await graph.ainvoke({"request": AnalysisRequest(interview_id=1, audio_file_path="/tmp/x.wav")})
        state: AgentState = result["state"]
        assert state.raw_transcript == "面试官：Q1\n候选人：A1"
        assert len(state.dialogue_list) == 2
        assert len(state.evaluation_list) == 1
        assert state.final_report.startswith("# 复盘报告")
        pipeline._evaluate_answers.assert_awaited_once()


# ── AgentPipeline × ToolRegistry（阶段 C：检索走 call_tool）──────

class TestPipelineRetrievalViaTool:

    @pytest.fixture
    def stub_retrieve_registry(self):
        """注册 retrieval.retrieve 桩工具，返回固定 docs"""
        from app.mcp.server import ToolRegistry, ToolSpec

        def _retrieve(question, top_k=6, use_hybrid=True, use_rerank=True):
            return {
                "question": question,
                "docs": [
                    {"doc_id": 1, "title": "基础", "content": "参考答案内容",
                     "source": "s.md", "question_no": "1", "section": "a", "score": 0.9},
                ],
                "metrics": None,
            }

        reg = ToolRegistry()
        reg.register(ToolSpec("retrieve.retrieve", "检索", _retrieve))
        return reg

    @pytest.mark.asyncio
    async def test_evaluate_goes_through_call_tool(self, stub_retrieve_registry, mocker):
        """装配 tool_registry 时，评估检索改走 call_tool + prompt_service.evaluate_answer"""
        prompt = mocker.MagicMock()
        prompt.evaluate_answer = mocker.AsyncMock(
            return_value='{"score": 85, "level": "PROFICIENT", "strengths": "s", '
                         '"weaknesses": "", "correction": "", "knowledge_points": ""}'
        )
        rag_mcp = mocker.MagicMock()
        rag_mcp.build_rag_context = lambda res: "CTX:" + "".join(d.content for d in res.docs)
        rag_mcp.limit_context_length = lambda raw: raw

        from app.services.agent_pipeline import AgentPipeline

        pipeline = AgentPipeline(prompt_service=prompt, rag_mcp=rag_mcp, tool_registry=stub_retrieve_registry)
        result = await pipeline._evaluate_single("问题", "我的回答")

        assert result is not None and result.score == 85
        prompt.evaluate_answer.assert_awaited_once()
        call_kwargs = prompt.evaluate_answer.await_args.kwargs
        assert "参考答案内容" in call_kwargs["ref_text"]   # 上下文确实来自工具返回 docs
        rag_mcp.rag_enhance_evaluate.assert_not_called()    # 未走旧链路

    @pytest.mark.asyncio
    async def test_evaluate_falls_back_without_tool_registry(self, mocker):
        """未装配 tool_registry 时回退到既存 rag_mcp.rag_enhance_evaluate，不改旧行为"""
        prompt = mocker.MagicMock()
        prompt.evaluate_answer = mocker.AsyncMock(
            return_value='{"score": 80, "level": "PROFICIENT", "strengths": "s", '
                         '"weaknesses": "", "correction": "", "knowledge_points": ""}'
        )
        rag_mcp = mocker.MagicMock()
        rag_mcp.rag_enhance_evaluate = mocker.AsyncMock(
            return_value='{"score": 80, "level": "PROFICIENT", "strengths": "s", '
                         '"weaknesses": "", "correction": "", "knowledge_points": ""}'
        )

        from app.services.agent_pipeline import AgentPipeline

        pipeline = AgentPipeline(prompt_service=prompt, rag_mcp=rag_mcp)  # 无 tool_registry
        result = await pipeline._evaluate_single("问题", "回答")
        assert result.score == 80
        rag_mcp.rag_enhance_evaluate.assert_awaited_once()
        prompt.evaluate_answer.assert_not_called()