"""
认证服务（app/services/auth_service.py）

v3.1 阶段 D：JWT 双 Token 认证（register / login / refresh + 当前用户解析）。

深模块：对外仅暴露
    register(phone, password, nickname) -> TokenPair
    login(phone, password)               -> TokenPair
    refresh(refresh_token)               -> TokenPair
    create_token_pair(user)              -> TokenPair
    parse_access(access_token)           -> User   （供各 API 的 Depends 使用）

内部封装密码哈希（PBKDF2-HMAC-SHA256，标准库无额外依赖）与 JWT 签发/校验。
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.config import settings
from app.core.database import Database
from app.core.exceptions import AuthCredentialsError, RegisterError
from app.models.entities import User

# 认证常量
_ITERATIONS = 120_000
_HASH_FUNC = "sha256"
_ACCESS = "access"
_REFRESH = "refresh"


class TokenPair(dict):
    """JWT 双 Token 结果（restricted dict，便于 FastAPI 直接序列化）"""

    def __init__(self, access_token: str, refresh_token: str, user_id: int):
        super().__init__(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user_id,
        )


class AuthService:
    """认证深模块（JWT 双 Token）"""

    def __init__(self, database: Optional[Database] = None):
        self.db = database if database is not None else Database()

    # ── 密码哈希（标准库 PBKDF2，格式：func$iterations$salt_hex$hash_hex）──

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac(_HASH_FUNC, password.encode("utf-8"), salt, _ITERATIONS)
        return f"pbkdf2${_HASH_FUNC}${_ITERATIONS}${salt.hex()}${dk.hex()}"

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        try:
            _func, _algo, iterations, salt_hex, hash_hex = stored.split("$")
            if _func != "pbkdf2" or _algo != _HASH_FUNC:
                return False
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
            dk = hashlib.pbkdf2_hmac(_HASH_FUNC, password.encode("utf-8"), salt, int(iterations))
            return secrets.compare_digest(dk, expected)
        except (ValueError, TypeError):
            return False

    # ── 业务动作 ──────────────────────────────────────────

    def register(self, phone: str, password: str, nickname: str = "") -> TokenPair:
        if not phone or not password:
            raise RegisterError(detail="手机号和密码不能为空")
        if len(password) < 6:
            raise RegisterError(detail="密码至少 6 位")
        if self.db.get_user_by_phone(phone) is not None:
            raise RegisterError(detail="该手机号已注册")
        user_id = self.db.create_user(phone, self._hash_password(password), nickname)
        user = self.db.get_user_by_id(user_id)
        return self.create_token_pair(user)

    def login(self, phone: str, password: str) -> TokenPair:
        user = self.db.get_user_by_phone(phone)
        if user is None or not self._verify_password(password, user.hashed_password):
            raise AuthCredentialsError(detail="手机号或密码错误")
        return self.create_token_pair(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        claims = self._decode(refresh_token, expected_type=_REFRESH)
        user = self.db.get_user_by_id(claims["user_id"])
        if user is None:
            raise AuthCredentialsError(detail="用户不存在")
        return self.create_token_pair(user)

    # ── JWT 签发 / 校验 ───────────────────────────────────

    def create_token_pair(self, user: User) -> TokenPair:
        now = datetime.now(timezone.utc)
        access_claims = {
            "sub": str(user.id),
            "user_id": user.id,
            "type": _ACCESS,
            "jti": secrets.token_hex(8),
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
        }
        refresh_claims = {
            "sub": str(user.id),
            "user_id": user.id,
            "type": _REFRESH,
            "jti": secrets.token_hex(8),
            "iat": now,
            "exp": now + timedelta(days=settings.jwt_refresh_expire_days),
        }
        access = jwt.encode(access_claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        refresh = jwt.encode(refresh_claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return TokenPair(access, refresh, user.id)

    def decode_access(self, access_token: str) -> dict:
        return self._decode(access_token, expected_type=_ACCESS)

    def _decode(self, token: str, expected_type: str) -> dict:
        try:
            claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.PyJWTError as e:
            raise AuthCredentialsError(detail="token 无效或已过期") from e
        if claims.get("type") != expected_type:
            raise AuthCredentialsError(detail="token 类型不匹配")
        return claims

    def parse_access(self, access_token: str) -> User:
        claims = self.decode_access(access_token)
        user = self.db.get_user_by_id(claims["user_id"])
        if user is None:
            raise AuthCredentialsError(detail="用户不存在")
        return user

    def __repr__(self) -> str:
        return f"<AuthService db={self.db.db_path}>"


# 便捷入口（避免调用方 import 服务直接引 App main）
def make_auth_service(database: Optional[Database] = None) -> AuthService:
    return AuthService(database=database)