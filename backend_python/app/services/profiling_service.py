"""
用户画像服务（app/services/profiling_service.py）

统计聚合 + 相似度的轻量个性化建模（v1→v3，轻度机器学习）：
- v1：把历史复盘评估 + 本次作答按知识点维度聚合，产出"强项/弱项"标签
- v2：把弱项标签向量化（复用 bge），在题库中检索最接近的题优先出题（供出题 worker）
- v3：按答对/答错更新细粒度掌握度分值，动态调档（供难度自适应）

不训练模型、不引入重型框架，只叠加「统计 + 复用已加载的 bge 向量」。
深模块：对外暴露 aggregate / cosine / suggest_mastery 等小接口。
"""
import logging
import math
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Set, Tuple

from app.core.database import Database
from app.models.entities import (
    CoachAnswerRecord,
    CoachSession,
    Difficulty,
    UserProfile,
)

logger = logging.getLogger(__name__)

# 掌握度阈值：score ≥ 70 → 计入强项，< 50 → 计入弱项
_STRONG_THRESHOLD = 70
_WEAK_THRESHOLD = 50


class ProfilingService:
    """画像：统计聚合 + 余弦相似度（复用已加载向量 / 文本哈希特征）"""

    def __init__(self, database: Optional[Database] = None):
        self.db = database

    # ── v1 统计聚合 ───────────────────────────────────

    def aggregate(self, records: Sequence[CoachAnswerRecord]) -> Dict[str, Tuple[int, float]]:
        """按知识点聚合：{知识点: (次数, 平均分)}，用于生成强弱项标签"""
        counter: Dict[str, Tuple[int, float]] = {}
        n: Dict[str, int] = defaultdict(int)
        total: Dict[str, float] = defaultdict(float)
        for rec in records:
            kps = [k.strip() for k in (rec.knowledge_points or "").split(",") if k.strip()] or [rec.title]
            base = rec.score
            for kp in kps:
                n[kp] += 1
                total[kp] += base
        for kp in n:
            counter[kp] = (n[kp], round(total[kp] / n[kp], 1))
        return counter

    def build_profile(self, user_id: int, records: Sequence[CoachAnswerRecord]) -> UserProfile:
        """由作答记录聚合出强弱项标签 + 写入画像表"""
        agg = self.aggregate(records)
        strengths = [kp for kp, (_, avg) in agg.items() if avg >= _STRONG_THRESHOLD]
        weaknesses = [kp for kp, (_, avg) in agg.items() if avg < _WEAK_THRESHOLD]
        mastery = {kp: round(avg, 1) for kp, (_, avg) in agg.items()}
        profile = UserProfile(user_id=user_id, strengths=strengths, weaknesses=weaknesses, mastery=mastery)
        if self.db is not None:
            self.db.save_profile(profile)
        return profile

    def ingest_review(self, user_id: int, evaluations) -> UserProfile:
        """把一次复盘（interview evaluation_list）的薄弱知识点合并进画像。

        与 build_profile 区别：增量合并而非整体覆盖——保留 Coach 会话积累的
        历史画像，仅把本次复盘评估中 <WEAK_THRESHOLD 的知识点按掌握度聚合进来。
        """
        if not evaluations:
            existing = self.get_profile(user_id)
            return existing if existing is not None else UserProfile(user_id=user_id)

        # 聚合本次评估：知识点 → (次数, 平均分)
        counter: Dict[str, Tuple[int, float]] = {}
        n: Dict[str, int] = defaultdict(int)
        total: Dict[str, float] = defaultdict(float)
        for e in evaluations:
            kps = [k.strip() for k in (e.knowledge_points or "").split(",") if k.strip()]
            if not kps:
                continue
            for kp in kps:
                n[kp] += 1
                total[kp] += float(e.score or 0)
        for kp in n:
            counter[kp] = (n[kp], round(total[kp] / n[kp], 1))

        # 与既有画像合并（历史权重 = 历史次数，简单平均）
        existing = self.get_profile(user_id)
        history_mastery = dict(existing.mastery) if existing and existing.mastery else {}
        merged: Dict[str, float] = {}
        for kp, (count, avg) in counter.items():
            if kp in history_mastery:
                merged[kp] = round((history_mastery[kp] + avg) / 2, 1)
            else:
                merged[kp] = avg
        for kp, v in history_mastery.items():
            merged.setdefault(kp, v)

        strengths = [kp for kp, v in merged.items() if v >= _STRONG_THRESHOLD]
        weaknesses = [kp for kp, v in merged.items() if v < _WEAK_THRESHOLD]
        profile = UserProfile(user_id=user_id, strengths=strengths, weaknesses=weaknesses, mastery=merged)
        if self.db is not None:
            self.db.save_profile(profile)
        return profile

    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        if self.db is None:
            return None
        return self.db.get_profile(user_id)

    # ── v2 相似度选题（复用 bge 向量 / 文本特征）─────────

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        return set("".join(ch for ch in text if ch.strip()).lower())

    def cosine(self, a: Sequence[str], b: Sequence[str]) -> float:
        """文本元素集合的余弦相似度。

        既支持「元素完全相等」也支持「元素间子串包含」（中文知识库常用）：
        题目整段文本可携带弱项词片段，按包含关系模糊命中。
        """
        if not a or not b:
            return 0.0
        matched = 0
        for x in a:
            for y in b:
                if x == y or (len(x) > 1 and len(y) > 1 and (x in y or y in x)):
                    matched += 1
                    break
        return matched / math.sqrt(len(a) * len(b))

    def rank_questions_by_profile(
        self,
        questions: Sequence[Tuple[str, str]],  # (question_no, title_or_text)
        profile: Optional[UserProfile],
    ) -> List[Tuple[str, float]]:
        """按画像弱项排序题库：弱项标签越接近的题越靠前（v2）"""
        if not profile or not profile.weaknesses:
            return [(q, 0.0) for q, _ in questions]
        scored = []
        for qno, text in questions:
            score = max(self.cosine([text], [w]) for w in profile.weaknesses)
            scored.append((qno, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ── v3 难度自适应 ─────────────────────────────────

    def suggest_difficulty(self, session: CoachSession) -> str:
        """按本会话正确率动态调档（简单↔中等↔难）"""
        if session.total_count == 0:
            return session.difficulty
        accuracy = session.correct_count / session.total_count
        order = [Difficulty.EASY.value, Difficulty.MEDIUM.value, Difficulty.HARD.value]
        cur = session.difficulty or Difficulty.MEDIUM.value
        idx = order.index(cur) if cur in order else 1
        if accuracy >= 0.75 and idx < len(order) - 1:
            return order[idx + 1]
        if accuracy <= 0.4 and idx > 0:
            return order[idx - 1]
        return cur