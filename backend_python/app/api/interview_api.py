"""
面试记录 API 路由（app/api/interview_api.py）

阶段 D：面试记录 CRUD（与前端 constants.dart 的 /interview/* 对齐）：
    POST   /interview             新建面试记录（返回 interview_id）
    GET    /interview/list        当前用户全部面试（倒序）
    GET    /interview/my          当前用户全部面试（别名，前端契约）
    GET    /interview/{id}        面试详情（归属校验）
    POST   /interview/{id}/analyze 触发复盘分析（转调 Orchestrator，支持 progress 回调）
"""
import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.exceptions import AppError, ForbiddenError
from app.models.entities import Interview, InterviewStatus, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])


class InterviewCreateRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    audio_file_path: str = Field(default="")


class InterviewOut(BaseModel):
    id: int
    user_id: int
    title: str
    audio_file_path: str = ""
    status: str = InterviewStatus.PENDING.value
    created_at: str = ""
    final_report: str = ""


def _to_out(iv: Interview) -> InterviewOut:
    return InterviewOut(
        id=iv.id, user_id=iv.user_id, title=iv.title,
        audio_file_path=iv.audio_file_path, status=iv.status,
        created_at=iv.created_at, final_report=iv.final_report or "",
    )


def _require_owned(db, interview_id: int, user_id: int) -> Interview:
    iv = db.get_interview(interview_id)
    if iv is None:
        raise ForbiddenError(detail="面试记录不存在")
    if iv.user_id != user_id:
        raise ForbiddenError(detail="无权访问该面试记录")
    return iv


@router.post("", response_model=InterviewOut)
async def create_interview(
    body: InterviewCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    db = request.app.state.database
    iv_id = db.create_interview(user.id, body.title, body.audio_file_path)
    return _to_out(db.get_interview(iv_id))


@router.get("/list", response_model=list[InterviewOut])
async def list_interviews(request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    return [_to_out(iv) for iv in db.list_interviews(user.id)]


@router.get("/my", response_model=list[InterviewOut])
async def my_interviews(request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    return [_to_out(iv) for iv in db.list_interviews(user.id)]


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(interview_id: int, request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    iv = _require_owned(db, interview_id, user.id)
    return _to_out(iv)


@router.post("/{interview_id}/analyze", response_model=dict)
async def analyze_interview(
    interview_id: int,
    request: Request,
    user: User = Depends(get_current_user),
):
    """触发复盘分析（转调 Orchestrator；进度经 WS 实时推送，协议见架构 §9.4）。

    复盘完成后在编排层收尾（§10.1：归并 → 持久化 → 推送）：
    - 状态/报告/评估明细落库（interviews / interview_evaluations 表）
    - 薄弱项回写画像（ProfilingService.ingest_review，§7.5 数据闭环）
    - 一键推荐针对性练习（CoachService，模糊基于画像弱项）
    """
    from app.models.schemas import AnalysisRequest, AnalysisStatus

    db = request.app.state.database
    orchestrator = request.app.state.orchestrator
    hub = getattr(request.app.state, "ws_hub", None)
    iv = _require_owned(db, interview_id, user.id)
    topic = f"interview.{iv.id}"

    if hub is not None:

        async def _on_progress(step: int, total: int, message: str, status: AnalysisStatus):
            await hub.broadcast(f"{topic}.progress", {
                "message": message, "percent": round(step / total * 100),
                "step": step, "total": total,
            })

        orchestrator.subscribe(_on_progress)

    try:
        response = await orchestrator.run(
            AnalysisRequest(interview_id=iv.id, audio_file_path=iv.audio_file_path)
        )
    except AppError as e:
        if hub is not None:
            await hub.broadcast(f"{topic}.error", {"message": str(e)})
        db.update_interview_status(interview_id, InterviewStatus.FAILED.value)
        raise e.to_http_exception()

    # ── 收尾：持久化 + 画像回写 + 推荐 + 推送 ──────────────
    recommendations = []
    if response.status == AnalysisStatus.COMPLETED:
        db.update_interview_status(interview_id, InterviewStatus.COMPLETED.value,
                                   response.report or "")
        if response.evaluations:
            db.save_interview_evaluations(interview_id, response.evaluations)
            profiling = getattr(request.app.state, "profiling_service", None)
            if profiling is not None:
                try:
                    profiling.ingest_review(user.id, response.evaluations)
                except Exception as e:  # noqa: BLE001
                    logger.warning("画像回写失败: %s", e)
        coach = getattr(request.app.state, "coach_service", None)
        if coach is not None:
            try:
                recommendations = coach.recommend_practice(user.id, limit=3)
            except Exception as e:  # noqa: BLE001
                logger.warning("推荐练习降级为空: %s", e)
        if hub is not None:
            await hub.broadcast(f"{topic}.complete", {
                "message": "复盘完成", "report": response.report or "",
                "recommendations": recommendations,
            })
    else:
        db.update_interview_status(interview_id, InterviewStatus.FAILED.value)
        if hub is not None:
            await hub.broadcast(f"{topic}.error", {"message": response.error or "分析失败"})

    return {
        "status": response.status.value,
        "interview_id": interview_id,
        "recommendations": recommendations,
    }