"""
重排序服务
使用 Cross-Encoder 对检索结果进行重排序
"""
import logging

logger = logging.getLogger(__name__)


class RerankerService:
    """
    重排序服务
    
    职责：使用 Cross-Encoder 模型对文档进行重排序
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
            
            scored_docs = list(zip(docs, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            reranked_docs = []
            for doc, score in scored_docs[:top_n]:
                doc.score = float(score)
                reranked_docs.append(doc)
            
            logger.info(f"重排序完成，返回 {len(reranked_docs)} 条结果")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return docs[:top_n]
    
    def _load_model(self):
        """延迟加载重排序模型"""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder("BAAI/bge-reranker-base")
                logger.info("重排序模型加载完成")
            except Exception as e:
                logger.warning(f"重排序模型加载失败: {e}，将跳过重排序步骤")
                self._model = False
