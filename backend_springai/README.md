# InterviewMentorAI 后端架构说明

## 项目概述

InterviewMentorAI 是一个AI驱动的面试复盘助手，后端采用 Spring Boot 3 + Spring AI 架构，实现了一套完整的 AI Agent 流水线，用于处理面试录音并生成结构化复盘报告。

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      AudioController                            │
│                    (音频上传控制器)                               │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  InterviewRecordService                          │
│                   (面试记录服务)                                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  InterviewAgentGraph                             │
│                   (AI Agent流水线调度器)                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  AsrService     │   │ DialogueParse   │   │ AnswerEvaluate  │
│  (Whisper ASR)  │   │    Node         │   │    Node         │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │               ┌─────────────────┐            │
         │               │   LlmService    │            │
         │               │ (大模型调用)     │            │
         │               └─────────────────┘            │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │      ReportGenNode           │
                    │   (复盘报告生成节点)          │
                    └─────────────────────────────┘
```

### AI Agent 流水线

项目采用状态图（StateGraph）模式编排 AI 流程，全局状态 `AgentState` 贯穿整个流水线：

```
音频上传 → Whisper ASR → DialogueParseNode → AnswerEvaluateNode → ReportGenNode
    │           │               │                    │                   │
    │           │               │                    │                   │
    ▼           ▼               ▼                    ▼                   ▼
 [初始化]  [语音转文字]    [说话人分离]          [回答评估]        [报告生成]
```

每个节点接收 `AgentState`，处理后返回更新的 `AgentState`，确保数据在节点间正确传递。

## 目录结构

```
backend_springai/
├── src/main/java/com/ecommerce/backend_springai/
│   ├── config/                    # 配置类
│   │   ├── CorsConfig.java       # 跨域配置
│   │   ├── WebClientConfig.java  # WebClient配置
│   │   └── WebConfig.java        # Web配置
│   ├── controller/                # 控制器层
│   │   ├── AudioController.java  # 音频上传控制器
│   │   └── RecordController.java # 记录查询控制器
│   ├── entity/                    # 实体类
│   │   ├── DialogueItem.java     # 对话项实体
│   │   ├── InterviewRecord.java  # 面试记录实体
│   │   └── dto/                  # 数据传输对象
│   │       ├── req/              # 请求DTO
│   │       │   └── AudioUploadReq.java
│   │       └── resp/             # 响应DTO
│   │           └── AnalysisResp.java
│   ├── repository/                # 数据访问层
│   │   └── InterviewRecordMapper.java
│   ├── service/                   # 业务逻辑层
│   │   ├── AsrService.java       # 语音转文字服务
│   │   ├── LlmService.java       # 大模型调用服务
│   │   ├── InterviewRecordService.java  # 记录服务
│   │   ├── InterviewAgentGraph.java     # Agent流水线调度器
│   │   └── agent/                # Agent节点
│   │       ├── AgentState.java   # 全局状态实体
│   │       ├── nodes/            # 处理节点
│   │       │   ├── DialogueParseNode.java    # 说话人分离节点
│   │       │   ├── AnswerEvaluateNode.java   # 回答评估节点
│   │       │   └── ReportGenNode.java        # 报告生成节点
│   │       └── prompts/          # 提示词模板
│   │           └── AgentPromptTemplate.java
│   └── util/                      # 工具类
│       ├── FileUtil.java         # 文件操作工具
│       └── ResultUtil.java       # 统一响应工具
├── src/main/resources/
│   ├── application.yml            # 应用配置
│   └── schema.sql                # 数据库初始化脚本
└── pom.xml                        # Maven依赖
```

## 核心模块说明

### 1. 音频上传模块（步骤1-3）

**AudioController** 负责接收前端上传的音频文件：

- 验证音频格式（wav/mp3/m4a）和大小（最大200MB）
- 生成唯一文件标识（UUID）
- 存储音频文件到服务端本地目录
- 创建面试记录（初始化AI流水线上下文）
- 异步触发AI处理流水线
- 返回「AI排队处理中」状态

### 2. 语音转文字模块（Whisper ASR）

**AsrService** 调用 Whisper API 进行语音识别：

- 读取音频文件
- 发送POST请求到 Whisper API
- 解析响应，提取转写文本
- 返回原始转写文本

### 3. 说话人分离模块（DialogueParseNode）

**DialogueParseNode** 通过AI语义分析区分说话人：

- 读取ASR输出的原始流水文本
- 使用大模型分析对话语义
- 自动区分面试官（INTERVIEWER）和面试者（CANDIDATE）
- 生成结构化问答对

### 4. 回答评估模块（AnswerEvaluateNode）

**AnswerEvaluateNode** 逐题评估面试者回答：

- 遍历每个问答对
- 调用LLM进行差异化评估
- 熟练项：精简概括优点
- 薄弱项：详细修正和拓展知识点
- 输出评估结果（得分、等级、优缺点等）

### 5. 报告生成模块（ReportGenNode）

**ReportGenNode** 生成完整的复盘报告：

- 汇总所有评估结果
- 生成Markdown格式报告
- 包含：整体概况、逐题复盘、知识点汇总、改进建议

## 配置说明

### application.yml

```yaml
# LLM配置
llm:
  api-key: ${LLM_API_KEY:sk-xxx}        # API密钥
  base-url: ${LLM_BASE_URL:https://api.deepseek.com/v1}  # API地址
  model-name: deepseek-chat              # 模型名称
  temperature: 0.3                       # 温度参数

# Whisper ASR配置
asr:
  api-key: ${ASR_API_KEY:sk-xxx}        # API密钥
  base-url: ${ASR_BASE_URL:https://api.openai.com/v1}  # API地址

# 音频存储配置
audio:
  storage:
    path: ./data/audio                   # 存储路径
```

## API接口

### 1. 上传面试录音

**POST** `/api/audio/upload`

请求参数：
- `file`: 音频文件（multipart/form-data）
- `title`: 面试标题（可选）
- `userId`: 用户ID（可选）
- `durationSeconds`: 面试时长（可选）

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "interviewId": 1001,
    "audioFileId": "uuid-xxx",
    "status": "PROCESSING",
    "message": "音频上传成功，AI复盘流水线已启动"
  }
}
```

### 2. 查询面试记录列表

**GET** `/api/record/list`

查询参数：
- `page`: 页码（默认1）
- `size`: 每页条数（默认10）

### 3. 查询面试记录详情

**GET** `/api/record/{id}`

### 4. 查询流水线状态

**GET** `/api/record/{id}/status`

## 运行方式

### 1. 配置环境变量

```bash
export LLM_API_KEY=your-api-key
export ASR_API_KEY=your-api-key
```

### 2. 启动应用

```bash
cd backend_springai
mvn spring-boot:run
```

### 3. 访问H2控制台

浏览器访问：http://localhost:8080/h2-console

## 注意事项

1. **API密钥安全**：请勿将API密钥提交到代码仓库
2. **音频文件大小**：最大支持200MB
3. **处理时间**：完整流水线处理时间取决于音频长度，通常需要1-5分钟
4. **错误处理**：流水线异常时会自动更新数据库状态为FAILED
