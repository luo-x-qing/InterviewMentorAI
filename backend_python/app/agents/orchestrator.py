"""
复盘 Orchestrator（app/agents/orchestrator.py）

v3.1 深模块（§8.2）：对外仅暴露
    async run(request) -> AnalysisResponse      # 触发一次完整多 Agent 复盘
    subscribe(progress_cb)                       # 订阅实时进度（Agent 完成时）
    build_graph()                                # LangGraph 多 Agent 状态图（阶段 B 拓扑）

内部封装全部多 Agent 调度 / 状态管理 / 降级策略（渐进迁移）：
- run() = 默认执行器 = 既有 AgentPipeline（§3.4：旧 5 步流水线降级为 Orchestrator 的默认执行器）
- build_graph() = 阶段 B 目标拓扑：ASR → 说话人分离 → 检索评估 → 反思增强 → 报告，
  各节点复用 AgentPipeline 既有能力（不重复实现），并接入 reflexion 反思回路与
  retrieval_agent 深度检索。可独立 ainvoke 运行或作 run() 的后续迁移落点。

进度协议：progress_cb(step: int, total: int, message: str, status: AnalysisStatus)
"""
import logging
from typing import Any, Awaitable, Callable, Optional

from app.models.schemas import (
    AgentState,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatus,
)
from app.services.agent_pipeline import AgentPipeline

logger = logging.getLogger(__name__)

# 阶段标签（对应 Agent 分工）
_STAGES = [
    ("语音识别", AnalysisStatus.ASR_COMPLETED),
    ("说话人分离", AnalysisStatus.DIALOGUE_PARSED),
    ("评估", AnalysisStatus.EVALUATION_COMPLETED),
    ("报告生成", AnalysisStatus.COMPLETED),
]
_TOTAL_STEPS = len(_STAGES)


class Orchestrator:
    """复盘 Orhestrator（深模块）"""

    def __init__(
        self,
        pipeline: Optional[AgentPipeline] = None,
        retrieval_agent=None,
        reflexion=None,
    ):
        self._pipeline = pipeline if pipeline is not None else AgentPipeline()
        # 阶段 B 可选依赖：深度检索 Agent + 反思回路（build_graph 用，缺省延迟装配）
        self._retrieval_agent = retrieval_agent
        self._reflexion = reflexion
        self._progress_cbs: list = []

    # ── 订阅 ──────────────────────────────────────────

    def subscribe(self, progress_cb: Callable[[int, int, str, AnalysisStatus], Awaitable[None]]) -> None:
        """注册进度回调（可在亚进程 / WebSocket 层为空）。"""
        self._progress_cbs.append(progress_cb)

    async def _emit(self, step: int, message: str, status: AnalysisStatus) -> None:
        for cb in self._progress_cbs:
            try:
                r = cb(step, _TOTAL_STEPS, message, status)
                if hasattr(r, "__await__"):
                    await r
            except Exception as e:  # noqa: BLE001
                logger.warning("进度回调异常: %s", e)

    # ── 对外主入口 ────────────────────────────────────

    async def run(self, request: AnalysisRequest) -> AnalysisResponse:
        """执行一次完整的多 Agent 面试复盘"""
        logger.info("Orchestrator 启动复盘 interview_id=%s", request.interview_id)

        # 阶段 0：初始化
        await self._emit(0, "开始分析", AnalysisStatus.PROCESSING)

        # 默认执行器：若已注入带 progress 钩子的 AgentPipeline，则由管线自身更新阶段进度
        if hasattr(self._pipeline, "progress_cb"):
            bound = self._pipeline.progress_cb
            self._pipeline.progress_cb = self._forward_progress  # type: ignore[attr-defined]

        try:
            response = await self._pipeline.run(request)
        finally:
            if hasattr(self._pipeline, "progress_cb"):
                self._pipeline.progress_cb = bound  # type: ignore[attr-defined]

        await self._emit(_TOTAL_STEPS, "完成", AnalysisStatus.COMPLETED)
        return response

    async def _forward_progress(self, step: int, message: str, status: AnalysisStatus) -> None:
        await self._emit(step, message, status)

    # ── LangGraph 状态图（阶段 B 目标拓扑）─────────────

    def build_graph(self):
        """返回已编译的 LangGraph StateGraph（多 Agent 节点拓扑）。

        节点复用 AgentPipeline 既有能力（语音识别 / 说话人分离 / 评估 / 报告），
        并在评估后插入反思回路（reflexion）对薄弱项做深度补充检索（retrieval_agent），
        再生成报告。可独立 ainvoke：
            result = await orchestrator.build_graph().ainvoke({"request": request})
        """
        from langgraph.graph import END, START, StateGraph

        from app.agents.reflexion import Reflexion
        from app.agents.retrieval_agent import RetrievalAgent

        reflexion = self._reflexion if self._reflexion is not None else Reflexion()
        retrieval_agent = self._retrieval_agent if self._retrieval_agent is not None else retrieval_agent_default()
        pipeline = self._pipeline

        # 图状态：{"request": AnalysisRequest, "state": AgentState}
        graph = StateGraph(dict)

        async def transcribe(state: dict) -> dict:
            request = state["request"]
            agent_state = AgentState(
                interview_id=request.interview_id,
                audio_file_path=request.audio_file_path,
            )
            agent_state.raw_transcript = await pipeline.prompt_service.transcribe_interview(
                request.audio_file_path
            )
            return {"state": agent_state}

        async def separate(state: dict) -> dict:
            agent_state = state["state"]
            agent_state.dialogue_list = await pipeline._parse_dialogue(agent_state)
            return {"state": agent_state}

        async def evaluate(state: dict) -> dict:
            agent_state = state["state"]
            agent_state.evaluation_list = await pipeline._evaluate_answers(agent_state)
            return {"state": agent_state}

        async def reflex(state: dict) -> dict:
            """反思增强：评估薄弱项 → 深度检索 → 记录追加扩展（进 final_report）"""
            agent_state = state["state"]
            keywords = reflexion.keywords_from(agent_state.evaluation_list)
            if keywords:
                extras = await reflexion.deep_retrieve(retrieval_agent, keywords)
                agent_state.final_report = reflexion.extend_report(extras)
            return {"state": agent_state}

        async def report(state: dict) -> dict:
            agent_state = state["state"]
            base = await pipeline._generate_report(agent_state)
            if agent_state.final_report:
                agent_state.final_report = base + "\n" + agent_state.final_report
            else:
                agent_state.final_report = base
            return {"state": agent_state}

        graph.add_node("transcribe", transcribe)
        graph.add_node("separate", separate)
        graph.add_node("evaluate", evaluate)
        graph.add_node("reflex", reflex)
        graph.add_node("report", report)

        graph.add_edge(START, "transcribe")
        graph.add_edge("transcribe", "separate")
        graph.add_edge("separate", "evaluate")
        graph.add_edge("evaluate", "reflex")
        graph.add_edge("reflex", "report")
        graph.add_edge("report", END)

        return graph.compile()

    # 其他 ─────────────────────────────────────────────

    def _transcribe_node(self):
        raise RuntimeError("内部节点需经 build_graph 注入")

    def __repr__(self) -> str:
        node_names = [n for n, _ in _STAGES]
        return f"<Orchestrator stages={node_names} default_executor={type(self._pipeline).__name__}>"


def retrieval_agent_default():
    """延迟装配默认检索 Agent（build_graph 未显式注入时）"""
    from app.agents.retrieval_agent import RetrievalAgent

    return RetrievalAgent()