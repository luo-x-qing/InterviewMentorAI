# InterviewMentorAI — Flutter 移动端

> Flutter 3.12+ 跨平台移动端（Android + iOS），Material 3 设计

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Flutter | 3.12+ | UI 框架 |
| Dart | 3.x | 编程语言 |
| Dio | 5.7 | HTTP 客户端 + JWT 拦截器 |
| record | 5.1 | 录音采集（WAV 16kHz） |
| permission_handler | 11.3 | 麦克风权限管理 |
| flutter_markdown | 0.7 | Markdown 报告渲染 |
| stomp_dart_client | 1.0 | STOMP WebSocket 协议 |
| shared_preferences | 2.3 | JWT Token 本地持久化 |
| intl | 0.19 | 国际化/格式化 |

## 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/login` | LoginPage | 登录/注册 |
| `/` | MainShell | 底部导航壳（5 Tab） |
| `/record` | RecordPage | 独立录音 + 上传（保留，面试流程中嵌入录音不跳转此页） |
| `/report` | ReportPage | 报告详情（支持多报告 + 模拟报告兜底） |

## 导航架构

```
MainShell（5 Tab）
├─ 主页   → HomePage
├─ 社区   → CommunityPage
├─ 题库   → QuestionBankPage
├─ 通知   → NotificationsPage
└─ 我     → ProfilePage
```

## 项目结构

```
frontend_flutter/
├── lib/
│   ├── main.dart                     # 应用入口 + 路由 + 认证守卫
│   ├── theme.dart                    # Material 3 完整主题
│   ├── pages/
│   │   ├── main_shell.dart           # 底部导航壳（IndexedStack 保持页面状态）
│   │   ├── login_page.dart           # 登录/注册
│   │   ├── home_page.dart            # 主页（录音入口/面试流程/评估预览）
│   │   ├── record_page.dart          # 录音（脉冲涟漪 + 音频波形 + 上传）
│   │   ├── report_page.dart          # 报告（雷达图 + 评分卡 + Markdown）
│   │   ├── community_page.dart       # 社区（占位）
│   │   ├── question_bank_page.dart   # 题库（占位）
│   │   ├── notifications_page.dart   # 通知（占位）
│   │   └── profile_page.dart         # 我（信息/菜单/退出）
│   ├── services/
│   │   ├── api_service.dart          # Dio 单例 + 401 自动刷新拦截器
│   │   ├── auth_service.dart         # 认证 API（登录/注册/刷新/登出）
│   │   ├── audio_service.dart        # 录音服务封装
│   │   ├── token_storage.dart        # Token 持久化
│   │   └── websocket_service.dart    # STOMP WebSocket 订阅
│   └── utils/
│       └── constants.dart            # 所有 API 地址常量
├── pubspec.yaml
└── README.md
```

## 页面功能

### 1. 登录页 (login_page)
- 登录/注册 Tab 切换
- 选填字段：昵称、邮箱、手机号
- 表单验证 + 错误提示 + 加载状态

### 2. 主页（个人）(home_page)
- 顶部胶囊式 3 Tab：**录音** / **面试流程** / **评估报告**
- 「录音」Tab：品牌标语 + 圆形麦克风按钮，点击跳转录音（或查看最近报告入口）
- 「面试流程」Tab：5 步引导（自我介绍→技术能力→项目经验→情景分析→总结提问），每步内嵌录音（波形+计时器）、停止后自动上传+推进下一步；步骤指示器（绿色✓/黄色⏳/紫色当前/灰色待进行）
- 「评估报告」Tab：有报告时显示报告卡片列表（点击进入详情），无报告时展示模拟报告（雷达图+评分条+优势建议卡片+查看完整报告按钮）

### 3. 录音页面 (record_page)
- 圆形渐变录音按钮，录音/停止动画切换
- 脉冲涟漪动画 + 模拟音频波形（48 条竖线）
- 实时计时器（mm:ss）
- 录音完成自动上传 → 跳转报告页面
- 分析等待状态 UI

