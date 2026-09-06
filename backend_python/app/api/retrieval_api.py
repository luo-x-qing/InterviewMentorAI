"""
文档检索 API 路由
提供文档检索、分块预览等接口
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.rag_service import RagService
from app.services.chunking_service import ChunkingService
from app.models.schemas import RagRetrievalResult
from app.main import get_rag_service, get_chunking_service
from app.core.exceptions import AppError, PipelineError
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


class RetrievalRequest(BaseModel):
    question: str
    top_k: int = Field(default_factory=lambda: settings.rag_top_k)
    use_hybrid: bool = True
    use_rerank: bool = Field(default_factory=lambda: settings.rag_use_rerank)


class RetrievalResponse(BaseModel):
    question: str
    docs: List[dict]
    total_count: int
    metrics: Optional[dict] = None


class ChunkPreviewRequest(BaseModel):
    text: str
    chunk_size: int = 300
    chunk_overlap: int = 60
    method: str = "fixed"


class ChunkPreviewResponse(BaseModel):
    chunks: List[str]
    total_chunks: int
    avg_length: float


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(
    request: RetrievalRequest,
    rag_service: RagService = Depends(get_rag_service)
):
    try:
        logger.info(f"执行RAG检索: {request.question}")
        
        result = rag_service.retrieve_by_question(
            request.question, 
            request.use_hybrid,
            request.use_rerank
        )
        
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
            total_count=len(docs_dict),
            metrics=result.metrics.model_dump() if result.metrics else None
        )
    except AppError:
        raise
    except Exception as e:
        raise PipelineError(detail=f"检索失败: {str(e)}") from e


@router.post("/chunks/preview", response_model=ChunkPreviewResponse)
async def preview_chunks(
    request: ChunkPreviewRequest,
    chunking_service: ChunkingService = Depends(get_chunking_service)
):
    try:
        chunks = chunking_service.split(
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
    except AppError:
        raise
    except Exception as e:
        raise PipelineError(detail=f"预览失败: {str(e)}") from e
