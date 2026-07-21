"""
应用异常层次结构

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
    └── PipelineError      # 流水线相关
"""
from fastapi import HTTPException


class AppError(Exception):
    """应用基础异常"""
    
    def __init__(self, message: str, detail: str = None):
        self.message = message
        self.detail = detail or message
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
