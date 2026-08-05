# InterviewMentorAI - Python AI 后端

> FastAPI + DashScope 驱动的 AI 面试分析引擎

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行时 |
| FastAPI | 0.104+ | Web 框架 |
| DashScope | - | ASR 语音识别 + LLM 对话 |
| OpenAI SDK | 1.0+ | LLM 调用 |
| SQLite + sqlite-vec | 0.1.6 | 向量数据库 |
| rank-bm25 | 0.2.2 | BM25 关键词检索 |
| httpx | 0.25+ | HTTP 客户端 |

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                       分层架构                               │
├─────────────────────────────────────────────────────────────┤
│  5. API 层         analysis.py / knowledge_api.py           │
│       ↓                    ↓                                │
│  4. 业务流水线     agent_pipeline.py   编排完整分析流程      │
│       ↓                                                     │
│  3. MCP 调度层    rag_mcp.py          检索+上下文+LLM 统一  │
│       ↓                        ↓                            │
│  2. RAG 工具层  rag_service.py    LLM 通用层  llm_service   │
│       ↓                        ↓                            │
│  1. 底层存储层    vector_db.py        SQLite + sqlite-vec   │
│       ↓                                                     │
│  0. 数据源层      data/rag_docs/      面试题库知识库         │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **向量数据库** | `core/vector_db.py` | SQLite + sqlite-vec，存储文本和向量，支持 BM25/向量/混合检索 |
| **LLM 客户端** | `services/llm_client.py` | 封装 DashScope/OpenAI 调用，支持流式/非流式 |
| **清洗服务** | `services/cleaning_service.py` | 去噪、规范化、内容指纹去重 |
| **结构化切面** | `services/chunking_service.py` | 以题目为粒度切分，保留题目编号与来源，超长答案二次切分 |
| **向量化服务** | `services/embedding_service.py` | DashScope Embedding + 本地缓存 |
| **重排序服务** | `services/reranker_service.py` | Cross-Encoder 相关性重排序（min-max 归一化） |
| **RAG 编排层** | `services/rag_service.py` | 混合检索（权重融合+阈值判定+默认重排+metrics） |
| **MCP 调度层** | `services/rag_mcp.py` | 上下文组装、长度截断、LLM 增强调用 |
| **入库管道** | `services/knowledge_service.py` | 幂等入库单入口（清洗→切面→向量化→落库→自检→回滚） |
| **Agent 流水线** | `services/agent_pipeline.py` | 编排 ASR → 分离 → RAG → 评估 → 报告 |
| **文档转换** | `services/doc_converter/` | PDF → 标准题库 MD（`PdfConverter`：NFKC 归一、章节/题目重组、跨页断行拼接）；Word/HTML → MD 规划中 |
| **配置管理** | `core/config.py` | 环境变量、API Key、模型配置 |

---

## Agent 流水线 (5 步)

```
输入: 音频文件
  ↓
Step 1: ASR 语音转文字 (DashScope paraformer-v2)
  ↓
Step 2: 说话人分离 (LLM 分析对话结构)
  ↓
Step 3: RAG 检索增强 (向量检索 70% + BM25 30%)
  ↓
Step 4: 逐段智能评估 (RAG 增强 LLM 评估)
  ↓
Step 5: 结构化报告 (Markdown 格式输出)
  ↓
输出: { transcript, dialogue, evaluations, report }
```

### Step 1: ASR 语音转文字

- 模型: DashScope paraformer-v2
- 输入: 音频文件路径
- 输出: 原始转录文本 + 时间戳

### Step 2: 说话人分离

- 模型: LLM (qwen-plus)
- 输入: 原始转录文本
- 输出: 结构化对话 JSON（区分面试官/面试者）

### Step 3: RAG 检索增强

- 混合检索: 向量检索 70% + BM25 30%
- 重排序: Cross-Encoder 相关性排序
- 上下文: 组装参考知识点，截断至 1800 字符

### Step 4: 逐段智能评估

- 对每段面试问答进行评估
- 结合 RAG 检索到的知识库内容
- 输出: 分数、等级、优点、不足、改进建议

### Step 5: 结构化报告

- 汇总所有评估结果
- 生成 Markdown 格式复盘报告
- 包含: 综合评分、薄弱项分析、改进建议

---

## RAG 系统

### 离线入库流程（幂等 + 自检）

```
题库文档 (MD/TXT)
  ↓
knowledge_service.import_document(file_path)   # 单入口
  ↓
清洗 (去噪 + 内容指纹)
  ↓
结构化切面 (题目粒度，保留 question_no / section)
  ↓
DashScope Embedding 生成向量
  ↓
蓝绿替换落库 (未变 skipped / 变更 updated)
  ↓
自检 (stats 对账 + BM25 抽样) → 失败回滚 → ImportReport
  ↓
目录对账 (reconcile_directory 清理已消失文件)
```

### 在线检索流程

```
查询文本
  ↓
混合检索
  ├─→ 向量检索 (cosine similarity) 70%
  └─→ BM25 关键词检索 30% (min-max 归一化)
  ↓
阈值判定 (任一路强命中放行，默认 0.25)
  ↓
重排序 (Cross-Encoder，默认开启 RAG_USE_RERANK=true)
  ↓
Top-K 结果返回 + 检索指标 metrics (命中数/得分/来源分布)
```

### 知识库内容

