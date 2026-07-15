"""
分析 API 路由
提供 AI 分析相关的接口
接收前端 HTTP 请求、参数校验、调用业务流水线、封装返回结果，不实现任何 AI 分析逻辑。
"""
import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalysisRequest, AnalysisResponse, AnalysisStatus
from app.services.agent_pipeline import agent_pipeline

logger = logging.getLogger(__name__)

#创建 FastAPI 路由实例，设置路由前缀和标签
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


#核心接口，接收前端请求，调用 Agent 流水线服务，返回分析结果
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_audio(request: AnalysisRequest) -> AnalysisResponse:
    """
    执行 AI 分析流水线
    
    Args:
        request: 分析请求，包含 interview_id 和 audio_file_path
        
    Returns:
        分析响应，包含状态、报告和评估结果
    """
    logger.info(f"收到分析请求: interview_id={request.interview_id}")
    
    try:
        # 执行 Agent 流水线
        response = agent_pipeline.run(request)
        
        if response.status == AnalysisStatus.FAILED:
            raise HTTPException(status_code=500, detail=response.error)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析请求处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


#检查服务健康状态的接口
@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "python-ai-backend"}
