"""
Coach 画像 Worker（app/agents/coach_workers/profiling_worker.py）

架构 §7：Coach 内部「画像」专职 Worker。
把本会话的作答记录聚合进用户画像（强弱项标签 + 掌握度），并给出结课建议。

深模块：仅暴露 update(user_id, records) -> UserProfile 与 suggest() -> str。
"""
import logging
from typing import List, Optional

from app.models.entities import CoachAnswerRecord, UserProfile
from app.services.profiling_service import ProfilingService

logger = logging.getLogger(__name__)


class ProfilingWorker:
    """画像 Worker：委托 ProfilingService 做统计聚合，负责会话内组合与结课建议"""

    def __init__(self, profiling: Optional[ProfilingService] = None):
        self._profiling = profiling if profiling is not None else ProfilingService()

    def set_profiling(self, profiling: ProfilingService) -> None:
        self._profiling = profiling

    def update(self, user_id: int, records: List[CoachAnswerRecord]) -> UserProfile:
        """聚合本会话作答记录，写入/合并用户画像，返回最新画像"""
        profile = self._profiling.build_profile(user_id, records)
        return profile

    def suggest(self, profile: Optional[UserProfile]) -> str:
        """基于画像给出结课学习建议（v0 规则模板）"""
        if profile is None:
            return "继续坚持每日陪练，逐步建立知识体系。"
        weak = profile.weaknesses
        if not weak:
            return "整体掌握良好，可尝试更高难度挑战。"
        top = weak[:3]
        return f"重点补强：{('、'.join(top))}。建议围绕这几个知识点做专项练习与复盘。"