### 4. 报告页面 (report_page)
- 雷达图（6 维度评分可视化）+ 总分 + 等级标签
- 5 项评分条 + 优势亮点/改进建议洞察卡片
- Markdown 渲染完整的复盘报告

### 5. 个人中心 (profile_page)
- 用户头像 + 昵称 + 个人用户标签
- 菜单项：面试记录、设置
- 退出登录按钮

## API 端点对照

| 分类 | Flutter 常量 | Java 后端路径 |
|------|-------------|---------------|
| 登录 | `loginApi` | `POST /auth/login` |
| 注册 | `registerApi` | `POST /auth/register` |
| 刷新 Token | `refreshTokenApi` | `POST /auth/refresh` |
| 创建面试 | `interviewCreateApi` | `POST /interview` |
| 面试详情 | `interviewDetailApi` | `GET /interview/{id}` |
| 面试列表 | `interviewListApi` | `GET /interview/list` |
| 我的面试 | `interviewMyListApi` | `GET /interview/my` |
| 上传音频 | `uploadAudioApi` | `POST /audio/upload` |
| 评估列表 | `reportEvaluationsApi` | `GET /report/interview/{id}/evaluations` |
| 获取报告 | `reportDetailApi` | `GET /report/interview/{id}/report` |
| 用户信息 | `userProfileApi` | `GET /user/profile` |
| 改密码 | `userPasswordApi` | `PUT /user/password` |

## WebSocket（STOMP）

| 订阅主题 | 推送时机 | 数据 |
|---------|----------|------|
| `/topic/interview/{id}` | 状态变更 | `{ status, message }` |
| `/topic/interview/{id}/progress` | AI 分析进度 | `{ progress(0-100), step }` |
| `/topic/interview/{id}/complete` | 分析完成 | `{ reportId }` |
| `/topic/interview/{id}/error` | 分析失败 | `{ error }` |


## 核心流程

### 面试录音上传（嵌入式）
```
面试流程 Tab → 看题 → 点击"开始回答" → AudioService.startRecord()
  → 录音中（波形+计时器）→ 点击"停止回答"
  → AudioService.stopRecord() → ApiService.uploadAudioBytes() 后台上传（不阻塞 UI）
  → 自动推进到下一步 → 5 步完成后 _finalizeInterview()
  → 合并报告 → 弹窗 → 查看 ReportPage
```



## 实现状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 登录/注册 | ✅ 完成 | JWT 双 Token |
| MainShell 底部导航 | ✅ 完成 | 个人 5 Tab，IndexedStack 保持状态 |
| 主页 3 Tab | ✅ 完成 | 录音入口/面试流程/评估预览，嵌入录音+步骤指示器 |
| 个人中心 | ✅ 完成 | 用户信息 + 菜单 + 退出 |
| 录音 + 上传 | ✅ 完成 | 脉冲/波形动画 + 自动上传（嵌入面试流程） |
| 报告展示 | ✅ 完成 | 雷达图 + 评分卡 + Markdown，支持多报告列表 + 模拟报告兜底 |

| WebSocket 服务 | ✅ 完成 | 服务层已实现，待页面集成 |
| 社区/题库/通知 | ⚠️ 占位 | 骨架页面，功能待开发 |
| 历史记录列表 | ⚠️ 待完善 | 服务层有 API，无对应页面 |
| 环境配置切换 | ❌ 未实现 | 常量硬编码 |
| iOS 麦克风权限 | ❌ 缺失 | Info.plist 缺 NSMicrophoneUsageDescription |

## 快速开始

```bash
cd frontend_flutter
flutter pub get
flutter run
```

配置后端地址：编辑 `lib/utils/constants.dart` 中的 `baseUrl` 和 `wsUrl`。

## 相关文档

| 文档 | 说明 |
|------|------|
| [Java 后端](../backend_springai/README.md) | Spring Boot 业务后端 |
| [Python 后端](../backend_python/README.md) | FastAPI AI 分析引擎 |
| [架构文档](../docs/architecture/architecture.md) | 整体架构设计 |
| [API 文档](../docs/api/api_document.md) | 完整接口说明 |
