#离线知识库入库脚本
import sys
import os

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.vector_db import VectorDB
from app.services.llm_client import LlmClient
from app.services.rag_service import RagService

if __name__ == "__main__":
    print("===== 开始批量加载面试知识库，分块向量化存入SQLite向量库 =====")
    vector_db = VectorDB()
    llm_client = LlmClient()
    rag_service = RagService(vector_db=vector_db, llm_service=llm_client)
    rag_service.batch_import_knowledge()
    print("===== 知识库入库完成，流水线可正常调用RAG检索 =====")
