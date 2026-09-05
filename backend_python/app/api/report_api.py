"""
复盘报告 API 路由（app/api/report_api.py）

阶段 D：复盘报告读取（与前端 constants.dart 的 /report/interview/{id}/* 对齐）：
    GET /report/interview/{id}/report        报告正文
    GET /report/interview/{id}/evaluations   评估明细
    GET /report/list                         当前用户全部报告列表
"""
import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.exceptions import ForbiddenError
from app.models.entities import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


class ReportOut(BaseModel):
    interview_id: int
    content: str
    created_at: str = ""


class EvaluationBrief(BaseModel):
    question: str = ""
    answer: str = ""
    score: int = 0
    level: str = ""
    strengths: str = ""
    weaknesses: str = ""


def _require_owned(db, interview_id: int, user_id: int):
    iv = db.get_interview(interview_id)
    if iv is None or iv.user_id != user_id:
        raise ForbiddenError(detail="无权访问该面试报告")
    return iv


@router.get("/interview/{interview_id}/report", response_model=ReportOut)
async def get_report(interview_id: int, request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    iv = _require_owned(db, interview_id, user.id)
    return ReportOut(interview_id=iv.id, content=iv.final_report or "", created_at=iv.created_at)


@router.get("/interview/{interview_id}/evaluations", response_model=list[EvaluationBrief])
async def get_evaluations(interview_id: int, request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    _require_owned(db, interview_id, user.id)
    # 评估明细持久化（interview_evaluations 表）属阶段 B 深化落点，当前骨架返回空
    return []


@router.get("/list", response_model=list[ReportOut])
async def list_reports(request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    return [
        ReportOut(interview_id=iv.id, content=iv.final_report or "", created_at=iv.created_at)
        for iv in db.list_interviews(user.id)
        if iv.final_report
    ]