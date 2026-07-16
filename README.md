# InterviewMentorAI

> AI 驱动的模拟面试复盘助手 —— 面试录音，Agent 自动生成会议纪要与评估报告。

---

## 项目定位

初级定位（安卓、苹果客户端）：面试时打开软件，自动录音，记录面试会话，面试结束之后，agent 自动生成会议纪要，并且针对我在面对面试官语气不确定、回答不正确的部分进行补充，并延申关联知识点，帮助面试者补充；针对我完全掌握的知识点只进行概述。

---

## 项目简介

InterviewMentorAI 是一款面向求职者的 **AI 面试复盘工具**，支持 Android 和 iOS 平台。用户在面试中一键开启录音，面试结束后 AI Agent 自动执行完整复盘流水线：

1. **语音转文字** — 基于 DashScope ASR 模型将面试录音转录为文本
2. **说话人分离** — LLM 分析对话语义，自动区分面试官与面试者的发言内容
3. **RAG 检索增强** — 从知识库检索相关技术知识点，为评估提供准确参考依据
4. **智能评估** — 逐段评估面试者回答质量，结合知识库给出得分与等级
5. **结构化报告** — 输出面试问题、回答内容、薄弱项/熟练项分析及改进建议

## 核心特性

| 特性 | 说明 |
|------|------|
| 一键录音 | Flutter 移动端支持 Android & iOS，面试开始即录音 |
| 说话人分离 | AI 自动区分面试官 / 面试者发言 |
| RAG 增强 | 基于知识库检索增强评估准确性，减少 LLM 幻觉 |
| 智能评估 | 熟练项简短概括 / 薄弱项详细修正与知识点拓展 |
| 结构化复盘 | 输出面试纪要 + Markdown 评估报告 |
| 知识库管理 | 支持多格式题库导入（PDF/Word/HTML/TXT/MD） |
| 历史对比 | 持久化面试档案，支持多次面试进步对比 |

---

## 技术架构

采用 **前后端分离 + Java/Python 双后端** 架构：

```
┌──────────────────────┐
│   Flutter 移动端      │
│  (Android + iOS)     │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐   ┌─────────┐
│  Java   │   │ Python  │
│业务后端  │◄─►│AI 后端   │
│(8080)   │   │(8000)   │
└────┬────┘   └────┬────┘
     │             │
     ▼             ▼
  数据库      LLM + ASR + RAG
```

### 模块说明

| 模块 | 技术栈 | 职责 |
|------|--------|------|
| **移动端** | Flutter 3.x | 录音采集、文件上传、报告展示、历史记录 |
| **Java 业务后端** | Spring Boot + MyBatis Plus | 音频文件管理、数据库 CRUD、API 网关 |
| **Python AI 后端** | FastAPI + DashScope | ASR 语音识别、LLM 对话分析、Agent 流水线 |
| **RAG 系统** | SQLite + sqlite-vec | 知识库存储、向量检索、混合检索、重排序 |
| **文档转换** | Python 脚本 | 多格式题库自动转换为 Markdown 入库 |

---

## RAG + MCP 架构

项目实现了完整的 **检索增强生成（RAG）** 系统，通过知识库检索增强 LLM 评估准确性。

### 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                       分层架构                               │
├─────────────────────────────────────────────────────────────┤
│  5. 业务流水线    agent_pipeline.py    编排完整分析流程       │
│       ↓                                                     │
│  4. MCP 调度层    rag_mcp.py          检索+上下文+LLM 统一   │
│       ↓                        ↓                            │
│  3. RAG 工具层  rag_service.py    LLM 通用层  llm_service   │
│       ↓                                                     │
│  2. 底层存储层    vector_db.py        SQLite + sqlite-vec    │
│       ↓                                                     │
│  1. 数据源层      data/rag_docs/      面试题库知识库          │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **向量数据库** | `vector_db.py` | SQLite + sqlite-vec，存储文本和向量，支持 BM25 和向量检索 |
| **RAG 业务层** | `rag_service.py` | 文档分块、向量化、混合检索、重排序 |
| **MCP 调度层** | `rag_mcp.py` | 上下文组装、长度截断、LLM 增强调用 |
| **文档转换** | `doc_converter/` | PDF/Word/HTML/TXT 转 Markdown |
| **API 接口** | `rag_api.py` | 知识库管理、检索调试、MCP 测试 |

### 离线入库流程

