# 架构设计文档

## 1. 系统总览

InterviewMentorAI 采用 **前后端分离** 架构，前端为 Flutter 移动端，后端为 Spring Boot AI Agent 服务。

```
用户(面试者)
    │
    ▼
┌─────────────────────┐
│   Flutter App        │
│  录音 + 音频上传     │
└─────────┬───────────┘
          │ POST /api/audio/upload (multipart/form-data)
          ▼
┌─────────────────────────────────────────────────────────┐
│              Spring Boot AI 后端                         │
│                                                         │
│  ┌─────────────┐    ┌──────────────────────────────┐   │
│  │ AudioCtrl   │───►│ AsrService (Whisper)          │   │
│  └─────────────┘    │   音频 → 文本 + 时间戳         │   │
│                     └──────────┬───────────────────┘   │
│                                │                        │
│                     ┌──────────▼───────────────────┐   │
│                     │ InterviewAgentGraph           │   │
│                     │ (AI Agent 流水线)              │   │
│                     │                              │   │
│                     │  Node1: DialogueParseNode    │   │
│                     │    说话人分离                  │   │
│                     │         │                    │   │
│                     │  Node2: AnswerEvaluateNode   │   │
│                     │    逐段回答评估               │   │
│                     │         │                    │   │
│                     │  Node3: ReportGenNode        │   │
│                     │    生成结构化复盘报告          │   │
│                     └──────────┬───────────────────┘   │
│                                │                        │
│                     ┌──────────▼───────────────────┐   │
│                     │ InterviewRecordService        │   │
│                     │   持久化 → 数据库              │   │
│                     └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
          │
          ▼
    MySQL / PostgreSQL
```

## 2. 核心流程 (Agent Pipeline)

面试结束后的 AI 复盘流水线按以下步骤执行：

```
音频文件上传
    │
    ▼
[Step 1] ASR 语音转文字
    │  Whisper 模型识别音频，输出带时间戳的文本片段
    │
    ▼
[Step 2] DialogueParseNode - 说话人分离
    │  LLM 分析对话语义，将文本片段标记为「面试官」或「面试者」
    │  输出: List<DialogueItem> (speaker + content + timestamp)
    │
    ▼
[Step 3] AnswerEvaluateNode - 回答评估
    │  LLM 逐段评估面试者回答质量
    │  标记: 🟢熟练项 / 🟨薄弱项
    │  薄弱项输出: 修正答案 + 拓展知识点 + 标准话术
    │
    ▼
[Step 4] ReportGenNode - 生成复盘报告
    │  汇总所有评估，生成结构化面试纪要
    │
    ▼
持久化存储 → 返回给客户端展示
```

## 3. Agent 状态管理

Agent 采用 **状态图 (StateGraph)** 模式编排，全局状态 `AgentState` 贯穿整个流水线：

```java
AgentState {
    String audioFileId;              // 原始音频ID
    List<TranscriptSegment> asrResult;  // ASR转录结果
    List<DialogueItem> dialogue;     // 说话人分离后的对话列表
    List<AnswerEvaluation> evaluations; // 各段回答评估
    InterviewReport report;          // 最终复盘报告
}
```

## 4. 数据库设计

### interview_record (面试主记录)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT | 用户ID |
| title | VARCHAR | 面试标题/岗位 |
| audio_file_url | VARCHAR | 原始音频存储路径 |
| duration_seconds | INT | 面试时长(秒) |
| report_json | TEXT | 完整复盘报告JSON |
| created_at | DATETIME | 创建时间 |

### dialogue_item (对话明细)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| interview_id | BIGINT FK | 关联面试记录 |
| speaker | VARCHAR | INTERVIEWER / CANDIDATE |
| content | TEXT | 对话内容 |
| start_time_ms | BIGINT | 起始时间(毫秒) |
| end_time_ms | BIGINT | 结束时间(毫秒) |
| evaluation | TEXT | 评估结果JSON (仅面试者发言) |

## 5. 技术选型决策

| 模块 | 选型 | 理由 |
|------|------|------|
| 移动端 | Flutter | 一套代码覆盖 Android + iOS |
| 后端框架 | Spring Boot 3 | 生态成熟、Spring AI 原生支持 |
| 语音识别 | Whisper API | 多语言、高精度、支持时间戳 |
| 大模型接入 | Spring AI | 统一抽象，方便切换模型供应商 |
| 数据库 | MySQL/PostgreSQL | 关系型数据、事务支持 |

## 6. 扩展方向

- **实时流式识别**: WebSocket + Whisper Streaming，实现边录边转
- **多人面试**: 增加说话人数量识别（3人以上小组面试）
- **面试题库**: 结合岗位 JD 自动生成模拟面试题
- **匿名面试**: 生成纯文本面试纪要，不关联用户身份
