# 架构设计文档

## 1. 系统总览

InterviewMentorAI 采用 **前后端分离 + Java/Python 双后端** 架构：

- **前端**: Flutter 3.12+ 移动端（Material 3 设计）
- **业务后端**: Java Spring Boot 3.2.5 + Java 17（业务 CRUD）
- **AI 后端**: Python FastAPI + DashScope（ASR + LLM + RAG，5步 Agent 流水线）
- **数据库**: MySQL 8.0
- **实时通信**: STOMP WebSocket + SockJS（状态推送）
- **知识库**: SQLite + sqlite-vec（向量检索）+ BM25 混合检索

```
                        用户(面试者)
                            │
                            ▼
             ┌──────────────────────────────┐
              │        Flutter 移动端         │
              │  登录/首页/录音/报告/个人中心     │
             └──────────────┬───────────────┘
                            │ HTTP (Dio) + JWT
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────┐    ┌─────────────────────────┐
│  Java 业务后端(8080) │    │  Python AI 后端 (8000)  │
│  Spring Boot 3.2.5  │    │  FastAPI + DashScope    │
│  MyBatis-Plus       │    │                         │
│  JWT                 │◄──►│  ASR / LLM / RAG / MCP │
│  STOMP WebSocket    │    │  5步 Agent 流水线       │
└────────┬────────────┘    │  SQLite 向量知识库      │
         │                 └─────────────────────────┘
         ▼
    MySQL 8.0
```

## 2. 双后端协作模式

### 职责划分

| 后端 | 技术栈 | 职责 |
|------|--------|------|
| **Java 业务后端** | Spring Boot 3.2.5 + MyBatis-Plus | JWT 认证、业务 CRUD、STOMP 推送、异步调用 AI |
| **Python AI 后端** | FastAPI + DashScope SDK | ASR 语音识别、LLM 对话分析、RAG 检索增强、MCP 上下文组装、5步 Agent 流水线 |

### 通信方式

```
Java 后端 (@Async 线程池)
   └─→ POST http://localhost:8000/api/v1/analysis/analyze
       请求: { audio_file_id, audio_file_path }
   ←── 响应: { status, transcript, dialogue, evaluations, report }

Java 后端收到响应后：
   1. 写入 t_interview / t_evaluation / t_report
   2. STOMP 推送给 Flutter 客户端
```

## 3. Flutter 移动端架构

### 技术栈

| 技术 | 用途 |
|------|------|
| Flutter 3.12+ / Dart 3.x | UI 框架 |
| Dio 5.7 | HTTP 客户端 + JWT 拦截器 |
| record 5.1 | 录音采集（WAV 16kHz） |
| stomp_dart_client | STOMP WebSocket 协议 |
| flutter_markdown | Markdown 报告渲染 |
| shared_preferences | JWT Token 本地持久化 |

### 页面

| 页面 | 功能 |
|------|------|
| login_page | 登录/注册，JWT 双 Token 管理 |
| home_page | 3 Tab 导航：录音入口 / 面试流程 5 步引导 / 评估预览雷达图 |
| record_page | 圆形渐变按钮 + 脉冲涟漪动画 + 音频波形 + 自动上传 |
| report_page | CustomPainter 雷达图 + 5 维评分条 + 洞察卡片 + Markdown 报告 |


### 5 个服务

| 服务 | 职责 |
|------|------|
| api_service | Dio 单例 + 401 自动刷新拦截器 |
| auth_service | 登录/注册/刷新/登出 API |
| audio_service | 录音生命周期管理 |
| token_storage | 双 Token 内存 + SharedPreferences 持久化 |
| websocket_service | STOMP 订阅（5 个主题） |

## 4. Java 业务后端架构

### 分层架构

```
Controller (8个, 34 API)
    ↓
Service (6个: 接口 + 实现, @Transactional)
    ↓
Mapper (9个: MyBatis-Plus + XML)
    ↓
Entity (13个实体)
```

### 基础设施

