"""
RAG 反思深度检索 API（app/api/research_api.py）

对应架构 §5.4「RAG 反思增强」与 §9.2「Research POST /research/deep」：
把评估标出的「薄弱项 / 未答考点」关键词反馈给检索 Agent，触发一轮针对性的
深度补充检索，返回可回灌报告 Agent 的「关联知识点扩展」参考。

复用既有深模块（Reflexion.deep_retrieve + RetrievalAgent.answer），不重复实现；
单个关键词检索失败由 Reflexion 内部降级（跳过该词），端点本身不失败。
"""
import logging
from typing import List

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.agents.reflexion import Reflexion
from app.agents.retrieval_agent import RetrievalAgent
from app.core.exceptions import AppError, PipelineError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


class ResearchDeepRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, max_length=10)
    max_keywords: int = Field(default=3, ge=1, le=10)


class ResearchDeepResponse(BaseModel):
    keywords: List[str]
    results: List[str]
    extension_report: str
    total_keywords: int


@router.post("/deep", response_model=ResearchDeepResponse)
async def research_deep(
    request: Request,
    body: ResearchDeepRequest,
) -> ResearchDeepResponse:
    retrieval_agent: RetrievalAgent = request.app.state.retrieval_agent
    keywords = [k.strip() for k in body.keywords if k and k.strip()][: body.max_keywords]
    try:
        reflexion = Reflexion(max_retrieve=len(keywords))
        results = await reflexion.deep_retrieve(retrieval_agent, keywords)
        extension = reflexion.extend_report(results)
        return ResearchDeepResponse(
            keywords=keywords,
            results=results,
            extension_report=extension,
            total_keywords=len(keywords),
        )
    except AppError:
        raise
    except Exception as e:
        raise PipelineError(detail=f"反思深度检索失败: {str(e)}") from e