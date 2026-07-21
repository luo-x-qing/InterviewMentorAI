"""
嵌入向量服务
负责文本向量化和缓存管理
"""
import os
import json
import hashlib
import logging
from app.core.config import settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    嵌入向量服务
    
    职责：调用 DashScope 生成向量，管理缓存
    不涉及分块、存储或检索
    """
    
    def __init__(self, llm_client=None, cache_file: str = None):
        self.embed_model = settings.embedding_model
        self._cache_file = cache_file or "./data/embedding_cache.json"
        self._cache: dict[str, list[float]] = {}
        
        # 依赖注入
        if llm_client is None:
            from app.services.llm_client import LlmClient
            self._llm_client = LlmClient()
        else:
            self._llm_client = llm_client
        
        self._load_cache()
    
    async def get_embedding(self, text: str) -> list[float]:
        """
        生成文本的嵌入向量（带缓存）
        
        Args:
            text: 待向量化的文本
            
        Returns:
            嵌入向量列表
        """
        cache_key = self._get_cache_key(text)
        
        if cache_key in self._cache:
            logger.debug(f"从缓存获取embedding: {text[:20]}...")
            return self._cache[cache_key]
        
        try:
            resp = await self._llm_client.client.embeddings.create(
                model=self.embed_model,
                input=text
            )
            embedding = resp.data[0].embedding
            
            self._cache[cache_key] = embedding
            if len(self._cache) % 100 == 0:
                self._save_cache()
            
            return embedding
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            raise EmbeddingError(f"向量化失败: {str(e)}")
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("Embedding缓存已清空")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{self.embed_model}:{text}".encode()).hexdigest()
    
    def _load_cache(self):
        """加载缓存"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.info(f"加载embedding缓存，共 {len(self._cache)} 条记录")
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            self._cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
