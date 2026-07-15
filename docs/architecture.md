# 架构设计文档

## 1. 系统总览

InterviewMentorAI 采用 **前后端分离 + Java/Python 双后端** 架构：

- **前端**: Flutter 移动端（录音、上传、展示）
- **业务后端**: Java Spring Boot（音频管理、数据库、API网关）
- **AI 后端**: Python + Transformer（语音识别、对话分析、报告生成）

```
                              用户(面试者)
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │       Flutter App            │
                    │  录音(record) + 上传(dio)    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │                             │
                    ▼                             ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   Java 业务后端 (8080)       │   │   Python AI 后端 (8000)     │
│   Spring Boot 2.7           │   │   FastAPI + Transformer     │
│                             │   │                             │
│  ┌─────────────────────┐    │   │  ┌─────────────────────┐   │
│  │ AudioController     │    │   │  │ ASR Service         │   │
│  │ - 音频上传/存储      │    │   │  │ - Paraformer 语音识别│   │
│  │ - 触发AI流水线       │───►│───│  │ - 输出原始文本       │   │
│  └─────────────────────┘    │   │  └──────────┬──────────┘   │
│                             │   │             │              │
│  ┌─────────────────────┐    │   │  ┌──────────▼──────────┐   │
│  │ RecordController    │    │   │  │ Agent Pipeline      │   │
│  │ - 查询面试记录      │◄───│◄──│  │ - DialogueParse     │   │
│  │ - 获取复盘报告      │    │   │  │ - AnswerEvaluate    │   │
│  └─────────────────────┘    │   │  │ - ReportGen         │   │
│                             │   │  └──────────┬──────────┘   │
│  ┌─────────────────────┐    │   │             │              │
│  │ InterviewRecordSvc  │    │   │  ┌──────────▼──────────┐   │
│  │ - MyBatis Plus CRUD │    │   │  │ LLM Service         │   │
│  └──────────┬──────────┘    │   │  │ - 千问/DeepSeek     │   │
│             │               │   │  └─────────────────────┘   │
└─────────────┼───────────────┘   └─────────────────────────────┘
              │
              ▼
        H2/MySQL 数据库
```

## 2. 双后端协作模式

### 职责划分

| 后端 | 技术栈 | 职责 |
|------|--------|------|
| **Java 业务后端** | Spring Boot + MyBatis Plus | 音频文件管理、数据库CRUD、API网关、权限控制 |
| **Python AI 后端** | FastAPI + Transformers | ASR语音识别、LLM对话分析、Agent流水线编排 |

### 通信方式

```
Java 后端 ──HTTP POST──► Python AI 后端
       ◄──HTTP Response──┘

请求: { "audio_file_path": "/path/to/audio.wav", "interview_id": 123 }
响应: { "status": "completed", "report": "...", "evaluations": [...] }
```

## 3. 核心流程 (Agent Pipeline)

面试结束后的 AI 复盘流水线按以下步骤执行：

```
音频文件上传 (Flutter → Java后端)
    │
    ▼
[Java] 音频存储 + 创建面试记录
    │  保存到本地/对象存储，创建数据库记录
    │
    ▼
[Java → Python] 调用AI后端
    │  POST /api/v1/analysis/analyze
    │
    ▼
[Python] Step 1: ASR 语音转文字
    │  阿里云 DashScope Paraformer 模型
    │  输出: 原始转写文本 (rawTranscript)
    │
    ▼
[Python] Step 2: DialogueParseNode - 说话人分离
    │  LLM (千问/DeepSeek) 分析对话语义
    │  输出: List<DialogueItem> (speaker + content)
    │
    ▼
[Python] Step 3: AnswerEvaluateNode - 回答评估
    │  LLM 逐段评估面试者回答质量
    │  评估维度: 得分(0-100) + 等级(熟练/薄弱) + 优点 + 缺陷
    │
    ▼
[Python] Step 4: ReportGenNode - 生成复盘报告
    │  汇总所有评估，生成 Markdown 格式复盘报告
    │
    ▼
[Python → Java] 返回分析结果
    │
    ▼
[Java] 持久化存储 → 返回给客户端展示
```

## 4. Agent 状态管理

Agent 采用 **状态图 (StateGraph)** 模式编排，全局状态 `AgentState` 贯穿整个流水线：

