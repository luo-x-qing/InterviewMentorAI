"""
Coach Agent（app/agents/coach.py）

架构 §7 Coach Agent 门面：对外暴露教练陪练四步接口（start/next/submit/end）。
实现与状态机位于 services.coach_service.CoachService（一个深模块）；
本模块是 Agent 命名空间下的薄导出门面，便于主流程统一从 agents 引用。

    from app.agents.coach import CoachAgent
"""
from app.services.coach_service import CoachService

CoachAgent = CoachService  # type: ignore[misc]

__all__ = ["CoachAgent"]