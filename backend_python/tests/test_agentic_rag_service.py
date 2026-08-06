"""Agentic RAG（langgraph 工作流）测试：检索→扩展→评估→合成"""
import asyncio
from types import SimpleNamespace

import pytest

from app.models.schemas import RagDoc, RagRetrievalResult
from app.services.agentic_rag_service import AgenticRagService, RagRetriever, parse_chunk_title


def _doc(doc_id, source, qno, title, content, score):
    return RagDoc(
        doc_id=doc_id, title=f"{source} · 题{qno} {title}", content=content,
        source=source, question_no=qno, score=score,
    )


class TestParseChunkTitle:
    def test_full_chunk_title(self):
        p = parse_chunk_title("3-2025年更新Java面试题最新版大合集(485页带答案).pdf · 题778 27、解释 Spring 框架中 bean 的生命周期。（1/6）")
        assert p["source"] == "3-2025年更新Java面试题最新版大合集(485页带答案).pdf"
        assert p["question_no"] == "778"
        assert p["index"] == 1 and p["total"] == 6
        assert "生命周期" in p["title"]

    def test_single_chunk_title(self):
        p = parse_chunk_title("Spring面试题.md · 题5 Spring Bean的作用域")
        assert p["index"] is None and p["total"] is None
        assert p["title"] == "Spring Bean的作用域"

    def test_unparseable(self):
        assert parse_chunk_title("无结构文本") is None


class TestStitchBlocks:
    def test_overlap_tail_dedup(self):
        svc = AgenticRagService(retrieve_fn=lambda q: [])
        parts = [
            "问题\nAAAAABBBBB",
            "BBBBBCCCCC",
            "CCCCCDDDDD",
        ]
        stitched = svc._stitch(parts)
        assert "BBBBB" in stitched and "CCCCC" in stitched and "DDDDD" in stitched
        assert stitched.count("BBBBB") == 1 and stitched.count("CCCCC") == 1


class TestAssessRule:
    def test_related_requires_score_and_keyword_hit(self):
        svc = AgenticRagService(retrieve_fn=lambda q: [])
        cand = {
            "score": 0.7, "full_answer": "Spring 容器实例化 bean，生命周期 初始化 销毁",
        }
        assert svc._is_related("Spring Bean 生命周期", cand)

    def test_low_score_not_related(self):
        svc = AgenticRagService(retrieve_fn=lambda q: [])
        cand = {"score": 0.44, "full_answer": "Spring 中 Bean 的注入方式有三种"}
        assert not svc._is_related("Spring Bean 生命周期", cand)

    def test_no_keyword_hit_not_related(self):
        svc = AgenticRagService(retrieve_fn=lambda q: [])
        cand = {"score": 0.9, "full_answer": "MySQL 索引 B+ 树结构"}
        assert not svc._is_related("Spring Bean 生命周期", cand)


class TestRagRetriever:
    """LangChain 标准化检索组件：RagDoc → Document"""

    def test_ainvoke_maps_docs_to_documents(self):
        doc = RagDoc(doc_id=1, title="s.md · 题1 标题", content="内容",
                     source="s.md", question_no="1", score=0.9)

        async def fake_retrieve(q, **kwargs):
            return RagRetrievalResult(question=q, docs=[doc])

        fake_rag = SimpleNamespace(retrieve_by_question=fake_retrieve)
        retriever = RagRetriever(fake_rag, top_k=4)
        result = asyncio.run(retriever.ainvoke("问题"))
        assert result[0].page_content == "内容"
        assert result[0].metadata["source"] == "s.md"
        assert result[0].metadata["question_no"] == "1"
        assert result[0].metadata["score"] == 0.9


class TestGraphFlow:
    @pytest.fixture()
    def service(self):
        return AgenticRagService(
            retrieve_fn=None,  # 下方各测试注入
            related_score_threshold=0.6, min_keyword_hits=1, max_iterations=2,
        )

    def test_long_answer_not_truncated(self):
        """命中超长题目（1/6）时，expand 拉取全部块拼接，答案不截断"""
        src = "3号.pdf"
        blocks = [_doc(i, src, "778", f"27、解释生命周期。（{i}/6）", f"生命周期要点{i}", 0.9)
                  for i in range(1, 7)]
        calls = {"n": 0}

        async def retrieve(q):
            calls["n"] += 1
            return [blocks[0]]

        def question_chunks(source, qno):
            return blocks

        async def run():
            svc = AgenticRagService(retrieve_fn=retrieve, question_chunks_fn=question_chunks)
            return await svc.answer("解释 Spring 框架中 bean 的生命周期")

        result = asyncio.run(run())
        assert calls["n"] == 1
        assert result.status == "answered"
        assert "生命周期要点6" in result.candidates[0].full_answer

    def test_unrelated_candidate_filtered(self):
        """低分无关候选标记 related=False，且排在相关候选之后"""
        src = "3号.pdf"
        related_doc = _doc(1, src, "778", "27、解释生命周期。（1/6）",
                           "Spring 容器实例化 bean，生命周期 初始化", 1.0)
        unrelated_doc = _doc(2, src, "999", "6、注入方式。（2/3）",
                             "Spring 中 Bean 的注入方式有三种", 0.44)

        async def retrieve(q):
            return [related_doc, unrelated_doc]

        def question_chunks(source, qno):
            return [related_doc] if qno == "778" else [unrelated_doc]

        async def run():
            svc = AgenticRagService(retrieve_fn=retrieve, question_chunks_fn=question_chunks)
            return await svc.answer("解释 Spring 框架中 bean 的生命周期")

        result = asyncio.run(run())
        assert len(result.candidates) == 2
        assert result.candidates[0].related is True
        assert result.candidates[1].related is False
        assert result.status == "answered"

    def test_all_unrelated_triggers_requery(self):
        """全不相关时走 re_query 二次检索，直到命中"""
        src = "3号.pdf"
        calls = {"n": 0}

        async def retrieve(q):
            calls["n"] += 1
            if calls["n"] == 1:
                return [_doc(1, src, "888", "8、无关题目。", "MySQL 索引 B+ 树", 0.5)]
            return [_doc(2, src, "778", "27、解释生命周期。（1/6）",
                         "Spring 容器实例化 bean，生命周期 初始化", 1.0)]

        def question_chunks(source, qno):
            return []

        async def run():
            svc = AgenticRagService(retrieve_fn=retrieve, question_chunks_fn=question_chunks)
            return await svc.answer("解释 Spring 框架中 bean 的生命周期")

        result = asyncio.run(run())
        assert calls["n"] == 2
        assert result.iterations == 2
        assert result.status == "answered"

    def test_no_match_stops_at_iteration_cap(self):
        """持续无相关候选时到达迭代上限即收尾，不死循环"""
        src = "3号.pdf"

        async def retrieve(q):
            return [_doc(1, src, "888", "8、无关题目。", "MySQL 索引 B+ 树", 0.5)]

        def question_chunks(source, qno):
            return []

        async def run():
            svc = AgenticRagService(retrieve_fn=retrieve, question_chunks_fn=question_chunks,
                                    max_iterations=2)
            return await svc.answer("解释 Spring 框架中 bean 的生命周期")

        result = asyncio.run(run())
        assert result.status == "no_match"
        assert result.iterations == 3
