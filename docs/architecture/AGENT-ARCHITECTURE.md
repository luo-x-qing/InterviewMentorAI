# InterviewMentorAI 架构设计文档（v3.1 · 全 Agent 驱动版）

> **状态**：现行方案（取代 v2.x Java/Python 双后端方案）
> **版本**：v3.1 ｜ **生效日期**：2026-09-05
> **v3.1 变更**：新增「MCP 协议封装业务接口」（业务能力即工具）与「AI 辅助面试 / 面试教练模块」（轻度机器学习分层落地）
> **旧方案**：已归档至 `docs/recycle_bin/`（不删除，仅归档保留）

---

## 1. 系统总览

InterviewMentorAI 采用 **全 Agent 驱动 + 单后端** 架构。不再使用 Java，全部业务与 AI 能力由一个 **Python FastAPI Agent 后端** 统一承载：

- **前端**：Flutter 3.12+ 移动端（Android + iOS）（保持不变）
- **后端**：Python FastAPI 单一 Agent 后端（承载认证 / 业务 / AI / RAG / 多 Agent 协作 / MCP 工具层）
- **AI 能力**：多 Agent 协作（LangGraph 编排）+ 机器学习（Embedding / Reranker / ASR / 轻量个性化建模）+ RAG 检索增强
- **Agent 与业务解耦**：业务接口统一经 MCP 协议封装为「工具」，Agent 通过标准协议调用，业务能力可被任何 MCP 兼容客户端复用
- **面试教练**：Coach Agent 支撑「AI 辅助面试」模块，提供模拟面试、个性化选题、难度自适应（轻度机器学习）
- **存储**：业务数据（SQLite / 后续可升级 MySQL）+ 向量库（SQLite + sqlite-vec）

```
                        用户(面试者)
                            │
                            ▼
             ┌──────────────────────────────┐
             │        Flutter 移动端         │
             │  登录/首页/录音/报告/模拟面试    │
             └──────────────┬───────────────┘
                            │ HTTP (Dio) + JWT / WebSocket
                            ▼
             ┌──────────────────────────────────────────┐
             │        Python FastAPI Agent 后端          │
             │  ┌────────────────────────────────────┐  │
             │  │   Agent 编排层 (LangGraph)          │  │
             │  │  复盘 Orchestrator + Coach + 专职Agent│  │
             │  └──────────────┬─────────────────────┘  │
             │  ┌──────────────▼─────────────────────┐  │
             │  │   MCP 工具层（业务接口即工具）       │  │
             │  │  auth/interview/report/knowledge/  │  │
             │  │  retrieval/coach 统一封装为 Tool    │  │
             │  └──────────────┬─────────────────────┘  │
             │  ┌──────────────▼─────────────────────┐  │
             │  │   AI 能力层                          │  │
             │  │   ML(ASR/Embedding/Reranker/轻量画像)│  │
             │  └──────────────┬─────────────────────┘  │
             │  ┌──────────────▼─────────────────────┐  │
             │  │   业务层（认证/CRUD/推送）           │  │
             │  └──────────────┬─────────────────────┘  │
             │  ┌──────────────▼─────────────────────┐  │
             │  │   存储层                            │  │
             │  │   SQLite + sqlite-vec              │  │
             │  └────────────────────────────────────┘  │
             └──────────────────────────────────────────┘
```

---

## 2. 架构演进说明

### 2.1 为什么转向全 Agent 驱动

| 维度 | 旧方案（v2.x） | 新方案（v3.x） |
|------|---------------|---------------|
| **后端语言** | Java (Spring Boot) + Python (FastAPI) 双后端 | **纯 Python 单后端**，移除 Java |
| **业务逻辑实现** | 手写 Controller/Service/Mapper | **Agent 协作执行**（Orchestrator + 专职 Agent） |
| **AI 流水线** | 固定 5 步串行流水线 | **多 Agent 状态图**，可并行/反思/重试/条件路由 |
| **知识注入** | RAG + MCP 上下文组装 | **Agent 化 RAG**（检索 Agent 自主规划查询/重查/合成） |
| **业务接口暴露形式** | REST Controller 手写映射 | **MCP 协议封装为工具**，Agent 统一调用，可被外部复用 |
| **机器学习** | 部分（ASR/Embedding） | **本地化基础不变量**（Embedding/Reranker 离线）+ **轻量个性化建模**（Coach 画像/推荐/自适应） |
| **产品形态** | 复盘为主 | 复盘 + **AI 辅助面试（模拟面试/个性化练习）** |
| **异步与推送** | @Async + STOMP 跨进程 | **FastAPI 原生异步 + WebSocket**，Agent 进度实时上报 |

### 2.2 移除 Java 后的职责迁移

| 原 Java 后端职责 | 迁移至 |
|------------------|--------|
| JWT 认证 / 用户 CRUD | Python `auth` / `user` 业务模块 + FastAPI Security（经 MCP 暴露为工具） |
| 面试 / 报告 / 知识库 CRUD | Python 业务层（复用 FastAPI + ORM），经 MCP 暴露为工具 |
| STOMP WebSocket 推送 | Python `websocket` 模块（FastAPI WebSocket / SSE） |
| 异步调用 Python AI | Agent 编排层内部直接调用（同进程，免跨服务） |
| MySQL schema | SQLite 单库（个人模式）→ 可无缝升级 MySQL |

> 注：`backend_springai/` 代码已随架构迁移删除，旧设计文档归档于 `docs/recycle_bin/` 供历史追溯。

---

## 3. 多 Agent 协作体系（核心）

### 3.1 Agent 编排模型

