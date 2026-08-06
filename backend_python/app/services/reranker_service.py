"""
重排序服务
使用本地 CrossEncoder（BAAI/bge-reranker-base）对检索结果重排序，完全离线；
保留 _model 注入接缝，供测试/离线场景使用
"""
import logging
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalBgeReranker:
    """
    本地 BGE CrossEncoder 重排器（离线）

    基于 transformers 的 AutoModelForSequenceClassification 加载
    BAAI/bge-reranker-base，输入 [query, document] 对，输出相关性 logits。
    首次加载从 HuggingFace 下载模型，之后完全离线。
    """

    def __init__(self, model_name: str = None):
        self._model_name = model_name or settings.rag_rerank_model
        self._tokenizer = None
        self._model = None
        self._lock = threading.Lock()

    @staticmethod
    def _from_pretrained_local_first(loader, model_name: str):
        """本地缓存优先加载：离线环境直接命中缓存，模型缺失时才联网下载"""
        try:
            return loader(model_name, cache_dir=settings.model_cache_dir, local_files_only=True)
        except OSError:
            logger.warning(f"本地模型 {model_name} 缓存缺失，尝试联网下载一次 ...")
            return loader(model_name, cache_dir=settings.model_cache_dir)

    def _ensure_loaded(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            logger.info(f"加载本地重排模型 {self._model_name} ...")
            self._tokenizer = self._from_pretrained_local_first(AutoTokenizer.from_pretrained, self._model_name)
            self._model = self._from_pretrained_local_first(AutoModelForSequenceClassification.from_pretrained, self._model_name)
            self._model.eval()
            logger.info(f"本地重排模型 {self._model_name} 加载完成")

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        """对 (query, document) 对批量打分"""
        import torch
        self._ensure_loaded()
        scores = []
        with torch.no_grad():
            for query, document in pairs:
                inputs = self._tokenizer(
                    query, document, return_tensors="pt",
                    truncation=True, max_length=512,
                )
                logits = self._model(**inputs).logits
                scores.append(float(logits.squeeze().item()))
        return scores


class RerankerService:
    """
    重排序服务
    
    职责：使用本地 CrossEncoder 模型对文档进行重排序
    不涉及分块、向量化或存储
    """

    def __init__(self):
        self._model = None

    def rerank(self, query: str, docs: list, top_n: int = 3) -> list:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            docs: 待重排序的文档列表 (RagDoc)
            top_n: 返回前 N 条结果
            
        Returns:
            重排序后的文档列表
        """
        if not docs:
            return []

        self._load_model()

        if self._model is False:
            return docs[:top_n]

        try:
            pairs = [(query, doc.content) for doc in docs]
            scores = self._model.predict(pairs)

            score_list = [float(s) for s in scores]
            if not score_list:
                return docs[:top_n]
            lo, hi = min(score_list), max(score_list)
            span = hi - lo

            scored_docs = list(zip(docs, score_list))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            reranked_docs = []
            for doc, score in scored_docs[:top_n]:
                # 归一化回写 score（T4.2）：重排得分映射到 [0,1]
                doc.score = (score - lo) / span if span > 0 else 0.0
                reranked_docs.append(doc)

            logger.info(f"重排序完成，返回 {len(reranked_docs)} 条结果")
            return reranked_docs

        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return docs[:top_n]

    def _load_model(self):
        """延迟加载本地重排序模型（bge-reranker-base，离线）"""
        if self._model is None:
            try:
                self._model = LocalBgeReranker(settings.rag_rerank_model)
                logger.info("本地重排序模型加载完成")
            except Exception as e:
                logger.warning(f"重排序模型加载失败: {e}，将跳过重排序步骤")
                self._model = False
