"""
ChunkingService 单元测试
测试接缝: ChunkingService.split()
"""
import pytest
from app.services.chunking_service import ChunkingService


class TestSplitFixedChunk:
    """固定长度分块测试"""

    def test_basic_split(self):
        service = ChunkingService()
        result = service.split("abcdefghij", method="fixed", chunk_size=4, chunk_overlap=0)
        assert result == ["abcd", "efgh", "ij"]

    def test_with_overlap(self):
        service = ChunkingService()
        result = service.split("abcdefghij", method="fixed", chunk_size=4, chunk_overlap=2)
        assert result == ["abcd", "cdef", "efgh", "ghij", "ij"]

    def test_text_shorter_than_chunk(self):
        service = ChunkingService()
        result = service.split("abc", method="fixed", chunk_size=5, chunk_overlap=0)
        assert result == ["abc"]

    def test_empty_text(self):
        service = ChunkingService()
        result = service.split("", method="fixed", chunk_size=4, chunk_overlap=0)
        assert result == []

    def test_uses_default_config(self):
        service = ChunkingService(chunk_size=10, chunk_overlap=2)
        result = service.split("a" * 20, method="fixed")
        assert len(result) == 3
        assert all(len(chunk) <= 10 for chunk in result)


class TestSplitParagraphChunk:
    """段落分块测试"""

    def test_paragraph_split(self):
        service = ChunkingService()
        text = "段落一\n\n段落二\n\n段落三"
        result = service.split(text, method="paragraph", chunk_size=5)
        assert result == ["段落一", "段落二", "段落三"]

    def test_merges_small_paragraphs(self):
        service = ChunkingService()
        text = "短段落一\n\n短段落二\n\n短段落三"
        result = service.split(text, method="paragraph", chunk_size=100)
        assert len(result) == 1
        assert "短段落一" in result[0]

    def test_splits_long_paragraphs(self):
        service = ChunkingService()
        text = "A" * 50 + "\n\n" + "B" * 50
        result = service.split(text, method="paragraph", chunk_size=60)
        assert len(result) == 2


class TestSplitSemanticChunk:
    """语义分块测试"""

    def test_semantic_split(self):
        service = ChunkingService()
        text = "第一句话。第二句话。第三句话。"
        result = service.split(text, method="semantic", chunk_size=100)
        assert len(result) >= 1

    def test_respects_sentence_boundaries(self):
        service = ChunkingService()
        text = "短句。" * 10
        result = service.split(text, method="semantic", chunk_size=20)
        assert all(len(chunk) <= 25 for chunk in result)


class TestSplitDispatcher:
    """分块调度器测试"""

    def test_default_method_is_fixed(self):
        service = ChunkingService()
        result = service.split("abcdefghij", chunk_size=4, chunk_overlap=0)
        assert result == ["abcd", "efgh", "ij"]

    def test_unknown_method_falls_back_to_fixed(self):
        service = ChunkingService()
        result = service.split("abcdefghij", method="unknown", chunk_size=4, chunk_overlap=0)
        assert result == ["abcd", "efgh", "ij"]
