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
    
    def __post_init__(self):
        """从环境变量加载配置"""
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "qwen3.5-omni-plus")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.llm_base_url = os.getenv("LLM_BASE_URL", "")
        self.audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "./data/audio")
        self.java_backend_url = os.getenv("JAVA_BACKEND_URL", "http://localhost:8080")


# 全局设置实例
settings = Settings()
