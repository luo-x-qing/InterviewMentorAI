"""
嵌入向量服务
负责文本向量化和缓存管理
"""
import os
import json
import hashlib
import logging
import threading
from app.core.config import settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class LocalBgeEncoder:
    """
    本地 BGE 嵌入编码器（离线）

    基于 transformers 加载 BAAI/bge-large-zh-v1.5（1024 维，与向量库维度一致），
    使用 [CLS] 向量 + L2 归一化，与 BGE 官方检索推荐一致。
    首次加载从 HuggingFace 下载模型，之后完全离线。
    """

    def __init__(self, model_name: str = None, device: str = None):
        self._model_name = model_name or settings.embedding_model
        self._tokenizer = None
        self._model = None
        self._lock = threading.Lock()
        self._device = device

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
            import torch
            from transformers import AutoModel, AutoTokenizer
            logger.info(f"加载本地嵌入模型 {self._model_name} ...")
            self._tokenizer = self._from_pretrained_local_first(AutoTokenizer.from_pretrained, self._model_name)
            self._model = self._from_pretrained_local_first(AutoModel.from_pretrained, self._model_name)
            # 设备优先 GPU（批量入库加速）；无 GPU 回退 CPU
            if self._device is None:
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = self._model.to(self._device)
            self._model.eval()
            logger.info(f"本地嵌入模型 {self._model_name} 加载完成（device={self._device}）")

    def encode(self, text: str) -> list[float]:
        """对单条文本生成归一化嵌入向量"""
        import torch
        self._ensure_loaded()
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True,
            max_length=512, padding=True,
        ).to(self._device)
        with torch.no_grad():
            outputs = self._model(**inputs)
        # BGE 检索推荐：[CLS] 向量 + L2 归一化
        cls_vec = outputs.last_hidden_state[:, 0]
        cls_vec = torch.nn.functional.normalize(cls_vec, p=2, dim=1)
        return cls_vec[0].tolist()


class EmbeddingService:
    """
    嵌入向量服务
    
    职责：本地模型生成向量，管理缓存
    不涉及分块、存储或检索
    """

    def __init__(self, encoder=None, cache_file: str = None):
        self.embed_model = settings.embedding_model
        self._cache_file = cache_file or "./data/embedding_cache.json"
        self._cache: dict[str, list[float]] = {}

        # 依赖注入：encoder 显式注入时使用之（测试 mock 场景）；
        # 否则懒加载本地 BGE 编码器（离线，无外部 API 依赖）
        self._encoder = encoder

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
            if self._encoder is None:
                self._encoder = LocalBgeEncoder()
            embedding = self._encoder.encode(text)

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
