#RAG 端到端演练脚本（T5.2）：临时库 + 伪 embedding，验证"入库幂等 → 检索 → 删除 → 对账"全链路。
#不触碰真实题库与 DashScope API 配额，可重复运行。运行：python tests/rag_e2e_check.py
import sys
import os
import asyncio
import tempfile

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.vector_db import VectorDB
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService

BANK = """# E2E演练题库

## 题目1：演练JVM是什么？
**问题：** 演练JVM是什么？
**标准答案：** 演练时JVM是Java虚拟机，负责执行字节码。
**评估要点：** 原理、内存模型。

## 题目2：演练HashMap原理？
**问题：** 演练HashMap原理？
**标准答案：** 演练时HashMap底层是数组加链表红黑树。
**评估要点：** 数据结构、冲突解决。
"""


async def _pseudo_embedding(text: str):
    """伪 embedding：确定性，不调用外部 API"""
    return [0.5] * 1024


def main():
    temp_dir = tempfile.mkdtemp(prefix="rag_e2e_")
    db_path = os.path.join(temp_dir, "e2e.db")
    bank_path = os.path.join(temp_dir, "E2E演练题库.md")

    # 伪 embedding 注入（覆盖 async 实例方法）
    EmbeddingService.get_embedding = staticmethod(lambda text: asyncio.run(_pseudo_embedding(text)))

    db = VectorDB(db_path=db_path)
    emb_svc = EmbeddingService(cache_file=os.path.join(temp_dir, "cache.json"))
    ks = KnowledgeService(
        vector_db=db,
        chunking_service=ChunkingService(),
        embedding_service=emb_svc,
    )

    failures = []

    def check(name, cond, detail=""):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
        if not cond:
            failures.append(name)

    # 1. 新题库全量入库（T3.1）
    with open(bank_path, "w", encoding="utf-8") as f:
        f.write(BANK)
    r = ks.import_document(bank_path)
    check("新题库入库为 imported", r.status == "imported",
          f"({r.question_count}题 / {r.chunk_count}块 / 自检{r.self_check})")
    check("入库自检通过", r.self_check == "passed")
    check("识别题目数=2", r.question_count == 2)

    # 2. 幂等重跑（T3.1）
    r2 = ks.import_document(bank_path)
    check("未变更重跑为 skipped（幂等）", r2.status == "skipped")

    # 3. 检索可用性（混合 + BM25）
    docs = db.search_bm25("JVM是什么", top_k=3)
    check("BM25 检索命中演练题", any("JVM" in d.title for d in docs))
    docs = db.search_hybrid(
        query="HashMap原理", query_emb=[0.5] * 1024, top_k=3, threshold=0.25
    )
    check("混合检索命中演练题", any("HashMap" in d.title for d in docs))

    # 4. 变更后蓝绿替换（T3.1）
    with open(bank_path, "w", encoding="utf-8") as f:
        f.write(BANK + "\n## 题目3：演练Redis？\n\n**问题：** 演练Redis？\n\n**标准答案：** 演练时Redis是缓存数据库。\n\n**评估要点：** 缓存。\n\n")
    r3 = ks.import_document(bank_path)
    check("变更文件走 updated（蓝绿替换）", r3.status == "updated")
    check("替换后题目数=3", r3.question_count == 3)
    docs = db.search_bm25("Redis", top_k=3)
    check("替换后新内容可检索", any("Redis" in d.title for d in docs))

    # 5. 文档级删除（T3.2）
    ks.delete_document(os.path.basename(bank_path))
    check("删除后 BM25 无残留", db.search_bm25("JVM", top_k=5) == [])

    # 6. 目录对账（D3）：删除库内来源后，对账不误清理其他
    stats = ks.get_stats()
    check("删除后库内文档数为 0", stats["total_documents"] == 0)
    removed = ks.reconcile_directory(temp_dir)
    check("对账清理数=0（来源已在库外）", removed == 0)

    print(f"\n演练结果：{'全部通过' if not failures else '存在失败'}")
    if failures:
        print("失败项：", failures)
        ks.close()
        sys.exit(1)
    ks.close()
    print("===== 端到端演练通过：入库幂等 → 检索 → 变更替换 → 删除 → 对账 全链路 OK =====")


if __name__ == "__main__":
    main()
