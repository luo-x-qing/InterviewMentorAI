"""
用户 API 路由（app/api/user_api.py）

阶段 D：当前用户资料端点（与前端 constants.dart 的 /user/profile 对齐）：
    GET  /user/profile        当前用户画像（薄弱点 / 强项 / 掌握度）
    PUT  /user/profile        当前用户资料（昵称等）
"""
import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.entities import User, UserProfileOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


class ProfileUpdateRequest(BaseModel):
    nickname: str = Field(default="", max_length=32)


@router.get("/profile", response_model=UserProfileOut)
async def get_profile(request: Request, user: User = Depends(get_current_user)):
    db = request.app.state.database
    profile = db.get_profile(user.id)
    if profile is None:
        return UserProfileOut(user_id=user.id)
    return UserProfileOut(
        user_id=profile.user_id,
        strengths=profile.strengths,
        weaknesses=profile.weaknesses,
        mastery=profile.mastery,
    )


@router.put("/profile", response_model=UserProfileOut)
async def update_profile(
    body: ProfileUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    from app.models import entities

    db = request.app.state.database
    if body.nickname:
        db.execute("UPDATE users SET nickname = ? WHERE id = ?", (body.nickname, user.id))
    profile = db.get_profile(user.id)
    if profile is None:
        return UserProfileOut(user_id=user.id)
    return UserProfileOut(
        user_id=profile.user_id,
        strengths=profile.strengths,
        weaknesses=profile.weaknesses,
        mastery=profile.mastery,
    )