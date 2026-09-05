"""
业务实体（app/models/entities.py）

v3.1 全 Agent 架构：业务数据实体。
延续既有约定：
- dataclass 作为领域模型（服务层内部使用）
- Pydantic 模型用于 API/工具传输与校验

对应架构文档 §7 Coach、§12 阶段 A 的业务表：
user / interview / report / coach_session / coach_session_question / user_profile
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ── 枚举 ─────────────────────────────────────────────


class InterviewStatus(str, Enum):
    """面试记录状态"""
    PENDING = "PENDING"    # 已创建，未分析
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CoachMode(str, Enum):
    """Coach 陪练模式"""
    TEXT = "TEXT"          # 文字作答
    VOICE = "VOICE"        # 语音作答（转写后走同一链路）


class CoachSessionStatus(str, Enum):
    """Coach 会话状态（状态机：idle→active→done）"""
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    DONE = "DONE"


class Difficulty(str, Enum):
    """题目难度档位"""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


# ── 领域实体（dataclass）─────────────────────────────


@dataclass
class User:
    """用户"""
    id: int
    phone: str
    nickname: str
    hashed_password: str = ""
    created_at: str = ""


@dataclass
class Interview:
    """面试记录"""
    id: int
    user_id: int
    title: str
    audio_file_path: str = ""
    status: str = InterviewStatus.PENDING.value
    created_at: str = ""
    final_report: str = ""


@dataclass
class Report:
    """复盘报告（与 interview 1:1，本次只保留对报告读取的骨架字段）"""
    interview_id: int
    content: str
    created_at: str = ""


@dataclass
class CoachQuestion:
    """Coach 会话中的一道题（含考察点）"""
    question_no: str
    title: str
    question: str
    answer: str = ""
    evaluation_points: str = ""
    difficulty: str = Difficulty.MEDIUM.value
    source: str = ""


@dataclass
class CoachSession:
    """Coach 陪练会话"""
    id: str                     # 会话句柄（UUID）
    user_id: int
    mode: str = CoachMode.TEXT.value
    status: str = CoachSessionStatus.IDLE.value
    difficulty: str = Difficulty.MEDIUM.value
    question_index: int = 0
    correct_count: int = 0
    total_count: int = 0
    created_at: str = ""


@dataclass
class CoachAnswerRecord:
    """每题作答记录（画像与自适应的输入，落库 coach_session_question）"""
    session_id: str
    question_no: str
    title: str
    answer: str
    score: int = 0
    level: str = "WEAK"
    knowledge_points: str = ""
    created_at: str = ""


@dataclass
class UserProfile:
    """用户薄弱点画像（统计聚合 + 相似度，v1→v3）"""
    user_id: int
    strengths: List[str] = field(default_factory=list)   # 强项标签（知识点）
    weaknesses: List[str] = field(default_factory=list)  # 弱项标签（知识点）
    mastery: dict = field(default_factory=dict)          # 知识点 → 0~100 掌握度
    updated_at: str = ""


# ── API/工具 传输模型（Pydantic）─────────────────────


class UserProfileOut(BaseModel):
    """画像输出"""
    user_id: int
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    mastery: dict = Field(default_factory=dict)


class CoachSessionHandle(BaseModel):
    """开会话返回的句柄"""
    session_id: str
    mode: str
    status: str
    difficulty: str


class CoachQuestionOut(BaseModel):
    """下一题输出"""
    question_no: str
    title: str
    question: str
    evaluation_points: str = ""
    difficulty: str = Difficulty.MEDIUM.value


class CoachFeedbackOut(BaseModel):
    """即时点评输出"""
    is_correct: bool
    score: int
    feedback: str
    correct_answer: str = ""


class CoachSessionReport(BaseModel):
    """结课报告输出"""
    session_id: str
    total_questions: int
    correct_answers: int
    accuracy: float
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: str = ""