采用 **Orchestrator-Workers 模型**（LangGraph `StateGraph` 编排），包含两条编排主线：

```
① 面试复盘 Orchestrator（任务拆解/调度/状态管理）
        ┌──────────┬──────────┬─────────┬──────────┬─────────┐
        ▼          ▼          ▼         ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ ASR    │ │说话人  │ │检索Agent│ │评估    │ │报告    │
   │ Agent  │ │分离Agent│ │(RAG)   │ │Agent  │ │Agent   │
   └────────┘ └────────┘ └─┬──────┘ └────────┘ └────────┘
                           ▼
                    ┌──────────────┐
                    │ 反思/重查回路  │
                    │ (Reflexion)  │
                    └──────────────┘

② 面试教练 Coach Agent（AI 辅助面试会话编排）
        ┌──────────┬──────────┬────────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────────┐
   │出题Agent│ │反馈Agent│ │画像Agent    │
   │(选题)  │ │(点评)  │ │(个性化建模) │
   └────────┘ └────────┘ └────────────┘
```

### 3.2 Agent 分工

| Agent | 职责 | 输入 | 输出 | 关键能力 |
|-------|------|------|------|----------|
| **复盘 Orchestrator** | 接收复盘分析请求，拆解为子任务，调度 Workers，归并结果，管理全局状态 | AnalysisRequest | AnalysisResponse | 状态图路由、条件分支、超时降级 |
| **ASR Agent** | 语音转文字 | 音频文件 | 原始转录文本 + 时间戳 | DashScope paraformer-v2 / 本地 Whisper |
| **说话人分离 Agent** | 区分面试官 / 面试者发言，重组问答对 | 转录文本 | 结构化 Dialogue 列表 | LLM 语义分析 + 兜底规则 |
| **检索 Agent（RAG）** | 为每个问题自主检索知识库，判定相关性，必要时重查 | 问题文本 | 相关参考上下文（含 metrics） | Agentic RAG（retrieve→expand→assess→re_query→finalize） |
| **评估 Agent** | 结合 RAG 上下文逐题评估回答质量 | 问答对 + RAG 上下文 | 单题 EvaluationResult | 评分/等级/优缺点/知识点扩展 |
| **报告 Agent** | 汇总全部评估，生成结构化复盘报告 | 全部评估结果 | Markdown 复盘报告 | 结构化工序、综合评分、薄弱项分析 |
| **Coach（面试教练）** | 编排 AI 辅助面试会话：选题、点评、画像、难度自适应 | 用户意图 / 会话消息 | 题目 / 即时反馈 / 画像 / 结课报告 | 会话状态机、个性化选题、轻量 ML 建模（见 §7） |
| **出题 Agent** | 按画像与难度从题库选题（RAG 检索 + 相似度匹配） | 画像 + 难度档位 | 一道面试题（含考察点） | Embedding 相似度选题 |
| **反馈 Agent** | 结合标准答案对用户回答即时点评 | 题目 + 回答 + 标准答案 | 点评（对/错/要点提示） | LLM + RAG 上下文 |
| **画像 Agent** | 汇总历史表现生成薄弱点画像 | 历史评估/作答记录 | 用户画像（强/弱项标签） | 统计聚合 + 聚类 |

> 出题/反馈/画像 Agent 是 Coach 的内部 Worker，仅经 Coach 对外暴露接口（深模块，内部可测试）。

### 3.3 Agent 协作协议

- **状态容器（Protocol）**：各 Agent 通过共享的 `AgentState`（含 `interview_id`、`audio_file_path`、`raw_transcript`、`dialogue_list`、`evaluation_list`、`final_report`、`progress`）协作与传递数据。
- **消息即进度**：每个 Agent 完成时更新 `progress`，后端据此推送实时进度到前端（WebSocket）。
- **条件路由**：LangGraph 条件边实现智能流转：
  - 检索全不相关 → 自动 `re_query` 二次检索（防死循环上限 max_iterations）
  - 单个 Agent 失败 → 走兜底路径（如说话人分离失败用规则兜底）或标记失败
- **可反思（Reflexion）**：评估 Agent 产出的薄弱项由 Orchestrator 回灌给检索 Agent，驱动深度二次检索（见 §5.4）。
- **MCP 工具调用**：Agent 需要触达业务/检索/知识库能力时，一律通过 **MCP 工具层**的标准 `call_tool` 调用（见 §6），不直接依赖具体业务实现。

### 3.4 与旧 5 步流水线的关系

旧 `agent_pipeline.py` 的 5 步（ASR → 分离 → RAG → 评估 → 报告）是**本版 Agent 分工的业务骨架**，保留其状态容器与结果模型，将其从「硬编码串行函数」重构为「LangGraph 多 Agent 状态图」。既有的 `AgentPipeline` 可降级为 Orchestrator 的默认执行器（fallback），实现渐进迁移。

---

## 4. 机器学习层（Machine Learning）

### 4.1 模型矩阵

| 能力 | 模型 | 形态 | 说明 |
|------|------|------|------|
| **语音识别** | DashScope paraformer-v2 | API | 中文高精度 ASR；本地备选 Whisper |
| **向量化 Embedding** | BAAI/bge-large-zh-v1.5 | **本地推理**（HuggingFace） | 语义向量，离线可用，不耗 API 配额 |
| **重排序 Reranker** | BAAI/bge-reranker-base | **本地推理**（HuggingFace） | Cross-Encoder 相关性重排 |
| **轻量个性化建模** | 统计聚合 + Embedding 相似度（复用 bge） | **本地计算** | Coach 画像 / 选题 / 难度自适应（不新增模型训练，见 §7.4） |
| **LLM 对话/评估** | qwen-plus / qwen3.5-omni-plus | API | 说话人分离、评估、点评、报告生成 |

