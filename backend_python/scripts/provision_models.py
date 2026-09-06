"""模型缓存预置脚本（离线分发用）

把 RAG 需要的两个本地模型下载到 `settings.model_cache_dir`（= backend_python/models/hf_cache，
docker-compose 已 bind mount 到容器 /app/models，镜像内不含 models）：
- BAAI/bge-large-zh-v1.5  （嵌入，1024 维）
- BAAI/bge-reranker-base  （重排，CrossEncoder）

用法（需要联网的构建机/开发机）：
    docker compose exec python-ai python scripts/provision_models.py
    # 仅检查缓存完整性不下载：
    docker compose exec python-ai python scripts/provision_models.py --verify-only

下载完成后缓存为 HF hub 标准结构；若目标交付环境是 Windows 且需要真实文件
（无符号链接权限），在容器内经 bind mount 执行一次符号链接展开即可：
    cd /app/models && for m in hf_cache/models--BAAI--*/; do
      for r in "$m"snapshots/*/; do for f in "$r"*; do
        [ -L "$f" ] && { t=$(readlink "$f"); rm -f "$f"; cp "$m"blobs/$(basename "$t") "$f"; }; done; done; done
"""
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("provision_models")


def _warn_no_env():
    import os
    if os.environ.get("HF_HUB_DOWNLOAD_TIMEOUT"):
        return
    logger.info("未设置 HF_TOKEN，下载限速稍低（匿名），功能不受影响；大规模下载可设置 HF_TOKEN")


def load_embedding(cache_dir: str, verify_only: bool = False):
    from transformers import AutoModel, AutoTokenizer

    model = "BAAI/bge-large-zh-v1.5"
    if verify_only:
        AutoTokenizer.from_pretrained(model, cache_dir=cache_dir, local_files_only=True)
        AutoModel.from_pretrained(model, cache_dir=cache_dir, local_files_only=True)
    else:
        AutoTokenizer.from_pretrained(model, cache_dir=cache_dir)
        AutoModel.from_pretrained(model, cache_dir=cache_dir)
    logger.info("embedding %s 就绪", model)


def load_reranker(cache_dir: str, verify_only: bool = False):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model = "BAAI/bge-reranker-base"
    if verify_only:
        AutoTokenizer.from_pretrained(model, cache_dir=cache_dir, local_files_only=True)
        AutoModelForSequenceClassification.from_pretrained(model, cache_dir=cache_dir, local_files_only=True)
    else:
        AutoTokenizer.from_pretrained(model, cache_dir=cache_dir)
        AutoModelForSequenceClassification.from_pretrained(model, cache_dir=cache_dir)
    logger.info("reranker %s 就绪", model)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="预置/校验 RAG 本地模型缓存")
    parser.add_argument("--verify-only", action="store_true",
                        help="仅用 local_files_only 校验缓存完整性，不联网下载")
    args = parser.parse_args(argv)

    from app.core.config import settings

    cache = Path(settings.model_cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    logger.info("model_cache_dir=%s", cache)

    _warn_no_env()
    load_embedding(str(cache), verify_only=args.verify_only)
    load_reranker(str(cache), verify_only=args.verify_only)
    logger.info("模型缓存就绪：%s", cache)
    return 0


if __name__ == "__main__":
    sys.exit(main())