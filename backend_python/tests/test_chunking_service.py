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


class TestChunkQuestions:
    """题目级结构化切面（P2 T2.1）"""

    def _make_questions(self, answer_repeat=1, count=1, question_no="1"):
        from app.models.schemas import Question
        return [
            Question(
                question_no=str(int(question_no) + i),
                title=f"题目{int(question_no) + i}",
                question=f"第{int(question_no) + i}题：请描述该技术的工作原理。",
                answer="标准答案。" * answer_repeat,
                evaluation_points="评估要点：原理、场景。",
                source="Python基础面试题.md",
                section="Python基础",
            )
            for i in range(count)
        ]

    def test_single_question_short(self):
        chunks = ChunkingService().chunk_questions(self._make_questions(), max_chunk_size=1000)
        assert len(chunks) == 1
        c = chunks[0]
        assert "请描述该技术的工作原理。" in c.content
        assert "标准答案" in c.content
        assert "Python基础面试题.md" in c.title
        assert "题1" in c.title
        assert c.question_no == "1"
        assert c.section == "Python基础"
        assert c.source == "Python基础面试题.md"

    def test_multiple_questions_one_chunk_each(self):
        chunks = ChunkingService().chunk_questions(
            self._make_questions(count=3, question_no="1"), max_chunk_size=1000
        )
        assert len(chunks) == 3
        assert len({c.question_no for c in chunks}) == 3

    def test_empty_questions(self):
        assert ChunkingService().chunk_questions([]) == []

    def test_long_answer_split_keeps_question_first(self):
        chunks = ChunkingService().chunk_questions(
            self._make_questions(answer_repeat=200), max_chunk_size=200
        )
        assert len(chunks) > 1
        assert "请描述该技术的工作原理。" in chunks[0].content
        assert all(len(c.content) <= 200 for c in chunks)

    def test_long_answer_title_carries_sequence(self):
        chunks = ChunkingService().chunk_questions(
            self._make_questions(answer_repeat=200), max_chunk_size=200
        )
        assert "（1/" in chunks[0].title and "/" + str(len(chunks)) + "）" in chunks[0].title
        assert all("（" in c.title for c in chunks)

    def test_each_question_at_least_one_chunk(self):
        chunks = ChunkingService().chunk_questions(
            self._make_questions(answer_repeat=300, count=3, question_no="1"),
            max_chunk_size=100,
        )
        assert len(chunks) >= 3
        assert len({c.question_no for c in chunks}) == 3

    def test_overlap_keeps_context_between_chunks(self):
        chunks = ChunkingService().chunk_questions(
            self._make_questions(answer_repeat=200), max_chunk_size=200, chunk_overlap=20
        )
        assert len(chunks) > 1
        tail = chunks[0].content[-20:].strip()
        assert tail and tail in chunks[1].content

    def test_long_question_still_respects_max_size(self):
        from app.models.schemas import Question
        q = Question(
            question_no="1", title="超长问题", question="第一问。" * 50,
            answer="标准答案。", evaluation_points="", source="a.md", section="",
        )
        chunks = ChunkingService().chunk_questions([q], max_chunk_size=100)
        assert len(chunks) >= 2
        assert all(len(c.content) <= 100 for c in chunks)
        compact = chunks[0].content.replace("\n", "")
        assert q.question[:50] in compact

    def test_content_not_lost_after_chunking(self):
        chunks = ChunkingService().chunk_questions(
            self._make_questions(answer_repeat=100), max_chunk_size=100, chunk_overlap=0
        )
        q = self._make_questions(answer_repeat=100)[0]
        joined = "\n".join(c.content for c in chunks)
        assert q.question.strip() in joined
        assert "标准答案" in joined
        assert "评估要点" in joined
