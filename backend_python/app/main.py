"""
InterviewMentorAI Python AI 后端
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from typing import Generator

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 严格按依赖顺序创建服务实例"""
    logger.info("Python AI 后端启动中...")
    logger.info(f"LLM 模型: {settings.llm_model_name}")
    
    # 按依赖拓扑排序依次创建服务实例
    # 1. 创建无依赖的基础服务
    from app.core.vector_db import VectorDB
    from app.services.llm_service import LlmService
    
    vector_db = VectorDB()
    llm_service = LlmService()
    
    # 2. 创建依赖基础服务的中间服务
    from app.services.rag_service import RagService
    from app.services.rag_mcp import RagMCP
    
    rag_service = RagService(vector_db=vector_db, llm_service=llm_service)
    rag_mcp = RagMCP(rag_service=rag_service, llm_service=llm_service)
    
    # 3. 创建依赖所有服务的顶层服务
    from app.services.agent_pipeline import AgentPipeline
    from app.services.knowledge_service import KnowledgeService
    
    agent_pipeline = AgentPipeline(llm_service=llm_service, rag_mcp=rag_mcp)
    knowledge_service = KnowledgeService(vector_db=vector_db)
    
    # 存储到app.state
    app.state.vector_db = vector_db
    app.state.llm_service = llm_service
    app.state.rag_service = rag_service
    app.state.rag_mcp = rag_mcp
    app.state.agent_pipeline = agent_pipeline
    app.state.knowledge_service = knowledge_service
    
    logger.info("所有服务实例创建完成")
    
    yield
    
    # 按依赖逆序清理资源
    logger.info("Python AI 后端关闭中...")
    if hasattr(app.state, 'knowledge_service'):
        app.state.knowledge_service.close()
    if hasattr(app.state, 'agent_pipeline'):
        app.state.agent_pipeline.close()
    if hasattr(app.state, 'rag_mcp'):
        app.state.rag_mcp.close()
    if hasattr(app.state, 'rag_service'):
        app.state.rag_service.close()
    if hasattr(app.state, 'llm_service'):
        app.state.llm_service.close()
    if hasattr(app.state, 'vector_db'):
        app.state.vector_db.close()
    logger.info("所有资源已清理")


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


# 依赖注入函数
def get_vector_db(request: Request):
    """获取向量数据库实例"""
    return request.app.state.vector_db


def get_llm_service(request: Request):
    """获取LLM服务实例"""
    return request.app.state.llm_service


def get_rag_service(request: Request):
    """获取RAG服务实例"""
    return request.app.state.rag_service


def get_rag_mcp(request: Request):
    """获取RAG-MCP调度层实例"""
    return request.app.state.rag_mcp


def get_agent_pipeline(request: Request):
    """获取Agent流水线实例"""
    return request.app.state.agent_pipeline


def get_knowledge_service(request: Request):
    """获取知识库管理服务实例"""
    return request.app.state.knowledge_service


# 注册路由
from app.api.analysis import router as analysis_router
from app.api.knowledge_api import router as knowledge_router
from app.api.retrieval_api import router as retrieval_router
from app.api.mcp_debug_api import router as mcp_debug_router

app.include_router(analysis_router)
app.include_router(knowledge_router)
app.include_router(retrieval_router)
app.include_router(mcp_debug_router)


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