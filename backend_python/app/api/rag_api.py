"""
RAG API 路由
提供知识库管理、检索调试等接口
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services.rag_service import rag_service
from app.services.rag_mcp import rag_mcp
from app.models.schemas import RagDoc, RagRetrievalResult

logger = logging.getLogger(__name__)

# 创建路由实例
router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


# 请求/响应模型
class KnowledgeImportRequest(BaseModel):
    """知识库导入请求"""
    file_paths: Optional[List[str]] = None  # 指定文件路径，None则导入全部


class KnowledgeImportResponse(BaseModel):
    """知识库导入响应"""
    success: bool
    message: str
    imported_count: int


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


@router.post("/knowledge/import", response_model=KnowledgeImportResponse)
async def import_knowledge(request: KnowledgeImportRequest = None):
    """
    导入知识库文档
    
    将指定目录下的.md和.txt文件进行分块、向量化，存入向量数据库。
    """
    try:
        logger.info("开始知识库导入")
        rag_service.batch_import_knowledge()
        
        return KnowledgeImportResponse(
            success=True,
            message="知识库导入完成",
            imported_count=0  # TODO: 返回实际导入数量
        )
    except Exception as e:
        logger.error(f"知识库导入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(request: RetrievalRequest):
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
async def preview_chunks(request: ChunkPreviewRequest):
    """
    预览分块结果
    
    将文本进行分块，返回分块结果供调试使用。
    支持三种分块策略：fixed（固定长度）、paragraph（按段落）、semantic（语义分块）
    """
    try:
        # 临时修改分块参数
        original_chunk_size = rag_service.chunk_size
        original_chunk_overlap = rag_service.chunk_overlap
        
        rag_service.chunk_size = request.chunk_size
        rag_service.chunk_overlap = request.chunk_overlap
        
        chunks = rag_service.split_chunks(request.text, request.method)
        
        # 恢复原参数
        rag_service.chunk_size = original_chunk_size
        rag_service.chunk_overlap = original_chunk_overlap
        
        avg_length = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
        
        return ChunkPreviewResponse(
            chunks=chunks,
            total_chunks=len(chunks),
            avg_length=round(avg_length, 2)
        )
    except Exception as e:
        logger.error(f"分块预览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """
    获取知识库统计信息
    
    返回知识库中文档数量、向量数量等统计信息。
    """
    try:
        from app.core.vector_db import vector_db
        
        # 查询文档数量
        doc_count = vector_db.conn.execute(
            "SELECT COUNT(*) FROM rag_docs"
        ).fetchone()[0]
        
        # 查询向量数量
        vector_count = vector_db.conn.execute(
            "SELECT COUNT(*) FROM rag_vectors"
        ).fetchone()[0]
        
        # 查询来源文件统计
        source_stats = vector_db.conn.execute(
            "SELECT source, COUNT(*) as count FROM rag_docs GROUP BY source"
        ).fetchall()
        
        return {
            "total_documents": doc_count,
            "total_vectors": vector_count,
            "source_files": [
                {"filename": row[0], "chunk_count": row[1]}
                for row in source_stats
            ]
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.delete("/knowledge/clear")
async def clear_knowledge():
    """
    清空知识库
    
    删除所有文档和向量数据。
    """
    try:
        from app.core.vector_db import vector_db
        
        vector_db.conn.execute("DELETE FROM rag_vectors")
        vector_db.conn.execute("DELETE FROM rag_docs")
        vector_db.conn.commit()
        
        logger.info("知识库已清空")
        return {"success": True, "message": "知识库已清空"}
    except Exception as e:
        logger.error(f"清空知识库失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


# ========== MCP调度层接口 ==========

class McpEvalRequest(BaseModel):
    """MCP评估测试请求"""
    question: str
    answer: str
    use_hybrid: bool = True
    use_rerank: bool = True


@router.post("/mcp/eval-test")
async def mcp_rag_eval_test(request: McpEvalRequest):
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
    except Exception as e:
        logger.error(f"MCP测试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MCP测试失败: {str(e)}")


@router.post("/mcp/context-preview")
async def mcp_context_preview(request: RetrievalRequest):
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
    except Exception as e:
        logger.error(f"MCP上下文预览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