### 4.2 本地推理优先原则

- **Embedding 与 Reranker 走本地模型**（缓存于 `backend_python/models/hf_cache/`），首次自动下载，之后完全离线。
- **ASR / LLM 走 DashScope API**，通过 `llm_client.py` 统一封装，支持流式/非流式。
- **个性化能力全部为轻度机器学习**：不新增模型训练、不引入重型框架，仅用「统计 + 复用已加载的 bge 向量」完成画像与推荐。
- 目标：**复盘与陪练主链路的检索/画像环节零 API 成本、可离线演练**（对齐既有 `tests/rag_e2e_check.py` 伪 embedding 离线演练模式）。

### 4.3 与既有资产的衔接

| 既有实现 | 新架构中的角色 |
|----------|---------------|
| `embedding_service.py` | 检索 Agent 的 Embedding 工具 + Coach 个性化选题的相似度底座（+向量缓存 `embedding_cache.json`） |
| `reranker_service.py` | 检索 Agent 的重排工具 |
| `cleaning_service.py` / `chunking_service.py` | 入库管道的清洗 / 结构化切面 |
| `agentic_rag_service.py`（LangGraph 工作流） | 检索 Agent 的核心工作流，**升级为独立的检索 Agent**，并经 MCP 暴露 `retrieve` / `answer` 工具 |
| `llm_client.py` / `prompt_service.py` | LLM 通信层 / 提示词编排 |

---

## 5. RAG（检索增强生成）

### 5.1 入库管道（Ingest Pipeline）

沿用单入口深度模块设计（`KnowledgeService.import_document`），全流程幂等 + 自检 + 回滚：

```
读取 MD/TXT/PDF → 清洗(去噪+指纹) → 结构化切面(题目粒度) → 向量化
  → 蓝绿替换落库 → 自检(stats 对账+BM25 抽样) → ImportReport
```

- **文档转换**：PDF → 标准题库 MD（`PdfConverter`：NFKC 归一、章节/题目重组、跨页拼接、OCR、CID 乱码过滤）；Word/HTML 规划中。
- **幂等语义**：指纹未变 `skipped`、变更 `updated`（蓝绿替换）、0 题或自检失败回滚、文件消失对账清理。

### 5.2 检索增强（在线链路）

```
问题 → 向量化(本地 bge-large-zh) → 混合检索(向量 70% + BM25 30%)
  → 阈值判定(任一通道强命中放行) → 重排(本地 bge-reranker)
  → 组装上下文(1800 字符截断) → LLM 增强
```

### 5.3 Agentic RAG（检索 Agent 工作流）

检索 Agent 内置 LangGraph 工作流，解决单块检索的**答案截断**与**无关候选**两个痛点：

```
retrieve ─▶ expand ─▶ assess ─┬─(相关/超限/无法改写)─▶ finalize
                              └─(全不相关)───────────▶ re_query ─▶ retrieve
```

| 节点 | 职责 |
|------|------|
| `retrieve` | LangChain `RagRetriever` 封装混合检索 + 重排，top_k=6 |
| `expand` | 按（来源, 题号）拉取同一题全部块拼接完整答案（去相邻块重叠） |
| `assess` | 离线规则相关性判定（相似度 ≥0.6 + 关键词重合），全流程可离线测试 |
| `re_query` | 全不相关时抽核心关键词二次检索（防死循环） |
| `finalize` | 组装答案候选，状态 answered / no_match |

### 5.4 RAG 反思增强

Orchestrator 将评估 Agent 标出的「薄弱项 / 未能答出的考点」关键词反馈给检索 Agent，触发一轮针对性的**深度补充检索**，回灌给报告 Agent 生成「关联知识点扩展」章节——完善「针对语气不确定、回答不正确的部分进行补充，并延伸关联知识点」的核心产品诉求。

> **公开导出**：该能力独立暴露为 `POST /research/deep`（§9.2，`app/api/research_api.py`），
> 接收薄弱项关键词列表，复用 `Reflexion.deep_retrieve + RetrievalAgent.answer`，返回扩展参考与
> 「关联知识点扩展」章节文本；单关键词检索失败降级跳过，端点不失败。

---

## 6. MCP 协议封装业务接口（业务能力即工具）

### 6.1 设计动机

v2.x 时代业务接口 = 手写 REST Controller，Agent 只能「调用写死的 HTTP 端点」。v3.x 要求 **Agent 中心**：Agent 是执行的主体，业务能力应作为其可自主选择的「工具」。

采用 **MCP（Model Context Protocol）** 把后端全部业务/检索能力统一封装为标准化工具：

- **接口即工具**：每个业务能力声明为 MCP Tool（名称 + 输入 schema + 输出 schema）。
- **标准化连接**：Agent 通过 MCP 客户端发现并调用工具，与具体业务实现解耦，可被任意 MCP 兼容客户端（本系统 Agent、外部 Agent、调试工具）复用。
- **一处实现，多方复用**：REST API（面向 Flutter）与 Agent 工具调用（面向大模型）共享同一套业务实现，仅暴露形式不同——REST 由 FastAPI Router 薄封装，工具由 MCP Server 封装。

### 6.2 MCP 工具清单

