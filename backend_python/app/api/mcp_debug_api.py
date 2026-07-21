"""
MCP调试 API 路由
提供MCP链路测试、上下文预览等调试接口
"""
import logging

from fastapi import APIRouter, HTTPException, Depends

from app.services.rag_service import RagService
from app.services.rag_mcp import RagMCP
from app.main import get_rag_service, get_rag_mcp
from app.models.schemas import McpEvalRequest, McpRetrievalRequest
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp-debug"])


@router.post("/eval-test")
async def mcp_rag_eval_test(
    request: McpEvalRequest,
    rag_mcp: RagMCP = Depends(get_rag_mcp)
):
    """
    MCP链路测试接口
    
    测试完整的RAG-MCP链路：检索→上下文组装→LLM增强评估
    不跑完整音频流水线，纯文本测试
    """
    try:
        logger.info(f"[MCP测试] 问题：{request.question[:50]}...")
        
        result = rag_mcp.rag_enhance_evaluate(
            question=request.question,
            answer=request.answer,
            use_hybrid=request.use_hybrid,
            use_rerank=request.use_rerank
        )
        
        return {
            "success": True,
            "llm_output": result,
            "question": request.question,
            "answer": request.answer
        }
    except AppError as e:
        logger.error(f"MCP测试失败: {e}", exc_info=True)
        raise e.to_http_exception()
    except Exception as e:
        logger.error(f"MCP测试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MCP测试失败: {str(e)}")


@router.post("/context-preview")
async def mcp_context_preview(
    request: McpRetrievalRequest,
    rag_service: RagService = Depends(get_rag_service),
    rag_mcp: RagMCP = Depends(get_rag_mcp)
):
    """
    MCP上下文预览接口
    
    预览RAG检索后MCP组装的完整上下文，用于调试
    """
    try:
        # 执行检索
        retrieval_res = rag_service.retrieve_by_question(
            request.question, 
            request.use_hybrid,
            request.use_rerank
        )
        
        # MCP组装上下文
        raw_context = rag_mcp.build_rag_context(retrieval_res)
        final_context = rag_mcp.limit_context_length(raw_context)
        
        return {
            "question": request.question,
            "retrieval_count": len(retrieval_res.docs),
            "raw_context_length": len(raw_context),
            "final_context_length": len(final_context),
            "raw_context": raw_context,
            "final_context": final_context,
            "docs": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "source": doc.source,
                    "score": round(doc.score, 4)
                }
                for doc in retrieval_res.docs
            ]
        }
    except AppError as e:
        logger.error(f"MCP上下文预览失败: {e}", exc_info=True)
        raise e.to_http_exception()
    except Exception as e:
        logger.error(f"MCP上下文预览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")