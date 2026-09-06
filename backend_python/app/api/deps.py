"""
共享 API 依赖（app/api/deps.py）

提供客户端认证依赖：从 app.state 取 AuthService 解析 Bearer Token → 当前用户。
供所有需要登录的业务路由使用，避免各 router 重复实现。
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthCredentialsError
from app.models.entities import User

_security = HTTPBearer(auto_error=False)


def get_auth_service(request: Request):
    """从 app.state 取 AuthService（lifespan 装配）"""
    return request.app.state.auth_service


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> User:
    """解析 Bearer Token → 当前用户；缺失或无效则 401"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
    auth = request.app.state.auth_service
    try:
        return auth.parse_access(credentials.credentials)
    except AuthCredentialsError:
        raise