"""
文档检索 API 路由
提供文档检索、分块预览等接口
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.rag_service import RagService
from app.models.schemas import RagRetrievalResult
from app.main import get_rag_service

logger = logging.getLogger(__name__)

# 创建路由实例
router = APIRouter(prefix="/retrieval", tags=["retrieval"])


# 请求/响应模型
class RetrievalRequest(BaseModel):
    """检索请求"""
    question: str
    top_k: int = 3
    use_hybrid: bool = True  # 是否使用混合检索
    use_rerank: bool = False  # 是否使用重排序


class RetrievalResponse(BaseModel):
    """检索响应"""
    question: str
    docs: List[dict]
    total_count: int


class ChunkPreviewRequest(BaseModel):
    """分块预览请求"""
    text: str
    chunk_size: int = 500
    chunk_overlap: int = 100
    method: str = "fixed"  # fixed, paragraph, semantic


class ChunkPreviewResponse(BaseModel):
    """分块预览响应"""
    chunks: List[str]
    total_chunks: int
    avg_length: float


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(
    request: RetrievalRequest,
    rag_service: RagService = Depends(get_rag_service)
):
    """
    检索相关文档
    
    根据用户问题，从知识库中检索最相关的文档片段。
    支持三种检索模式：
    - 混合检索（默认）：结合BM25关键词匹配和向量语义检索
    - 仅向量检索：只使用向量相似度检索
    - 重排序：对检索结果进行Cross-Encoder重排序
    """
    try:
        logger.info(f"执行RAG检索: {request.question}")
        
        result = rag_service.retrieve_by_question(
            request.question, 
            request.use_hybrid,
            request.use_rerank
        )
        
        # 转换为字典格式
        docs_dict = [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "content": doc.content,
                "source": doc.source,
                "score": round(doc.score, 4)
            }
            for doc in result.docs
        ]
        
        return RetrievalResponse(
            question=result.question,
            docs=docs_dict,
            total_count=len(docs_dict)
        )
    except Exception as e:
        logger.error(f"检索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.post("/chunks/preview", response_model=ChunkPreviewResponse)
async def preview_chunks(
    request: ChunkPreviewRequest,
    rag_service: RagService = Depends(get_rag_service)
):
    """
    预览分块结果
    
    将文本进行分块，返回分块结果供调试使用。
    支持三种分块策略：fixed（固定长度）、paragraph（按段落）、semantic（语义分块）
    """
    try:
        chunks = rag_service.split_chunks(
            request.text, 
            request.method,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        avg_length = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
        
        return ChunkPreviewResponse(
            chunks=chunks,
            total_chunks=len(chunks),
            avg_length=round(avg_length, 2)
        )
    except Exception as e:
        logger.error(f"分块预览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")