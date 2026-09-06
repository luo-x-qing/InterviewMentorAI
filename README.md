# InterviewMentorAI

> AI 驱动的模拟面试复盘助手 —— 面试录音，多 Agent 自动生成会议纪要与评估报告。

---

## 项目简介

InterviewMentorAI 是一款面向求职者的 **AI 面试复盘工具**，支持 Android 和 iOS 平台。用户在面试中一键开启录音，面试结束后由 **多 Agent 协作**自动执行完整复盘流程：

1. **语音转文字** — 基于 ASR 模型（DashScope paraformer-v2）将面试录音转录为文本
2. **说话人分离** — 专职 Agent 分析对话语义，自动区分面试官与面试者的发言内容
3. **RAG 检索增强** — 检索 Agent 从知识库检索相关技术知识点，为评估提供准确参考依据
4. **智能评估** — 评估 Agent 逐段评估面试者回答质量，结合知识库给出得分与等级
5. **反思增强** — 对薄弱项做深度补充检索，延伸关联知识点
6. **结构化报告** — 报告 Agent 汇总输出面试问题、回答内容、薄弱项/熟练项分析及改进建议

**初级定位（安卓、苹果客户端）：** 面试时打开软件，自动录音，记录面试会话，面试结束之后，Agent 自动生成会议纪要，并且针对我在面对面试官语气不确定、回答不正确的部分进行补充，并延伸关联知识点，帮助面试者补充；针对我完全掌握的知识点只进行概述。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 一键录音 | Flutter 移动端支持 Android & iOS，面试开始即录音 |
| 说话人分离 | 专责 Agent 自动区分面试官 / 面试者发言 |
| RAG 增强 | 检索 Agent 基于知识库检索增强评估准确性，减少 LLM 幻觉 |
| 多 Agent 协作 | LangGraph 编排 Orchestrator + 专职 Agent，可并行/反思/重试 |
| 机器学习 | 本地 Embedding / Reranker 推理 + ASR，离线可用 |
| 智能评估 | 熟练项简短概括 / 薄弱项详细修正与知识点拓展 |
| 结构化复盘 | 输出面试纪要 + Markdown 评估报告 |
| 知识库管理 | 支持多格式题库导入（PDF/Word/HTML/TXT/MD） |
| 实时推送 | WebSocket 实时推送分析进度和状态 |

---

## 技术架构（v3.0 · 全 Agent 驱动）

采用 **纯 Python 单后端 + 全 Agent 驱动** 架构，**不再使用 Java**。业务、认证、AI、RAG、多 Agent 协作统一由 FastAPI 承载；业务接口经 **MCP 协议封装为工具**，供 Agent 统一调用；并提供 **AI 辅助面试（Coach）** 模块，用轻度机器学习支撑个性化陪练：

```
┌─────────────────────────┐
│   Flutter 移动端         │
│  (Android + iOS)        │
└────────────┬────────────┘
             │ HTTP + JWT / WebSocket
┌────────────▼────────────┐
│  Python FastAPI 后端     │
│  ┌────────────────────┐ │
│  │ Agent 编排层        │ │  复盘 Orchestrator + Coach
│  │ (LangGraph)        │ │  ASR/分离/检索/评估/报告
│  └─────────┬──────────┘ │  陪练(出题/反馈/画像)
│  ┌─────────▼──────────┐ │
│  │ MCP 工具层          │ │  业务接口即工具
│  │ (auth/interview/…) │ │  call_tool 统一调用
│  └─────────┬──────────┘ │
│  ┌─────────▼──────────┐ │
│  │ AI 能力层           │ │  ML(ASR/Embedding/
│  └─────────┬──────────┘ │  Reranker/轻量画像)+RAG
│  ┌─────────▼──────────┐ │
│  │ 业务层              │ │  认证/CRUD/WebSocket 推送
│  └─────────┬──────────┘ │
│  ┌─────────▼──────────┐ │
│  │ 存储层              │ │  SQLite + sqlite-vec
│  └────────────────────┘ │
└─────────────────────────┘
```

### 模块说明