> **职责边界（v3.1 落地约定）**：`auth` / `interview` / `report` 三模块能力**仅由 REST 提供**（§9.1），**不封装为 MCP 工具**——当前 Agent 执行链路（复盘 Orchestrator、Coach、检索 Agent）只有「检索 / 入库 / 陪练」三类消费场景，且 REST 与工具共享同一业务实现（`coach_service` 等），无可信消费方需要它们经 `call_tool` 调用。若未来出现 Agent 化运营 / 后台场景再以浅适配器补齐（见实现要点）。

| Tool | 输入 | 输出 | 用途 |
|------|------|------|------|
| `knowledge.import` | 文件/目录 | ImportReport | 入库知识库 |
| `knowledge.stats` | - | 统计信息 | 知识库健康 |
| `retrieve.retrieve` | 问题 + top_k | 候选 + metrics | 直接检索调试 |
| `rag.answer` | 问题 | RagAnswerResult（完整候选） | Agentic RAG 合成答案 |
| `coach.start` | mode / 目标 | 会话句柄 | 开启模拟面试（见 §7） |
| `coach.next_question` | 会话句柄 | 题目 + 考察点 | Coach 出题 |
| `coach.submit_answer` | 会话句柄 + 回答 | 即时反馈 | Coach 点评 |
| `coach.end` | 会话句柄 | 结课报告 | 结束会话（画像更新） |
| `coach.recommend` | 画像弱项 | 推荐题目 | 复盘后一键推荐练习 |

### 6.3 架构位置

```
Agent（复盘 Orchestrator / Coach / 出题 / 反馈）
        │  MCP client（call_tool）
        ▼
┌───────────────────────────────┐
│     MCP 工具层 (app/mcp/)      │
│  ├─ knowledge_tools.py         │  入库/统计（封装 KnowledgeService）
│  ├─ retrieval_tools.py         │  检索/合成（封装 rag_service / agentic_rag）
│  └─ coach_tools.py             │  Coach 会话（封装 CoachService）
│                                 │  auth/interview/report：REST-only（§6.2）
└───────────────┬───────────────┘
                │  同进程直接调用（进程内 MCP）／可选 Stdio Server
                ▼
   业务服务层 / AI 能力层 / RAG 层（单一实现）
```

### 6.4 实现要点

- **进程内 MCP（默认）**：先以 `FastMCP`/`mcp` SDK 在同进程内注册工具，Agent（LangGraph 节点 / LangChain Tool calling）用本地 `ClientSession` 调用——零网络开销，进 口型是标准 `call_tool(name, arguments)`。
- **可选独立 Server**：后续如需让外部 Agent / 第三方客户端接入，可增配独立 MCP Server（`mcp.run(stdio_server())` 或 SSE），业务实现零改动。
- **鉴权**：工具内部复用与 REST 相同的认证/会话校验，防止 Agent 越权。
- **迁移兼容**：现有 `rag_mcp.py`（MCP 调度层，非标准协议）逻辑保留，作为 `knowledge_tools` / `retrieval_tools` 的底层实现迁移至标准 MCP 封装。

---

## 7. AI 辅助面试 / 面试教练模块（Coach Agent）

> 对应产品诉求的「AI 辅助面试模块」，能力以模拟面试陪练为核心，全部使用**轻度机器学习**。

### 7.1 产品能力

| 能力 | 说明 | 依赖 ML |
|------|------|---------|
| **模拟面试** | 按用户节奏出一题、收一答、即时点评，可文字/语音 | 基础：RAG 选题 + LLM 点评 |
| **薄弱点画像** | 汇总历史复盘/作答，输出「你哪类考点总答不好」 | ✅ 统计聚合 + 聚类 |
| **个性化选题** | 专挑薄弱知识点出题 | ✅ Embedding 相似度 |
| **难度自适应** | 答对提升难度、答错降低难度，贴近真实面试曲线 | ✅ 画像 + 相似度计分 |

### 7.2 会话模型（深模块接口）

Coach 对外只暴露 4 个方法，内部封装全部 Worker 编排与状态管理：

```
start_session(user_id, mode)      -> SessionHandle      # 建会话、初始化画像
next_question(session)            -> Question            # 出题（含考察点 + 难度档位）
submit_answer(session, answer)    -> Feedback            # 即时点评（正确性/要点/改进）
end_session(session)              -> SessionReport       # 结课报告（正确率/薄弱项/建议）
```

### 7.3 会话状态机

```
idle ──start_session──▶ active ──next_question/submit_answer──▶ (循环至题目用完或用户结束)
                           │
                           └──end_session──▶ done ──画像写入 / 生成 SessionReport
```

- 每题作答记录落库（`coach_session_question`），作为画像与自适应的输入。
- 会话中途可暂停/恢复（状态持久化）。

### 7.4 轻度机器学习分层（逐级增强，均轻量）

> 不训练模型、不引入重型框架，只叠加「统计 + 复用已加载的 bge 向量」。与产品路线对齐：先跑通 RAG 驱动，再逐级加入个性化。

| 版本 | 能力 | 机器学习手段 | 说明 |
|------|------|--------------|------|
| **v0** | RAG 驱动选题 | 无需 ML | 从题库按类别/关键词随机选题，LLM 点评。先跑通模拟面试闭环。 |
| **v1** | 薄弱点画像 | 统计聚合（频率 / 平均分 / 等级分布） | 把历史复盘评估 + 本次作答按知识点维度聚合，产出「强项/弱项」标签，写用户画像表。 |
| **v2** | 个性化选题 | Embedding 相似度（薄弱项标签 ↔ 题库向量） | 用 bge 把画像弱项标签向量化，在题库中检索最接近的题目优先出题（复用 `rag_service`/`agentic_rag`）。 |
| **v3** | 难度自适应 | 画像 + 相似度计分 | 按答对/答错更新细粒度掌握度分值，动态调档（简单↔中等↔难），选题时按档位加权。 |

