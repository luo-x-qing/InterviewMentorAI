#离线知识库入库脚本
import sys
import os

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.vector_db import VectorDB
from app.services.llm_client import LlmClient
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService

if __name__ == "__main__":
    print("===== 开始批量加载面试知识库，分块向量化存入SQLite向量库 =====")
    vector_db = VectorDB()
    llm_client = LlmClient()
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService(llm_client=llm_client)
    knowledge_service = KnowledgeService(
        vector_db=vector_db,
        chunking_service=chunking_service,
        embedding_service=embedding_service
    )
    knowledge_service.batch_import_knowledge()
    print("===== 知识库入库完成，流水线可正常调用RAG检索 =====")
