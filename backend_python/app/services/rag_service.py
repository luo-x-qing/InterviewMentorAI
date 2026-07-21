"""
RAG 业务层
纯检索入口，编排 EmbeddingService、RerankerService、VectorDB
"""
import logging
from app.core.config import settings
from app.models.schemas import RagDoc, RagRetrievalResult

logger = logging.getLogger(__name__)


class RagService:
    """
    RAG 业务服务
    
    职责：编排检索流程（混合检索 + 重排序）
    不直接处理分块、向量化或重排序逻辑
    """
    
    def __init__(self, vector_db=None, embedding_service=None, reranker_service=None,
                 top_k: int = None, threshold: float = None):
        self.top_k = top_k if top_k is not None else settings.rag_top_k
        self.threshold = threshold if threshold is not None else settings.rag_similar_threshold
        
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
                             use_rerank: bool = False) -> RagRetrievalResult:
        """
        在线检索入口
        
        Args:
            interview_question: 面试问题
            use_hybrid: 是否使用混合检索
            use_rerank: 是否使用重排序
            
        Returns:
            检索结果
        """
        logger.info(f"执行RAG检索，面试问题：{interview_question}")
        
        query_emb = await self.embedding_service.get_embedding(interview_question)
        
        if use_hybrid:
            hit_docs = self.vector_db.search_hybrid(
                query=interview_question,
                query_emb=query_emb,
                top_k=self.top_k * 2 if use_rerank else self.top_k,
                threshold=self.threshold,
                vector_weight=0.7,
                bm25_weight=0.3
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
            docs=hit_docs
        )
    
    def close(self):
        """清理资源"""
        self.embedding_service.clear_cache()
        logger.info("RAG服务资源清理完成")
