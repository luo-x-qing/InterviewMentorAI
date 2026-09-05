"""
WebSocket 实时推送 API（app/api/ws_api.py）

v3.1 阶段 A：原生 WebSocket 进度推送端点（取代 Java STOMP）。

    连接：ws://host/ws?token=<access_token>&subscribe=interview.3,coach.abc
    - token：JWT access token（缺失/无效 → 403，不握手）
    - subscribe：逗号分隔的主题前缀列表
    推送：{"type": "interview.3.progress", "payload": {"message": "...", "percent": 50}}

Q：为什么握手用 query 传 token？
A：浏览器 WebSocket 无法设置 Authorization 头；query + 仅首次握手校验可避免 token 泄漏
   到日志（FastAPI ws.query_params 不回显完整 URL）。
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.exceptions import AuthCredentialsError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def ws_progress(ws: WebSocket):
    """原生 WebSocket：认证 + 主题订阅 + 推送到前端。"""
    token: Optional[str] = ws.query_params.get("token")
    topics_raw: Optional[str] = ws.query_params.get("subscribe", "")

    # 1. token 校验（不通过则拒绝握手）
    auth = ws.app.state.auth_service
    try:
        user = auth.parse_access(token or "")
    except (AuthCredentialsError, Exception) as e:
        logger.warning("WS 鉴权失败: %s", e)
        await ws.close(code=4401)
        return

    # 2. 订阅主题（附带 user.{id}.notifications 自动订阅）
    topics = [t.strip() for t in (topics_raw or "").split(",") if t.strip()]
    topics = list(dict.fromkeys(topics))
    topics.append(f"user.{user.id}.notifications")
    hub = ws.app.state.ws_hub

    await hub.connect(ws, topics)
    try:
        while True:
            # 客户端消息可忽略（当前仅单向推送）；receive 阻塞直到断开
            await ws.receive()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(ws)