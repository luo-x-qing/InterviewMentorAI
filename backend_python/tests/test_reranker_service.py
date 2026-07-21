"""
RerankerService 单元测试
测试接缝: RerankerService.rerank()
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.reranker_service import RerankerService
from app.models.schemas import RagDoc


class TestRerank:
    """重排序测试"""

    def test_reranks_documents_by_score(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.3, 0.9, 0.5]
        service = RerankerService()
        service._model = mock_model

        docs = [
            RagDoc(doc_id=1, title="a", content="内容A", source="s1", score=0.5),
            RagDoc(doc_id=2, title="b", content="内容B", source="s2", score=0.6),
            RagDoc(doc_id=3, title="c", content="内容C", source="s3", score=0.4),
        ]

        result = service.rerank("查询", docs, top_n=2)

        assert len(result) == 2
        assert result[0].doc_id == 2
        assert result[1].doc_id == 3

    def test_empty_docs_returns_empty(self):
        service = RerankerService()
        result = service.rerank("查询", [], top_n=3)
        assert result == []

    def test_model_load_failure_returns_original(self):
        service = RerankerService()
        service._model = False

        docs = [
            RagDoc(doc_id=1, title="a", content="内容A", source="s1", score=0.5),
        ]

        result = service.rerank("查询", docs, top_n=3)
        assert len(result) == 1
        assert result[0].doc_id == 1

    def test_rerank_error_returns_original(self):
        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("Model error")
        service = RerankerService()
        service._model = mock_model

        docs = [
            RagDoc(doc_id=1, title="a", content="内容A", source="s1", score=0.5),
        ]

        result = service.rerank("查询", docs, top_n=3)
        assert len(result) == 1
        assert result[0].doc_id == 1