### 7.5 反馈与复盘的数据闭环

```
模拟面试（Coach）记录作答 ──▶ 画像更新（v1）
        │
        ▼
下次复盘报告 / Coach 出题 ──▶ 针对弱项定向练习（v2 / v3）
```

Coach 的画像同时回写评估 Agent 的「薄弱项」输出，形成「练习 → 复盘 → 再练习」的学生成长闭环。

---

## 8. 后端模块架构（单后端）

### 8.1 分层

```
API 层:            auth / user / interview / report / knowledge / retrieval / analysis / coach / ws
   ↓
Agent 编排层:      orchestrator.py（复盘 LangGraph）+ coach.py（陪练会话）+ 各专职 Agent
   ↓
MCP 工具层:        app/mcp/*  (knowledge/retrieval/coach tools；auth/interview/report 走 REST，§6.2)
   ↓
业务服务层:        auth_service / interview_service / report_service / knowledge_service / coach_service / websocket_service
   ↓
AI 能力层:         llm_client / asr_service / embedding_service / reranker_service / profiling_service
   ↓
RAG 层:            rag_service / agentic_rag / rag_mcp / chunking_service / cleaning_service
   ↓
存储层:            repository（业务表 + 画像表）+ vector_db（SQLite + sqlite-vec）
```

### 8.2 模块深度设计要点（遵循 deep-module 原则）

- **复盘 Orchestrator = 深模块**：对外仅暴露 `run(request) -> response` 与 `subscribe(progress_cb)`，内部封装全部多 Agent 调度、状态管理、降级策略与反思逻辑。调用方无需了解 Agent 拓扑。
- **Coach = 深模块**：对外仅暴露 §7.2 的 4 个方法，内部封装出题/反馈/画像全部细节；个性化建模对外不可见，可随 v0→v3 演进而接口不变。
- **检索 Agent = 深模块**：对外仅暴露 `answer(question) -> RagAnswerResult`，内部封装混合检索、重排、expand/assess/re_query 全部细节（对齐既有 `AgenticRagService.answer()`）。
- **MCP 工具层 = 浅适配器**：工具只做「schema 声明 + 参数校验 + 转发业务服务」，不含业务逻辑；业务逻辑居于 Services，一次实现，REST 与 MCP 双通道复用。
- **接口即测试面**：各 Agent 的对外方法即测试入口——Orchestrator 的 `run`、Coach 的 4 方法、检索 Agent 的 `answer`、评估 Agent 的单题评估方法，均可离线 mock 上游后直接测试。

### 8.3 可观测错误契约（错误处理单一出口）

> 所有异常统一经 `app/core/exceptions.py` `register_error_handlers` 出口（深度模块，`main.py` 与测试均装配同一份）。

| 异常来源 | HTTP | 响应体 | 日志 |
|----------|------|--------|------|
| `AppError` 及其子类（业务/预期错误） | 由异常自身（401/403/409/429/504/…） | `{detail, error_code, trace_id}` | `ERROR`：`trace_id=… code=… method=… path=… message=…` + **完整调用栈**（定位抛出点） |
| 未捕获 `Exception`（意外故障） | 500 | `{detail: 服务器内部错误, error_code: INTERNAL_SERVER_ERROR, trace_id}`（**不透出内部堆栈**） | `ERROR`：未捕获异常 + trace_id + method/path + **完整 traceback** |
| `HTTPException`（路由/校验链路兼容层） | 原样透传 | `{detail}`（保持既有契约，5xx 亦原样） | 仅 **5xx** 补记 `ERROR` |

- **`error_code`**：稳定机器码，默认 = 异常类名（如 `AuthCredentialsError`），可用 `error_code=` 显式覆盖（如 `KnowledgeImportError(..., error_code="KB_IMPORT_FAILED")`），便于前端/监控按码处理。
- **`trace_id`**：响应体与日志的关联键。维护者拿到客户端报错即可 `grep "trace_id=xxxxxxxxxxxx"` 后端日志，一行锁定 method/path/异常类型与完整栈。
- **单一出口纪律**：API 层不重复「记日志→转 HTTPException 500」兜底（`analysis.py` 的重复 catch 已并入本出口）；业务层按语义抛 `AppError` 子类即可，其余交给出口。API 层一律**纯 `raise`（不调 `to_http_exception()` 翻译）**——翻译会把 `AppError` 抹成裸 `HTTPException` 而丢 `error_code`/`trace_id`；`to_http_exception()` 仅由出口 handler 内部取状态码/头。`auth/deps/user/interview/coach/knowledge/retrieval/mcp_debug` 已验证该契约（冒烟：coach 无题库 409 且带 `error_code=QUESTION_BANK_EMPTY`）。MCP `call_tool` 失败另记「工具名 + 完整栈」（不记入参，避免敏感信息）。
- **测试**：`tests/test_error_observability.py`（响应体字段 + 日志可追溯 + 未捕获不发散）；`tests/test_exceptions.py`（层次与状态码）。

---

## 9. API 设计

