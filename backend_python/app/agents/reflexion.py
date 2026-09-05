"""
RAG 反思增强回路（app/agents/reflexion.py）

对应架构 §3.3「可反思（Reflexion）」与 §5.4「RAG 反思增强」：
复盘时把评估 Agent 标出的「薄弱项 / 未答出的考点」关键词反馈给检索 Agent，
触发一轮针对性的深度补充检索，回灌给报告 Agent 生成「关联知识点扩展」。

对外小接口：
    keywords_from(evaluations)   # 由评估结果抽取薄弱项关键词
    deep_retrieve(agent, keywords)  # 对每个关键词触发补充检索，返回扩展参考
    extend_report(ext#)          # 生成「关联知识点扩展」章节文本
"""
import logging
from typing import List, Sequence, Set

from app.agents.retrieval_agent import RetrievalAgent
from app.models.schemas import EvaluationResult

logger = logging.getLogger(__name__)


class Reflexion:
    """反思增强回路（深模块：内部封装关键词抽取与轮询）"""

    def __init__(self, max_retrieve: int = 3):
        self.max_retrieve = max_retrieve

    def keywords_from(self, evaluations: Sequence[EvaluationResult]) -> List[str]:
        """从评估结果里抽取薄弱项 / 知识点关键词（去重、限长）"""
        found: List[str] = []
        seen: Set[str] = set()
        for ev in evaluations:
            candidates = []
            if getattr(ev, "knowledge_points", None):
                candidates += [k.strip() for k in str(ev.knowledge_points).split(",")]
            if getattr(ev, "weaknesses", None):
                candidates += [str(ev.weaknesses)]
            for kw in candidates:
                if not kw or kw in seen:
                    continue
                seen.add(kw)
                found.append(kw)
                if len(found) >= self.max_retrieve:
                    return found
        return found

    async def deep_retrieve(self, agent: RetrievalAgent, keywords: Sequence[str]) -> List[str]:
        """对每个关键词触发检索 Agent 补充检索，拼接扩展参考文本"""
        blocks = []
        for kw in keywords:
            try:
                res = await agent.answer(kw)
                if res.status == "answered" and res.candidates:
                    blocks.append(self._format_block(kw, res))
            except Exception as e:  # noqa: BLE001
                logger.warning("反思深度检索失败(%s): %s", kw, e)
        return blocks

    @staticmethod
    def _format_block(keyword: str, res) -> str:
        lines = [f"### 关联知识点：{keyword}"]
        for c in res.candidates[:2]:
            lines.append(f"- {c.title}（{c.source}）")
            if c.full_answer:
                lines.append(f"  {c.full_answer[:300]}")
        return "\n".join(lines)

    def extend_report(self, extras: Sequence[str]) -> str:
        """把补充检索结果拼成「关联知识点扩展」章节"""
        if not extras:
            return ""
        return "\n\n## 关联知识点扩展\n\n针对本次回答不完整或不确定的部分，补充以下关联知识点：\n\n" + "\n\n".join(extras)