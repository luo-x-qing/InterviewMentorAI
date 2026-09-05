"""
Coach 出题 Worker（app/agents/coach_workers/question_worker.py）

架构 §7：Coach 内部「出题」专职 Worker。
职责：从知识库（题库）为当前用户挑选下一题，并按画像做弱项优先 + 难度自适应。

深模块：对外仅暴露 select(profile, difficulty, ...) -> CoachQuestion；
题目来源可通过 question_source 注入（默认：知识库随机/关键词匹配，可替换为检索 Agent 回流）。
"""
import logging
import random
from typing import Callable, List, Optional

from app.models.entities import CoachQuestion, UserProfile

logger = logging.getLogger(__name__)

QuestionSource = Callable[[int], List[CoachQuestion]]  # 注入式题目源


class QuestionWorker:
    """出题 Worker（v0 规则版：按难度档筛选 + 画像弱项优先随机）"""

    def __init__(self, question_source: Optional[QuestionSource] = None, max_try: int = 10):
        self.question_source = question_source
        self.max_try = max_try

    def set_question_source(self, source: QuestionSource) -> None:
        """注入候选题目源（调度时装配；测试可注入内存题库）"""
        self.question_source = source

    def select(self, profile: Optional[UserProfile], difficulty: str, limit: int = 3) -> CoachQuestion:
        """为下一位考生出题：难度优先，命中弱项标签者靠前，否则随机兜底"""
        pool = self._candidates(difficulty)
        if not pool:
            raise RuntimeError("知识库无可用题目，无法出题")

        # 画像弱项优先
        if profile and profile.weaknesses:
            def _hit(q: CoachQuestion) -> int:
                text = (q.title + q.question + q.evaluation_points)
                return sum(1 for w in profile.weaknesses if w in text)

            pool.sort(key=_hit, reverse=True)
            head = [q for q in pool if _hit(q) > 0]
            if head:
                pool = head[:limit]

        return random.choice(pool[:limit])

    def _candidates(self, difficulty: str) -> List[CoachQuestion]:
        if self.question_source is None:
            logger.warning("出题 Worker 未装配题目源，返回空候选")
            return []
        all_q = self.question_source(self.max_try)
        # 优先同难度档，次选 Medium
        same = [q for q in all_q if q.difficulty == difficulty]
        if same:
            return same
        med = [q for q in all_q if q.difficulty == "MEDIUM"]
        return med or all_q