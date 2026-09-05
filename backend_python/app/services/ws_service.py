"""
WebSocket 广播服务（app/services/ws_service.py）

v3.1 阶段 A：原生 WebSocket 实时推送（替代 Java 后端 STOMP），协议对齐架构 §9.4：
    interview.{id}.progress / complete / error
    coach.{sessionId}.feedback
    user.{id}.notifications

连接：ws://host/ws?token=<access>&subscribe=interview.3,coach.abc
- token：JWT access token（认证当前用户；无效/缺失则握手 403）
- subscribe：逗号分隔的主题（决定该连接接收哪些广播；可重复指定通用主题 user.{id}.notifications）

消息：JSON {"type": "<topic>", "payload": {...}}
推送：WebSocketHub.broadcast(topic, payload) 精确投递到订阅该主题的连接。
"""
import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

_TOPIC_RE = re.compile(r"^[A-Za-z]+\.\S+$")


class WebSocketHub:
    """广播中枢（深模块）：连接注册 + 主题订阅 + 精确广播。"""

    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._subs: Dict[str, List[WebSocket]] = {}   # topic -> 订阅连接
        self._lock = asyncio.Lock()

    # ── 连接管理 ──────────────────────────────────────

    async def connect(self, ws: WebSocket, topics: List[str]) -> None:
        """接受连接并登记主题订阅（握手前由路由完成 token 校验）"""
        await ws.accept()
        async with self._lock:
            self._connections.append(ws)
            for t in topics:
                if _TOPIC_RE.match(t or ""):
                    self._subs.setdefault(t, []).append(ws)
        logger.info("WS 连接接入 topics=%s 当前=%d", topics, len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._connections:
                self._connections.remove(ws)
            for topic in list(self._subs):
                if ws in self._subs[topic]:
                    self._subs[topic].remove(ws)
                    if not self._subs[topic]:
                        del self._subs[topic]
        logger.info("WS 连接断开 剩余=%d", len(self._connections))

    # ── 广播 ──────────────────────────────────────────

    async def broadcast(self, topic: str, payload: Any) -> int:
        """向订阅该主题（或主题前缀，如 interview.3）的连接推送 JSON；返回推送成功数"""
        async with self._lock:
            targets = [
                w for sub, ws_list in self._subs.items()
                if topic == sub or topic.startswith(sub + ".")
                for w in ws_list
            ]
        if not targets:
            return 0
        message = _encode({"type": topic, "payload": payload})
        delivered = 0
        dead: List[WebSocket] = []
        for ws in targets:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(message)
                    delivered += 1
                else:
                    dead.append(ws)
            except Exception as e:  # noqa: BLE001（单个连接异常不影响其余）
                logger.warning("WS 推送失败 topic=%s err=%s", topic, e)
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)
        return delivered

    # ── 工具 ──────────────────────────────────────────

    @staticmethod
    def interview_topic_prefix(interview_id: int) -> str:
        return f"interview.{interview_id}"

    async def serve(self, ws: WebSocket, topics: List[str]) -> None:
        """常驻循环：持有连接直到断开（真实客户端可能仅收不发）"""
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            await self.disconnect(ws)
        finally:
            await self.disconnect(ws)

    def close(self) -> None:
        self._connections.clear()
        self._subs.clear()


def _encode(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)