| 模块 | 技术栈 | 职责 | 详细文档 |
|------|--------|------|----------|
| **Flutter 移动端** | Flutter 3.12 | 录音采集、文件上传、报告展示、历史记录、模拟面试 | [前端架构](frontend_flutter/README.md) |
| **Python Agent 后端** | FastAPI + LangGraph + DashScope | 认证/业务 CRUD、多 Agent 编排（复盘 + Coach）、ASR、LLM、RAG、ML、MCP 工具层 | [Agent 架构设计](docs/architecture/AGENT-ARCHITECTURE.md) |
| **RAG 系统** | SQLite + sqlite-vec + 本地 bge 模型 | 知识库存储、向量检索、BM25 混合检索、重排序 | [Agent 架构设计](docs/architecture/AGENT-ARCHITECTURE.md) |
| **MCP 工具层** | mcp SDK / FastMCP | 业务接口（auth/interview/report/knowledge/retrieval/coach）封装为标准化工具 | [Agent 架构设计](docs/architecture/AGENT-ARCHITECTURE.md) |
| **AI 辅助面试（Coach）** | Coach Agent + 轻量 ML | 模拟面试陪练：个性化选题、即时点评、薄弱点画像、难度自适应 | [Agent 架构设计](docs/architecture/AGENT-ARCHITECTURE.md) |

### 多 Agent 协作

Orchestrator-Workers 模型（LangGraph `StateGraph` 编排），两条主线：

```
① 面试复盘 Orchestrator（任务拆解/调度/状态管理）
   ├─ ASR Agent          语音转文字
   ├─ 说话人分离 Agent    重组问答对
   ├─ 检索 Agent（RAG）   逐题检索增强 → 失败 re_query
   ├─ 评估 Agent         逐题评估（并发）
   └─ 报告 Agent         汇总生成 Markdown 报告
        └─ 反思回路：薄弱项 → 深度检索 → 知识点扩展

② 面试教练 Coach Agent（AI 辅助面试）
   ├─ 出题 Agent         按画像与难度选题（RAG + 相似度）
   ├─ 反馈 Agent         即时点评（LLM + RAG 上下文）
   └─ 画像 Agent         汇总历史表现生成薄弱点画像（轻量 ML）
```

### MCP 协议封装业务接口

后端全部业务/检索能力经 **MCP 协议**封装为标准化工具（`call_tool` 统一调用），Agent 与业务实现解耦，REST（面向 Flutter）与 MCP（面向 Agent）共享同一实现，可被任意 MCP 兼容客户端复用。

### 机器学习

| 能力 | 模型 | 形态 |
|------|------|------|
| 语音识别 | DashScope paraformer-v2 | API |
| 向量化 | bge-large-zh-v1.5 | **本地推理**（离线可用，支撑 RAG + Coach 个性化） |
| 重排序 | bge-reranker-base | **本地推理**（离线可用） |
| 轻量画像 | 统计聚合 + Embedding 相似度 | **轻度机器学习**（无训练开销） |
| LLM | qwen-plus / qwen3.5-omni-plus | API |

---

## Python Agent 后端概述

### Agent 流水线（多 Agent 协作）

```
音频 → [ASR Agent] → [说话人分离 Agent] → [检索 Agent(RAG)]
    → [评估 Agent] → [反思增强] → [报告 Agent] → 结构化报告
```

| 步骤 | 模型/能力 | 说明 |
|------|-----------|------|
| ASR 语音转文字 | DashScope paraformer-v2 | 面试录音转文本 |
| 说话人分离 | LLM (qwen-plus) | 区分面试官/面试者发言 |
| RAG 检索增强 | 向量检索 70% + BM25 30% + 重排 | 检索知识库相关知识点 |
| 逐段智能评估 | 评估 Agent + RAG 上下文 | 每道题评估打分 |
| 反思增强 | RAG 反思维度 | 薄弱项深度检索、知识点扩展 |
| 结构化报告 | 报告 Agent 汇总 | 生成 Markdown 复盘报告 |

### 核心组件

