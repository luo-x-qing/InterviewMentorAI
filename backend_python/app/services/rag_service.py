"""
RAG 业务层
纯检索入口，编排 EmbeddingService、RerankerService、VectorDB
"""
import logging
from app.core.config import settings
from app.models.schemas import RagDoc, RagRetrievalResult, RetrievalMetrics

logger = logging.getLogger(__name__)


class RagService:
    """
    RAG 业务服务
    
    职责：编排检索流程（混合检索 + 重排序 + 观测埋点）
    不直接处理分块、向量化或重排序逻辑
    """
    
    def __init__(self, vector_db=None, embedding_service=None, reranker_service=None,
                 top_k: int = None, threshold: float = None,
                 vector_weight: float = None, bm25_weight: float = None):
        self.top_k = top_k if top_k is not None else settings.rag_top_k
        self.threshold = threshold if threshold is not None else settings.rag_similar_threshold
        self.vector_weight = vector_weight if vector_weight is not None else settings.rag_vector_weight
        self.bm25_weight = bm25_weight if bm25_weight is not None else settings.rag_bm25_weight
        
        # 依赖注入
        if vector_db is None:
            from app.core.vector_db import VectorDB
            self.vector_db = VectorDB()
        else:
            self.vector_db = vector_db
        
        if embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()
        else:
            self.embedding_service = embedding_service
        
        if reranker_service is None:
            from app.services.reranker_service import RerankerService
            self.reranker_service = RerankerService()
        else:
            self.reranker_service = reranker_service
    
    async def retrieve_by_question(self, interview_question: str, use_hybrid: bool = True,
                             use_rerank: bool = None) -> RagRetrievalResult:
        """
        在线检索入口
        
        Args:
            interview_question: 面试问题
            use_hybrid: 是否使用混合检索
            use_rerank: 是否使用重排序（默认取 settings.rag_use_rerank，T4.2 默认开启）
            
        Returns:
            检索结果
        """
        use_rerank = settings.rag_use_rerank if use_rerank is None else use_rerank
        logger.info(f"执行RAG检索，面试问题：{interview_question}")
        
        query_emb = await self.embedding_service.get_embedding(interview_question)
        
        if use_hybrid:
            hit_docs = self.vector_db.search_hybrid(
                query=interview_question,
                query_emb=query_emb,
                top_k=self.top_k * 2 if use_rerank else self.top_k,
                threshold=self.threshold,
                vector_weight=self.vector_weight,
                bm25_weight=self.bm25_weight
            )
            logger.info(f"混合检索匹配文档数量：{len(hit_docs)}")
        else:
            hit_docs = self.vector_db.search_vector(
                query_emb,
                self.top_k * 2 if use_rerank else self.top_k,
                self.threshold
            )
            logger.info(f"向量检索匹配文档数量：{len(hit_docs)}")
        
        if use_rerank and hit_docs:
            hit_docs = self.reranker_service.rerank(interview_question, hit_docs, self.top_k)
            logger.info(f"重排序后文档数量：{len(hit_docs)}")
        
        return RagRetrievalResult(
            question=interview_question,
            docs=hit_docs,
            metrics=self._collect_metrics(hit_docs)
        )
    
    @staticmethod
    def _collect_metrics(docs: list[RagDoc]) -> RetrievalMetrics:
        """检索观测埋点（T4.3）：命中数 / 得分分布 / 来源分布"""
        if not docs:
            return RetrievalMetrics(hit_count=0)
        scores = [d.score for d in docs]
        sources: dict[str, int] = {}
        for d in docs:
            sources[d.source] = sources.get(d.source, 0) + 1
        return RetrievalMetrics(
            hit_count=len(docs),
            score_min=min(scores),
            score_max=max(scores),
            score_mean=round(sum(scores) / len(scores), 4),
            sources=sources,
        )
    
    def close(self):
        """清理资源"""
        self.embedding_service.clear_cache()
        logger.info("RAG服务资源清理完成")
