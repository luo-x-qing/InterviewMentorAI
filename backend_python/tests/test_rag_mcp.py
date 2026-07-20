import pytest
from app.models.schemas import RagDoc, RagRetrievalResult


@pytest.fixture
def mock_rag_service(mocker):
    mock = mocker.MagicMock()
    mock.retrieve_by_question.return_value = RagRetrievalResult(
        question="test",
        docs=[
            RagDoc(doc_id=1, title="t1", content="Java HashMap底层原理", source="src", score=0.85),
        ],
    )
    return mock


@pytest.fixture
def mock_prompt_service(mocker):
    mock = mocker.MagicMock()
    mock.evaluate_answer.return_value = "llm评估结果"
    return mock


@pytest.fixture
def rag_mcp(mock_rag_service, mock_prompt_service):
    from app.services.rag_mcp import RagMCP

    return RagMCP(rag_service=mock_rag_service, prompt_service=mock_prompt_service)


class TestBuildRagContext:
    def test_with_docs(self, rag_mcp):
        result = RagRetrievalResult(
            question="q",
            docs=[RagDoc(doc_id=1, title="t1", content="内容", source="src", score=0.85)],
        )
        context = rag_mcp.build_rag_context(result)
        assert "内容" in context
        assert "src" in context

    def test_empty_docs(self, rag_mcp):
        result = RagRetrievalResult(question="q", docs=[])
        context = rag_mcp.build_rag_context(result)
        assert context == ""


class TestLimitContextLength:
    def test_within_limit(self, rag_mcp):
        text = "短文本"
        assert rag_mcp.limit_context_length(text, max_chars=100) == text

    def test_exceeds_limit(self, rag_mcp):
        text = "A" * 2000
        truncated = rag_mcp.limit_context_length(text, max_chars=100)
        assert len(truncated) <= 100 + 20
        assert "已截断" in truncated


class TestRagEnhanceEvaluate:
    def test_full_pipeline(self, rag_mcp, mock_rag_service, mock_prompt_service):
        result = rag_mcp.rag_enhance_evaluate(question="Java是什么", answer="一种语言")
        assert result == "llm评估结果"
        mock_rag_service.retrieve_by_question.assert_called_once_with(
            interview_question="Java是什么", use_hybrid=True, use_rerank=True
        )
        mock_prompt_service.evaluate_answer.assert_called_once()
        args = mock_prompt_service.evaluate_answer.call_args[1]
        assert args["question"] == "Java是什么"
        assert args["answer"] == "一种语言"