| 组件 | 实现 | 说明 |
|------|------|------|
| 认证 | JwtAuthenticationFilter | JWT 双 Token（access 2h, refresh 7d） |
| 异步 | ThreadPoolTaskExecutor + @Async | 核心4线程，最大8线程 |
| WebSocket | STOMP + SockJS | 5 个推送主题 |
| 异常 | GlobalExceptionHandler | 统一业务/系统异常处理 |

### API 端点

| 模块 | 端点数 | 路径前缀 |
|------|--------|----------|
| Auth | 3 | `/auth/*` |
| User | 3 | `/user/*` |
| Interview | 5 | `/interview/*` |
| Session | 4 | `/session/*` |
| Report | 7 | `/report/*` |
| Knowledge | 6 | `/knowledge/*` |

### 数据库

## 5. Python AI 后端架构

### 分层架构

```
API 层: analysis.py / knowledge_api.py / retrieval_api.py / mcp_debug_api.py
    ↓
Agent 流水线: agent_pipeline.py (5步编排)
    ↓
MCP 调度层: rag_mcp.py (上下文组装 + LLM 增强)
    ↓
RAG 工具层: rag_service.py / chunking_service.py / embedding_service.py / reranker_service.py
    ↓
LLM/ASR: llm_client.py (DashScope / OpenAI)
    ↓
存储层: vector_db.py (SQLite + sqlite-vec)
    ↓
数据源: data/rag_docs/ (面试题库)
```

### 5 步 Agent 流水线

```
Step 1: ASR 语音转文字 (DashScope paraformer-v2)
Step 2: 说话人分离 (LLM 分析对话语义)
Step 3: RAG 检索增强 (向量 70% + BM25 30% + 重排序)
Step 4: 逐段智能评估 (LLM + RAG 上下文)
Step 5: 结构化报告 (Markdown 输出)
```

### 8 个 API 端点

| 端点 | 用途 |
|------|------|
| `POST /api/v1/analysis/analyze` | 执行 AI 分析流水线 |
| `GET /api/v1/analysis/health` | 健康检查 |
| `POST /api/v1/rag/knowledge/import` | 导入知识库文档 |
| `POST /api/v1/rag/retrieve` | 检索调试 |
| `POST /api/v1/rag/chunks/preview` | 分块预览 |
| `GET /api/v1/rag/knowledge/stats` | 知识库统计 |
| `POST /api/v1/rag/mcp/eval-test` | MCP 评估测试 |
| `POST /api/v1/rag/mcp/context-preview` | MCP 上下文预览 |

## 6. 实时通信（STOMP）

| 主题 | 推送时机 |
|------|----------|
| `/topic/interview/{id}` | 面试状态变更 |
| `/topic/interview/{id}/progress` | AI 分析进度 |
| `/topic/interview/{id}/complete` | 分析完成 |
| `/topic/interview/{id}/error` | 分析失败 |
| `/topic/user/{userId}/notifications` | HR 修正通知 |

## 7. 核心业务流程

```
面试录音 → 上传音频 → Java 异步调用 Python AI
  → ASR 转文字 → 说话人分离 → RAG 检索增强
  → 逐段评估 → 生成报告 → Java 持久化
  → STOMP 推送 → Flutter 展示报告
```

## 8. 技术选型

| 模块 | 选型 | 理由 |
|------|------|------|
| 移动端框架 | Flutter 3.12+ | Android + iOS 一套代码 |
| 录音 | record | 跨平台 WAV 录音 |
| HTTP | Dio + Stomp | 可靠文件上传 + 实时推送 |
| 业务框架 | Spring Boot 3.2.5 + Java 17 | 稳定、生态成熟、LTS |
| ORM | MyBatis-Plus | 简化 CRUD + 复杂查询 XML |
| 数据库 | MySQL 8.0 | 生产级（开发用 H2） |
| AI 框架 | FastAPI | 高性能异步 Python Web |
| ASR | DashScope paraformer-v2 | 中文高精度、国内稳定 |
| LLM | DashScope qwen-plus | 中文能力强 |
| 向量存储 | SQLite + sqlite-vec | 轻量、无需额外服务 |
| 检索 | BM25 + 向量混合 | 提高召回率 |
