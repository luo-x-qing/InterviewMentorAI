# InterviewMentorAI

> AI 驱动的模拟面试复盘助手 —— 面试录音，Agent 自动生成会议纪要与评估报告。

---

## 项目简介

InterviewMentorAI 是一款面向求职者的 **AI 面试复盘工具**，支持 Android 和 iOS 平台。用户在面试中一键开启录音，面试结束后 AI Agent 自动执行完整复盘流水线：

1. **语音转文字** — 基于 DashScope ASR 模型将面试录音转录为文本
2. **说话人分离** — LLM 分析对话语义，自动区分面试官与面试者的发言内容
3. **RAG 检索增强** — 从知识库检索相关技术知识点，为评估提供准确参考依据
4. **智能评估** — 逐段评估面试者回答质量，结合知识库给出得分与等级
5. **结构化报告** — 输出面试问题、回答内容、薄弱项/熟练项分析及改进建议

**初级定位（安卓、苹果客户端）：** 面试时打开软件，自动录音，记录面试会话，面试结束之后，Agent 自动生成会议纪要，并且针对我在面对面试官语气不确定、回答不正确的部分进行补充，并延伸关联知识点，帮助面试者补充；针对我完全掌握的知识点只进行概述。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 一键录音 | Flutter 移动端支持 Android & iOS，面试开始即录音 |
| 说话人分离 | AI 自动区分面试官 / 面试者发言 |
| RAG 增强 | 基于知识库检索增强评估准确性，减少 LLM 幻觉 |
| 智能评估 | 熟练项简短概括 / 薄弱项详细修正与知识点拓展 |
| 结构化复盘 | 输出面试纪要 + Markdown 评估报告 |
| 知识库管理 | 支持多格式题库导入（PDF/Word/HTML/TXT/MD） |
| 实时推送 | STOMP WebSocket 实时推送分析进度和状态 |

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
   MySQL 8.0    LLM + ASR + RAG
   (个人模式)    (DashScope + SQLite)
