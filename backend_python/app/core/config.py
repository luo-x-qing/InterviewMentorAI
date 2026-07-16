"""
核心配置模块
从 .env 文件加载环境变量配置
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Settings:
    """应用配置 - 所有配置从环境变量读取"""
    
    # DashScope API 配置
    dashscope_api_key: str = ""
    
    # LLM 模型配置（支持 ASR 语音识别）
    llm_model_name: str = ""
    llm_temperature: float = 0.3
    llm_base_url: str = ""
    
    # 音频文件存储路径
    audio_storage_path: str = "./data/audio"
    
    # Java 业务后端地址
    java_backend_url: str = "http://localhost:8080"

    # RAG配置（全部环境变量可覆盖，0008运维优化）
    rag_doc_root: str = "./data/rag_docs"
    sqlite_db_path: str = "./data/interview.db"
    embedding_model: str = "text-embedding-v3"
    rag_top_k: int = 3          # 单次检索返回3条｜0004检索条数调优
    rag_similar_threshold: float = 0.01  # 低于0.01直接过滤无关文档｜0004相似度过滤
    chunk_size: int = 500       # 分块大小｜0002文档分块
    chunk_overlap: int = 100    # 重叠20%｜0002重叠参数
    
    def __post_init__(self):
        """从环境变量加载配置"""
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "qwen3.5-omni-plus")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.llm_base_url = os.getenv("LLM_BASE_URL", "")
        self.audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "./data/audio")
        self.java_backend_url = os.getenv("JAVA_BACKEND_URL", "http://localhost:8080")
         # RAG环境变量加载
        self.rag_doc_root = os.getenv("RAG_DOC_ROOT", "./data/rag_docs")
        self.sqlite_db_path = os.getenv("SQLITE_DB_PATH", "./data/interview.db")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
        self.rag_top_k = int(os.getenv("RAG_TOP_K", "3"))
        self.rag_similar_threshold = float(os.getenv("RAG_THRESHOLD", "0.01"))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))


# 全局设置实例
settings = Settings()