### 9.1 业务 API（原 Java 职责，迁入 Python 单后端）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Auth | POST | `/auth/login` | 登录（JWT 双 Token） |
| Auth | POST | `/auth/register` | 注册 |
| Auth | POST | `/auth/refresh` | 刷新 Token |
| User | GET | `/user/profile` | 个人信息 |
| User | PUT | `/user/password` | 改密码（校验旧密码，§9.1 已落地） |
| Interview | POST | `/interview` | 创建面试 |
| Interview | GET | `/interview/{id}` | 面试详情 |
| Interview | GET | `/interview/my` | 我的面试列表 |
| Report | GET | `/report/interview/{id}/report` | 获取报告 |
| Report | GET | `/report/interview/{id}/evaluations` | 评估列表 |
| Knowledge | POST | `/knowledge/import` | 导入知识库 |
| Knowledge | GET | `/knowledge/stats` | 知识库统计 |

### 9.2 AI / Agent API

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Analysis | POST | `/api/v1/analysis/analyze` | 触发多 Agent 面试复盘 |
| Analysis | GET | `/api/v1/analysis/health` | 健康检查 |
| Retrieval | POST | `/retrieval/retrieve` | 检索调试（含 metrics） |
| Retrieval | POST | `/retrieval/chunks/preview` | 分块预览 |
| Research | POST | `/research/deep` | RAG 反思深度检索（§5.4） |

### 9.3 Coach API（AI 辅助面试）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Coach | POST | `/coach/session` | 开启模拟面试会话（拍mode） |
| Coach | GET | `/coach/session/{id}/question` | 获取下一题（注：代码为 GET .../question，非早期文档的 POST .../next） |
| Coach | POST | `/coach/session/{id}/answer` | 提交回答，获取即时反馈 |
| Coach | POST | `/coach/session/{id}/end` | 结束会话，生成结课报告 |
| Coach | GET | `/coach/profile` | 查看我的薄弱点画像（已落地，走 ProfilingService） |
| Coach | GET | `/coach/recommend` | 复盘后一键推荐针对性练习（按画像弱项选题，无需会话） |

> 注：`/coach/*` 面向 Flutter 直连；Agent 内部（例如复盘后自动推荐一次针对性练习）走 MCP `coach.*` 工具。二者共享同一 `coach_service`。
>
> **前端接入（已落地）**：底部导航 Tab2 社区 → 陪练；新建 `pages/coach/` 三页
> （`coach_home_page.dart` 主页/薄弱点画像/推荐练习、`coach_session_page.dart` 会话/即时点评
> 双入口、`coach_report_page.dart` 结课报告）+ `services/coach_service.dart`
> （`startSession/nextQuestion/submitAnswer/endSession/recommend/getProfile`），
> WS `coach.{sessionId}.feedback` 实时点评订阅。

### 9.4 文件上传与实时推送

- **音频上传**：`POST /audio/upload`（multipart 字段 `audioFile`，已落地 `app/api/audio_api.py`）。
  上传即建面试记录并返回 `{interview_id, id, title, status, created_at}`。前端链路：
  `uploadAudioBytes` → 拿 `interview_id` → `WebSocketService.connect(interviewId:)` 订阅进度 →
  `POST /interview/{id}/analyze` 触发复盘 → WS 实时进度 → `GET /report/interview/{id}/report` 拉报告。
- **实时进度**：WebSocket（FastAPI 原生）替代原 STOMP：

| 主题（message 类型） | 推送时机 |
|----------------------|----------|
| `interview.{id}.progress` | 每个 Agent 完成时（0-100%） |
| `interview.{id}.complete` | 全链路完成（payload 携带 `report` + `recommendations`） |
| `interview.{id}.error` | 失败 |
| `coach.{sessionId}.feedback` | Coach 即时点评 |
| `user.{id}.notifications` | 通知 |

> 前端 `websocket_service.dart` 已改为原生 WebSocket：`connect({int? interviewId, String? coachSessionId})`，
> 按 `topic.suffix` 分发 `.progress/.complete/.error` 与 `.feedback`（STOMP 迁移已完成）。

---

## 10. 核心业务流程

### 10.1 面试复盘（多 Agent 协作）

```
面试录音 → 上传音频 → POST /analyze
  → Orchestrator 拆解任务
  → ASR Agent 语音转文字
  → 说话人分离 Agent 重组问答对
  → 检索 Agent（RAG）逐题检索增强  [失败→re_query]
  → 评估 Agent 逐题评估（并发）
  → RAG 反思增强（薄弱项深度检索）
  → 报告 Agent 汇总生成 Markdown 报告
  → Orchestrator 归并 → 持久化（interviews 状态/报告 +
        interview_evaluations 逐题明细）→ 画像回写（薄弱项）→
        一键推荐针对性练习（CoachService 按画像弱项选题）→
        WebSocket 推送（complete 携带 report + recommendations）→ Flutter 展示
```

> **持久化落点**：`POST /interview/{id}/analyze` 完成编排层收尾（§8.1 API 层）——
> COMPLETED 写 `interviews.status/final_report` 与逐题评估表；FAILED 写状态。画像回写
> 与推荐降级为「尽力而为」，失败不阻断复盘主流程。

### 10.2 AI 辅助面试（Coach 陪练）

```
用户在「模拟面试」模块点击开始（POST /coach/session）
  → Coach 读取用户画像（v1；无画像则 v0 直接开始）
  → 出题 Agent 选题（v2 弱项优先，v3 按难度档位加权）
  → 用户作答（文字 / 录音转写）→ POST /coach/session/{id}/answer
  → 反馈 Agent 即时点评 → WebSocket 推送 → 回答记录落库
  → 循环直至结束 → end_session 更新画像 + 生成结课报告
```

### 10.3 知识库入库

```
拖入题库文件 → /knowledge/import → 清洗 → 结构化切面 → 本地向量化
  → 蓝绿替换落库 → 自检 → ImportReport（前端可查看入库统计）
```

---

## 11. 技术选型