```
data/rag_docs/          # 13 份 MD 题库 + 1 份 PDF（经 PdfConverter 实时转换入库）
├── 通用评估标准.md              # 面试评估维度和评分规则
├── 技术难点标准答案.md          # Java 技术难点标准答案
├── Java面试题库/                # Java 基础/集合/多线程/JVM/Spring/MySQL
├── Python面试题库/              # Python 基础/进阶/框架/数据库
└── 系统设计面试题.md            # 高并发/缓存/消息队列/微服务
```

### 入库与演练

```bash
# 全量入库（幂等：未变更跳过 / 变更蓝绿替换 / 自检失败回滚）
python scripts/rag_init.py

# 端到端演练（临时库 + 伪 embedding，12 项断言全 PASS，不耗 API 配额）
python tests/rag_e2e_check.py

# 检索质量评估（对比 P0 空库基线 0%，跌破基线 exit 1）
python tests/rag_eval_script.py
```

---

## API 接口

### 分析接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/analysis/analyze` | POST | 执行 AI 分析流水线 |
| `/api/v1/analysis/health` | GET | 健康检查 |

**请求示例**

```json
POST /api/v1/analysis/analyze
{
  "audio_file_id": "uuid-xxx",
  "audio_file_path": "/data/audio/uuid-xxx.wav"
}
```

**响应示例**

```json
{
  "status": "COMPLETED",
  "interview_id": 5001,
  "transcript": "...",
  "dialogue": [...],
  "evaluations": [...],
  "report": "Markdown 报告内容"
}
```

### RAG 接口（知识库生命周期）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/knowledge/import` | POST | 导入知识库（file_paths 缺省则扫描全目录，幂等） |
| `/knowledge/reconcile` | POST | 目录对账，清理已消失题库 |
| `/knowledge/stats` | GET | 知识库统计 |
| `/knowledge/clear` | DELETE | 清空知识库 |
| `/knowledge/{source}` | DELETE | 文档级删除 |

### 检索接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/retrieval/retrieve` | POST | 检索调试（响应含 metrics） |
| `/retrieval/chunks/preview` | POST | 分块预览 |

### MCP 调试接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/mcp/eval-test` | POST | MCP 评估测试 |
| `/mcp/context-preview` | POST | MCP 上下文预览 |

---

## 项目结构

```
backend_python/
├── app/
│   ├── main.py                      # FastAPI 应用入口
│   ├── core/
│   │   ├── config.py                # 配置管理 (环境变量)
│   │   └── vector_db.py            # SQLite + sqlite-vec 向量数据库
│   ├── models/
│   │   └── schemas.py              # Pydantic 数据模型
│   ├── api/
│   │   ├── analysis.py             # 分析 API
│   │   ├── knowledge_api.py        # 知识库 API
│   │   ├── retrieval_api.py        # 检索 API
│   │   └── mcp_debug_api.py        # MCP 调试 API
│   └── services/
│       ├── llm_client.py           # LLM 通信层
│       ├── cleaning_service.py     # 清洗 + 内容指纹
│       ├── chunking_service.py     # 结构化切面（题目粒度）
│       ├── embedding_service.py    # 向量化 + 缓存
│       ├── reranker_service.py     # 重排序
│       ├── rag_service.py          # RAG 检索编排
│       ├── rag_mcp.py              # MCP 调度层
│       ├── knowledge_service.py    # 入库管道单入口
│       ├── agent_pipeline.py       # Agent 流水线
│       └── doc_converter/          # 文档转换（PDF 已落地，Word/HTML 规划中）
├── data/
│   └── rag_docs/                   # 知识库目录
├── scripts/
│   └── rag_init.py                 # 离线入库脚本
├── tests/                          # 测试
├── requirements.txt                # Python 依赖
└── .env                            # 环境变量 (DASHSCOPE_API_KEY)
```

---

## 快速开始

### 环境要求

- Python 3.10+
- DashScope API Key

### 安装

```bash
cd backend_python

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# .env 文件
DASHSCOPE_API_KEY=your-api-key
```

### 入库知识库

```bash
python scripts/rag_init.py
```

### 启动

```bash
uvicorn app.main:app --reload --port 8000
```

服务默认运行在 `http://localhost:8000`

API 文档: `http://localhost:8000/docs`

---

## 与 Java 后端的交互

Python 后端为无状态 AI 服务，不参与业务认证与租户隔离，仅接收 Java 后端的分析请求。

```
Java 后端 (@Async)
  ↓ POST http://localhost:8000/api/v1/analysis/analyze
  ↓ { audio_file_id, audio_file_path }
Python AI 后端
  ↓ 执行 5 步 Agent 流水线
  ↓ 返回 { status, transcript, dialogue, evaluations, report }
Java 后端
  ↓ 解析响应
  ↓ 写入 t_interview / t_evaluation / t_report
  ↓ STOMP 推送给 Flutter
```

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | DashScope API 密钥 |
| `LLM_MODEL` | LLM 模型名称 (默认 qwen-plus) |
| `EMBEDDING_MODEL` | Embedding 模型 (默认 text-embedding-v3) |
| `ASR_MODEL` | ASR 模型 (默认 paraformer-v2) |
| `RAG_TOP_K` | 返回文档数 (默认 3) |
| `RAG_THRESHOLD` | 混合检索阈值 (默认 0.25，任一通道强命中放行) |
| `RAG_VECTOR_WEIGHT` | 向量检索权重 (默认 0.7) |
| `RAG_BM25_WEIGHT` | BM25 权重 (默认 0.3) |
| `RAG_USE_RERANK` | 是否默认重排 (默认 true) |
