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
| **向量数据库** | `core/vector_db.py` | SQLite + sqlite-vec，存储文本和向量，支持 BM25 和向量检索 |
| **LLM 服务** | `services/llm_service.py` | 封装 DashScope/OpenAI 调用，支持流式/非流式 |
| **RAG 业务层** | `services/rag_service.py` | 文档分块、向量化、混合检索、重排序 |
| **MCP 调度层** | `services/rag_mcp.py` | 上下文组装、长度截断、LLM 增强调用 |
| **知识库服务** | `services/knowledge_service.py` | 文档导入、分块、向量化入库 |
| **Agent 流水线** | `services/agent_pipeline.py` | 编排 ASR → 分离 → RAG → 评估 → 报告 |
| **文档转换** | `services/doc_converter/` | PDF/Word/HTML/TXT 转 Markdown |
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

### 离线入库流程

```
题库文档 (PDF/Word/HTML/TXT/MD)
  ↓
doc_converter 转换为 Markdown
  ↓
rag_service 分块 (500字符, 重叠100)
  ↓
DashScope Embedding 生成向量
  ↓
SQLite 存储 (文本 + 向量 + 元数据)
```

### 在线检索流程

```
查询文本
  ↓
混合检索
  ├─→ 向量检索 (DashScope embedding + cosine similarity) 70%
  └─→ BM25 关键词检索 30%
  ↓
重排序 (Cross-Encoder)
  ↓
Top-K 结果返回
```

### 知识库内容

```
data/rag_docs/
├── 通用评估标准.md              # 面试评估维度和评分规则
├── 技术难点标准答案.md          # Java 技术难点标准答案
├── Java面试题库/                # Java 基础/集合/多线程/JVM/Spring/MySQL
├── Python面试题库/              # Python 基础/进阶/框架/数据库
└── 系统设计面试题.md            # 高并发/缓存/消息队列/微服务
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

### RAG 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/rag/knowledge/import` | POST | 导入知识库文档 |
| `/api/v1/rag/retrieve` | POST | 检索调试 |
| `/api/v1/rag/chunks/preview` | POST | 分块预览 |
| `/api/v1/rag/knowledge/stats` | GET | 知识库统计 |

### MCP 调试接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/rag/mcp/eval-test` | POST | MCP 评估测试 |
| `/api/v1/rag/mcp/context-preview` | POST | MCP 上下文预览 |

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
│       ├── chunking_service.py     # 文档分块
│       ├── embedding_service.py    # 向量化 + 缓存
│       ├── reranker_service.py     # 重排序
│       ├── rag_service.py          # RAG 检索编排
│       ├── rag_mcp.py              # MCP 调度层
│       ├── knowledge_service.py    # 知识库管理
│       ├── agent_pipeline.py       # Agent 流水线
│       └── doc_converter/          # 文档转换工具
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

Python 后端不感知租户概念，所有多租户逻辑由 Java 侧处理。

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
| `EMBEDDING_MODEL` | Embedding 模型 (默认 text-embedding-v2) |
| `ASR_MODEL` | ASR 模型 (默认 paraformer-v2) |
