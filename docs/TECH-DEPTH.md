# 技术深度与广度

一份面向「工程深读」的导航文档：把 InterviewMentorAI 里值得展开的技术决策、实现细节与取舍讲清楚。
每一条都对应仓库中真实可读的代码，配合 [Agent 架构设计](architecture/AGENT-ARCHITECTURE.md)（讲"应该建成什么样"）
与 [部署指南](../DEPLOYMENT.md)（讲"怎么跑起来"），本文讲"为什么这样做、代价是什么、换你会怎样"。

> 三条技术主线贯穿全文：
>
> 1. **一条 Agent 化主线的渐进演进** —— 架构不是推倒重来，而是一步步从双后端迁到单后端、再把业务能力封装成工具交给 Agent；
> 2. **一组工程纪律** —— 可测、可回滚、可观测被当作一等公民写进设计（指纹幂等、蓝绿替换、错误单一出口、回归测试门禁）；
> 3. **AI 全套件的克制引入** —— 触达 ASR / LLM / Embedding / Reranker / OCR / 多 Agent，但每一个能力都选择最小的可行形态，能本地跑就不上云。

---

## 1. 演进：为什么是现在这个样子

要理解代码，先理解它是怎么一步步变成这样的。

### 1.1 三次架构跃迁

| 阶段 | 形态 | 核心命题 | 出处 |
|------|------|----------|------|
| v2 | Java 双后端（Java 业务 + Python AI） | 语言分区隔离业务与 AI | `docs/recycle_bin/`（归档） |
| v3.0 | Python 单后端，FastAPI 一体化 | 一个进程扛起业务、认证、AI、RAG、Agent | `AGENT-ARCHITECTURE.md` |
| v3.x | Agent 化：Orchestrator + MCP 工具层 | 业务接口即工具，Agent 统一调用，REST 与 MCP 共享一套实现 | 本文 §2.1 / §2.2 |

第一次跃迁的理由很朴素：Java 与 Python 之间只有一条 `REST` 管道？不——当时的割裂点在于**领域被切成两半**：
业务模型在一门语言里，AI 能力在另一门语言里，任何跨界的改动（比如评估一个面试回答要同时查业务数据与知识库）都要穿两次进程边界。
统一到 Python 单后端后，`interview.db`（业务 + 向量）与 `rag_*` 表同库共存（`database.py`），跨界改动变成同一个进程里的一次函数调用。
这个决定放弃了 Java 的生态，换来了**领域模型的连续性**和对 AI 能力的直接支配。

第二次跃迁（Agent 化）不在换语言，而在换**交互范式**：把业务能力从"给前端调用的函数"重定义为"给 Agent 调用的工具"。

### 1.2 演进的原则

从 git 历史看，演进是**一条连续线而非几次重写**：

```
25bbd24 style(ui)              —— UI 风格收敛（Material 3）
022af86 fix(coach)             —— 知识库无题时 409 而非 500（降级，不崩溃）
b0aa91d feat(observability)    —— 错误响应单一出口：error_code + trace_id + 完整栈
e70d42c refactor(errors)       —— 单一出口落实到全 API 层（API 层不再自己翻译异常）
25d7ac5 fix(coach)             —— 出题候选池无偏随机抽样，修复题库垄断
a2fa6f3 feat(release)          —— 深度检索公开端点 + 部署工具链（配置注入/离线模型/入库引导）
```

三条看得见的原则：

- **渐进迁移，不推倒重写**：v2 → v3 不是删除重写，而是把旧设计归档到 `docs/recycle_bin/`，让新架构从旧文档里继承审过的决策。
- **保留降级路径**：Orchestrator 落地后，旧 5 步 `AgentPipeline` 没有被删除，而是退化成为 Orchestrator 的**默认执行器**（`orchestrator.py` 注释明示），LangGraph `StateGraph` 可独立 `ainvoke` 随时接管。
- **错误发生在"最靠近源头"的地方修正**：观测性先落地（`b0aa91d`），再在整个 API 层铺开（`e70d42c`），最后才轮到 Coach 的行为修复——基础设施稳定了再谈业务正确性。

