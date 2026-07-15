# InterviewMentorAI

> AI 驱动的模拟面试复盘助手 —— 一键录音，AI 自动完成说话人分离、回答评估与结构化复盘报告。

---

## 项目简介

InterviewMentorAI 是一款面向求职者的 **AI 面试复盘工具**。用户在面试中一键开启录音，面试结束后 AI Agent 自动执行完整复盘流水线：

1. **语音转文字** — 基于 DashScope Paraformer 模型将面试录音转录为文本
2. **说话人分离** — LLM 分析对话语义，区分面试官与面试者的发言内容
3. **智能评估** — AI 逐段评估面试者的回答质量，给出得分与等级
4. **结构化报告** — 输出面试问题、回答内容、薄弱项/熟练项分析及改进建议

## 核心特性

| 特性 | 说明 |
|------|------|
| 一键录音 | Flutter 移动端支持 Android & iOS，面试开始即录音 |
| 说话人分离 | AI 自动区分面试官 / 面试者发言 |
| 智能评估 | 熟练项简短概括 / 薄弱项详细修正与知识点拓展 |
| 结构化复盘 | 输出面试纪要 + Markdown 评估报告 |
| 历史对比 | 持久化面试档案，支持多次面试进步对比 |

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
  数据库      LLM + ASR
```

| 模块 | 技术栈 | 说明 |
|------|--------|------|
| **移动端** | Flutter 3.x | 录音、上传、报告展示 |
| **Java 业务后端** | Spring Boot 2.7 + MyBatis Plus | 音频管理、数据库CRUD、API网关 |
| **Python AI 后端** | FastAPI + Transformers | ASR语音识别、LLM对话分析、Agent流水线 |

## 项目结构

```
InterviewMentorAI/
├── README.md
├── docs/                            # 文档
│   ├── architecture.md              # 架构设计文档
│   ├── api_document.md              # API 接口文档
│   └── interview_intro.md           # 面试讲解文稿
├── frontend_flutter/                # Flutter 移动端
├── backend_java/                    # Java 业务后端 (Spring Boot)
├── backend_python/                  # Python AI 后端 (FastAPI)
└── demo_assets/                     # 测试素材
```

## 快速开始

### Python AI 后端

```bash
cd backend_python
pip install -r requirements.txt

# 配置环境变量
export DASHSCOPE_API_KEY=your-api-key

# 启动
uvicorn app.main:app --reload --port 8000
```

### Java 业务后端

```bash
cd backend_java

# 配置环境变量 (或修改 application.yml)
export DASHSCOPE_API_KEY=your-api-key

# 启动
mvn spring-boot:run
```

### 前端启动

```bash
cd frontend_flutter
flutter pub get
flutter run
```

## API 概览

### Java 业务后端 (8080)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/audio/upload` | POST | 上传面试录音 |
| `/api/record/list` | GET | 获取历史面试记录 |
| `/api/record/{id}` | GET | 获取面试记录详情 |

### Python AI 后端 (8000)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/analysis/analyze` | POST | 执行AI分析流水线 |
| `/api/v1/health` | GET | 健康检查 |

> 详细接口文档见 [docs/api_document.md](docs/api_document.md)

## 面试讲解

本项目完整讲解文稿见 [docs/interview_intro.md](docs/interview_intro.md)，涵盖：

- 项目背景与需求分析
- Java/Python 双后端协作设计
- AI Agent 流水线设计思路
- 技术选型与架构决策
- 难点攻克与亮点总结

## License

MIT
=======
初级定位（安卓、苹果客户端）：面试时打开软件，自动录音，记录面试会话，面试结束之后，agent 自动生成会议纪要，并且针对我在面对面试官语气不确定、回答不正确的部分进行补充，并延申关联知识点，帮助面试者补充；针对我完全掌握的知识点只进行概述。
>>>>>>> 49d6d144176d36416b7bd07eace0f0724025250f
