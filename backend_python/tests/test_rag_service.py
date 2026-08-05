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


class TestP4RetrievalConfig:
    """P4 T4.1/T4.2/T4.3：参数化配置 / 重排默认开启 / 检索观测埋点"""

    @pytest.mark.asyncio
    async def test_rerank_enabled_by_default(self, rag_service, mock_reranker_service):
        """T4.2 验收：检索接口默认返回重排结果"""
        result = await rag_service.retrieve_by_question("Java HashMap", use_hybrid=True)
        mock_reranker_service.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_weights_passed_to_hybrid(self, rag_service, mock_vector_db):
        """T4.1 验收：权重来自实例配置（settings 可调）"""
        await rag_service.retrieve_by_question("Java HashMap", use_hybrid=True, use_rerank=False)
        mock_vector_db.search_hybrid.assert_called_once()
        kwargs = mock_vector_db.search_hybrid.call_args.kwargs
        assert kwargs["vector_weight"] == rag_service.vector_weight
        assert kwargs["bm25_weight"] == rag_service.bm25_weight
        assert kwargs["vector_weight"] + kwargs["bm25_weight"] == pytest.approx(1.0)

    def test_custom_weights_override_settings(self, mock_vector_db, mock_embedding_service, mock_reranker_service):
        svc = RagService(vector_db=mock_vector_db, embedding_service=mock_embedding_service,
                         reranker_service=mock_reranker_service, vector_weight=0.8, bm25_weight=0.2)
        assert svc.vector_weight == 0.8
        assert svc.bm25_weight == 0.2

    @pytest.mark.asyncio
    async def test_metrics_collected(self, rag_service):
        """T4.3：命中数 / 得分分布 / 来源分布"""
        result = await rag_service.retrieve_by_question("Java HashMap", use_hybrid=True, use_rerank=False)
        assert result.metrics is not None
        assert result.metrics.hit_count == 1
        assert result.metrics.score_max >= result.metrics.score_min
        assert result.metrics.sources.get("src") == 1

    @pytest.mark.asyncio
    async def test_metrics_empty_when_no_hits(self, mock_vector_db, mock_embedding_service, mock_reranker_service):
        mock_vector_db.search_hybrid.return_value = []
        svc = RagService(vector_db=mock_vector_db, embedding_service=mock_embedding_service,
                         reranker_service=mock_reranker_service)
        result = await svc.retrieve_by_question("不存在的问题", use_rerank=False)
        assert result.metrics is not None
        assert result.metrics.hit_count == 0
        assert result.metrics.sources == {}


class TestClose:
    def test_clears_embedding_cache(self, rag_service, mock_embedding_service):
        rag_service.close()
        mock_embedding_service.clear_cache.assert_called_once()
