# InterviewMentorAI

> AI 驱动的模拟面试复盘助手 —— 一键录音，AI 自动完成说话人分离、回答评估与结构化复盘报告。

---

## 项目简介

InterviewMentorAI 是一款面向求职者的 **AI 面试复盘工具**。用户在面试中一键开启录音，面试结束后 AI Agent 自动执行完整复盘流水线：

1. **语音转文字** — 基于 Whisper 模型将面试录音转录为文本
2. **说话人分离** — 区分面试官与面试者的发言内容
3. **智能评估** — AI 逐段评估面试者的回答质量
4. **结构化报告** — 输出面试问题、回答内容、薄弱项/熟练项分析及改进建议

## 核心特性

| 特性 | 说明 |
|------|------|
| 一键录音 | Flutter 移动端支持 Android & iOS，面试开始即录音 |
| 说话人分离 | AI 自动区分面试官 / 面试者发言 |
| 智能评估 | 🟢 熟练项简短概括 / 🟨 薄弱项详细修正与知识点拓展 |
| 结构化复盘 | 输出面试纪要 + 评估报告，支持导出 |
| 历史对比 | 持久化面试档案，支持多次面试进步对比 |

## 技术架构

```
┌──────────────────────┐       REST API       ┌──────────────────────────────┐
│   Flutter 移动端      │ ◄──────────────────► │   Spring Boot AI 后端         │
│  (Android + iOS)     │                      │   (Spring AI + Whisper)      │
└──────────────────────┘                      └──────────┬───────────────────┘
                                                         │
                                          ┌──────────────┼──────────────┐
                                          │              │              │
                                     Whisper ASR    Spring AI LLM   MySQL/PG
                                     (语音转文字)   (评估/报告生成)  (数据持久化)
```

- **前端**: Flutter (Dart)
- **后端**: Java 17 + Spring Boot 3 + Spring AI
- **语音识别**: OpenAI Whisper API (本地部署或云端)
- **大模型**: 支持 OpenAI / 通义千问 / DeepSeek 等 (通过 Spring AI 统一接入)
- **数据库**: MySQL / PostgreSQL

## 项目结构

```
InterviewMentorAI/
├── README.md
├── .gitignore
├── docs/
│   ├── architecture.md          # 架构流程图文字说明
│   ├── api_document.md          # 前后端接口文档
│   └── interview_intro.md       # 面试项目讲解文稿
├── demo_assets/                 # 测试音频、截图素材
├── frontend_flutter/            # Flutter 移动端
└── backend_springai/            # Spring Boot AI 后端
```

## 快速开始

### 后端启动

```bash
cd backend_springai

# 配置环境变量 (或修改 application.yml)
export OPENAI_API_KEY=your-api-key
export DB_URL=jdbc:mysql://localhost:3306/interview_mentor

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

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/audio/upload` | POST | 上传面试录音，触发 AI 复盘流水线 |
| `/api/record/list` | GET | 获取历史面试记录列表 |
| `/api/record/{id}` | GET | 获取单条面试记录详情及评估报告 |

> 详细接口文档见 [docs/api_document.md](docs/api_document.md)

## 面试讲解

本项目完整讲解文稿见 [docs/interview_intro.md](docs/interview_intro.md)，涵盖：

- 项目背景与需求分析
- AI Agent 流水线设计思路
- 技术选型与架构决策
- 难点攻克与亮点总结

## License

MIT
