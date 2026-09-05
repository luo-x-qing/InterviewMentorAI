"""
检索 Agent（app/agents/retrieval_agent.py）

深模块：对外仅暴露 answer(question)，内部封装混合检索、重排、
expand / assess / re_query 全部细节（复用既有 AgenticRagService 的 LangGraph 工作流）。

供复盘 Orchestrator / 出题 worker / Coach 的检索侧调用；亦可作为 RAG 反思回路的落点。
"""
import logging
from typing import Callable, Optional

from app.models.schemas import RagAnswerResult
from app.services.agentic_rag_service import AgenticRagService

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """检索 Agent（深模块：answer 即全部对外接口）"""

    def __init__(self, agentic_rag: Optional[AgenticRagService] = None):
        # 默认延迟装配：可在运维时注入已完成检索装配的 agentic_rag
        self._agentic_rag = agentic_rag

    async def answer(self, question: str) -> RagAnswerResult:
        """对一个问题做 Agentic RAG 答案合成（检索→扩展→评估→必要时重查→合成）"""
        if self._agentic_rag is None:
            raise RuntimeError("检索 Agent 未装配 agentic_rag")
        return await self._agentic_rag.answer(question)

    async def retrieve_candidates(self, question: str) -> list:
        """返回候选题（供出题 worker / Coach 做相似度选题），空列表兜底"""
        if self._agentic_rag is None:
            return []
        try:
            res = await self._agentic_rag.answer(question)
            return list(res.candidates)
        except Exception as e:  # noqa: BLE001
            logger.warning("检索 Agent retrieve_candidates 降级为空: %s", e)
            return []

    def close(self) -> None:
        if self._agentic_rag is not None:
            try:
                self._agentic_rag.close()
            except Exception:  # noqa: BLE001
                pass