"""
核心配置模块
使用 pydantic-settings 从 .env 文件加载环境变量配置
"""
import os
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend_python），所有相对路径以此为基准，不依赖启动目录（CWD）
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _resolve_project_path(value: str) -> str:
    """相对路径锚定到项目根：无论从哪个目录启动，路径都指向项目内同一位置"""
    p = Path(value)
    if p.is_absolute():
        return str(p)
    return str((BASE_DIR / p).resolve())


class Settings(BaseSettings):
    """应用配置 - 所有配置自动从环境变量读取"""

    # DashScope API 配置
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")

    # LLM 模型配置（支持 ASR 语音识别）
    llm_model_name: str = Field(default="qwen3.5-omni-plus", alias="LLM_MODEL_NAME")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")

    # 音频文件存储路径（锚定项目内）
    audio_storage_path: str = Field(default=str(DATA_DIR / "audio"), alias="AUDIO_STORAGE_PATH")

    # Java 业务后端地址
    java_backend_url: str = Field(default="http://localhost:8080", alias="JAVA_BACKEND_URL")

    # RAG配置（本地离线模型：首次自动从 HuggingFace 下载到项目内缓存，之后完全离线）
    rag_doc_root: str = Field(default=str(DATA_DIR / "rag_docs"), alias="RAG_DOC_ROOT")
    sqlite_db_path: str = Field(default=str(DATA_DIR / "interview.db"), alias="SQLITE_DB_PATH")
    # 本地模型缓存目录（HuggingFace hub 格式，随项目可移植）
    model_cache_dir: str = Field(default=str(BASE_DIR / "models" / "hf_cache"), alias="MODEL_CACHE_DIR")
    # PDF 图片 OCR（离线，RapidOCR；识别图片区域文字并入对应题目答案）
    pdf_ocr_enabled: bool = Field(default=True, alias="PDF_OCR_ENABLED")
    pdf_ocr_resolution: int = Field(default=300, alias="PDF_OCR_RESOLUTION")
    embedding_model: str = Field(default="BAAI/bge-large-zh-v1.5", alias="EMBEDDING_MODEL")
    # 以下 Key 配置已离线化废弃（保留字段仅兼容 .env），本地模型不再调用外部 API
    rag_api_key: str = Field(default="", alias="RAG_API_KEY")
    rag_rerank_base_url: str = Field(default="", alias="RAG_RERANK_BASE_URL")
    rag_rerank_model: str = Field(default="BAAI/bge-reranker-base", alias="RAG_RERANK_MODEL")
    rag_top_k: int = Field(default=3, alias="RAG_TOP_K")
    rag_similar_threshold: float = Field(default=0.25, alias="RAG_THRESHOLD")
    rag_vector_weight: float = Field(default=0.7, alias="RAG_VECTOR_WEIGHT")
    rag_bm25_weight: float = Field(default=0.3, alias="RAG_BM25_WEIGHT")
    rag_use_rerank: bool = Field(default=True, alias="RAG_USE_RERANK")
    chunk_size: int = Field(default=300, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=60, alias="CHUNK_OVERLAP")

    @field_validator("rag_doc_root", "sqlite_db_path", "model_cache_dir", "audio_storage_path")
    @classmethod
    def _anchor_paths(cls, value: str) -> str:
        """路径锚定项目根：.env 或环境变量里的相对路径同样基于 BASE_DIR 解析"""
        return _resolve_project_path(value)

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


# 全局设置实例
settings = Settings()
