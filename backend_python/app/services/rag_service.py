#rag上层业务：分块/向量化/检索
import os
import json
import hashlib
import logging
from typing import List
from app.core.config import settings
from app.models.schemas import RagDoc, RagRetrievalResult

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self, vector_db=None, llm_service=None):
        self.embed_model = settings.embedding_model
        self.top_k = settings.rag_top_k
        self.threshold = settings.rag_similar_threshold
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        # 重排序模型（延迟加载）
        self._reranker = None
        # Embedding缓存
        self._embedding_cache = {}
        self._cache_file = "./data/embedding_cache.json"
        
        # 依赖注入
        if vector_db is None:
            from app.core.vector_db import VectorDB
            self.vector_db = VectorDB()
        else:
            self.vector_db = vector_db
            
        if llm_service is None:
            from app.services.llm_service import LlmService
            self.llm_service = LlmService()
        else:
            self.llm_service = llm_service
            
        self._load_cache()

    def split_fixed_chunk(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """固定长度滑动分块｜0002文档分块课程基础方案"""
        size = chunk_size if chunk_size is not None else self.chunk_size
        overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap
        
        chunks = []
        start = 0
        full_len = len(text)
        step = size - overlap
        while start < full_len:
            end = min(start + size, full_len)
            chunks.append(text[start:end])
            start += step
        return chunks

    def split_paragraph_chunk(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """按段落分块｜保留语义完整性"""
        size = chunk_size if chunk_size is not None else self.chunk_size
        
        # 按双换行符分段
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前段落加上新段落超过限制，保存当前块
            if len(current_chunk) + len(para) + 1 > size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
            else:
                current_chunk = current_chunk + "\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def split_semantic_chunk(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """语义分块｜按句子边界切分，保持语义完整"""
        import re
        
        size = chunk_size if chunk_size is not None else self.chunk_size
        
        # 按句子结束符分割
        sentences = re.split(r'([。！？\n])', text)
        
        # 重新组合句子
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if sentence.strip():
                combined_sentences.append(sentence)
        
        chunks = []
        current_chunk = ""
        
        for sentence in combined_sentences:
            if len(current_chunk) + len(sentence) > size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def split_chunks(self, text: str, method: str = "fixed", chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
        """统一的分块入口方法"""
        if method == "paragraph":
            return self.split_paragraph_chunk(text, chunk_size, chunk_overlap)
        elif method == "semantic":
            return self.split_semantic_chunk(text, chunk_size, chunk_overlap)
        else:
            return self.split_fixed_chunk(text, chunk_size, chunk_overlap)

    def _load_reranker(self):
        """延迟加载重排序模型"""
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder("BAAI/bge-reranker-base")
                logger.info("重排序模型加载完成")
            except Exception as e:
                logger.warning(f"重排序模型加载失败: {e}，将跳过重排序步骤")
                self._reranker = False

    def rerank_documents(self, query: str, docs: list, top_n: int = 3) -> list:
        """使用Cross-Encoder对检索结果进行重排序"""
        if not docs:
            return []
        
        self._load_reranker()
        
        if self._reranker is False:
            # 如果模型加载失败，直接返回原结果
            return docs[:top_n]
        
        try:
            # 构建查询-文档对
            pairs = [(query, doc.content) for doc in docs]
            
            # 计算重排序分数
            scores = self._reranker.predict(pairs)
            
            # 按分数排序
            scored_docs = list(zip(docs, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 返回top_n结果
            reranked_docs = []
            for doc, score in scored_docs[:top_n]:
                doc.score = float(score)
                reranked_docs.append(doc)
            
            logger.info(f"重排序完成，返回 {len(reranked_docs)} 条结果")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return docs[:top_n]

    def _load_cache(self):
        """加载embedding缓存"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._embedding_cache = json.load(f)
                logger.info(f"加载embedding缓存，共 {len(self._embedding_cache)} 条记录")
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            self._embedding_cache = {}

    def _save_cache(self):
        """保存embedding缓存"""
        try:
            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._embedding_cache, f)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{self.embed_model}:{text}".encode()).hexdigest()

    def get_text_embedding(self, text: str) -> list[float]:
        """调用DashScope生成向量｜带缓存"""
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self._embedding_cache:
            logger.debug(f"从缓存获取embedding: {text[:20]}...")
            return self._embedding_cache[cache_key]
        
        # 调用API
        try:
            resp = self.llm_service.client.embeddings.create(
                model=self.embed_model,
                input=text
            )
            embedding = resp.data[0].embedding
            
            # 保存到缓存
            self._embedding_cache[cache_key] = embedding
            if len(self._embedding_cache) % 100 == 0:  # 每100条保存一次
                self._save_cache()
            
            return embedding
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            raise Exception(f"向量化失败: {str(e)}")

    def batch_import_knowledge(self, chunk_method: str = "fixed"):
        """离线批量导入知识库｜0001离线数据准备阶段"""
        root = settings.rag_doc_root
        if not os.path.exists(root):
            os.makedirs(root)
            logger.info(f"创建知识库目录 {root}")
            return
        
        imported_count = 0
        for filename in os.listdir(root):
            if not filename.endswith((".md", ".txt")):
                continue
            file_path = os.path.join(root, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                full_text = f.read()
            
            # 使用指定的分块策略
            chunk_list = self.split_chunks(full_text, chunk_method)
            
            for idx, chunk_text in enumerate(chunk_list):
                chunk_title = f"{filename} 片段{idx+1}"
                emb = self.get_text_embedding(chunk_text)
                self.vector_db.insert_chunk(chunk_title, chunk_text, filename, emb)
                imported_count += 1
            
            logger.info(f"导入文件 {filename}，分块数量: {len(chunk_list)}")
        
        logger.info(f"全部知识库分块向量化入库完成，共导入 {imported_count} 个分块")
        # 保存缓存
        self._save_cache()

    def retrieve_by_question(self, interview_question: str, use_hybrid: bool = True, use_rerank: bool = False) -> RagRetrievalResult:
        """在线检索入口｜0004推理阶段检索，流水线调用"""
        logger.info(f"执行RAG检索，面试问题：{interview_question}")
        
        query_emb = self.get_text_embedding(interview_question)
        
        if use_hybrid:
            # 混合检索：BM25 + 向量检索
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
            # 仅向量检索
            hit_docs = self.vector_db.search_vector(
                query_emb, 
                self.top_k * 2 if use_rerank else self.top_k, 
                self.threshold
            )
            logger.info(f"向量检索匹配文档数量：{len(hit_docs)}")
        
        # 重排序
        if use_rerank and hit_docs:
            hit_docs = self.rerank_documents(interview_question, hit_docs, self.top_k)
            logger.info(f"重排序后文档数量：{len(hit_docs)}")
        
        return RagRetrievalResult(
            question=interview_question,
            docs=hit_docs
        )

    def close(self):
        """清理资源"""
        self._embedding_cache.clear()
        logger.info("RAG服务资源清理完成")