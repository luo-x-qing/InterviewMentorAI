"""
InterviewMentorAI Python AI 后端
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis import router as analysis_router
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Python AI 后端启动中...")
    logger.info(f"LLM 模型: {settings.llm_model_name}")
    yield
    logger.info("Python AI 后端关闭中...")


# 创建 FastAPI 应用
app = FastAPI(
    title="InterviewMentorAI Python Backend",
    description="AI Agent 语音识别与分析服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analysis_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "InterviewMentorAI Python AI Backend",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
