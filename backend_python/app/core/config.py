"""
核心配置模块
使用 pydantic-settings 从 .env 文件加载环境变量配置
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置 - 所有配置自动从环境变量读取"""

    # DashScope API 配置
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")

    # LLM 模型配置（支持 ASR 语音识别）
    llm_model_name: str = Field(default="qwen3.5-omni-plus", alias="LLM_MODEL_NAME")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")

    # 音频文件存储路径
    audio_storage_path: str = Field(default="./data/audio", alias="AUDIO_STORAGE_PATH")

    # Java 业务后端地址
    java_backend_url: str = Field(default="http://localhost:8080", alias="JAVA_BACKEND_URL")

    # RAG配置
    rag_doc_root: str = Field(default="./data/rag_docs", alias="RAG_DOC_ROOT")
    sqlite_db_path: str = Field(default="./data/interview.db", alias="SQLITE_DB_PATH")
    embedding_model: str = Field(default="text-embedding-v3", alias="EMBEDDING_MODEL")
    rag_top_k: int = Field(default=3, alias="RAG_TOP_K")
    rag_similar_threshold: float = Field(default=0.01, alias="RAG_THRESHOLD")
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


# 全局设置实例
settings = Settings()