---

## 2. 分层解剖

自顶向下，每一层解决一类问题，并对外暴露**小而完整**的接口（深模块思想，详见 `AGENT-ARCHITECTURE.md` §8.2）。

### 2.1 Agent 编排层：从流水线到状态机

**对外接口**（`app/agents/orchestrator.py`）：

- `async run(request) -> AnalysisResponse` —— 跑完一次完整复盘；
- `subscribe(progress_cb)` —— 注入进度回调；
- `build_graph()` —— 拿到可独立 `ainvoke` 的 LangGraph 状态图。

**内部是一个五节点状态机**：

```
START → transcribe → separate → evaluate → reflex → report → END
```

`reflex` 是点睛之笔：评估 Agent 产出薄弱项列表后，反思回路先 `reflexion.keywords_from(评估列表)` 抽出关键词，
再 `deep_retrieve(retrieval_agent, keywords)` 做深度检索，最后把补充材料 `extend_report()` 追加进最终报告。
这不是把评估结果简单拼进报告——它复用了检索 Agent 的能力去**主动补课**，形成 评估 → 反思 → 深检索 → 报告 的闭环。

进度协议是显式的：`progress_cb(step, total, message, status)`，`_TOTAL_STEPS=4`。位置上它把「编排」和「进度呈现」解耦：

| 组件 | 角色 | 文件 |
|------|------|------|
| Orchestrator | 状态机 + 默认执行器降级 | `app/agents/orchestrator.py` |
| AgentPipeline | 旧流水线（降级执行器） | `app/services/agent_pipeline.py` |
| Reflexion | 反思回路（关键词抽取 + 深度检索） | `app/agents/reflexion.py`（对应实现） |

**为什么值得展开**：这是一个"把上一个版本的代码当作默认降级路径"的迁移范式。`ainvoke` 直接跑全流程的测试
（`test_agent_arch.py::test_build_graph_ainvoke_runs_full_flow`）保证状态图和默认执行器行为一致，迁移是**可验证的**。

### 2.2 MCP 工具层：业务接口即工具

`app/mcp/` 用一个轻量 `ToolRegistry` 把业务能力注册成标准化工具（共 10 个）：

| 域 | 工具 | 形式 |
|----|------|------|
| retrieval | `retrieve.retrieve`（混合检索+重排）、`rag.answer`（Agentic RAG 合成） | REST + MCP |
| knowledge | `knowledge.import` / `import_many` / `stats` | REST + MCP |
| coach | `coach.start` / `next_question` / `submit_answer` / `end` / `recommend` | REST + MCP |
| 业务域 | auth / interview / report / user / audio / research | **仅 REST** |

**ToolRegistry 的核心**（`app/mcp/server.py`）：

- `ToolSpec` = name / description / handler / input_model —— Pydantic input_model 负责 `call_tool` 时的参数校验；
- `call_tool(name, arguments)`：校验 → await handler → `_to_jsonable` 序列化，Agent 侧始终拿到纯 JSON；
- 可选 `to_mcp_server()` 返回 FastMCP，等于整个工具集随时可作为 MCP Server 对外暴露。

**REST 与 MCP 共享实现**：`main.py` 把同一批服务对象分别注入 FastAPI Router（薄门面）和 ToolRegistry。
一处实现，两个入口。内部链路也真的走工具：`agent_pipeline._evaluate_single` 优先 `call_tool("retrieve.retrieve", …)`
取检索上下文，缺省才回落旧封装——评估的每一题都过工具层，而不是绕过。

**"仅 REST"的边界是一个刻意决策**（`AGENT-ARCHITECTURE.md` §6.2）：auth / interview / report 这类**写入型业务**不暴露给
Agent 工具，避免 Agent 在无人监督下操作他人数据。真正开放给工具的是"检索"与"陪练"这类**能力型**接口。
工具开放边界 = 权限边界，这是在架构层面的取舍，不是偷懒。

