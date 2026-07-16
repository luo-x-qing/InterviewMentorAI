"""
知识库管理服务
提供知识库统计、清空等管理功能
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库管理服务"""
    
    def __init__(self, vector_db=None):
        # 依赖注入
        if vector_db is None:
            from app.core.vector_db import VectorDB
            self.vector_db = VectorDB()
        else:
            self.vector_db = vector_db
    
    def get_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            包含文档数量、向量数量、来源文件统计的字典
        """
        try:
            # 查询文档数量
            doc_count = self.vector_db.conn.execute(
                "SELECT COUNT(*) FROM rag_docs"
            ).fetchone()[0]
            
            # 查询向量数量
            vector_count = self.vector_db.conn.execute(
                "SELECT COUNT(*) FROM rag_vectors"
            ).fetchone()[0]
            
            # 查询来源文件统计
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
        
        删除所有文档和向量数据
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
        logger.info("知识库管理服务资源清理完成")