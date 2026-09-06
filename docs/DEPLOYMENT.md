# 部署指南（docker-compose 双容器）

截图对应架构文档 `docs/architecture/AGENT-ARCHITECTURE.md`。生产形态：

- **python-ai**（`backend_python/`，FastAPI + AI + MCP 工具层，端口 8000）
- **flutter-web**（`frontend_flutter/`，Flutter Web 构建 + nginx 伺服，端口 80，反代全部 API 与 WS）

## 0. 前置准备

1. **DashScope API Key**（语音识别/LLM）：export `DASHSCOPE_API_KEY=sk-...`
2. **JWT 强密钥**（会话签名，必须与默认值不同）：

   ```bash
   export JWT_SECRET=$(openssl rand -hex 32)
   ```

3. **本地模型缓存**（已随项目预置，**无需联网**）：RAG 使用本地 `BAAI/bge-large-zh-v1.5`（嵌入，1024 维）与
   `BAAI/bge-reranker-base`（重排，CrossEncoder），离线缓存已下载到
   `backend_python/models/hf_cache`（约 7GB，HF hub 真实文件格式，`.gitignore` 与 `.dockerignore`
   均排除，不入 git/镜像）；docker-compose 已把该目录 **bind mount** 到容器 `/app/models`，
   与 `settings.model_cache_dir=/app/models/hf_cache` 对齐，启动即可离线加载。
   移交/克隆项目时需携带此目录（或迁移后在目标 `${JWT}…` 服务器重新下载一次：见下方「重新下载模型」）。

   > **重新下载模型**（缓存缺失/需补全时，在能联网的构建机上执行）：
   > ```bash
   > docker compose exec python-ai python scripts/provision_models.py        # 下载/补全
   > docker compose exec python-ai python scripts/provision_models.py --verify-only  # 校验
   > ```

   相对路径均锚定 `backend_python/` 目录（`config.py`），与启动目录无关。

## 1. 构建与启动

```bash
# 生产基址（Web 前端 API/WS 指向本机，nginx 同源反代）；默认 localhost:8000 仅开发用
export API_BASE_URL=http://your-server-ip-or-domain

docker compose build --no-cache
docker compose up -d
docker compose ps           # 两个容器均应为 Up
```

## 2. 首次数据引导

`python_data` 卷初始为空 → SQLite 会自动建表，但**知识库（题库）为空**，需执行一次性入库引导
（幂等，重跑会跳过未变更文件；`rag_docs/` 已 bind mount 进容器，增删文档后重跑即可增量更新）：

```bash
docker compose exec python-ai python scripts/bootstrap_import.py
# 只入库 Markdown/TXT（跳过 PDF）：
docker compose exec python-ai python scripts/bootstrap_import.py --ext md txt
```

PDF 说明：OCR 默认开启（`PDF_OCR_ENABLED=true`），纯文字层 PDF 秒级入库；
文字层损坏（CID 乱码）的 PDF 需整页 OCR，耗时长，可预先人工剔除或按 `--ext` 跳过。

## 3. 验证清单

```bash
# 后端存活 + 服务装配（应为 10 个 MCP 工具注册提示）
curl http://localhost:8000/
curl http://localhost:8000/api/v1/analysis/health

# Web 前端
curl -I http://localhost/            # 200 OK

# 知识库已入库
curl http://localhost:8000/knowledge/stats

# 完整业务冒烟（注册 → 登录 → 开启陪练会话）
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" \
     -d '{"phone":"13800000000","password":"secret123","nickname":"tester"}'
curl -X POST http://localhost:8000/coach/session -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" -d '{"mode":"mixed"}'
```

## 4. 数据持久化

| 卷 / 挂载 | 内容 |
|-----------|------|
| `python_data:/app/data` | SQLite（业务 + 向量）、上传音频 `data/audio` |
| `./backend_python/data/rag_docs:/app/data/rag_docs` | 题库源（入库输入，可与卷同步增改） |
| `./backend_python/models:/app/models` | 本地模型缓存（嵌入 + 重排，离线预置，免联网） |

重建镜像不丢数据；题库源变更后重跑 §2 的 bootstrap 即可增量入库（指纹幂等）。

## 5. 安全与生产注意事项

- **JWT_SECRET**：务必注入强随机密钥，否则回落到文档标注的开发默认值（不安全）。
- **HTTPS / WSS**：生产请在反向代理或 `frontend_flutter/nginx.conf` 前加 TLS 终止；
  前端基址传 `https://...` 时 WS 自动派生为 `wss://`（`constants.dart`）。
- **CORS**：后端 `allow_origins=["*"]` 为开发便利；同源部署（§1 的 `API_BASE_URL`）不受影响，
  需要收紧时修改 `backend_python/app/main.py` 的 CORS 白名单。
- 端口放行：80（前端）、可选 8000（后端调试）；App 走 80 全量反向代理。

## 6. 常见问题

- **`/research/deep` 等新端点不生效**：`docker compose up -d --build` 重建 python-ai 镜像。
- **Coach 出题 `QUESTION_BANK_EMPTY`**：未跑引导（§2），或知识库 0 题（`knowledge/stats` 复查）。
- **首次请求很慢**：模型懒加载到内存需数秒~数十秒，属正常。
- **CI**：本仓库当前未配置 CI 流水线，可用本地 `backend_python` 全量 pytest（281 passed + 6 skipped）把门。