| 模块 | 选型 | 理由 |
|------|------|------|
| 后端框架 | **FastAPI** | 高性能异步，承载业务 + AI 统一入站 |
| Agent 编排 | **LangGraph**（StateGraph） | 状态化多 Agent 工作流、条件路由、可反思 |
| 检索组件 | **LangChain**（RagRetriever） | 标准化 BaseRetriever / Document |
| MCP | **mcp SDK / FastMCP** | 标准协议封装业务接口，工具可复用、可外连 |
| 语音识别 | DashScope paraformer-v2 | 中文高精度、国内稳定 |
| Embedding | **bge-large-zh-v1.5（本地）** | 中文语义向量、离线可用；同时支撑 RAG 与 Coach 个性化选题 |
| Reranker | **bge-reranker-base（本地）** | Cross-Encoder 重排 |
| 轻量画像 | 统计聚合 + 余弦相似度（复用 bge） | 轻度机器学习，无训练开销 |
| LLM | qwen-plus / qwen3.5-omni-plus | 中文能力强 |
| 向量存储 | SQLite + sqlite-vec | 轻量、零运维 |
| 业务存储 | SQLite（个人模式）→ MySQL（可选） | 渐进扩展，无需 Java ORM |
| 混合检索 | BM25 + 向量（0.3 : 0.7）+ 重排 | 提高召回率与精度 |
| 前端 | Flutter 3.12+（不变）+ WebSocket | 跨平台（Android + iOS） |

---

## 12. 迁移路径

> `backend_springai/` **已删除**（历史实现归档至 `docs/recycle_bin/` 文档），新架构代码落在 Python 单后端内渐进演进。

> **骨架状态**：阶段 A/B/C/D 的核心接口、深模块骨架与业务 REST 已全部落地（`app/models/entities.py`、`app/core/database.py`、`app/mcp/*`、`app/agents/*`、`app/services/coach_service.py`、`app/services/profiling_service.py`、`app/services/auth_service.py`、`app/services/ws_service.py`、`app/api/*`），实体/库/MCP/Coach/画像/认证/WS 均有单测覆盖（`tests/test_agent_arch.py` + `tests/test_api_stage_d.py` + `tests/test_review_closing.py` + `tests/test_error_observability.py` + 既有回归，全量 281 passed + 6 skipped（`test_knowledge_e2e.py` 基于已删除旧接口、按文件头意图 skip，新链路单测见 `test_import_pipeline.py`；`test_research_api.py` 覆盖 `/research/deep` 反射深度检索端点））。以下编号勾选为实际落地状态。

### 阶段 A：业务能力迁入（无 Java）

1. ✅ `backend_python/` 新增 `auth` / `user` / `interview` / `report` 业务模块与 JWT 认证（`app/services/auth_service.py` 双 Token、`app/api/{auth,user,interview,report}_api.py`）。
2. ✅（骨架）新增 SQLite 业务表：`app/core/database.py`（user / interview / coach_session / coach_session_question / user_profile 五表 + 兼容补列），实体见 `app/models/entities.py`。
3. ✅ 新增原生 WebSocket / SSE 实时推送模块，替换 STOMP（`app/services/ws_service.py` `WebSocketHub` + `app/api/ws_api.py` `/ws`；主题 `interview.{id}.progress/complete/error`、`coach.{sessionId}.feedback`、`user.{id}.notifications`，JWT query 认证）。
4. ✅ Flutter 前端切换 API 基址到 Python 单后端（`constants.dart` 单源），`websocket_service.dart` 从 STOMP 迁移至原生 `web_socket_channel`（移除 `stomp_dart_client` 依赖），`auth_service.dart` / `login_page.dart` 对齐后端 `/auth/*` 契约。

### 阶段 B：流水线 Agent 化

5. ✅ `app/agents/orchestrator.py`：对外 `run(request)` + `subscribe(progress_cb)` + `build_graph()`（LangGraph StateGraph：transcribe→separate→evaluate→reflex→report，节点复用 `AgentPipeline` 既有能力，reflex 接反思回路，可 `ainvoke` 独立运行）。默认执行器仍为既有 `AgentPipeline`。
6. ✅（骨架）`app/agents/reflexion.py`：反思回路（薄弱项 → 深度检索 → 知识点扩展）。
7. ✅（骨架）`app/agents/retrieval_agent.py`：检索 Agent（包装 `AgenticRagService.answer`，`retrieve_candidates` 候选兜底）。

### 阶段 C：MCP 工具层

8. ✅（骨架）`app/mcp/server.py`（`ToolRegistry`：`register / list_tools / call_tool`）+ `app/mcp/retrieval_tools.py`、`app/mcp/knowledge_tools.py`（浅适配器转发既有服务）。**职责边界**：`auth / interview / report` 仅 REST 提供（§6.2 约定），当前实际注册工具 = retrieval（2）+ knowledge（3）+ coach（5），共 10 个。
9. ✅ Coach 业务服务注册为 MCP 工具（`app/mcp/coach_tools.py`）；REST（`app/api/coach_api.py`）与 MCP 双通道共享同一 `CoachService` 实现。
10. ✅ `AgentPipeline` 装配 `tool_registry`，评估单题前的检索改走 `call_tool("retrieve.retrieve", ...)`（未装配时回落既有 `rag_mcp` 链路，向后兼容）；Orchestrator 默认执行器即此 AgentPipeline。

### 阶段 D：AI 辅助面试（Coach）

