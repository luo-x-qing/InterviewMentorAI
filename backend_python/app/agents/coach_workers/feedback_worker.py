"""
Coach 反馈 Worker（app/agents/coach_workers/feedback_worker.py）

架构 §7：Coach 内部「反馈」专职 Worker。
对考生答案做即时点评：正确性判定 + 打分 + 简短反馈。

v0 规则版：以「评估要点命中」为评分核心（可注入 judging_fn 替换为 LLM 点评）；
对外仅暴露 evaluate(question, answer) -> CoachFeedbackOut。
"""
import logging
import re
from typing import Callable, Optional

from app.models.entities import CoachQuestion, CoachAnswerRecord
from app.models.entities import CoachFeedbackOut

logger = logging.getLogger(__name__)

JudgeFn = Callable[[CoachQuestion, str], CoachFeedbackOut]  # 注入式点评函数


class FeedbackWorker:
    """反馈 Worker（v0 规则评分：按评估要点关键词命中计分）"""

    def __init__(self, judging_fn: Optional[JudgeFn] = None):
        self.judging_fn = judging_fn

    def set_judging_fn(self, fn: JudgeFn) -> None:
        self.judging_fn = fn

    def evaluate(self, question: CoachQuestion, answer: str) -> CoachFeedbackOut:
        if self.judging_fn is not None:
            return self.judging_fn(question, answer)
        return self._rule_judge(question, answer)

    def to_record(self, question: CoachQuestion, feedback: CoachFeedbackOut, session_id: str) -> CoachAnswerRecord:
        """把一次作答落为画像输入记录（供 profiling 聚合）"""
        return CoachAnswerRecord(
            session_id=session_id,
            question_no=question.question_no,
            title=question.title,
            answer=feedback.correct_answer or "",
            score=feedback.score,
            level="STRONG" if feedback.is_correct else "WEAK",
            knowledge_points=question.evaluation_points,
        )

    @staticmethod
    def _rule_judge(question: CoachQuestion, answer: str) -> CoachFeedbackOut:
        if not answer.strip():
            return CoachFeedbackOut(is_correct=False, score=0, feedback="未作答。请按面试场景给出你的回答。")

        # 评估要点 → 命中的要点数量（按分号/逗号/换行切）
        points = [p.strip() for p in re.split(r"[;；,，\n]", question.evaluation_points or "") if p.strip()]
        answer_text = answer.lower()
        hits = sum(1 for p in points if p.lower() in answer_text)
        total = max(len(points), 1)
        ratio = hits / total
        score = int(100 * ratio)
        is_correct = ratio >= 0.5
        feedback = (
            f"要点命中 {hits}/{total}。"
            + ("表现不错，覆盖了核心考察点。" if is_correct else "建议对照参考要点补充作答。")
        )
        return CoachFeedbackOut(
            is_correct=is_correct, score=score,
            feedback=feedback, correct_answer=question.answer,
        )