### 2.3 检索与 RAG：从"查一次"到"Agent 工作流"

三层设计，逐层加深：

**第一层——混合检索**（`app/services/rag_service.py` → `app/core/vector_db.py`）：

- 向量通道：SQLite 内嵌 **sqlite-vec**，`VECTOR_DIM=1024`，本地 `bge-large-zh-v1.5` 产出 [CLS] 向量并 L2 归一化；无扩展时降级为普通 BLOB 表 + Python 余弦，功能不减、只慢一点；
- 关键词通道：自实现 BM25（jieba 分词 + OKAPI，`k1=1.5, b=0.75`）；
- 融合：`total = 0.7 * vector_norm + 0.3 * bm25_norm`（权重可配），阈值放行「任一路强命中」——避免某一通道的强信号被对方稀释掉。

**第二层——Agentic RAG**（`app/services/agentic_rag_service.py`）：把"查一次"升级成 LangGraph 工作流：

```
retrieve → expand → assess → (re_query → retrieve) → finalize
```

它修的是真实问题：① 检索结果常被截断成一两个分块 → `expand` 按 `source + question_no` 把同题全块聚合；② 无关候选混进来 →
`assess` 用离线规则（相似度阈值 0.6 + 关键词命中 ≥1）过滤；③ 确实没命中 → `re_query` 换关键词重来。

**第三层——反思回路**（`POST /research/deep`，`app/api/research_api.py`）：把上面内藏在报告里的反思能力
导出为公开端点（body `{keywords, max_keywords}`），复用 `Reflexion.deep_retrieve`。一次索引、多层取用，
这是设计出的复用，而不是事后凑。

**值得展开的工程细节**：评估链路底层走工具层（`call_tool("retrieve.retrieve")`），意味着从"检索一次"到"Agent
反思补课"全部路径共享同一个 `RetrievalAgent`——没有第二套实现，也就没有同步漂移。

### 2.4 知识入库管道：指纹、蓝绿替换、自检、回滚

`app/services/knowledge_service.py` 把"导入文档"做成一条**可审计、可回滚**的管道：

```
清洗(CleaningService) → 结构化切面(ChunkingService) → 向量化(EmbeddingService)
  → 指纹幂等 → 蓝绿替换 → self_check 自检 → 通过才提交指纹
```

- **指纹幂等**：`CleaningService.fingerprint(raw)` 与 `vector_db.file_fingerprint(source)` 比对，命中 → `skipped`；
  新文件 → `imported`；同指纹不同版本 → `updated`。docker 重启后再跑同一次入库，是安全的"no-op"。
- **蓝绿替换**：先插新块、成功后删旧块、并更新指纹；任一步失败走 `_rollback_inserted` / `_rollback_replace`
  两种回滚（后者会清当前块、重插旧块、还原旧指纹）——入库失败后数据回到导入前，绝不留半套。
- **自检闭环**：入库后 stats 对账（题目数 / 分块数 / 向量数）+ 前两块 BM25 抽样检索必须命中本来源；
  0 题入库 → 回滚指纹并记 `self_check="empty"`；自检不过 → 全量回滚并记为 `failed`。
  这意味着"入库成功"是一个**被验证过的声明**，而不只是"没有抛异常"。
- **脏数据防线**：PDF 里 `(cid:xxx)` 乱码块在入库前就被丢弃；乱码页在转换阶段会整页走 RapidOCR（300dpi + 裁剪图片区域）
  离线识别替换——两处兜底（转换层 + 入库层）保证乱码不落地。

这条管道是"工程纪律"主线的代表：**导入这种看似平凡的操作，被做成了增、改、跳、败四态齐全、且每种状态都可解释的系统**。

### 2.5 本地推理与模型工程

- 嵌入 `BAAI/bge-large-zh-v1.5`（1024 维）+ 重排 `BAAI/bge-reranker-base`（CrossEncoder）均为**本地推理**：
  一律先 `local_files_only=True` 命中 `models/hf_cache`，未命中才降级联网下载（`embedding_service.py` / `reranker_service.py`）。
