# API 接口文档

## 基础信息

- Base URL: `http://localhost:8080/api`
- Content-Type: `application/json`
- 认证方式: Bearer Token (规划中，当前未实现)

---

## 1. 上传面试录音

### POST `/api/audio/upload`

上传面试音频文件，触发 AI 复盘流水线。流水线异步执行，返回 `interviewId` 用于后续查询。

**Request**

Content-Type: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 音频文件 (wav/mp3/m4a, 最大200MB) |
| title | String | 否 | 面试标题，如 "Java后端二面" |
| userId | Long | 否 | 用户ID (当前版本可选) |

**Response**

```json
{
  "code": 200,
  "message": "音频上传成功，AI复盘流水线已启动",
  "data": {
    "interviewId": 1001,
    "status": "PROCESSING"
  }
}
```

**错误码**

| code | 说明 |
|------|------|
| 400 | 文件格式不支持 |
| 413 | 文件过大 |
| 500 | 服务端异常 |

---

## 2. 查询面试记录列表

### GET `/api/record/list`

获取历史面试记录列表，按时间倒序排列。

**Query Parameters**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | Long | 否 | 用户ID |
| page | Integer | 否 | 页码，默认 1 |
| size | Integer | 否 | 每页条数，默认 10 |

**Response**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "records": [
      {
        "interviewId": 1001,
        "title": "Java后端二面",
        "durationSeconds": 1860,
        "status": "COMPLETED",
        "createdAt": "2025-07-10T14:30:00"
      }
    ]
  }
}
```

---

## 3. 查询单条面试记录详情

### GET `/api/record/{id}`

获取指定面试记录的完整复盘报告，包括对话列表和各段评估。

**Path Parameters**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 面试记录ID |

**Response**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "interviewId": 1001,
    "title": "Java后端二面",
    "durationSeconds": 1860,
    "status": "COMPLETED",
    "dialogue": [
      {
        "speaker": "INTERVIEWER",
        "content": "请介绍一下你对 Spring IOC 的理解？",
        "startTimeMs": 0,
        "endTimeMs": 5200
      },
      {
        "speaker": "CANDIDATE",
        "content": "IOC 是控制反转，核心思想是将对象的创建和依赖管理交给 Spring 容器...",
        "startTimeMs": 5500,
        "endTimeMs": 18000,
        "evaluation": {
          "level": "PROFICIENT",
          "comment": "回答准确，涵盖了核心概念和实际应用场景",
          "improvements": null
        }
      }
    ],
    "report": {
      "summary": "整体表现良好，对 Spring 生态掌握扎实",
      "proficientCount": 5,
      "weakCount": 2,
      "weakItems": [
        {
          "question": "请介绍一下分布式事务的解决方案",
          "yourAnswer": "可以用 2PC...",
          "standardAnswer": "常见方案包括：1) 2PC/3PC 2) TCC 3) 本地消息表 4) Saga 5) Seata框架...",
          "knowledgePoints": ["CAP定理", "BASE理论", "Seata AT模式"],
          "suggestedReply": "分布式事务有多种解决方案，根据一致性要求选择..."
        }
      ]
    }
  }
}
```

---

## 4. 查询复盘流水线状态

### GET `/api/record/{id}/status`

查询 AI 复盘流水线的执行状态。

**Response**

```json
{
  "code": 200,
  "data": {
    "interviewId": 1001,
    "status": "COMPLETED",
    "progress": 100,
    "currentStep": "REPORT_GENERATED"
  }
}
```

**status 枚举值**

| 值 | 说明 |
|------|------|
| PROCESSING | 流水线执行中 |
| ASR_COMPLETED | 语音转文字完成 |
| DIALOGUE_PARSED | 说话人分离完成 |
| EVALUATION_COMPLETED | 回答评估完成 |
| COMPLETED | 复盘报告生成完毕 |
| FAILED | 执行失败 |
