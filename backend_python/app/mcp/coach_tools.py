"""
MCP Coach 工具（浅适配器）

把 CoachService 四步接口封装为标准工具（供 Agent / 外部 MCP 客户端调用）。
只做 schema 声明 + 参数校验 + 转发，不含业务逻辑。
"""
import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.mcp.server import ToolRegistry, ToolSpec
from app.models.entities import CoachMode
from app.services.coach_service import CoachService

logger = logging.getLogger(__name__)


class CoachStartArgs(BaseModel):
    """coach.start 入参"""
    user_id: int
    mode: str = CoachMode.TEXT.value
    difficulty: str = Field(default="MEDIUM")


class CoachNextArgs(BaseModel):
    """coach.next_question 入参"""
    session_id: str


class CoachSubmitArgs(BaseModel):
    """coach.submit_answer 入参"""
    session_id: str
    answer: str


class CoachEndArgs(BaseModel):
    """coach.end 入参"""
    session_id: str


class CoachTools:
    """Coach 工具注册集合"""

    def __init__(self, coach: Optional[CoachService] = None):
        self.coach = coach

    def register(self, registry: ToolRegistry) -> None:
        registry.register_many([
            ToolSpec(
                name="coach.start",
                description="开启一场面试陪练会话，返回 session_id（状态机进入 active）",
                handler=self._start,
                input_model=CoachStartArgs,
            ),
            ToolSpec(
                name="coach.next_question",
                description="为当前会话出下一题（难度自适应 + 画像弱项优先）",
                handler=self._next,
                input_model=CoachNextArgs,
            ),
            ToolSpec(
                name="coach.submit_answer",
                description="提交本题作答，返回即时评分与反馈",
                handler=self._submit,
                input_model=CoachSubmitArgs,
            ),
            ToolSpec(
                name="coach.end",
                description="结束会话：聚合画像、难度结算，返回结课报告",
                handler=self._end,
                input_model=CoachEndArgs,
            ),
        ])
        logger.info("已注册 Coach 工具: coach.start / next_question / submit_answer / end")

    async def _start(self, user_id: int, mode: str, difficulty: str):
        if self.coach is None:
            raise ValueError("Coach 工具未装配 coach_service")
        return self.coach.start_session(user_id, mode=mode, difficulty=difficulty)

    async def _next(self, session_id: str):
        if self.coach is None:
            raise ValueError("Coach 工具未装配 coach_service")
        return self.coach.next_question(session_id)

    async def _submit(self, session_id: str, answer: str):
        if self.coach is None:
            raise ValueError("Coach 工具未装配 coach_service")
        return self.coach.submit_answer(session_id, answer)

    async def _end(self, session_id: str):
        if self.coach is None:
            raise ValueError("Coach 工具未装配 coach_service")
        return self.coach.end_session(session_id)