#离线知识库入库脚本（P5：接通 import_document 单入口，幂等 + 自检 + 目录对账）
import sys
import os

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.vector_db import VectorDB
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService


def main():
    print("===== 开始批量入库面试题库（幂等 + 自检）=====")
    vector_db = VectorDB()
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()
    knowledge_service = KnowledgeService(
        vector_db=vector_db,
        chunking_service=chunking_service,
        embedding_service=embedding_service
    )

    root = settings.rag_doc_root
    total_questions = 0
    total_chunks = 0
    failed = []
    for p in knowledge_service.list_doc_files(root):
        fn = os.path.basename(p)
        r = knowledge_service.import_document(p)
        total_questions += r.question_count
        total_chunks += r.chunk_count
        print(f"  {fn}: {r.status} · {r.question_count}题 / {r.chunk_count}块 / 自检{r.self_check}")
        if r.status == "failed":
            failed.append(fn)

    removed = knowledge_service.reconcile_directory(root)
    stats = knowledge_service.get_stats()
    print(f"===== 入库完成：{total_questions} 题 / {total_chunks} 块 =====")
    print(f"库内统计：文档 {stats['total_documents']} · 向量 {stats['total_vectors']} · 来源 {len(stats['source_files'])}")
    print(f"目录对账清理：{removed} 个已消失题库")
    if failed:
        print(f"失败题库：{failed}")
        knowledge_service.close()
        sys.exit(1)
    print("===== 知识库入库完成，流水线可正常调用RAG检索 =====")
    knowledge_service.close()


if __name__ == "__main__":
    main()