```python
# Python AgentState (dataclass)
@dataclass
class AgentState:
    interview_id: int                    # 面试记录ID
    audio_file_path: str                 # 音频文件路径
    raw_transcript: str                  # ASR语音识别原始文本
    dialogue_list: List[DialogueItem]    # 说话人分离后的对话列表
    evaluation_list: List[EvaluationResult]  # 各段回答评估结果
    final_report: str                    # 最终复盘报告(Markdown)

@dataclass
class EvaluationResult:
    question: str            # 面试官问题
    answer: str              # 面试者原始回答
    score: int               # 评估得分(0-100)
    level: str               # PROFICIENT(熟练) / WEAK(薄弱)
    strengths: str           # 优点总结
    weaknesses: str          # 缺陷分析
    correction: str          # 修正方案(仅薄弱项)
    knowledge_points: str    # 拓展知识点(仅薄弱项)
```

## 5. 数据库设计

使用 H2 内存/文件数据库（开发阶段），ORM 使用 MyBatis Plus。

### interview_record (面试主记录)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO_INCREMENT | 主键 |
| audio_file_id | VARCHAR | 音频文件UUID标识 |
| audio_file_path | VARCHAR | 音频文件存储路径 |
| duration_seconds | INT | 面试时长(秒) |
| status | VARCHAR | PROCESSING/ASR_COMPLETED/DIALOGUE_PARSED/EVALUATION_COMPLETED/COMPLETED/FAILED |
| raw_transcript | TEXT | ASR语音识别原始文本 |
| dialogue_json | TEXT | 对话列表JSON字符串 |
| report_json | TEXT | AI生成的复盘报告JSON |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 6. 技术选型决策

| 模块 | 选型 | 理由 |
|------|------|------|
| **移动端** | | |
| 框架 | Flutter 3.x | 一套代码覆盖 Android + iOS + Web |
| 录音 | record | 跨平台录音支持，输出 WAV 格式 |
| 网络 | dio | 成熟的 HTTP 客户端，支持文件上传 |
| Markdown | flutter_markdown | 用于展示 AI 生成的复盘报告 |
| **Java 业务后端** | | |
| 框架 | Spring Boot 2.7.18 | 生态成熟、Java 8 兼容 |
| ORM | MyBatis Plus | 简化数据库操作，自动生成 SQL |
| 数据库 | H2 → MySQL/PostgreSQL | 开发→生产平滑迁移 |
| JSON | Jackson | Spring 默认集成 |
| **Python AI 后端** | | |
| 框架 | FastAPI | 高性能异步框架，自动生成API文档 |
| ASR | DashScope Paraformer | 多语言、高精度、国内访问稳定 |
| LLM | 千问/DeepSeek | 中文能力强，支持多种模型切换 |
| Agent | LangGraph / 自研 | 状态图模式，流水线可追踪 |
| ML | Transformers | HuggingFace 生态，模型丰富 |

## 7. 项目目录结构

```
InterviewMentorAI/
├── README.md
├── docs/                            # 文档
│   ├── architecture.md              # 架构设计文档
│   ├── api_document.md              # API 接口文档
│   └── interview_intro.md           # 面试讲解文稿
├── frontend_flutter/                # Flutter 移动端
│   └── lib/
│       ├── pages/                   # 页面
│       ├── services/                # 服务(audio_service, api_service)
│       └── utils/                   # 工具类
├── backend_java/                    # Java 业务后端
│   └── src/main/java/
│       ├── config/                  # 配置类
│       ├── controller/              # API 控制器
│       ├── entity/                  # 实体类
│       ├── repository/              # 数据访问层
│       ├── service/                 # 业务逻辑
│       └── util/                    # 工具类
├── backend_python/                  # Python AI 后端
│   ├── app/
│   │   ├── api/                     # FastAPI 路由
│   │   ├── core/                    # 核心配置
│   │   ├── services/                # AI 服务
│   │   │   ├── asr_service.py       # 语音识别
│   │   │   ├── llm_service.py       # 大模型调用
│   │   │   └── agent_pipeline.py    # Agent 流水线
│   │   └── models/                  # 数据模型
│   ├── requirements.txt
│   └── Dockerfile
└── demo_assets/                     # 测试素材
```