| 组件 | 文件 | 说明 |
|------|------|------|
| Agent 编排 | `app/agents/orchestrator.py` | LangGraph 多 Agent 状态图编排（复盘） |
| Coach 会话 | `app/agents/coach.py` + `services/coach_service.py` | AI 辅助面试：出题/反馈/画像/难度自适应 |
| MCP 工具层 | `app/mcp/*.py` | 业务接口封装为标准化工具（call_tool） |
| 向量数据库 | `core/vector_db.py` | SQLite + sqlite-vec |
| RAG 业务层 | `services/rag_service.py` | 分块/向量化/检索/重排序 |
| Agentic RAG | `services/agentic_rag_service.py` | 检索 Agent 工作流（检索→扩展→评估→合成） |
| 画像服务 | `services/profiling_service.py` | 薄弱点画像（统计聚合 + 相似度，轻量 ML） |
| LLM 服务 | `services/llm_client.py` | DashScope/OpenAI 调用封装 |

> 详细架构见 [Agent 架构设计文档](docs/architecture/AGENT-ARCHITECTURE.md)

---

## Flutter 移动端概述

基于 Flutter 3.12 的跨平台移动端（Android + iOS）。

### 页面结构

| 页面 | 文件 | 功能 |
|------|------|------|
| 登录注册 | `login_page.dart` | JWT 双 Token 登录/注册 |
| 首页 | `home_page.dart` | 3 Tab：录音入口/面试流程/评估预览 |
| 录音 | `record_page.dart` | 脉冲动画 + 波形 + 自动上传 |
| 报告 | `report_page.dart` | 雷达图 + 评分卡 + Markdown 报告 |

### 核心流程

```
面试录音 → 上传音频 → 等待多 Agent 分析(WebSocket 推送) → 查看报告
```

> 详细架构见 [前端架构文档](frontend_flutter/README.md)

---

## 项目结构

```
InterviewMentorAI/
├── frontend_flutter/                  # Flutter 移动端
│   ├── lib/
│   │   ├── main.dart                  # 应用入口 + 路由 + 认证守卫
│   │   ├── theme.dart                 # Material 3 主题（品牌色/圆角）
│   │   ├── pages/                     # 页面（登录/首页/录音/报告/个人中心等）
│   │   ├── services/                  # 5个服务（API/认证/录音/Token/WebSocket）
│   │   └── utils/                     # 常量配置（API地址）
│   ├── pubspec.yaml
│   └── README.md                      # 前端架构说明
│
├── backend_python/                    # Python Agent 后端（业务 + AI 一体化）
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口 (lifespan)
│   │   ├── core/
│   │   │   ├── config.py              # 配置管理
│   │   │   └── vector_db.py           # SQLite + sqlite-vec 向量数据库
│   │   ├── agents/                    # ★ 多 Agent 层（编排/ASR/分离/检索/评估/报告/Coach）
│   │   ├── mcp/                       # ★ MCP 工具层（业务接口即工具，standard call_tool）
│   │   ├── services/
│   │   │   ├── agent_pipeline.py      # Agent 流水线
│   │   │   ├── agentic_rag_service.py # Agentic RAG（LangGraph）
│   │   │   ├── rag_service.py         # RAG 业务层
│   │   │   ├── coach_service.py       # Coach 面试陪练（出题/反馈/画像）
│   │   │   ├── profiling_service.py   # 薄弱点画像（轻量 ML）
│   │   │   ├── llm_client.py          # LLM 调用封装
│   │   │   ├── knowledge_service.py   # 知识库服务
│   │   │   └── doc_converter/         # 文档转换 (PDF/Word/HTML→MD)
│   │   ├── api/                       # API 接口（含 /coach/*）
│   │   └── models/                    # Pydantic 数据模型
│   ├── data/rag_docs/                 # 知识库 (面试题库)
│   ├── scripts/rag_init.py            # 离线入库脚本
│   ├── requirements.txt
│   └── README.md                      # Python 后端架构说明
│
├── docs/                              # 项目文档中心
│   ├── README.md                      # 文档索引
│   ├── TECH-DEPTH.md                  # ★ 技术深度与广度（决策/实现/取舍）
│   ├── architecture/
│   │   └── AGENT-ARCHITECTURE.md      # ★ 现行 Agent 架构设计
│   ├── recycle_bin/                   # ★ 回收站（陈旧的 Java 双后端设计文档归档）
│   │   └── README.md                  # 回收站说明
│   ├── api/                           # API 接口文档
│   ├── dev/                           # 开发日志
│   ├── learning/                      # 学习资料
│   └── agents/                        # Agent 文档
├── docker-compose.yml                 # Docker 编排
└── README.md                          # 本文件 (项目入口)
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Flutter 3.12+
- DashScope API Key
- （可选）本地模型：bge-large-zh-v1.5 / bge-reranker-base（首次自动下载）

### Python Agent 后端

```bash
cd backend_python
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DASHSCOPE_API_KEY=your-api-key

