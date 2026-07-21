"""
分块服务
提供固定长度、段落、语义三种分块策略
"""
import re
import logging
from app.core.config import settings

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
