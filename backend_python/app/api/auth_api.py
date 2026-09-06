"""
认证 API 路由（app/api/auth_api.py）

阶段 D：JWT 双 Token 认证端点（与前端 constants.dart 的 /auth/* 契约对齐）：
    POST /auth/register       注册（手机号 + 密码，返回双 Token）
    POST /auth/login          登录（返回双 Token）
    POST /auth/refresh        刷新 Token（refresh_token → 新双 Token）
    GET  /auth/me             当前用户信息（Bearer）
"""
import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.exceptions import AuthError, RegisterError
from app.models.entities import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20, description="手机号")
    password: str = Field(..., min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=32)


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20)
    password: str = Field(..., min_length=6, max_length=64)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int


class UserOut(BaseModel):
    id: int
    phone: str
    nickname: str
    created_at: str = ""


@router.post("/register", response_model=TokenPairOut)
async def register(body: RegisterRequest, request: Request):
    auth = request.app.state.auth_service
    try:
        tokens = auth.register(body.phone, body.password, body.nickname)
        return TokenPairOut(**tokens)
    except RegisterError:
        raise


@router.post("/login", response_model=TokenPairOut)
async def login(body: LoginRequest, request: Request):
    auth = request.app.state.auth_service
    try:
        tokens = auth.login(body.phone, body.password)
        return TokenPairOut(**tokens)
    except AuthError:
        raise


@router.post("/refresh", response_model=TokenPairOut)
async def refresh(body: RefreshRequest, request: Request):
    auth = request.app.state.auth_service
    try:
        tokens = auth.refresh(body.refresh_token)
        return TokenPairOut(**tokens)
    except AuthError:
        raise


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, phone=user.phone, nickname=user.nickname, created_at=user.created_at)