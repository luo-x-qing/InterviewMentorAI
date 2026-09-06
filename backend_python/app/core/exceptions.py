"""
应用异常层次结构（错误处理的单一出口 · 深度模块）

所有自定义异常继承自 AppError，支持精确捕获和分层处理。
API 层根据异常类型映射到不同的 HTTP 状态码。

层次结构:
    AppError (base)
    ├── LlmError           # LLM 调用相关
    │   ├── LlmTimeoutError
    │   └── LlmRateLimitError
    ├── VectorDbError      # 向量数据库相关
    │   ├── VectorDbInsertError
    │   └── VectorDbSearchError
    ├── EmbeddingError     # 向量化相关
    ├── ChunkingError      # 分块相关
    ├── KnowledgeError     # 知识库管理相关
    │   └── KnowledgeImportError
    ├── PipelineError      # 流水线相关
    └── AuthError          # 认证/授权（阶段 D）
        ├── AuthCredentialsError  → 401
        ├── RegisterError         → 409
        └── ForbiddenError        → 403

错误响应契约（§8.3 可观测错误）：
- 业务/预期错误：`{detail, error_code, trace_id}`，error_code 为稳定机器码
  （默认 = 异常类名，可用 error_code= 显式覆盖），trace_id 关联后端日志。
- 未捕获异常：`500 {detail: 服务器内部错误, error_code: INTERNAL_SERVER_ERROR, trace_id}`，
  不透出内部堆栈；完整 traceback 与 trace_id 进入日志，供维护者快速锁定。
"""
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """应用基础异常"""

    def __init__(self, message: str, detail: str = None, error_code: str = None):
        self.message = message
        self.detail = detail or message
        self.error_code = error_code or type(self).__name__
        super().__init__(self.message)

    def to_http_exception(self, status_code: int = 500) -> HTTPException:
        """转换为 FastAPI HTTPException"""
        return HTTPException(status_code=status_code, detail=self.detail)


# ─── LLM 异常 ──────────────────────────────────────────────

class LlmError(AppError):
    """LLM 调用异常基类"""
    pass


class LlmTimeoutError(LlmError):
    """LLM 调用超时"""
    def __init__(self, message: str = "LLM 调用超时", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=504, detail=self.detail)


class LlmRateLimitError(LlmError):
    """LLM 调用频率限制"""
    def __init__(self, message: str = "LLM 调用频率超限", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=429, detail=self.detail)


# ─── 向量数据库异常 ─────────────────────────────────────────

class VectorDbError(AppError):
    """向量数据库异常基类"""
    pass


class VectorDbInsertError(VectorDbError):
    """向量数据库插入失败"""
    def __init__(self, message: str = "文档入库失败", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=500, detail=self.detail)


class VectorDbSearchError(VectorDbError):
    """向量数据库检索失败"""
    def __init__(self, message: str = "向量检索失败", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=500, detail=self.detail)


# ─── 向量化异常 ─────────────────────────────────────────────

class EmbeddingError(AppError):
    """向量化异常"""
    def __init__(self, message: str = "向量化失败", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=500, detail=self.detail)


# ─── 分块异常 ───────────────────────────────────────────────

class ChunkingError(AppError):
    """文档分块异常"""
    def __init__(self, message: str = "文档分块失败", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=500, detail=self.detail)


# ─── 知识库异常 ─────────────────────────────────────────────

class KnowledgeError(AppError):
    """知识库管理异常基类"""
    pass


class KnowledgeImportError(KnowledgeError):
    """知识库导入失败"""
    def __init__(self, message: str = "知识库导入失败", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=500, detail=self.detail)


# ─── 流水线异常 ─────────────────────────────────────────────

class PipelineError(AppError):
    """Agent 流水线异常"""
    def __init__(self, message: str = "流水线执行失败", detail: str = None):
        super().__init__(message, detail)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=500, detail=self.detail)


# ─── 认证异常（阶段 D：用户 /auth /user 业务）────────────────

class AuthError(AppError):
    """认证/授权异常基类"""
    pass


class AuthCredentialsError(AuthError):
    """凭证无效（登录失败 / token 无效 / 已过期）"""
    def __init__(self, message: str = "凭证无效或已过期", detail: str = None):
        super().__init__(message, detail)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=401, detail=self.detail, headers={"WWW-Authenticate": "Bearer"})


class RegisterError(AuthError):
    """注册冲突（手机号已存在）"""
    def __init__(self, message: str = "注册失败", detail: str = None):
        super().__init__(message, detail)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=409, detail=self.detail)


class ForbiddenError(AuthError):
    """资源归属校验失败（用户无权访问他人资源）"""
    def __init__(self, message: str = "无权访问该资源", detail: str = None):
        super().__init__(message, detail)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=403, detail=self.detail)


def _new_trace_id() -> str:
    """短 trace_id：客户端响应与后端日志的关联键（grep 一行定位）"""
    return uuid.uuid4().hex[:12]


def register_error_handlers(app: FastAPI) -> None:
    """注册全局异常处理器——错误响应的唯一出口（生产 main 与测试均可复用）。

    - AppError：记录带完整栈的错误日志（含 trace_id/method/path），返回
      `{detail, error_code, trace_id}`，状态码/headers 由异常自身决定。
    - HTTPException：5xx 补记错误日志，其余透传原样（不改变现有契约）。
    - 未捕获 Exception：完整 traceback 入日志，返回安全兜底 500（不透内部文本）。
    """

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        trace_id = _new_trace_id()
        logger.error(
            "业务异常 trace_id=%s code=%s method=%s path=%s message=%s",
            trace_id, exc.error_code, request.method, request.url.path, exc.message,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        http_exc = exc.to_http_exception()
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"detail": http_exc.detail, "error_code": exc.error_code, "trace_id": trace_id},
            headers=http_exc.headers or {},
        )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        # 5xx 属服务器故障，补记日志便于定位；4xx 系正常业务驳回，保持静默透传
        if exc.status_code >= 500:
            logger.error(
                "HTTP 5xx trace_id=%s status=%s method=%s path=%s detail=%s",
                _new_trace_id(), exc.status_code, request.method, request.url.path, exc.detail,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers or {},
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = _new_trace_id()
        logger.error(
            "未捕获异常 trace_id=%s method=%s path=%s 类型=%s",
            trace_id, request.method, request.url.path, type(exc).__name__,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误",
                "error_code": "INTERNAL_SERVER_ERROR",
                "trace_id": trace_id,
            },
        )
