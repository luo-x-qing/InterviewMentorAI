"""
异常层次结构单元测试
"""
import pytest
from app.core.exceptions import (
    AppError,
    LlmError, LlmTimeoutError, LlmRateLimitError,
    VectorDbError, VectorDbInsertError, VectorDbSearchError,
    EmbeddingError,
    ChunkingError,
    KnowledgeError, KnowledgeImportError,
    PipelineError
)


class TestAppError:
    def test_base_exception(self):
        err = AppError("测试错误", "详细信息")
        assert err.message == "测试错误"
        assert err.detail == "详细信息"
        assert str(err) == "测试错误"
    
    def test_to_http_exception(self):
        err = AppError("测试错误", "详细信息")
        http_err = err.to_http_exception(status_code=500)
        assert http_err.status_code == 500
        assert http_err.detail == "详细信息"
    
    def test_default_detail(self):
        err = AppError("测试错误")
        assert err.detail == "测试错误"


class TestLlmError:
    def test_inheritance(self):
        assert issubclass(LlmError, AppError)
    
    def test_to_http_exception(self):
        err = LlmError("LLM 调用失败")
        http_err = err.to_http_exception()
        assert http_err.status_code == 500


class TestLlmTimeoutError:
    def test_inheritance(self):
        assert issubclass(LlmTimeoutError, LlmError)
        assert issubclass(LlmTimeoutError, AppError)
    
    def test_default_message(self):
        err = LlmTimeoutError()
        assert err.message == "LLM 调用超时"
    
    def test_to_http_exception(self):
        err = LlmTimeoutError()
        http_err = err.to_http_exception()
        assert http_err.status_code == 504


class TestLlmRateLimitError:
    def test_inheritance(self):
        assert issubclass(LlmRateLimitError, LlmError)
        assert issubclass(LlmRateLimitError, AppError)
    
    def test_default_message(self):
        err = LlmRateLimitError()
        assert err.message == "LLM 调用频率超限"
    
    def test_to_http_exception(self):
        err = LlmRateLimitError()
        http_err = err.to_http_exception()
        assert http_err.status_code == 429


class TestVectorDbError:
    def test_inheritance(self):
        assert issubclass(VectorDbError, AppError)


class TestVectorDbInsertError:
    def test_inheritance(self):
        assert issubclass(VectorDbInsertError, VectorDbError)
        assert issubclass(VectorDbInsertError, AppError)
    
    def test_default_message(self):
        err = VectorDbInsertError()
        assert err.message == "文档入库失败"


class TestVectorDbSearchError:
    def test_inheritance(self):
        assert issubclass(VectorDbSearchError, VectorDbError)
        assert issubclass(VectorDbSearchError, AppError)


class TestEmbeddingError:
    def test_inheritance(self):
        assert issubclass(EmbeddingError, AppError)
    
    def test_default_message(self):
        err = EmbeddingError()
        assert err.message == "向量化失败"


class TestChunkingError:
    def test_inheritance(self):
        assert issubclass(ChunkingError, AppError)
    
    def test_default_message(self):
        err = ChunkingError()
        assert err.message == "文档分块失败"


class TestKnowledgeError:
    def test_inheritance(self):
        assert issubclass(KnowledgeError, AppError)


class TestKnowledgeImportError:
    def test_inheritance(self):
        assert issubclass(KnowledgeImportError, KnowledgeError)
        assert issubclass(KnowledgeImportError, AppError)


class TestPipelineError:
    def test_inheritance(self):
        assert issubclass(PipelineError, AppError)
    
    def test_default_message(self):
        err = PipelineError()
        assert err.message == "流水线执行失败"
    
    def test_to_http_exception(self):
        err = PipelineError("流水线失败", "详细信息")
        http_err = err.to_http_exception()
        assert http_err.status_code == 500
        assert http_err.detail == "详细信息"
