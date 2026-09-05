"""
复盘 Orchestrator（app/agents/orchestrator.py）

v3.1 深模块（§8.2）：对外仅暴露
    async run(request) -> AnalysisResponse      # 触发一次完整多 Agent 复盘
    subscribe(progress_cb)                       # 订阅实时进度（Agent 完成时）

内部封装全部多 Agent 调度 / 状态管理 / 降级策略（渐进迁移）：
- 默认执行器 = 既有 AgentPipeline（§3.4：旧 5 步流水线降级为 Orchestrator 的默认执行器）
- 预留 LangGraph StateGraph 编排骨架：build_graph() 是迁移到「检索 Agent + 反思回路 + 评估 Agent」
  拓扑的落点，届时各节点即各专职 Agent。

进度协议：progress_cb(step: int, total: int, message: str, status: AnalysisStatus)
"""
import logging
from typing import Awaitable, Callable, Optional

from app.models.schemas import (
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

    def __init__(self, pipeline: Optional[AgentPipeline] = None):
        self._pipeline = pipeline if pipeline is not None else AgentPipeline()
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

    # ── LangGraph 编排骨架（渐进迁移落点）───────────────

    def build_graph(self):
        """返回 LangGraph StateGraph（多 Agent 节点拓扑）。

        现状：默认执行器为既有 AgentPipeline；迁移阶段 B 时，以此骨架把
        语音识别 / 分离 / 检索 / 评估 / 报告 替换为独立专职 Agent 节点，
        并接入 reflexion 反思回路。
        """
        raise NotImplementedError(
            "多 Agent 状态图拓扑为阶段 B 迁移落点，当前由既有 AgentPipeline 作默认执行器"
        )