- **离线分发**是本项目认真做过的事：模型缓存约 7GB、以 **符号链接展开后的真实文件** 预置在 `backend_python/models/hf_cache`
  （`.gitignore` / `.dockerignore` 双排除，不入库不磨镜像）；docker-compose 用 bind mount `./backend_python/models:/app/models`
  喂给容器，`settings.model_cache_dir=/app/models/hf_cache` 一一对应。`scripts/provision_models.py` 支持联网重下与
  `--verify-only` 离线校验——克隆到任何机器都能原地复现。
- LLM（DashScope qwen）与 OCR（RapidOCR ONNX）走 API / 本地引擎两条路，摄像头不触碰用户音频文件边界之外的东西。

### 2.6 Coach：以轻量 ML 逼近个性化

陪练不是花架子，而是把一系列小而扎实的机器学习点串起来：

- **会话状态机**：`COACH_IDLE → ACTIVE → DONE`，非 ACTIVE 的写入一律 `ConflictError(409)`——会话是有纪律的资源。
- **出题 Worker**（`question_worker.py`）：候选池先按难度过滤 → 按画像弱项加权 → 最后 `random.choice`；
  候选池来自 `vector_db.get_questions_for_coach`，用 `ORDER BY RANDOM()` 做**无偏抽样**——这是从真实 bug
  （doc_id 靠前的题库垄断、后入库题库不可见）修出来的：库里有 420 题却只抽头几题，是无偏抽样修复的动机。
- **难度自适应**：`ProfilingService.suggest_difficulty` —— 正确率 ≥0.75 升档、≤0.4 降档，EASY/MEDIUM/HARD 三档切换。
- **画像闭环**：复盘里 <50 分的知识点通过 `ingest_review` **增量合并**进历史画像（不是整体覆盖），于是
  "我上次面试哪里弱"变成了今天出题的输入；复盘一结束还会自动触发 `recommend_practice(limit=3)` 推练习。
- **反馈 Worker** 的 v0 是规则评分（评估要点关键词命中、`ratio≥0.5` 判对），但 `judging_fn` 可注入——规则保证零成本稳定，
  LLM 随时可替换接入。

**克制之处**：画像 = 统计聚合 + Embedding 相似度，没有任何训练开销，却完成了"记弱项"这件事。先证明价值，再谈模型。

### 2.7 错误契约与可观测性：错误也是一种协议

`app/core/exceptions.py` 定义了一套贯穿全栈的错误协议：

- 统一异常基类 `AppError(message, detail=None, error_code=None)`：`error_code` 默认取**类名**，状态码由子类自报
  （`LlmTimeoutError→504`、`LlmRateLimitError→429`、`AuthCredentialsError→401`、`ForbiddenError→403`、`ConflictError→409`…）；
- 全局 `register_error_handlers` 是**唯一**出口（`main.py` 注册）：`AppError → {detail, error_code, trace_id}` 且日志带
  `trace_id/method/path/error_code` 与完整堆栈；未捕获 `Exception → {detail:"服务器内部错误", error_code:"INTERNAL_SERVER_ERROR", trace_id}`，
  **绝不把内部堆栈回传客户端**；
- 演进路径写进 git：先有观测性（`b0aa91d`），再把它铺满 API 层（`e70d42c`，API 层不再各自 `to_http_exception` 翻译，
  语义异常直抛，由全局 handler 统一翻译）。`trace_id`（uuid hex 前 12 位）让一条用户报障能在一行日志里从网关追到内部调用栈。

配套 `tests/test_error_observability.py`（8 个用例，含未捕获异常契约）把它钉成回归。

### 2.8 实时通道：WebSocket 主题订阅

`/ws` 握手带 `?token=<JWT access>&subscribe=interview.3,coach.abc`，token 无效直接 `close(4401)` 拒绝握手机。
握手成功后自动追加 `user.{id}.notifications` 订阅。推送主题形成稳定协议：

