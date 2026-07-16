#离线知识库入库脚本
import sys
import os

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import rag_service

if __name__ == "__main__":
    print("===== 开始批量加载面试知识库，分块向量化存入SQLite向量库 =====")
    rag_service.batch_import_knowledge()
    print("===== 知识库入库完成，流水线可正常调用RAG检索 =====")