11. ✅ `app/services/coach_service.py` 会话状态机（idle→active→done）+ `app/mcp/coach_tools.py` + REST `/coach/session|{id}/question|{id}/answer|{id}/end`（`app/api/coach_api.py`，Bearer 认证 + 归属校验）。
12. ✅（骨架）`app/services/profiling_service.py`（v1 统计聚合 + v2 相似度选题 + v3 难度自适应，`suggest_difficulty`）+ 画像表。
13. ✅ Coach 经 MCP `coach.*` 工具接入（已在 `main.py` 装配）；复盘后一键推荐针对性练习已接 Orchestrator（`/coach/recommend` REST + `coach.recommend` MCP + 复盘响应/WS complete 携带 `recommendations`，按画像弱项选题）。进度：`/interview/{id}/analyze` 收尾完成持久化 / 画像回写 / 推荐（§10.1）。

13.5. ✅（缺口补齐）复盘闭环：`interview_evaluations` 逐题明细表 + `update_interview_status(COMPLETED/FAILED)` 状态流转；`ProfilingService.ingest_review` 复盘薄弱项合并画像（§7.5）；`QuestionWorker` 生产题库源（`build_knowledge_question_source`，从知识库投影候选，Coach 出题/推荐生产可用）。

### 阶段 E：收尾（✅ 已完成）

14. ✅ 移除 `docker-compose.yml` 中的 MySQL / java-api 服务，仅保留 python-ai + flutter-web。
15. ✅ 更新 CI 去掉 Java 步骤；删除 `backend_springai/` 与相关 Java 引用。

---

## 13. 可测试性（接口即测试面）

| 测试面 | 入口 | 离线能力 |
|--------|------|----------|
| 入库管道 | `KnowledgeService.import_document` | 伪 embedding 离线（`tests/rag_e2e_check.py`） |
| 检索质量 | `RagService.retrieve_by_question` | 基线与门禁（`tests/rag_eval_script.py`） |
| Agentic RAG | `AgenticRagService.answer` | 离线规则 assess，无 LLM |
| MCP 工具 | `call_tool("knowledge.import", ...)` | 工具级集成测试，校验 schema 与转发 |
| Orchestrator | `run(request)` | mock ASR/LLM 后全链路调度测试 |
| 评估 Agent | 单题 `evaluate(question, answer)` | mock RAG 上下文后测试 |
| Coach 会话 | `start_session / next_question / submit_answer / end_session` | mock LLM + 伪向量后测试状态机、画像更新、难度档位切换 |
| 画像/选题 | `profiling_service.aggregate` / `retrieval_tools.filter_by_profile` | 统计与相似度可离线断言 |

---

## 14. 目录结构（目标态）

```
backend_python/
├── app/
│   ├── main.py                      # FastAPI 入口（含业务 Router + WS + MCP 注册）
│   ├── api/                         # auth/user/interview/report/knowledge/retrieval/analysis/coach/audio/ws/mcp/research
│   ├── agents/                      # ★ 多 Agent 层
│   │   ├── orchestrator.py          #   复盘 Orchestrator（LangGraph StateGraph）
│   │   ├── retrieval_agent.py       #   检索 Agent（封装 agentic_rag）
│   │   ├── reflexion.py             #   反思增强回路（§5.4；经 /research/deep 导出）
│   │   ├── coach.py                 #   ★ Coach 会话编排（出题/反馈/画像）
│   │   └── coach_workers/           #   ★ Coach 内部 Worker（出题/反馈/画像）
│   │       ├── question_worker.py   #     出题（选题）
│   │       ├── feedback_worker.py   #     即时点评
│   │       └── profiling_worker.py  #     画像聚合
│   │   （ASR/说话人分离/评估/报告不再单列 Agent 文件：能力在 agent_pipeline.py，
│   │      build_graph 以 transcribe→separate→evaluate→report 节点复用，§3.4 渐进策略）
│   ├── mcp/                         # ★ MCP 工具层
│   │   ├── server.py                #   工具注册 + 进程内 ClientSession
│   │   ├── knowledge_tools.py
│   │   ├── retrieval_tools.py
│   │   └── coach_tools.py           # （auth/interview/report：REST-only，§6.2）
│   ├── services/                    # 业务服务（auth/interview/report/knowledge/coach/ws）
│   │   ├── coach_service.py         #   ★ Coach 业务实现（深模块）
│   │   ├── profiling_service.py     #   ★ 画像（统计聚合 + 相似度）
│   │   └── (既有 rag_service/llm_client/embedding/reranker/agentic_rag 等保留)
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py              # ★ 业务库（SQLite，含画像表/会话表）新增
│   │   └── vector_db.py             # 向量库（SQLite + sqlite-vec）
│   └── models/
│       ├── schemas.py               # AI 模型
│       └── entities.py              # ★ 业务实体（user/interview/report/profile/coach_session）新增
├── data/
│   ├── rag_docs/                    # 题库知识库
│   └── interview.db                 # SQLite（业务 + 向量）
├── scripts/                         # rag_init / rag_query 等
├── tests/                           # pytest 全链路（含 coach / mcp 集成测试）
└── requirements.txt
```

---

## 15. 相关文档

| 文档 | 说明 |
|------|------|
| [根 README](../../README.md) | 项目入口（本方案摘要） |
| [文档索引](../README.md) | 全部文档索引 |
| [部署指南](../DEPLOYMENT.md) | docker-compose 双容器部署 + 首次入库引导 + 验证清单 |
| [回收站（旧方案）](../recycle_bin/README.md) | 旧 Java/Python 双后端设计文档归档 |
| [Python 后端实现说明](../../backend_python/README.md) | 既有 Python AI 资产（将承载新架构） |