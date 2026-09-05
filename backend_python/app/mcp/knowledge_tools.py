"""
MCP 知识库工具（浅适配器）

把 KnowledgeService（入库管道 / 统计 / 对账）封装为标准工具。
只做 schema 声明 + 参数校验 + 转发，不含业务逻辑。
"""
import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from app.mcp.server import ToolRegistry, ToolSpec
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class KnowledgeImportArgs(BaseModel):
    """knowledge.import 入参"""
    file_path: str
    max_chunk_size: Optional[int] = None


class KnowledgeImportManyArgs(BaseModel):
    """knowledge.import_many 入参：批量入库"""
    file_paths: List[str]
    max_chunk_size: Optional[int] = None


class KnowledgeTools:
    """知识库工具注册集合（复刻原 rag_mcp 的 Agent 工具职责，标准 MCP 封装）"""

    def __init__(self, knowledge_service: Optional[KnowledgeService] = None):
        self.knowledge_service = knowledge_service

    def register(self, registry: ToolRegistry) -> None:
        registry.register_many([
            ToolSpec(
                name="knowledge.import",
                description="把一份题库文件（MD/TXT/PDF）入库：清洗→切面→向量化→自检→入库报告",
                handler=self._import,
                input_model=KnowledgeImportArgs,
            ),
            ToolSpec(
                name="knowledge.import_many",
                description="批量入库多份题库文件，返回每份的入库报告",
                handler=self._import_many,
                input_model=KnowledgeImportManyArgs,
            ),
            ToolSpec(
                name="knowledge.stats",
                description="知识库统计：题目数 / 分块数 / 向量数 / 来源分布 / 健康度",
                handler=self._stats,
            ),
        ])
        logger.info("已注册知识库工具: knowledge.import / import_many / stats")

    async def _import(self, file_path: str, max_chunk_size: Optional[int]):
        if self.knowledge_service is None:
            raise ValueError("知识库工具未装配 knowledge_service")
        report = self.knowledge_service.import_document(file_path, max_chunk_size)
        return {
            "path": report.path, "status": report.status,
            "question_count": report.question_count, "chunk_count": report.chunk_count,
            "vector_count": report.vector_count, "deduplicated_count": report.deduplicated_count,
            "self_check": report.self_check, "error": report.error,
        }

    async def _import_many(self, file_paths: List[str], max_chunk_size: Optional[int]):
        return [await self._import(p, max_chunk_size) for p in file_paths]

    async def _stats(self):
        if self.knowledge_service is None:
            raise ValueError("知识库工具未装配 knowledge_service")
        return self.knowledge_service.get_stats()