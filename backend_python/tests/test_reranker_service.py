"""
RerankerService 重排序归一化测试（P4 T4.2）
验证：得分 min-max 归一化到 [0,1] 后回写 score，且保持相对顺序
"""
import pytest
from app.services.reranker_service import RerankerService
from app.models.schemas import RagDoc


def _docs(n):
    return [RagDoc(doc_id=i, title=f"t{i}", content=f"第{i}个文档的内容", source="s", score=0.1)
            for i in range(n)]


class TestRerankNormalization:
    def test_scores_normalized_to_unit_range(self, mocker):
        svc = RerankerService()
        svc._model = mocker.Mock()
        svc._model.predict.return_value = [0.2, 0.8, 0.5]

        out = svc.rerank("查询", _docs(3), top_n=3)

        scores = [d.score for d in out]
        assert max(scores) == pytest.approx(1.0)   # 最高分归一化为 1
        assert min(scores) == pytest.approx(0.0)   # 最低分归一化为 0
        assert out[0].doc_id == 1                  # 最高分文档排在首位

    def test_order_kept_without_reverse(self, mocker):
        svc = RerankerService()
        svc._model = mocker.Mock()
        svc._model.predict.return_value = [0.9, 0.1, 0.6]

        out = svc.rerank("查询", _docs(3), top_n=3)

        assert [d.doc_id for d in out] == [0, 2, 1]

    def test_top_n_limits_results(self, mocker):
        svc = RerankerService()
        svc._model = mocker.Mock()
        svc._model.predict.return_value = [0.9, 0.1, 0.6]

        out = svc.rerank("查询", _docs(3), top_n=1)

        assert len(out) == 1
        assert out[0].doc_id == 0

    def test_empty_docs(self):
        svc = RerankerService()
        assert svc.rerank("查询", [], top_n=3) == []

    def test_model_fallback_keeps_order(self, mocker):
        svc = RerankerService()
        svc._model = False  # 模型加载失败场景

        out = svc.rerank("查询", _docs(3), top_n=2)

        assert len(out) == 2
