"""
RagService 单元测试
测试接缝: RagService.retrieve_by_question()
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.rag_service import RagService
from app.models.schemas import RagDoc


@pytest.fixture
def mock_vector_db():
    mock = MagicMock()
    mock.search_hybrid.return_value = [
        RagDoc(doc_id=1, title="t1", content="Java HashMap底层原理", source="src", score=0.85),
    ]
    mock.search_vector.return_value = [
        RagDoc(doc_id=1, title="t1", content="Java HashMap底层原理", source="src", score=0.85),
    ]
    return mock


@pytest.fixture
def mock_embedding_service():
    mock = MagicMock()
    mock.get_embedding = AsyncMock(return_value=[0.1] * 1024)
    return mock


@pytest.fixture
def mock_reranker_service():
    mock = MagicMock()
    mock.rerank.return_value = [
        RagDoc(doc_id=1, title="t1", content="Java HashMap底层原理", source="src", score=0.9),
    ]
    return mock


@pytest.fixture
def rag_service(mock_vector_db, mock_embedding_service, mock_reranker_service):
    return RagService(
        vector_db=mock_vector_db,
        embedding_service=mock_embedding_service,
        reranker_service=mock_reranker_service
    )


class TestRetrieveByQuestion:
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, rag_service, mock_vector_db, mock_embedding_service):
        result = await rag_service.retrieve_by_question("Java HashMap", use_hybrid=True)
        assert len(result.docs) == 1
        mock_vector_db.search_hybrid.assert_called_once()
        mock_embedding_service.get_embedding.assert_called_once_with("Java HashMap")

    @pytest.mark.asyncio
    async def test_vector_only_retrieval(self, rag_service, mock_vector_db):
        result = await rag_service.retrieve_by_question("Java HashMap", use_hybrid=False)
        assert len(result.docs) == 1
        mock_vector_db.search_vector.assert_called_once()

    @pytest.mark.asyncio
    async def test_rerank_called_when_enabled(self, rag_service, mock_reranker_service):
        result = await rag_service.retrieve_by_question("Java HashMap", use_hybrid=True, use_rerank=True)
        mock_reranker_service.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_rerank_not_called_when_disabled(self, rag_service, mock_reranker_service):
        result = await rag_service.retrieve_by_question("Java HashMap", use_hybrid=True, use_rerank=False)
        mock_reranker_service.rerank.assert_not_called()


class TestClose:
    def test_clears_embedding_cache(self, rag_service, mock_embedding_service):
        rag_service.close()
        mock_embedding_service.clear_cache.assert_called_once()
