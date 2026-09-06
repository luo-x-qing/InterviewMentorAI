"""
Coach 会话服务（app/services/coach_service.py）

架构 §7 Coach 深模块：对外仅暴露 4 个方法（状态机 idle→active→done）：
    start_session(user_id, mode, difficulty) -> CoachSessionHandle
    next_question(session_id)                 -> CoachQuestionOut
    submit_answer(session_id, answer)         -> CoachFeedbackOut
    end_session(session_id)                   -> CoachSessionReport

内部封装：会话持久化 + 出题/反馈/画像 Worker 编排 + 难度自适应。

状态约束：
- submit_answer 仅 active 态可调用；自动推进 difficulty（v3）
- end_session 聚合画像并生成结课报告
"""
import logging
from typing import Optional

from app.core.database import Database
from app.models.entities import (
    CoachSession,
    CoachSessionHandle,
    CoachSessionStatus,
    CoachQuestionOut,
    CoachFeedbackOut,
    CoachSessionReport,
)
from app.services.profiling_service import ProfilingService

logger = logging.getLogger(__name__)


class CoachService:
    """Coach 陪练会话（深模块）"""

    def __init__(
        self,
        database: Optional[Database] = None,
        question_worker=None,
        feedback_worker=None,
        profiling: Optional[ProfilingService] = None,
    ):
        # 延迟导入，避免 app.agents 聚合导入造成的循环依赖
        from app.agents.coach_workers.question_worker import QuestionWorker
        from app.agents.coach_workers.feedback_worker import FeedbackWorker
        from app.agents.coach_workers.profiling_worker import ProfilingWorker

        self.db = database if database is not None else Database()
        self.question_worker = question_worker if question_worker is not None else QuestionWorker()
        self.feedback_worker = feedback_worker if feedback_worker is not None else FeedbackWorker()
        self._profiling = profiling if profiling is not None else ProfilingService(self.db)
        self.profiling_worker = ProfilingWorker(self._profiling)

    # ── start_session ─────────────────────────────────

    def start_session(self, user_id: int, mode: str = "TEXT", difficulty: str = "MEDIUM") -> CoachSessionHandle:
        session = self.db.create_coach_session(user_id, mode=mode, difficulty=difficulty)
        self._set_status(session, CoachSessionStatus.ACTIVE)
        logger.info("Coach 会话已开启 session=%s mode=%s", session.id, mode)
        return CoachSessionHandle(
            session_id=session.id, mode=session.mode,
            status=session.status, difficulty=session.difficulty,
        )

    # ── next_question ─────────────────────────────────

    def next_question(self, session_id: str) -> CoachQuestionOut:
        session = self._require_active(session_id)
        question = self._select_question(session)
        return CoachQuestionOut(
            question_no=question.question_no,
            title=question.title,
            question=question.question,
            evaluation_points=question.evaluation_points,
            difficulty=question.difficulty,
        )

    # ── recommend_practice（复盘后一键推荐针对性练习）────

    def recommend_practice(self, user_id: int, limit: int = 3) -> list:
        """按画像弱项为用户推荐针对性练习（不开启会话，适用于复盘后）。

        复用出题 Worker 的题库源与弱项优先逻辑；无画像/无题目时返回空列表。
        """
        profile = self._profiling.get_profile(user_id)
        questions = self.question_worker.recommend(profile, limit=limit)
        return [
            CoachQuestionOut(
                question_no=q.question_no, title=q.title, question=q.question,
                evaluation_points=q.evaluation_points, difficulty=q.difficulty,
            )
            for q in questions
        ]

    # ── submit_answer ─────────────────────────────────

    def submit_answer(self, session_id: str, answer: str) -> CoachFeedbackOut:
        session = self._require_active(session_id)
        question = self._current_question(session)
        feedback = self.feedback_worker.evaluate(question, answer)

        # 落作答记录（供画像）
        rec = self.feedback_worker.to_record(question, feedback, session.id)
        self.db.add_answer_record(rec)

        # 推进会话统计 + 难度自适应（v3）
        session.question_index += 1
        session.total_count += 1
        if feedback.is_correct:
            session.correct_count += 1
        session.difficulty = self._profiling.suggest_difficulty(session)
        self.db.update_coach_session(session)
        return feedback

    # ── end_session ───────────────────────────────────

    def end_session(self, session_id: str) -> CoachSessionReport:
        session = self._require_active(session_id)
        records = self.db.list_answer_records(session_id)
        profile = self.profiling_worker.update(session.user_id, records)

        accuracy = (session.correct_count / session.total_count) if session.total_count else 0.0
        self._set_status(session, CoachSessionStatus.DONE)
        return CoachSessionReport(
            session_id=session.id,
            total_questions=session.total_count,
            correct_answers=session.correct_count,
            accuracy=round(accuracy, 2),
            weaknesses=list(profile.weaknesses if profile else []),
            suggestions=self.profiling_worker.suggest(profile),
        )

    # ── helpers ───────────────────────────────────────

    def _require_active(self, session_id: str) -> CoachSession:
        session = self.db.get_coach_session(session_id)
        if session is None:
            raise KeyError(f"会话不存在: {session_id}")
        if session.status != CoachSessionStatus.ACTIVE.value:
            raise ValueError(f"会话不在进行中: {session.status}")
        return session

    def _set_status(self, session: CoachSession, status: CoachSessionStatus) -> None:
        session.status = status.value
        self.db.update_coach_session(session)

    def _current_question(self, session: CoachSession) -> "object":
        """配合 next_question 的一致性：以最新出题作予答判定基准。

        骨架阶段使用占位实现（从知识库取难度对应的一道题作参考）；接入
        真实出题路线后替换为按 session.question_index 从会话追问队列取题。
        """
        return self._select_question(session)

    def _select_question(self, session: CoachSession):
        """出题（含无题库可用时的降级）：知识库无题时给业务可读错误而非 500"""
        profile = self._profiling.get_profile(session.user_id)
        try:
            return self.question_worker.select(profile, session.difficulty)
        except RuntimeError as e:
            raise ValueError(str(e)) from e