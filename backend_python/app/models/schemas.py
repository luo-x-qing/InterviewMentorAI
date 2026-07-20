"""
数据模型定义
定义 Agent 流水线中使用的数据结构
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


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
    score: float = Field(default=0.0, ge=0.0)  # 相似度（向量 0~1 / BM25 无上界）


class RagRetrievalResult(BaseModel):
    """单道面试题检索返回包｜0004检索结果封装"""
    question: str
    docs: List[RagDoc]


class McpEvalRequest(BaseModel):
    """MCP评估测试请求"""
    question: str
    answer: str
    use_hybrid: bool = True
    use_rerank: bool = True


class McpRetrievalRequest(BaseModel):
    """MCP检索请求（用于上下文预览）"""
    question: str
    top_k: int = 3
    use_hybrid: bool = True
    use_rerank: bool = False