```
interview.{id}.progress | complete | error      —— 复盘全过程进度
coach.{sessionId}.feedback                       —— 陪练即时点评
user.{id}.notifications                          —— 系统通知
```

前端据此驱动 `AnalysisProgress` 状态机（idle/uploading/processing/completed/failed），后端 `WebSocketHub`
按精确/前缀匹配广播——进度不是轮询来的，而是事件广播。行业里"实时"方案不少，这里选的是**零额外依赖的可解释协议**。

### 2.9 认证与配置

- **JWT 双 Token**：access 30 分钟 + refresh 7 天；前端 Dio 拦截器收到 401 自动刷新并重试原请求（`X-Retry` 头防死循环），
  刷新失败才登出——用户感知上的"单点一次点击"背后是两段 Token 的生命周期管理。
- **配置即代码**：`pydantic-settings`，所有相对路径由 `_resolve_project_path` 锚定 `BASE_DIR`，容器内外不因工作目录漂移
  而失控；`JWT_SECRET` 支持环境注入（默认值仅用于开发，部署必须覆盖）。

### 2.10 部署与分发

- 双容器编排：`python-ai`（8000）+ `flutter-web`（80，nginx 反代，`/coach/` `/knowledge/` `/retrieval/` `/research/` `/api/`
  全部转发，WebSocket upgrade 透传）；`python_data:/app/data` 为持久卷。
- **首次部署引导**：`scripts/bootstrap_import.py` 幂等入库（`imported/updated/skipped/failed/questions` 五态聚合，
  任一失败退出码 2），`rag_init.py` / `rag_query.py` 提供运维侧的查验手段。详见 [部署指南](../DEPLOYMENT.md)。

---

## 3. 测试与回归：错误在源头被拦截

- 后端 **281 passed + 6 skipped**（22 个 `test_*.py` + conftest），覆盖：向量库、混合检索、Agentic RAG 工作流、
  Agent 流水线、工具注册、Coach（生命周期 / 无题降级 / 画像弱项优先）、知识库 E2E、入库管道、清洗 / 分块 / 文档转换 / 嵌入 / 重排、
  LLM / Prompt、错误契约、深度检索、编排状态图。
- 刻意设计的测试形态：**接口即测试面**——每次 Agent 方法 / 工具 / Worker 都有对应的确定性用例，上游 LLM / ASR 一律
  mock（`test_evaluate_goes_through_call_tool` 验证评估真的走了工具层）；`test_error_observability` 钉死错误契约；
  `test_coach_question_without_knowledge_base` 钉死"无题 → 409 而非 500"的降级语义。
- 前端 `analyze 0 issues`，`flutter test` 5 项通过。
- 回归故事：Coach 无偏抽样从真实 bug 来，修完后 420 题 PDF 题库可被随机抽取，且由测试守住。

---

## 4. 技术广度全景

一个"移动端 App"项目里实际发生了这些技术面：

| 维度 | 具体技术 | 落点 |
|------|----------|------|
| 客户端 | Flutter（Android + iOS + Web）、自定义 CustomPainter 雷达图、flutter_markdown 报告渲染、脉冲/波形动效 | `frontend_flutter/` |
| 实时 | WebSocket 主题订阅、Dio 拦截器 Token 自动刷新 | `ws_service` / `api_service.dart` |
| 服务端 | FastAPI + lifespan 装配 + 12 个 Router、pydantic-settings 配置中心 | `app/main.py` / `core/config.py` |
| Agent | LangGraph 状态机、Orchestrator-Workers、反思回路、降级执行器 | `app/agents/` |
| 工具化 | 自研轻量 ToolRegistry（MCP 兼容、可导出 FastMCP Server） | `app/mcp/` |
| 检索 | sqlite-vec 向量 + 自实现 BM25 混合检索 + 本地 bge 重排 | `core/vector_db.py` / `services/rag_service.py` |
| 模型 | 本地 Embedding / Reranker（离线分发）、DashScope LLM/ASR、RapidOCR 本地 OCR | `services/embedding_service.py` 等 |
| 数据工程 | 指纹幂等、蓝绿替换、自检回滚、多种文档格式转换（PDF/Word/HTML/TXT/MD） | `services/knowledge_service.py` / `doc_converter/` |
| 可观测 | trace_id / error_code 贯通日志与响应、全局错误单一出口 | `core/exceptions.py` |
| 测试 | 281 用例、确定性 mock、回归门禁 | `tests/` |
| 部署 | docker-compose 双容器、离线模型 bind、幂等入库引导、镜像卫生 | `docker-compose.yml` / `scripts/` |

