"""
MCP 检索工具（浅适配器）

包装 RAG 检索 与 Agentic RAG 答案合成，声明为标准工具。
只做「schema 声明 + 参数校验 + 转发业务服务」，不含业务逻辑。
"""
import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from app.mcp.server import ToolRegistry, ToolSpec
from app.core.config import settings
from app.services.rag_service import RagService
from app.services.agentic_rag_service import AgenticRagService

logger = logging.getLogger(__name__)


class RetrieveArgs(BaseModel):
    """retrieve.retrieve 入参"""
    question: str
    top_k: int = Field(default_factory=lambda: settings.rag_top_k)
    use_hybrid: bool = True
    use_rerank: bool = Field(default_factory=lambda: settings.rag_use_rerank)


class RagAnswerArgs(BaseModel):
    """rag.answer 入参"""
    question: str


class RetrievalTools:
    """检索工具注册集合"""

    def __init__(
        self,
        rag_service: Optional[RagService] = None,
        agentic_rag: Optional[AgenticRagService] = None,
    ):
        self.rag_service = rag_service
        self.agentic_rag = agentic_rag

    def register(self, registry: ToolRegistry) -> None:
        registry.register_many([
            ToolSpec(
                name="retrieve.retrieve",
                description="对一道面试题做混合检索（向量+BM25）+ 重排，返回候选参考上下文",
                handler=self._retrieve,
                input_model=RetrieveArgs,
            ),
            ToolSpec(
                name="rag.answer",
                description="Agentic RAG 答案合成：检索→扩展→评估→必要时重查→组装完整答案候选",
                handler=self._answer,
                input_model=RagAnswerArgs,
            ),
        ])
        logger.info("已注册检索工具: retrieve.retrieve / rag.answer")

    async def _retrieve(self, question: str, top_k: int, use_hybrid: bool, use_rerank: bool):
        if self.rag_service is None:
            raise ValueError("检索工具未装配 rag_service")
        result = self.rag_service.retrieve_by_question(question, use_hybrid, use_rerank)
        return {
            "question": result.question,
            "docs": [
                {
                    "doc_id": d.doc_id, "title": d.title, "content": d.content,
                    "source": d.source, "question_no": d.question_no,
                    "section": d.section, "score": round(d.score, 4),
                }
                for d in result.docs
            ],
            "metrics": result.metrics.model_dump() if result.metrics else None,
        }

    async def _answer(self, question: str):
        if self.agentic_rag is None:
            raise ValueError("检索工具未装配 agentic_rag")
        res = await self.agentic_rag.answer(question)
        return {
            "question": res.question,
            "status": res.status,
            "iterations": res.iterations,
            "candidates": [
                {
                    "source": c.source, "question_no": c.question_no, "title": c.title,
                    "score": round(c.score, 4), "full_answer": c.full_answer,
                    "related": c.related,
                }
                for c in res.candidates
            ],
            "log": res.log,
        }