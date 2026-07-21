"""
EmbeddingService 单元测试
测试接缝: EmbeddingService.get_embedding()
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.embedding_service import EmbeddingService


class TestGetEmbedding:
    """向量化测试"""

    @pytest.mark.asyncio
    async def test_calls_api_on_cache_miss(self):
        mock_llm = MagicMock()
        mock_llm.client.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])])
        )
        service = EmbeddingService(llm_client=mock_llm)

        result = await service.get_embedding("测试文本")

        assert result == [0.1, 0.2, 0.3]
        mock_llm.client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cache_hit(self):
        mock_llm = MagicMock()
        service = EmbeddingService(llm_client=mock_llm)
        service._cache = {"cached_key": [0.4, 0.5, 0.6]}

        with patch.object(service, "_get_cache_key", return_value="cached_key"):
            result = await service.get_embedding("测试文本")

        assert result == [0.4, 0.5, 0.6]
        mock_llm.client.embeddings.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self):
        mock_llm = MagicMock()
        mock_llm.client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
        service = EmbeddingService(llm_client=mock_llm)

        with pytest.raises(Exception, match="向量化失败"):
            await service.get_embedding("测试文本")

    def test_clear_cache(self):
        mock_llm = MagicMock()
        service = EmbeddingService(llm_client=mock_llm)
        service._cache = {"key": [0.1]}

        service.clear_cache()

        assert service._cache == {}
