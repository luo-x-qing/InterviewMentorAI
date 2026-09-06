"""
知识库管理 API 路由
提供知识库导入、统计、清空、文档级生命周期接口
"""
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.knowledge_service import KnowledgeService
from app.main import get_knowledge_service
from app.core.exceptions import AppError, KnowledgeError, KnowledgeImportError

logger = logging.getLogger(__name__)

# 创建路由实例
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# 请求/响应模型
class KnowledgeImportRequest(BaseModel):
    """知识库导入请求"""
    file_paths: Optional[List[str]] = None  # 指定文件路径，None则导入全部


class ImportReportBrief(BaseModel):
    """单文件入库报告摘要（T3.3）"""
    source: str
    status: str
    self_check: str = ""
    question_count: int = 0
    chunk_count: int = 0
    error: str = ""


class KnowledgeImportResponse(BaseModel):
    """知识库导入响应"""
    success: bool
    message: str
    imported_count: int
    reports: List[ImportReportBrief] = []


@router.post("/import", response_model=KnowledgeImportResponse)
async def import_knowledge(
    request: KnowledgeImportRequest = None,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    导入知识库题库（单入口 import_document：幂等 + 自检）

    - file_paths 为空时扫描 rag_doc_root 下全部 MD/TXT
    - 未变更文件跳过、变更文件蓝绿替换、自检失败回滚
    """
    try:
        logger.info("开始知识库导入")
        if request and request.file_paths:
            paths = request.file_paths
        else:
            paths = knowledge_service.list_doc_files()
        if not paths:
            return KnowledgeImportResponse(success=True, message="无题库文件", imported_count=0)

        reports = []
        for p in paths:
            r = knowledge_service.import_document(p)
            reports.append(ImportReportBrief(
                source=os.path.basename(p),
                status=r.status,
                self_check=r.self_check,
                question_count=r.question_count,
                chunk_count=r.chunk_count,
                error=r.error,
            ))

        failed = [r for r in reports if r.status == "failed"]
        return KnowledgeImportResponse(
            success=not failed,
            message=f"导入完成，{len(reports)} 个题库" if not failed else f"{len(failed)} 个题库导入失败",
            imported_count=len(reports),
            reports=reports,
        )
    except AppError:
        raise
    except Exception as e:
        raise KnowledgeImportError(detail=f"导入失败: {str(e)}") from e


@router.post("/reconcile")
async def reconcile_knowledge(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """目录对账：清理已从磁盘消失题库的旧分块与指纹（D3）"""
    try:
        removed = knowledge_service.reconcile_directory()
        return {"success": True, "removed": removed, "message": f"目录对账完成，清理 {removed} 个已消失题库"}
    except AppError:
        raise
    except Exception as e:
        raise KnowledgeError(detail=f"目录对账失败: {str(e)}") from e


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
    except AppError:
        raise
    except Exception as e:
        raise KnowledgeError(detail=f"获取统计失败: {str(e)}") from e


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
    except AppError:
        raise
    except Exception as e:
        raise KnowledgeError(detail=f"清空失败: {str(e)}") from e


@router.delete("/{source}")
async def delete_document(
    source: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """文档级生命周期：删除某来源题库的全部分块与指纹（T3.2）"""
    try:
        knowledge_service.delete_document(source)
        return {"success": True, "message": f"已删除题库 {source}"}
    except AppError:
        raise
    except Exception as e:
        raise KnowledgeError(detail=f"删除失败: {str(e)}") from e
