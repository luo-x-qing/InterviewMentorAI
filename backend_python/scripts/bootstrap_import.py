"""首次部署知识库入库引导（如 AGENT-ARCHITECTURE.md §15 部署章节所述）。

容器内执行（镜像已内置本脚本 + 依赖；幂等，可多次运行）：

    docker compose exec python-ai python scripts/bootstrap_import.py
    # 仅入库 Markdown/TXT：
    docker compose exec python-ai python scripts/bootstrap_import.py --ext md txt

遍历 settings.rag_doc_root（docker-compose 已将其 bind mount 到
./backend_python/data/rag_docs），逐个调用 KnowledgeService.import_document：
- 指纹未变 -> skipped（幂等）
- 指纹变更 -> updated（蓝绿替换）
- 内容损坏/自检不过 -> failed 并打印原因
汇总 ImportReport 输出导入/更新/跳过/失败计数。
"""
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="首次部署知识库入库引导")
    parser.add_argument("--ext", nargs="+", default=["md", "txt", "pdf"],
                        help="参与入库的文件扩展名（默认 md txt pdf）")
    parser.add_argument("--root", default=None,
                        help="题库根目录（默认 settings.rag_doc_root）")
    args = parser.parse_args(argv)

    from app.core.config import settings
    from app.core.vector_db import VectorDB
    from app.services.chunking_service import ChunkingService
    from app.services.embedding_service import EmbeddingService
    from app.services.knowledge_service import KnowledgeService

    exts = {e.lower().lstrip(".") for e in args.ext}
    root = Path(args.root or settings.rag_doc_root)
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lstrip(".").lower() in exts
    )
    if not files:
        print(f"[bootstrap] {root} 下未找到可导入文件（扩展名: {sorted(exts)}）")
        return 1

    print(f"[bootstrap] 发现 {len(files)} 个文件：{root}")
    vector_db = VectorDB()
    knowledge = None
    try:
        knowledge = KnowledgeService(
            vector_db=vector_db,
            chunking_service=ChunkingService(),
            embedding_service=EmbeddingService(),
        )
        summary = {"imported": 0, "updated": 0, "skipped": 0, "failed": 0, "questions": 0}
        for f in files:
            try:
                report = knowledge.import_document(str(f))
                summary[report.status] = summary.get(report.status, 0) + 1
                summary["questions"] += getattr(report, "question_count", 0) or 0
                note = getattr(report, "error", "") or ""
                print(f"[{report.status}] {f.name}{' - ' + note if note else ''}")
            except Exception as e:  # noqa: BLE001
                summary["failed"] += 1
                print(f"[failed] {f.name}: {e}")
        print(f"[bootstrap] 完成：{summary}")
        return 0 if summary["failed"] == 0 else 2
    finally:
        if knowledge is not None:
            knowledge.close()
        vector_db.close()


if __name__ == "__main__":
    sys.exit(main())