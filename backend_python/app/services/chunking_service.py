"""
分块服务
提供固定长度、段落、语义三种通用分块策略，以及题目级结构化切面（P2）
"""
import re
import logging
from app.core.config import settings
from app.models.schemas import Question, QuestionChunk

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    分块服务
    
    职责：将文本按指定策略分割为块
    不涉及向量化、存储或检索
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap
    
    def split(self, text: str, method: str = "fixed", chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """
        统一分块入口
        
        Args:
            text: 待分块文本
            method: 分块策略 (fixed/paragraph/semantic)
            chunk_size: 块大小（可选，默认使用配置值）
            chunk_overlap: 重叠大小（可选，默认使用配置值）
            
        Returns:
            分块列表
        """
        if method == "paragraph":
            return self._split_paragraph(text, chunk_size, chunk_overlap)
        elif method == "semantic":
            return self._split_semantic(text, chunk_size, chunk_overlap)
        else:
            return self._split_fixed(text, chunk_size, chunk_overlap)
    
    def _split_fixed(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """固定长度滑动分块"""
        size = chunk_size if chunk_size is not None else self.chunk_size
        overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap
        
        if not text:
            return []
        
        chunks = []
        start = 0
        full_len = len(text)
        step = size - overlap
        
        while start < full_len:
            end = min(start + size, full_len)
            chunks.append(text[start:end])
            start += step
        
        return chunks
    
    def _split_paragraph(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """按段落分块，保留语义完整性"""
        size = chunk_size if chunk_size is not None else self.chunk_size
        
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) + 1 > size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
            else:
                current_chunk = current_chunk + "\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_semantic(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """按句子边界切分，保持语义完整"""
        size = chunk_size if chunk_size is not None else self.chunk_size
        
        sentences = re.split(r'([。！？\n])', text)
        
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if sentence.strip():
                combined_sentences.append(sentence)
        
        chunks = []
        current_chunk = ""
        
        for sentence in combined_sentences:
            if len(current_chunk) + len(sentence) > size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    # ---------- 题目级结构化切面（P2 · 落实 ADR-0002 D1） ----------

    def chunk_questions(self, questions: list[Question], max_chunk_size: int = None,
                        chunk_overlap: int = None) -> list[QuestionChunk]:
        """题目级切面：一道题目切为一个或多个块，问题始终保留在首块

        超长答案按句/段边界二次切分；块标题携带「来源 · 题号 [· 序号]」。
        """
        size = max_chunk_size if max_chunk_size is not None else self.chunk_size
        overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap

        chunks = []
        for q in questions:
            full = self._compose_question(q)
            if len(full) <= size:
                chunks.append(self._make_chunk(q, full, 1, 1))
            else:
                parts = self._split_long(full, q, size, overlap)
                total = len(parts)
                for index, part in enumerate(parts, start=1):
                    chunks.append(self._make_chunk(q, part, index, total))
        return chunks

    @staticmethod
    def _compose_question(q: Question) -> str:
        """组装题目文本：问题 → 标准答案 → 评估要点"""
        parts = [q.question, q.answer]
        if q.evaluation_points:
            parts.append("评估要点：" + q.evaluation_points)
        return "\n\n".join(p for p in parts if p and p.strip())

    @staticmethod
    def _make_chunk(q: Question, content: str, index: int, total: int) -> QuestionChunk:
        """构造切块：title 携带来源/题号；多块时追加块序号"""
        base = f"{q.source} · 题{q.question_no} {q.title}" if q.source else f"题{q.question_no} {q.title}"
        title = base if total == 1 else f"{base}（{index}/{total}）"
        return QuestionChunk(
            title=title,
            content=content,
            question_no=q.question_no,
            section=q.section,
            source=q.source,
        )

    def _split_long(self, full: str, q: Question, size: int, overlap: int) -> list[str]:
        """超长题目二次切分：首块保留完整问题，相邻块间保留重叠上下文（句/段边界）"""
        prefix = q.question.strip()
        rest = full[len(prefix):].strip("\n")
        rest_sents = self._split_sentences(rest, size)

        # 问题本身不超限时原样保留在首块；超限才走句边界切分
        if len(prefix) <= size:
            sentences = rest_sents
            current = prefix
        else:
            sentences = self._split_sentences(prefix, size) + rest_sents
            current = ""

        parts = []
        for sent in sentences:
            if not current:
                current = sent
                continue
            if len(current) + 1 + len(sent) <= size:
                current += "\n" + sent
            else:
                parts.append(current)
                # 相邻块保留上块尾部 overlap 字符，衔接上下文
                tail = current[-overlap:] if overlap and len(current) > overlap else ""
                if tail and len(tail) + 1 + len(sent) <= size:
                    current = tail + "\n" + sent
                else:
                    current = sent
        if current:
            parts.append(current)
        return parts

    @staticmethod
    def _split_sentences(text: str, size: int) -> list[str]:
        """按段/句边界切句：段落边界优先，段内按句号切分；无标点超长句硬切兜底"""
        sentences = []
        for para in re.split(r"\n\s*\n", text):
            for s in re.split(r"(?<=[。！？；])\s*", para):
                s = s.strip()
                if not s:
                    continue
                while len(s) > size:
                    sentences.append(s[:size])
                    s = s[size:]
                sentences.append(s)
        return sentences
