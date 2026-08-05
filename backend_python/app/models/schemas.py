"""
数据模型定义
定义 Agent 流水线中使用的数据结构
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config import settings


class Speaker(str, Enum):
    """说话人类型"""
    INTERVIEWER = "INTERVIEWER"
    CANDIDATE = "CANDIDATE"


class EvaluationLevel(str, Enum):
    """评估等级"""
    PROFICIENT = "PROFICIENT"  # 熟练
    WEAK = "WEAK"  # 薄弱


class AnalysisStatus(str, Enum):
    """分析状态"""
    PROCESSING = "PROCESSING"
    ASR_COMPLETED = "ASR_COMPLETED"
    DIALOGUE_PARSED = "DIALOGUE_PARSED"
    EVALUATION_COMPLETED = "EVALUATION_COMPLETED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class DialogueItem:
    """对话条目"""
    speaker: Speaker
    content: str
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None


@dataclass
class EvaluationResult:
    """评估结果"""
    question: str
    answer: str
    score: int  # 0-100
    level: EvaluationLevel
    strengths: str
    weaknesses: str
    correction: str = ""  # 仅薄弱项
    knowledge_points: str = ""  # 仅薄弱项


@dataclass
class AgentState:
    """Agent 全局状态"""
    interview_id: int
    audio_file_path: str
    raw_transcript: str = ""
    dialogue_list: List[DialogueItem] = field(default_factory=list)
    evaluation_list: List[EvaluationResult] = field(default_factory=list)
    final_report: str = ""


@dataclass
class Question:
    """题目（一等概念）：一道完整 Q-A 及其溯源元数据"""
    question_no: str            # 题号，如 "1"
    title: str                  # 题目标题，如 "Python列表和元组区别"
    question: str               # 问题文本
    answer: str                 # 标准答案
    evaluation_points: str = "" # 评估要点
    source: str = ""            # 来源题库文件名
    section: str = ""           # 题目所在章节


@dataclass
class QuestionChunk:
    """结构化切面产物：一道题目切成的块（含溯源元数据）"""
    title: str                  # 块标题：来源 · 题号 [· 块序号]
    content: str                # 块内容（问题+答案+评估要点）
    question_no: str = ""       # 题号
    section: str = ""           # 章节
    source: str = ""            # 来源题库文件名


@dataclass
class ImportReport:
    """入库报告：入库管道每次执行的产物（识别题目数/分块数/向量数/去重数/失败项/自检结论）"""
    path: str
    status: str                 # imported / updated / skipped / failed
    question_count: int = 0     # 识别题目数
    chunk_count: int = 0        # 分块数
    vector_count: int = 0       # 向量数
    deduplicated_count: int = 0 # 指纹去重跳过数
    self_check: str = ""        # 自检结论：passed / failed
    error: str = ""             # 失败项


# ========== API 请求/响应模型 (Pydantic) ==========

class AnalysisRequest(BaseModel):
    """分析请求"""
    interview_id: int
    audio_file_path: str


class AnalysisResponse(BaseModel):
    """分析响应"""
    status: AnalysisStatus
    interview_id: int
    report: Optional[str] = None
    evaluations: Optional[List[EvaluationResult]] = None
    error: Optional[str] = None


class RagDoc(BaseModel):
    """检索单条文档结构体｜0003向量存储元数据设计"""
    doc_id: int
    title: str       # 文档片段标题
    content: str      # 知识库原文参考
    source: str       # 来源文件名，用于溯源
    question_no: str = ""  # 题目题号（结构化切面落库）
    section: str = ""      # 题目所在章节
    score: float = Field(default=0.0, ge=0.0)  # 相似度（向量 0~1 / BM25 无上界）


class RagRetrievalResult(BaseModel):
    """单道面试题检索返回包｜0004检索结果封装"""
    question: str
    docs: List[RagDoc]
    metrics: Optional["RetrievalMetrics"] = None


class RetrievalMetrics(BaseModel):
    """检索观测指标（T4.3）：命中数 / 得分分布 / 来源分布"""
    hit_count: int = 0
    score_min: float = 0.0
    score_max: float = 0.0
    score_mean: float = 0.0
    sources: Dict[str, int] = Field(default_factory=dict)


class McpEvalRequest(BaseModel):
    """MCP评估测试请求"""
    question: str
    answer: str
    use_hybrid: bool = True
    use_rerank: bool = True


class McpRetrievalRequest(BaseModel):
    """MCP检索请求（用于上下文预览）"""
    question: str
    top_k: int = Field(default_factory=lambda: settings.rag_top_k)
    use_hybrid: bool = True
    use_rerank: bool = Field(default_factory=lambda: settings.rag_use_rerank)