```

### 模块说明

| 模块 | 技术栈 | 职责 | 详细文档 |
|------|--------|------|----------|
| **Flutter 移动端** | Flutter 3.12 | 录音采集、文件上传、报告展示、历史记录 | [前端架构](frontend_flutter/README.md) |
| **Java 业务后端** | Spring Boot 3.2.5 + Java 17 | JWT 认证、业务 CRUD、异步调用 | [Java 后端架构](backend_springai/README.md) |
| **Python AI 后端** | FastAPI + DashScope | ASR 语音识别、LLM 对话分析、RAG 检索增强、Agent 流水线 | [Python 后端架构](backend_python/README.md) |
| **RAG 系统** | SQLite + sqlite-vec | 知识库存储、向量检索、BM25 混合检索、重排序 | [RAG+MCP 架构](docs/architecture/RAG_MCP_Architecture.md) |

---

## Java 业务后端概述

基于 Spring Boot 3.2.5 + Java 17 的业务后端。

### 基础设施

- **认证授权**：Spring Security + JWT 双 Token（accessToken 2h + refreshToken 7d）
- **异步框架**：ThreadPoolTaskExecutor + @Async，异步调用 Python AI 后端
- **WebSocket**：STOMP + SockJS，实时推送分析进度和状态

### 业务模块

| 模块 | 接口数 | 说明 |
|------|--------|------|
| Auth | 3 | 登录/注册/刷新Token |
| User | 3 | 个人信息查看/修改/改密码 |
| Interview | 5 | 创建面试/上传音频/详情/列表 |
| Report | 3 | 评估列表/报告详情/报告列表 |
| Knowledge | 6 | 知识库CRUD/搜索 |

### 数据库设计

> 详细架构见 [Java 后端架构文档](backend_springai/README.md)

---

## Python AI 后端概述

基于 FastAPI + DashScope 的 AI 面试分析引擎。

### Agent 流水线（5步）

```
音频文件 → ASR转文字 → 说话人分离 → RAG检索增强 → 逐段评估 → 结构化报告
```

| 步骤 | 模型 | 说明 |
|------|------|------|
| ASR 语音转文字 | DashScope paraformer-v2 | 面试录音转文本 |
| 说话人分离 | LLM (qwen-plus) | 区分面试官/面试者发言 |
| RAG 检索增强 | 向量检索 70% + BM25 30% | 检索知识库相关知识点 |
| 逐段智能评估 | LLM + RAG 上下文 | 每道题评估打分 |
| 结构化报告 | LLM 汇总 | 生成 Markdown 复盘报告 |

### 核心组件

| 组件 | 文件 | 说明 |
|------|------|------|
| 向量数据库 | `vector_db.py` | SQLite + sqlite-vec |
| RAG 业务层 | `rag_service.py` | 分块/向量化/检索/重排序 |
| MCP 调度层 | `rag_mcp.py` | 上下文组装/截断/LLM 增强 |
| Agent 流水线 | `agent_pipeline.py` | 5步分析流程编排 |
| LLM 服务 | `llm_service.py` | DashScope/OpenAI 调用封装 |

> 详细架构见 [Python 后端架构文档](backend_python/README.md)

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
面试录音 → 上传音频 → 等待AI分析(STOMP推送) → 查看报告
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
├── backend_springai/                  # Java 业务后端
│   ├── pom.xml
│   ├── src/main/java/com/interview/mentor/
│   │   ├── InterviewMentorApplication.java
│   │   ├── config/                    # SecurityConfig + CorsConfig + MyBatisPlusConfig
│   │   ├── security/                  # JWT (Provider + Filter + UserDetailsService)
│   │   ├── async/                     # AsyncConfig 线程池
│   │   ├── websocket/                 # WebSocketConfig + WsPushService
│   │   ├── exception/                 # BusinessException + GlobalExceptionHandler
│   │   ├── entity/                    # 7个实体类 + 7个DTO
│   │   ├── mapper/                    # 6个Mapper接口
│   │   ├── service/                   # 5个Service (接口+实现)
│   │   └── controller/                # 6个Controller (25+个API)
│   ├── src/main/resources/
│   │   ├── application.yml            # 应用配置
│   │   ├── schema.sql                 # 单库建表脚本 (7表)
│   │   └── mapper/                    # MyBatis XML
│   └── README.md                      # Java 后端架构说明
│
├── backend_python/                    # Python AI 后端
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口 (lifespan)
│   │   ├── core/
│   │   │   ├── config.py              # 配置管理
│   │   │   └── vector_db.py           # SQLite + sqlite-vec 向量数据库
│   │   ├── services/
│   │   │   ├── agent_pipeline.py      # Agent 5步流水线
│   │   │   ├── rag_service.py         # RAG 业务层
│   │   │   ├── rag_mcp.py             # MCP 调度层
│   │   │   ├── llm_service.py         # LLM 调用封装
│   │   │   ├── knowledge_service.py   # 知识库服务
│   │   │   └── doc_converter/         # 文档转换 (PDF/Word/HTML→MD)
│   │   ├── api/                       # API 接口
│   │   └── models/                    # Pydantic 数据模型
│   ├── data/rag_docs/                 # 知识库 (面试题库)
│   ├── scripts/rag_init.py            # 离线入库脚本
│   ├── requirements.txt
│   └── README.md                      # Python 后端架构说明
│
├── docs/                              # 项目文档中心
│   ├── README.md                      # 文档索引
│   ├── architecture/                  # 架构设计
│   ├── plans/                         # 技术方案
│   ├── reports/                       # 项目报告 & 评审
│   ├── learning/                      # 学习资料
│   ├── vision/                        # 项目愿景
│   ├── dev/                           # 开发日志
│   └── agents/                        # Agent 文档
├── docker-compose.yml                 # Docker 编排
└── README.md                          # 本文件 (项目入口)
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Java 17+
- Flutter 3.12+
- MySQL 8.0+
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
cd backend_springai

# 初始化数据库
mysql -u root -p -e "CREATE DATABASE interview_mentor DEFAULT CHARSET utf8mb4;"
mysql -u root -p interview_mentor < src/main/resources/schema.sql

# 配置环境变量
export MYSQL_PASSWORD=your-password
export JWT_SECRET=your-secret-key

# 启动
mvn spring-boot:run
```

### Flutter 移动端

```bash
cd frontend_flutter
flutter pub get
flutter run
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [Java 后端架构](backend_springai/README.md) | Spring Boot 业务后端说明 |
| [Python 后端架构](backend_python/README.md) | FastAPI AI 引擎完整说明 |
| [前端架构](frontend_flutter/README.md) | Flutter 移动端完整说明 |
| [MVP 技术方案](docs/plans/INTERVIEW-MVP-PLAN.html) | 完整技术方案（浏览器打开） |
| [RAG+MCP 架构](docs/architecture/RAG_MCP_Architecture.md) | RAG 系统详细设计 |
| [API 接口文档](docs/api/api_document.md) | 完整 API 接口说明 |
| [架构设计文档](docs/architecture/architecture.md) | 整体架构设计说明 |
| [文档索引](docs/README.md) | 全部文档目录 |

---

## License

MIT