所谓广度，不是"用过很多库"，而是**一条业务链上每个环节都亲自动过手**：录音采集 → 上传 → 转写 → 分离 → 检索 →
评估 → 反思 → 报告 → 推送 → 展示，没有一处是只看过文档的。

---

## 5. 关键取舍

| 决策 | 选择 | 放弃 | 为什么 |
|------|------|------|--------|
| 后端语言 | Python 单后端 | Java 双后端 | 领域连续性优先于语言生态（§1.1） |
| 存储 | SQLite + sqlite-vec | pgvector / Milvus | 单人项目零运维、单文件可交付；向量量级在万级以内，够用且诚实 |
| 重排序 | 本地 bge-reranker | 只用向量 top-k | 混合检索后 0.3/0.7 融合仍可能混入无关项，重排把相关性再质检一遍 |
| Agent 形态 | StateGraph + 降级执行器 | 全部重写 | 渐进迁移可验证，旧路径可回退 |
| MCP | 自研轻量 ToolRegistry | 重度框架 | 30 行核心满足"工具即函数"，且随时可导出 FastMCP |
| 工具边界 | 业务域 REST-only | 全部开放 | 开放边界 = 权限边界，Agent 不碰写入型业务（§2.2） |
| 画像 | 统计 + Embedding 相似度 | 训练模型 | 零训练成本先验证价值（§2.6） |
| 模型 | 本地 bge + API LLM | 全 API / 全本地 | 高频低延迟的走本地，强语义理解走 API，成本与速度分流 |
| 错误 | 全局单一出口 | 各层自己翻译 | 错误也是协议，trace_id 贯通才能一行定位（§2.7） |

---

## 附录 A：深读路线图

```text
想理解"Agent 怎么跑起来"   → 2.1 编排层 → orchestrator.py → test_agent_arch.py
想理解"检索凭什么准"       → 2.3 RAG → vector_db.py → agentic_rag_service.py
想理解"导入为什么不坏"     → 2.4 入库管道 → knowledge_service.py 及其测试
想理解"陪练怎么个性化"     → 2.6 Coach → coach_service.py → question_worker.py
想理解"错误怎么定位"       → 2.7 错误契约 → exceptions.py → test_error_observability.py
想理解"怎么交付"           → 2.10 部署 → DEPLOYMENT.md → docker-compose.yml
```

## 附录 B：文中数字的来源

- 测试计数：仓库内 pytest 实测（286 passed + 0 skipped；含 5 条知识库 E2E）。本轮从「281 + 6 skipped」升到「286 + 0」，把 6 条 skip 的 E2E 转正。
- 知识库库存：`data/rag_docs/` 现为 16 个源文件（13 `.md` + 3 `.pdf`）。部署容器 `python_ai` 卷内实测
  `KnowledgeService.get_stats()` = **4452 docs / 4452 vectors**，16 文件全部入库、0 failed。
  其中 3 个 PDF 经 OCR（RapidOCR + pymupdf 渲染）分块数**显著大于**裸文本抽取：576→658 / 1875→2440 / 202→1224，
  印证了图片式 PDF 必须走 OCR 才能完整入库；`questions=1620` 可被 Coach 抽取。
- 模型缓存：`backend_python/models/hf_cache` 含 `bge-large-zh-v1.5` 与 `bge-reranker-base`（约 7GB，符号链接已展开为真实文件）。