# 入库知识库
python scripts/rag_init.py

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### Flutter 移动端

```bash
cd frontend_flutter
flutter pub get
flutter run
```

---

## 技术方向展望

当前版本（全 Agent 驱动 v3）技术主线已经很明确，下表是计划的下一步——分为**近期可落地**、**中期拓展**、**长期愿景**三档。

### 近期（已立项 / 可快速落地）

- **评测集门禁**：为 RAG 与 Coach 建立 golden 问答集，跑分进入 CI 回归门禁——每次改动都用"检索命中率 / 回答质量"说话，而不是"没报错"。
- **流式输出**：评估与报告改为 SSE / WebSocket 增量推送，前端边生成边渲染，替代"等 2 分钟看整篇"。
- **异步任务队列**：ASR / 深度检索 / 批量报告改为任务队列（如 ARQ / Celery + Redis），长任务与 HTTP 生命周期解耦，支持并发复盘。
- **GPU 加速可选**：本地 bge 推理支持 CUDA / ONNX Runtime FP16，嵌入与重排延迟进一步下降。
- **模型路由与成本治理**：按问题难度/类型在 qwen 系列间路由，加 LLM-KV 缓存，把单次复盘成本压一个量级。

### 中期（架构级拓展）

- **多租户与数据权限**：从单用户演进到"房间 / 组织 + 行级可见性"，为真实用户规模与多人协作做准备。
- **RAG 质量工程**：引入 RAGAS 式评测维度（忠实度 / 相关性 / 上下文召回），chunk 参数调优、增量索引（只向量化改动文件）、混合检索权重自动寻优。
- **画像升级**：从"统计 + 相似度"升级为 LLM 标签抽取 + Embedding 融合的多轮记忆画像，Coach 出题真正做到"越练越懂你"。
- **自主 Agent 闭环**：Agent 不再被 REST 被动调用，而是主动调度（自动催练、每日小测、弱项自动推送练习），编排与运营自动化。
- **可观测性平台**：Prometheus 指标 + OpenTelemetry trace + Sentry 兜底，`trace_id` 从 HTTP 一路串到 Agent 节点与队列。

### 长期（愿景 / 研究向）

- **微调轻量模型**：基于用户弱项数据做低资源 LoRA / QLoRA 微调"面试画像模型"，替换统计画像，验证"数据积累 → 个性化模型"的完整闭环。
- **向量体系演进**：万级向量量级升级到 pgvector / Milvus，支撑混合检索 + 时间衰减 + 用户级权重。
- **独立 MCP Server 发布**：把 `retrieval/coach/knowledge` 组件发布为可被任意 MCP 客户端调用的独立服务，Agent 生态复用。
- **流式 ASR**：移动端边录边转写，复盘从"录完再算"变成"十分钟后即得初稿"。

> 每一步都延续相同的工程纪律：**可测、可回滚、可观测**。详细技术深读见 [技术深度与广度](docs/TECH-DEPTH.md)。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [技术深度与广度](docs/TECH-DEPTH.md) | ★ 技术决策/实现细节/取舍全景（演进入口 + 分层解剖 + 深度/广度索引） |
| [技术方向展望](README.md#技术方向展望) | 本项目 Roadmap（近期/中期/长期） |
| [Agent 架构设计](docs/architecture/AGENT-ARCHITECTURE.md) | 现行全 Agent 架构设计（多 Agent 协作/ML/RAG/MCP 工具层/Coach 陪练模块） |
| [Python 后端架构](backend_python/README.md) | Python Agent 后端说明 |
| [前端架构](frontend_flutter/README.md) | Flutter 移动端说明 |
| [API 接口文档](docs/api/api_document.md) | API 接口说明 |
| [回收站（旧方案）](docs/recycle_bin/README.md) | 旧 Java/Python 双后端设计文档归档 |
| [文档索引](docs/README.md) | 全部文档目录 |

---

## License

MIT