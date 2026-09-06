"""
InterviewMentorAI Python AI 后端
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def _retrieve_docs(rag_service, query: str) -> list:
    """把 RagService 检索结果（RagRetrievalResult）规整为 AgenticRag 需要的 RagDoc 列表"""
    result = await rag_service.retrieve_by_question(query, use_hybrid=True, use_rerank=True)
    return list(result.docs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 严格按依赖顺序创建服务实例"""
    logger.info("Python AI 后端启动中...")
    logger.info(f"LLM 模型: {settings.llm_model_name}")
    
    # 1. 创建无依赖的基础服务
    from app.core.vector_db import VectorDB
    from app.services.llm_client import LlmClient
    from app.services.chunking_service import ChunkingService
    
    vector_db = VectorDB()
    llm_client = LlmClient()
    chunking_service = ChunkingService()
    
    # 2. 创建依赖基础服务的中间服务
    from app.services.embedding_service import EmbeddingService
    from app.services.reranker_service import RerankerService
    
    embedding_service = EmbeddingService()
    reranker_service = RerankerService()
    
    # 3. 创建依赖中间服务的业务服务
    from app.services.prompt_service import PromptService
    from app.services.rag_service import RagService
    from app.services.rag_mcp import RagMCP
    
    prompt_service = PromptService(llm_client=llm_client)
    rag_service = RagService(
        vector_db=vector_db,
        embedding_service=embedding_service,
        reranker_service=reranker_service
    )
    rag_mcp = RagMCP(rag_service=rag_service, prompt_service=prompt_service)
    
    # 4. v3.1 全 Agent 架构：Agentic RAG / MCP 工具层（先于 AgentPipeline，供 call_tool 注入）
    from app.services.agentic_rag_service import AgenticRagService
    from app.mcp.server import ToolRegistry
    from app.mcp.retrieval_tools import RetrievalTools
    from app.mcp.knowledge_tools import KnowledgeTools
    from app.agents.retrieval_agent import RetrievalAgent

    agentic_rag = AgenticRagService(
        retrieve_fn=lambda query: _retrieve_docs(rag_service, query),
    )
    retrieval_agent = RetrievalAgent(agentic_rag=agentic_rag)

    tool_registry = ToolRegistry()
    RetrievalTools(rag_service=rag_service, agentic_rag=agentic_rag).register(tool_registry)

    from app.services.agent_pipeline import AgentPipeline

    agent_pipeline = AgentPipeline(
        prompt_service=prompt_service,
        rag_mcp=rag_mcp,
        tool_registry=tool_registry,
    )
    from app.services.knowledge_service import KnowledgeService

    knowledge_service = KnowledgeService(
        vector_db=vector_db,
        chunking_service=chunking_service,
        embedding_service=embedding_service
    )
    KnowledgeTools(knowledge_service=knowledge_service).register(tool_registry)

    # 5. v3.1 业务库 / Coach / Orchestrator
    from app.core.database import Database
    from app.mcp.coach_tools import CoachTools
    from app.services.auth_service import AuthService
    from app.services.coach_service import CoachService
    from app.services.profiling_service import ProfilingService
    from app.agents.orchestrator import Orchestrator
    from app.agents.coach_workers.question_worker import QuestionWorker, build_knowledge_question_source

    database = Database()
    auth_service = AuthService(database=database)
    profiling_service = ProfilingService(database=database)
    coach_service = CoachService(database=database)
    # 生产题库源：从知识库投影候选（无题库 → 空列表降级），Coach 出题/推荐可用
    coach_service.question_worker.set_question_source(build_knowledge_question_source(vector_db))
    CoachTools(coach=coach_service).register(tool_registry)

    orchestrator = Orchestrator(pipeline=agent_pipeline)

    # 6. 阶段 A：WebSocket 广播中枢（Orchestrator / Coach 进度钩子注入）
    from app.services.ws_service import WebSocketHub

    ws_hub = WebSocketHub()
    
    # 存储到 app.state
    app.state.vector_db = vector_db
    app.state.llm_client = llm_client
    app.state.chunking_service = chunking_service
    app.state.embedding_service = embedding_service
    app.state.reranker_service = reranker_service
    app.state.prompt_service = prompt_service
    app.state.rag_service = rag_service
    app.state.rag_mcp = rag_mcp
    app.state.agent_pipeline = agent_pipeline
    app.state.knowledge_service = knowledge_service
    app.state.agentic_rag = agentic_rag
    app.state.database = database
    app.state.auth_service = auth_service
    app.state.coach_service = coach_service
    app.state.profiling_service = profiling_service
    app.state.retrieval_agent = retrieval_agent
    app.state.tool_registry = tool_registry
    app.state.orchestrator = orchestrator
    app.state.ws_hub = ws_hub
    
    logger.info(f"所有服务实例创建完成（tool_registry 已注册 {len(tool_registry.list_tools())} 个工具）")
    
    yield
    
    # 按依赖逆序清理资源
    logger.info("Python AI 后端关闭中...")
    if hasattr(app.state, 'knowledge_service'):
        app.state.knowledge_service.close()
    if hasattr(app.state, 'rag_service'):
        app.state.rag_service.close()
    if hasattr(app.state, 'vector_db'):
        app.state.vector_db.close()
    if hasattr(app.state, 'database'):
        app.state.database.close()
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

# 全局异常处理：AppError 子类统一转 HTTP 状态码
from app.core.exceptions import register_error_handlers
register_error_handlers(app)


# 依赖注入函数
def get_vector_db(request: Request):
    return request.app.state.vector_db


def get_llm_client(request: Request):
    return request.app.state.llm_client


def get_chunking_service(request: Request):
    return request.app.state.chunking_service


def get_embedding_service(request: Request):
    return request.app.state.embedding_service


def get_reranker_service(request: Request):
    return request.app.state.reranker_service


def get_prompt_service(request: Request):
    return request.app.state.prompt_service


def get_rag_service(request: Request):
    return request.app.state.rag_service


def get_rag_mcp(request: Request):
    return request.app.state.rag_mcp


def get_agent_pipeline(request: Request):
    return request.app.state.agent_pipeline


def get_knowledge_service(request: Request):
    return request.app.state.knowledge_service


def get_database(request: Request):
    return request.app.state.database


def get_coach_service(request: Request):
    return request.app.state.coach_service


def get_tool_registry(request: Request):
    return request.app.state.tool_registry


def get_orchestrator(request: Request):
    return request.app.state.orchestrator


def get_retrieval_agent(request: Request):
    return request.app.state.retrieval_agent


# 注册路由
from app.api.analysis import router as analysis_router
from app.api.knowledge_api import router as knowledge_router
from app.api.retrieval_api import router as retrieval_router
from app.api.mcp_debug_api import router as mcp_debug_router
from app.api.auth_api import router as auth_router
from app.api.user_api import router as user_router
from app.api.interview_api import router as interview_router
from app.api.report_api import router as report_router
from app.api.coach_api import router as coach_router
from app.api.ws_api import router as ws_router

app.include_router(analysis_router)
app.include_router(knowledge_router)
app.include_router(retrieval_router)
app.include_router(mcp_debug_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(interview_router)
app.include_router(report_router)
app.include_router(coach_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "service": "InterviewMentorAI Python AI Backend",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
