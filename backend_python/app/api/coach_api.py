"""
Coach 陪练 API 路由（app/api/coach_api.py）

阶段 D：Coach 深模块的 REST 前端（薄门面，转调 CoachService）+ 阶段 C 已注册 MCP 工具。
    POST  /coach/session                    开会话（返回 session_id）
    GET   /coach/session/{id}/question      出下一题
    POST  /coach/session/{id}/answer        提交作答 → 即时反馈
    POST  /coach/session/{id}/end           结课 → 会话报告
"""
import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.exceptions import AppError, ForbiddenError
from app.models.entities import (
    CoachFeedbackOut,
    CoachQuestionOut,
    CoachSessionHandle,
    CoachSessionReport,
    User,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coach", tags=["coach"])


class StartSessionRequest(BaseModel):
    mode: str = Field(default="TEXT", pattern="^(TEXT|VOICE)$")
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=4000)


def _get_coach(request: Request):
    return request.app.state.coach_service


def _require_owned_session(coach, db, session_id: str, user_id: int):
    session = db.get_coach_session(session_id)
    if session is None or session.user_id != user_id:
        raise ForbiddenError(detail="无权访问该陪练会话")
    return session


@router.post("/session", response_model=CoachSessionHandle)
async def start_session(
    body: StartSessionRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    try:
        handle = _get_coach(request).start_session(user.id, mode=body.mode, difficulty=body.difficulty)
        return handle
    except AppError as e:
        raise e.to_http_exception()


@router.get("/session/{session_id}/question", response_model=CoachQuestionOut)
async def next_question(session_id: str, request: Request, user: User = Depends(get_current_user)):
    coach = _get_coach(request)
    _require_owned_session(coach, request.app.state.database, session_id, user.id)
    try:
        return coach.next_question(session_id)
    except AppError as e:
        raise e.to_http_exception()
    except KeyError as e:
        raise ForbiddenError(detail=str(e)).to_http_exception()
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/session/{session_id}/answer", response_model=CoachFeedbackOut)
async def submit_answer(
    session_id: str,
    body: SubmitAnswerRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    coach = _get_coach(request)
    _require_owned_session(coach, request.app.state.database, session_id, user.id)
    try:
        feedback = coach.submit_answer(session_id, body.answer)
        hub = getattr(request.app.state, "ws_hub", None)
        if hub is not None:
            await hub.broadcast(f"coach.{session_id}.feedback", {
                "is_correct": feedback.is_correct,
                "score": feedback.score,
                "feedback": feedback.feedback,
                "correct_answer": feedback.correct_answer,
            })
        return feedback
    except AppError as e:
        raise e.to_http_exception()
    except KeyError as e:
        raise ForbiddenError(detail=str(e)).to_http_exception()
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/session/{session_id}/end", response_model=CoachSessionReport)
async def end_session(session_id: str, request: Request, user: User = Depends(get_current_user)):
    coach = _get_coach(request)
    _require_owned_session(coach, request.app.state.database, session_id, user.id)
    try:
        return coach.end_session(session_id)
    except AppError as e:
        raise e.to_http_exception()
    except KeyError as e:
        raise ForbiddenError(detail=str(e)).to_http_exception()
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=str(e))