```
题库文档(PDF/Word/HTML/TXT/MD)
        ↓
    doc_converter 转换为 Markdown
        ↓
    rag_service 分块（500字符，重叠100）
        ↓
    DashScope Embedding 生成向量
        ↓
    SQLite 存储（文本 + 向量 + 元数据）
```

### 在线评估流程

```
面试问题
    ↓
rag_mcp.rag_enhance_evaluate()
    │
    ├─→ 混合检索（向量检索 70% + BM25 30%）
    ├─→ 重排序（Cross-Encoder）
    ├─→ 组装参考上下文
    ├─→ 截断超长内容（1800字符）
    └─→ LLM 生成评估结果
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

> 详细架构说明见 [RAG_MCP_Architecture.md](RAG_MCP_Architecture.md)

---

## 项目结构

```
InterviewMentorAI/
├── frontend_flutter/                  # Flutter 移动端
│   └── lib/
├── backend_java/                      # Java 业务后端 (Spring Boot)
│   └── src/
├── backend_python/                    # Python AI 后端 (FastAPI)
│   ├── app/
│   │   ├── api/                       # API 接口
│   │   │   ├── analysis.py            # 分析接口
│   │   │   └── rag_api.py             # RAG 接口
│   │   ├── core/                      # 核心模块
│   │   │   ├── config.py              # 配置管理
│   │   │   └── vector_db.py           # 向量数据库
│   │   ├── models/                    # 数据模型
│   │   │   └── schemas.py
│   │   └── services/                  # 业务服务
│   │       ├── llm_service.py         # LLM 服务
│   │       ├── rag_service.py         # RAG 业务层
│   │       ├── rag_mcp.py             # MCP 调度层
│   │       ├── agent_pipeline.py      # Agent 流水线
│   │       └── doc_converter/         # 文档转换 Skill
│   ├── data/
│   │   └── rag_docs/                  # 知识库目录
│   ├── scripts/
│   │   └── rag_init.py                # 离线入库脚本
│   └── tests/
├── docs/                              # 项目文档
│   ├── architecture.md
│   ├── api_document.md
│   └── interview_intro.md
├── demo_assets/                       # 测试素材
├── RAG_MCP_Architecture.md            # RAG 架构详细说明
└── README.md
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Java 17+
- Flutter 3.x
- DashScope API Key

### Python AI 后端

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

### Java 业务后端

```bash
cd backend_java

# 配置 application.yml 或环境变量
export DASHSCOPE_API_KEY=your-api-key

# 启动服务
mvn spring-boot:run
```

### Flutter 移动端

```bash
cd frontend_flutter

flutter pub get
flutter run
```

---

## API 概览

### Java 业务后端 (8080)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/audio/upload` | POST | 上传面试录音 |
| `/api/record/list` | GET | 获取历史面试记录 |
| `/api/record/{id}` | GET | 获取面试记录详情 |

### Python AI 后端 (8000)

**分析接口**

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/analysis/analyze` | POST | 执行 AI 分析流水线 |
| `/api/v1/analysis/health` | GET | 健康检查 |

**RAG 接口**

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/rag/knowledge/import` | POST | 导入知识库 |
| `/api/v1/rag/retrieve` | POST | 检索调试 |
| `/api/v1/rag/chunks/preview` | POST | 分块预览 |
| `/api/v1/rag/knowledge/stats` | GET | 知识库统计 |
| `/api/v1/rag/mcp/eval-test` | POST | MCP 评估测试 |
| `/api/v1/rag/mcp/context-preview` | POST | MCP 上下文预览 |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [RAG+MCP 架构详细说明](RAG_MCP_Architecture.md) | RAG 系统、MCP 层、Skill 系统详细设计 |
| [API 接口文档](docs/api_document.md) | 完整 API 接口说明 |
| [架构设计文档](docs/architecture.md) | 整体架构设计说明 |
| [面试讲解文稿](docs/interview_intro.md) | 项目讲解文稿 |

---

## License

MIT
=======
初级定位（安卓、苹果客户端）：面试时打开软件，自动录音，记录面试会话，面试结束之后，agent 自动生成会议纪要，并且针对我在面对面试官语气不确定、回答不正确的部分进行补充，并延申关联知识点，帮助面试者补充；针对我完全掌握的知识点只进行概述。
>>>>>>> 49d6d144176d36416b7bd07eace0f0724025250f
