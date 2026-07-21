"""
知识库管理服务
提供知识库统计、清空、批量导入等管理功能
"""
import os
import logging
from typing import Dict
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库管理服务"""
    
    def __init__(self, vector_db=None, chunking_service=None, embedding_service=None):
        # 依赖注入
        if vector_db is None:
            from app.core.vector_db import VectorDB
            self.vector_db = VectorDB()
        else:
            self.vector_db = vector_db
        
        if chunking_service is None:
            from app.services.chunking_service import ChunkingService
            self.chunking_service = ChunkingService()
        else:
            self.chunking_service = chunking_service
        
        if embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()
        else:
            self.embedding_service = embedding_service
    
    def batch_import_knowledge(self, chunk_method: str = "fixed"):
        """离线批量导入知识库（从文件读取、分块、向量化、入库）"""
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
            
            chunk_list = self.chunking_service.split(full_text, chunk_method)
            
            for idx, chunk_text in enumerate(chunk_list):
                chunk_title = f"{filename} 片段{idx+1}"
                emb = self.embedding_service.get_embedding(chunk_text)
                self.vector_db.insert_chunk(chunk_title, chunk_text, filename, emb)
                imported_count += 1
            
            logger.info(f"导入文件 {filename}，分块数量: {len(chunk_list)}")
        
        logger.info(f"全部知识库分块向量化入库完成，共导入 {imported_count} 个分块")
        self.embedding_service._save_cache()
    
    def get_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            包含文档数量、向量数量、来源文件统计的字典
        """
        try:
            doc_count = self.vector_db.conn.execute(
                "SELECT COUNT(*) FROM rag_docs"
            ).fetchone()[0]
            
            vector_count = self.vector_db.conn.execute(
                "SELECT COUNT(*) FROM rag_vectors"
            ).fetchone()[0]
            
            source_stats = self.vector_db.conn.execute(
                "SELECT source, COUNT(*) as count FROM rag_docs GROUP BY source"
            ).fetchall()
            
            return {
                "total_documents": doc_count,
                "total_vectors": vector_count,
                "source_files": [
                    {"filename": row[0], "chunk_count": row[1]}
                    for row in source_stats
                ]
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise
    
    def clear_all(self) -> None:
        """
        清空知识库
        """
        try:
            self.vector_db.conn.execute("DELETE FROM rag_vectors")
            self.vector_db.conn.execute("DELETE FROM rag_docs")
            self.vector_db.conn.commit()
            logger.info("知识库已清空")
        except Exception as e:
            logger.error(f"清空知识库失败: {e}")
            raise
    
    def close(self):
        """清理资源"""
        self.embedding_service.clear_cache()
        logger.info("知识库管理服务资源清理完成")
