"""
知识库管理 API 路由
提供知识库导入、统计、清空等接口
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.knowledge_service import KnowledgeService
from app.main import get_knowledge_service
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

# 创建路由实例
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# 请求/响应模型
class KnowledgeImportRequest(BaseModel):
    """知识库导入请求"""
    file_paths: Optional[List[str]] = None  # 指定文件路径，None则导入全部


class KnowledgeImportResponse(BaseModel):
    """知识库导入响应"""
    success: bool
    message: str
    imported_count: int


@router.post("/import", response_model=KnowledgeImportResponse)
async def import_knowledge(
    request: KnowledgeImportRequest = None,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    导入知识库文档
    
    将指定目录下的.md和.txt文件进行分块、向量化，存入向量数据库。
    """
    try:
        logger.info("开始知识库导入")
        imported_count = knowledge_service.batch_import_knowledge()

        return KnowledgeImportResponse(
            success=True,
            message="知识库导入完成",
            imported_count=imported_count
        )
    except AppError as e:
        logger.error(f"知识库导入失败: {e}", exc_info=True)
        raise e.to_http_exception()
    except Exception as e:
        logger.error(f"知识库导入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/stats")
async def get_knowledge_stats(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    获取知识库统计信息
    
    返回知识库中文档数量、向量数量等统计信息。
    """
    try:
        return knowledge_service.get_stats()
    except AppError as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise e.to_http_exception()
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.delete("/clear")
async def clear_knowledge(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    清空知识库
    
    删除所有文档和向量数据。
    """
    try:
        knowledge_service.clear_all()
        return {"success": True, "message": "知识库已清空"}
    except AppError as e:
        logger.error(f"清空知识库失败: {e}", exc_info=True)
        raise e.to_http_exception()
    except Exception as e:
        logger.error(f"清空知识库失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")
