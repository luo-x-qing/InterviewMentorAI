"""
MCP 工具层核心（app/mcp/server.py）

把后端全部业务/检索能力统一封装为标准化工具（Tool）：
- 工具只做「schema 声明 + 参数校验 + 转发业务服务」（浅适配器），不含业务逻辑
- Agent（LangGraph 节点 / 复盘 Orchestrator / Coach 内部 Worker）经 call_tool 调用
- 一处实现：REST 由 FastAPI Router 薄封装、工具由本层封装，共享同一业务服务

深模块接口（对外仅 3 个方法 + 注册入口）：
    register(tool)        # 注册一个工具（ToolSpec）
    list_tools()          # 列出全部工具（含 input schema）
    call_tool(name, args) # 调用工具，返回业务服务的结果值

底层的 FastMCP 用于把工具暴露为标准 MCP 协议（可选 stdio/SSE server），
进程内 Agent 走轻量的 call_tool（解包 FastMCP 的 TextContent/meta）。
"""

import inspect
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """工具调用异常"""


class ToolSpec:
    """一个工具的声明：名称 + 输入 schema + 处理函数"""

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        input_model: Optional[type] = None,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.input_model = input_model  # Pydantic 模型，用于参数校验与 schema 生成


class ToolRegistry:
    """进程内工具注册表 + 进程内调用器（深模块）"""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._mcp: Optional[FastMCP] = None

    # ── 注册 ──────────────────────────────────────────

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ToolError(f"工具已注册: {spec.name}")
        self._tools[spec.name] = spec
        logger.debug("已注册 MCP 工具: %s", spec.name)

    def register_many(self, specs: List[ToolSpec]) -> None:
        for spec in specs:
            self.register(spec)

    # ── 查询 ──────────────────────────────────────────

    def list_tools(self) -> List[Dict[str, Any]]:
        """返回工具清单（名称 + 描述 + 入参 schema）"""
        out = []
        for name, spec in self._tools.items():
            schema = None
            if spec.input_model is not None:
                try:
                    schema = spec.input_model.model_json_schema()
                except Exception:  # pydantic v1 兼容
                    schema = spec.input_model.schema()
            out.append({
                "name": name,
                "description": spec.description,
                "input_schema": schema,
            })
        return out

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    # ── 调用 ──────────────────────────────────────────

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具，返回业务服务的结果（已整合 FastMCP 的分层协议）"""
        spec = self._tools.get(name)
        if spec is None:
            raise ToolError(f"未知工具: {name}")

        # 参数校验 / 规范化（用 input_model 校验并序列化）
        if spec.input_model is not None and arguments is not None:
            try:
                parsed = spec.input_model(**arguments)
                kwargs = parsed.model_dump()
            except ValidationError as e:
                raise ToolError(f"工具 {name} 参数非法: {e}") from e
        else:
            kwargs = dict(arguments or {})

        result = spec.handler(**kwargs)

        # 等待异步 handler
        if inspect.isawaitable(result):
            result = await result

        # 序列化：Pydantic / dataclass / 原生类型 → JSON 可表达
        return self._to_jsonable(result)

    # ── 私有 ──────────────────────────────────────────

    @staticmethod
    def _to_jsonable(value: Any) -> Any:
        """把业务结果规整为 JSON 可表达值（供 Agent 直接消费 / WebSocket 推送）"""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, BaseModel):
            return value.model_dump()
        if hasattr(value, "__dataclass__"):
            from dataclasses import asdict
            return asdict(value)
        if isinstance(value, (list, tuple)):
            return [ToolRegistry._to_jsonable(v) for v in value]
        if isinstance(value, dict):
            return {k: ToolRegistry._to_jsonable(v) for k, v in value.items()}
        return str(value)

    # ── FastMCP 标准协议兜底（可选 stdio/SSE server）────

    def to_mcp_server(self) -> FastMCP:
        """返回标准 FastMCP server（可 run stdio/SSE）。

        进程内 Agent 走轻量的 call_tool（本类核心接口）；当需要把工具暴露给
        外部 MCP 兼容客户端时，用此 server 挂一个装饰器注册同名 handler：
            srv = registry.to_mcp_server()
            @srv.tool()
            def knowledge_import(file_path: str) -> str:
                return asyncio.run(registry.call_tool("knowledge.import", {...}))
        本骨架不强制动态映射，保持对 FastMCP 内部实现的零依赖。
        """
        if self._mcp is None:
            self._mcp = FastMCP("interview-mentor")
        return self._mcp