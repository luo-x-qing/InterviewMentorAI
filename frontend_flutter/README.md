# frontend_flutter

一个新的 Flutter 项目。

## 入门指南

本项目是 Flutter 应用的起步项目。

以下是一些帮助你入门的资源（如果你是第一次接触 Flutter 项目）：

- [学习 Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [编写你的第一个 Flutter 应用](https://docs.flutter.dev/get-started/codelab)
- [Flutter 学习资源](https://docs.flutter.dev/reference/learning-resources)

如需 Flutter 开发帮助，请查看
[在线文档](https://docs.flutter.dev/)，其中提供了教程、示例、移动开发指南以及完整的 API 参考。

---

# InterviewMentorAI - Flutter 移动端架构

> Flutter 3.12 跨平台移动端（Android + iOS）

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Flutter | 3.12+ | UI 框架 |
| Dart | 3.x | 编程语言 |
| Dio | 5.7 | HTTP 客户端 |
| record | 5.1 | 录音采集 |
| permission_handler | 11.3 | 权限管理 |
| flutter_markdown | 0.7 | Markdown 渲染 |
| path_provider | 2.1 | 文件路径 |

---

## 项目结构

```
frontend_flutter/
├── lib/
│   ├── main.dart                     # 应用入口
│   ├── pages/
│   │   ├── home_page.dart            # 首页（历史记录列表）
│   │   ├── record_page.dart          # 录音页面
│   │   └── report_page.dart          # 报告展示页面
│   ├── services/
│   │   ├── api_service.dart          # HTTP API 调用封装
│   │   └── audio_service.dart        # 录音服务封装
│   └── utils/
│       └── constants.dart            # 常量定义（API 地址等）
├── pubspec.yaml                      # 依赖配置
└── README.md                         # 本文件
```

---

## 页面功能

### 1. 首页 (home_page)

- 显示历史面试记录列表
- 每条记录显示：标题、时间、状态、评分
- 支持下拉刷新
- 点击进入报告详情

### 2. 录音页面 (record_page)

- 一键开始/停止录音
- 实时录音时长显示
- 录音完成后自动上传
- 支持 HR 邀请码入口

### 3. 报告页面 (report_page)

- Markdown 格式渲染复盘报告
- 显示逐条评估（分数、等级、优缺点）
- 支持 AI 评分 + HR 修正评分对比
- 弱项知识点拓展展示

---

## API 调用

### 认证相关

```dart
// 登录
POST /auth/login
{ "username": "...", "password": "..." }
→ { "accessToken", "refreshToken", "userInfo" }

// 注册
POST /auth/register
{ "username", "password", "nickname", "email", "phone" }

// 刷新 Token
POST /auth/refresh?refreshToken=xxx
```

### 面试相关

```dart
// 创建面试记录
POST /interview
{ "jobRole": "Java开发" }
→ { "id": 5001, "status": "CREATED" }

// 上传音频
POST /interview/{id}/audio
Content-Type: multipart/form-data
→ { "id": 5001, "status": "PROCESSING" }

// 获取面试详情
GET /interview/{id}

// 我的面试列表
GET /interview/my?page=1&size=10

// 本租户面试列表（HR）
GET /interview/list?page=1&size=10
```

### 报告相关

```dart
// 获取评估列表
GET /report/interview/{id}/evaluations
→ [{ "question", "answer", "aiScore", "aiLevel", ... }]

// 获取复盘报告
GET /report/interview/{id}/report
→ { "reportMarkdown", "finalMarkdown", "avgScore", ... }
```

### 知识库相关

```dart
// 知识库列表
GET /knowledge/list?page=1&size=10

// 搜索知识库
GET /knowledge/search?keyword=xxx&page=1&size=10
```

### 面试会话（邀请码）

```dart
// 通过邀请码查看会话
GET /session/code/{inviteCode}
→ { "id", "title", "candidateName", "status" }

// 检查邀请码有效性
GET /session/code/{inviteCode}/valid
→ true / false
```

---

## WebSocket (STOMP)

### 订阅主题

```dart
// 面试状态变更
/topic/interview/{id}
→ { "type": "INTERVIEW_STATUS", "status": "PROCESSING", "message": "..." }

// AI 分析进度
/topic/interview/{id}/progress
→ { "type": "ANALYSIS_PROGRESS", "progress": 40, "step": "ASR识别中" }

// 分析完成
/topic/interview/{id}/complete
→ { "type": "ANALYSIS_COMPLETE", "reportId": 1001 }

// 分析失败
/topic/interview/{id}/error
→ { "type": "ANALYSIS_FAILED", "error": "..." }

// HR 修正通知
/topic/user/{userId}/notifications
→ { "type": "HR_CORRECTION", "reportId": 1001, "message": "您的面试报告已被HR修正" }
```

---

## 核心流程

### 面试录音流程

```
1. 用户点击"开始面试"
   ↓
2. 创建面试记录 (POST /interview)
   ↓
3. 开始录音 (record 包)
   ↓
4. 面试结束，停止录音
   ↓
5. 上传音频 (POST /interview/{id}/audio)
   ↓
6. 等待 AI 分析 (STOMP 订阅进度)
   ↓
7. 分析完成，跳转报告页面
```

### HR 邀请流程

```
1. HR 创建面试会话 (POST /session/create)
   → 获得邀请码 "ABC123"
   ↓
2. HR 将邀请码发送给候选人
   ↓
3. 候选人输入邀请码 (GET /session/code/ABC123)
   ↓
4. 候选人进入录音页面
   ↓
5. 录音完成，自动绑定会话 (POST /interview)
```

---

## 待实现功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 登录/注册页面 | ❌ | JWT Token 管理 |
| STOMP 客户端 | ❌ | 替换轮询为 WebSocket 订阅 |
| HR 修正页面 | ❌ | 评估列表 + 修正交互 |
| 历史记录页面 | ⚠️ | 基础列表已有，需对接 API |
| 报告详情页面 | ⚠️ | Markdown 渲染已有，需对接评估数据 |
| 邀请码入口 | ❌ | 候选人通过邀请码进入录音 |
| 环境切换 | ❌ | 开发/生产环境配置切换 |

---

## 快速开始

### 环境要求

- Flutter 3.12+
- Dart 3.x
- Android Studio / Xcode

### 安装

```bash
cd frontend_flutter

# 获取依赖
flutter pub get

# 运行
flutter run
```

### 配置

编辑 `lib/utils/constants.dart`：

```dart
class ApiConstants {
  static const String baseUrl = 'http://10.0.2.2:8080'; // Android 模拟器
  // static const String baseUrl = 'http://localhost:8080'; // iOS 模拟器
  static const String wsUrl = 'http://10.0.2.2:8080/ws';
}
```

---

## 与后端的交互关系

```
Flutter 移动端
  ↓ HTTP (Dio)
Java 业务后端 (8080)
  ↓ @Async RestClient
Python AI 后端 (8000)
  ↓ 5 步 Agent 流水线
  ↓ 响应
Java 业务后端
  ↓ STOMP 推送
Flutter 移动端 (实时状态更新)
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [Java 后端 README](../backend_springai/README.md) | Java 业务后端架构 |
| [Python 后端 README](../backend_python/README.md) | Python AI 后端架构 |
| [MVP 技术方案](../INTERVIEW-MVP-PLAN.html) | 完整技术方案文档 |
