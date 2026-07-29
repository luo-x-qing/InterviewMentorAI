# API 接口文档

## 总览

项目包含两套 API 服务：

| 服务 | 地址 | 技术栈 | 接口数 |
|------|------|--------|--------|
| Java 业务后端 | `http://localhost:8080` | Spring Boot 3.2.5 | 32 |
| Python AI 后端 | `http://localhost:8000` | FastAPI | 8 |

---

# Java 业务后端 API（32 个端点）

## 基础信息

- **Base URL**: `http://localhost:8080`
- **Content-Type**: `application/json`
- **认证**: Bearer Token (JWT accessToken)
- **刷新**: 通过 refreshToken 获取新的 accessToken
- **接口总数**: 28 个

---

## 一、认证模块 (Auth) — 3 个端点

### POST `/auth/login`

用户登录。

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGci...",
  "refreshToken": "eyJhbGci...",
  "tokenType": "Bearer",
  "expiresIn": 7200,
  "userInfo": {
    "id": 1,
    "username": "zhangsan",
    "nickname": "张三"
  }
}
```

### POST `/auth/register`

用户注册。

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "nickname": "可选",
  "email": "可选",
  "phone": "可选"
}
```

### POST `/auth/refresh`

刷新 accessToken。参数：`refreshToken`（Query 或 Header）。

---

## 二、用户模块 (User) — 3 个端点

### GET `/user/profile`

获取当前用户信息。**权限**: 已认证

### PUT `/user/profile`

修改个人信息。**权限**: 已认证

### PUT `/user/password`

修改密码。**权限**: 已认证

**Request Body:**
```json
{
  "oldPassword": "string",
  "newPassword": "string"
}
```

---

## 三、面试模块 (Interview) — 5 个端点

### POST `/interview`

创建面试记录。**权限**: 已认证

**Request Body:**
```json
{
  "jobRole": "Java开发",
  "title": "可选标题"
}
```

### POST `/interview/{id}/audio`

上传面试音频文件。**权限**: 已认证

**Request**: `multipart/form-data`，字段名 `file`

### GET `/interview/{id}`

获取面试详情。**权限**: 已认证

### GET `/interview/list`

所有面试列表。**权限**: 已认证

参数: `page, size, status`（可选过滤）

### GET `/interview/my`

当前用户的面试列表。**权限**: 已认证

参数: `page, size`

---

## 四、评估与报告 (Report) — 3 个端点

### GET `/report/interview/{id}/evaluations`

获取指定面试的逐条评估列表。**权限**: 已认证

### GET `/report/interview/{id}/report`

获取复盘报告（Markdown）。**权限**: 已认证

### GET `/report/list`

报告列表。**权限**: 已认证

参数: `page, size`

---

## 六、知识库 (Knowledge) — 6 个端点

### POST `/knowledge`

创建知识库文档。**权限**: 已认证

### PUT `/knowledge/{id}`

更新知识库文档。**权限**: 已认证

### DELETE `/knowledge/{id}`

删除知识库文档。**权限**: 已认证

### GET `/knowledge/{id}`

获取文档详情。**权限**: 已认证

### GET `/knowledge/list`

文档列表。**权限**: 已认证

参数: `page, size`

### GET `/knowledge/search`

搜索知识库文档。**权限**: 已认证

参数: `keyword, page, size`

---

# Python AI 后端 API（8 个端点）

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **Swagger Docs**: `http://localhost:8000/docs`

---

## 一、分析接口 — 2 个端点

### POST `/api/v1/analysis/analyze`

执行 AI 分析流水线（5 步 Agent）。

**Request Body:**
```json
{
  "audio_file_id": "uuid-xxx",
  "audio_file_path": "/data/audio/uuid-xxx.wav"
}
```

**Response:**
```json
{
  "status": "COMPLETED",
  "interview_id": 5001,
  "transcript": "原始转写文本...",
  "dialogue": [
    {
      "speaker": "INTERVIEWER",
      "content": "请介绍 Spring IOC"
    }
  ],
  "evaluations": [
    {
      "question": "请介绍 Spring IOC",
      "score": 85,
      "level": "PROFICIENT",
      "strengths": "概念准确",
      "weaknesses": "缺少源码分析"
    }
  ],
  "report": "## 面试复盘报告\n\n### 综合评分..."
}
```

### GET `/api/v1/analysis/health`

健康检查。

**Response:**
```json
{
  "status": "healthy",
  "asr_model": "paraformer-v2",
  "llm_model": "qwen-plus",
  "rag_docs_count": 42
}
```

---

## 二、RAG 知识库接口 — 4 个端点

### POST `/api/v1/rag/knowledge/import`

导入文档到知识库（支持 PDF/Word/HTML/TXT/MD）。

### POST `/api/v1/rag/retrieve`

检索调试 - 查看混合检索结果。

### POST `/api/v1/rag/chunks/preview`

预览文档分块结果（500字符，重叠100）。

### GET `/api/v1/rag/knowledge/stats`

知识库统计信息（文档数、分块数、向量数）。

---

## 三、MCP 调试接口 — 2 个端点

### POST `/api/v1/rag/mcp/eval-test`

MCP 评估测试 - 测试上下文组装 + LLM 评估效果。

### POST `/api/v1/rag/mcp/context-preview`

MCP 上下文预览 - 查看检索结果如何组装到 LLM 上下文中。

---

# WebSocket (STOMP) 推送协议

## 端点

`ws://localhost:8080/ws` (SockJS 兼容)

## 订阅主题

| 主题 | 推送数据 | 说明 |
|------|----------|------|
| `/topic/interview/{id}` | `{ status, message }` | 面试状态变更 |
| `/topic/interview/{id}/progress` | `{ progress(0-100), step }` | AI 分析进度 |
| `/topic/interview/{id}/complete` | `{ reportId }` | 分析完成 |
| `/topic/interview/{id}/error` | `{ error }` | 分析失败 |
| `/topic/user/{userId}/notifications` | `{ reportId, message }` | 通知 |
