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

    def recommend(self, profile: Optional[UserProfile], limit: int = 3) -> list:
        """推荐针对性练习：按画像弱项从题库选多道；无画像/无候选题时降级为空列表。

        供复盘后 Coach 推荐练习（不依赖会话难度档位），池为空返回 []（而非抛错）。
        弱项命中优先，不足 limit 时用其余题目补足。
        """
        if self.question_source is None:
            return []
        try:
            pool = self.question_source(self.max_try)
        except Exception as e:  # noqa: BLE001
            logger.warning("推荐选题降级为空：%s", e)
            return []
        if not pool:
            return []

        seen, out = set(), []

        def _append(q: CoachQuestion):
            if q.question_no in seen:
                return
            seen.add(q.question_no)
            out.append(q)

        if profile and profile.weaknesses:
            def _hit(q: CoachQuestion) -> int:
                text = (q.title + q.question + q.evaluation_points)
                return sum(1 for w in profile.weaknesses if w in text)

            for q in sorted(pool, key=_hit, reverse=True):
                if _hit(q) > 0:
                    _append(q)
                if len(out) >= limit:
                    break

        for q in pool:
            if len(out) >= limit:
                break
            _append(q)
        return out

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


def build_knowledge_question_source(vector_db) -> QuestionSource:
    """生产题库源（浅适配器）：从知识库检索拉取候选题目用作 Coach 出题/推荐。

    复用 `agentic_rag` 之外的同步检索链路（RagService 查候选），以「题名」为查询
    投影出 CoachQuestion；未命中返回空列表。供 main.py 装配 QuestionWorker。
    """

    def _source(_limit: int):
        try:
            candidates = vector_db.get_questions_for_coach(_limit)
        except Exception as e:  # noqa: BLE001
            logger.warning("题库源降级为空：%s", e)
            return []
        out = []
        for c in candidates:
            out.append(CoachQuestion(
                question_no=str(c.get("question_no", "")),
                title=c.get("title", "") or str(c.get("question_no", "")),
                question=c.get("content", "")[:2000],
                answer=c.get("answer", ""),
                evaluation_points=c.get("evaluation_points", ""),
                difficulty=c.get("difficulty", "MEDIUM"),
                source=c.get("source", ""),
            ))
        return out

    return _source