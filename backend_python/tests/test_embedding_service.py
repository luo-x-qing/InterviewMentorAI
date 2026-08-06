"""
EmbeddingService 单元测试
测试接缝: EmbeddingService.get_embedding()（本地 BGE 编码器，注入 mock）
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.embedding_service import EmbeddingService


class TestGetEmbedding:
    """向量化测试"""

    @pytest.mark.asyncio
    async def test_calls_encoder_on_cache_miss(self):
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [0.1, 0.2, 0.3]
        service = EmbeddingService(encoder=mock_encoder)

        result = await service.get_embedding("测试文本")

        assert result == [0.1, 0.2, 0.3]
        mock_encoder.encode.assert_called_once_with("测试文本")

    @pytest.mark.asyncio
    async def test_returns_cache_hit(self):
        mock_encoder = MagicMock()
        service = EmbeddingService(encoder=mock_encoder)
        service._cache = {"cached_key": [0.4, 0.5, 0.6]}

        with patch.object(service, "_get_cache_key", return_value="cached_key"):
            result = await service.get_embedding("测试文本")

        assert result == [0.4, 0.5, 0.6]
        mock_encoder.encode.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_encoder_error(self):
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = Exception("encode error")
        service = EmbeddingService(encoder=mock_encoder)

        with pytest.raises(Exception, match="向量化失败"):
            await service.get_embedding("测试文本")

    def test_clear_cache(self):
        service = EmbeddingService(encoder=MagicMock())
        service._cache = {"key": [0.1]}

        service.clear_cache()

        assert service._cache == {}

    def test_default_constructor_is_lazy(self):
        """默认构造不加载模型（懒加载，避免阻塞/离线测试失败）"""
        service = EmbeddingService()
        assert service._encoder is None
