# InterviewMentorAI - Java 业务后端

> Spring Boot 3.2.5 + Java 17 多租户 SaaS 业务后端

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Java | 17 | 运行时 |
| Spring Boot | 3.2.5 | Web 框架 |
| Spring Security | 6.x | 认证授权（JWT） |
| MyBatis-Plus | 3.5.6 | ORM |
| MySQL | 8.0+ | 数据库 |
| WebSocket | STOMP + SockJS | 实时推送 |
| Lombok | - | 代码简化 |

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        分层架构                                  │
├─────────────────────────────────────────────────────────────────┤
│  Controller     REST API 入口 + 参数校验 + 权限注解              │
│       ↓                                                         │
│  Service        业务逻辑层（事务管理、业务规则）                  │
│       ↓                                                         │
│  Mapper         数据访问层（MyBatis-Plus + XML 复杂查询）        │
│       ↓                                                         │
│  Entity         数据实体（对应数据库表）                          │
├─────────────────────────────────────────────────────────────────┤
│  Security       JWT Filter Chain（认证 → 租户解析 → 权限校验）   │
│  Tenant         多租户上下文（ThreadLocal + Filter）             │
│  WebSocket      STOMP 推送服务（异步状态通知）                   │
│  Async          线程池 + @Async（AI 分析异步调用）               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 多租户设计

### 数据隔离策略

- **平台数据**（`platform` schema）：用户、角色、权限、租户、订阅
- **租户数据**（`tenant_{id}` schema）：面试记录、评估、报告、知识库

### 租户上下文流转

```
HTTP Request
  ↓
JwtAuthenticationFilter  → 解析 JWT，提取 username
  ↓
TenantFilter             → 从 JWT/请求头解析 tenantId
  ↓                         → 查询 schemaName
TenantContext.set()      → ThreadLocal 存储 { tenantId, schemaName }
  ↓
Controller / Service     → 通过 TenantContext.getTenantId() 获取当前租户
  ↓
TenantContext.clear()    → 请求结束，清理 ThreadLocal
```

---

## 认证授权

### JWT 双 Token 机制

| Token | 有效期 | 用途 |
|-------|--------|------|
| accessToken | 2 小时 | API 鉴权 |
| refreshToken | 7 天 | 刷新 accessToken |

### 三层角色 RBAC

| 角色 | 权限 |
|------|------|
| `PLATFORM_ADMIN` | 全部权限：租户管理、订阅管理、成员管理 |
| `TENANT_ADMIN` | 租户内管理：成员管理、知识库、查看所有面试 |
| `TENANT_MEMBER` | 基础操作：创建面试、上传音频、查看自己报告 |

### 预置权限码

```
interview:create, interview:view, interview:view_all,
report:view, report:edit, report:export,
knowledge:manage, tenant:manage, member:manage, subscription:manage
```

---

## 业务模块

### 1. 认证模块 (Auth)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/auth/login` | POST | 用户登录 | 公开 |
| `/auth/register` | POST | 用户注册（默认分配 TENANT_MEMBER） | 公开 |
| `/auth/refresh` | POST | 刷新 Token | 公开 |

### 2. 用户模块 (User)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/user/profile` | GET | 获取当前用户信息 | 已认证 |
| `/user/profile` | PUT | 修改个人信息 | 已认证 |
| `/user/password` | PUT | 修改密码 | 已认证 |

### 3. 租户管理 (Tenant)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/tenant/create` | POST | 创建租户 | PLATFORM_ADMIN |
| `/tenant/members` | GET | 租户成员列表 | TENANT_ADMIN |
| `/tenant/invite` | POST | 邀请成员 | TENANT_ADMIN |

### 4. 订阅管理 (Subscription)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/subscription/current` | GET | 当前订阅状态 | 已认证 |
| `/subscription/stats` | GET | 订阅统计 | 已认证 |
| `/subscription/upgrade` | POST | 升级计划 | TENANT_ADMIN |

### 5. 面试模块 (Interview)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/interview` | POST | 创建面试记录 | TENANT_MEMBER |
| `/interview/{id}/audio` | POST | 上传音频 + 触发 AI | TENANT_MEMBER |
| `/interview/{id}` | GET | 面试详情 | 已认证 |
| `/interview/list` | GET | 本租户面试列表 | 已认证 |
| `/interview/my` | GET | 我的面试列表 | TENANT_MEMBER |

### 6. 面试会话 (InterviewSession)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/session/create` | POST | HR 创建面试会话 | TENANT_ADMIN |
| `/session/code/{code}` | GET | 候选人通过邀请码查看 | 公开 |
| `/session/code/{code}/valid` | GET | 检查邀请码有效性 | 公开 |
| `/session/list` | GET | HR 会话列表 | TENANT_ADMIN |

### 7. 评估与报告 (Report)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/report/interview/{id}/evaluations` | GET | 评估列表 | 已认证 |
| `/report/evaluation/{id}/correct` | PUT | HR 逐条修正评估 | report:edit |
| `/report/interview/{id}/report` | GET | 获取复盘报告 | 已认证 |
| `/report/interview/{id}/report` | PUT | HR 修正报告内容 | report:edit |
| `/report/list` | GET | 报告列表 | 已认证 |
| `/report/stats` | GET | 租户报告统计 | 已认证 |
| `/report/pending-review` | GET | 待 HR 修正列表 | TENANT_ADMIN |

### 8. 知识库 (Knowledge)

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/knowledge` | POST | 创建知识库 | knowledge:manage |
| `/knowledge/{id}` | PUT | 更新文档 | knowledge:manage |
| `/knowledge/{id}` | DELETE | 删除文档 | knowledge:manage |
| `/knowledge/{id}` | GET | 文档详情 | 已认证 |
| `/knowledge/list` | GET | 文档列表 | 已认证 |
| `/knowledge/search` | GET | 搜索文档 | 已认证 |

---

## 异步调用流程

```
Flutter 上传音频
  ↓
InterviewController.uploadAudio()
  1. 保存文件到磁盘
  2. 创建 t_interview (PROCESSING)
  3. 返回 { interviewId, status: "PROCESSING" }
  └──→ @Async aiAnalysisExecutor
        ├─ STOMP 推送: /topic/interview/{id} → PROCESSING
        ├─ RestClient POST http://localhost:8000/api/v1/analysis/analyze
        │    (Python AI 后端处理中...)
        ├─ 收到响应后:
        │    ├─ 更新 t_interview: raw_transcript, status=COMPLETED
        │    ├─ 插入 t_evaluation: 逐条评估结果
        │    ├─ 插入 t_report: report_markdown
        │    └─ STOMP 推送: /topic/interview/{id} → COMPLETED
        └─ 异常处理:
             ├─ 更新 t_interview: status=FAILED
             └─ STOMP 推送: /topic/interview/{id} → FAILED
```

---

## STOMP 推送协议

| 主题 | 用途 | 数据 |
|------|------|------|
| `/topic/interview/{id}` | 面试状态变更 | status, message |
| `/topic/interview/{id}/progress` | AI 分析进度 | progress(0-100), step |
| `/topic/interview/{id}/complete` | 分析完成 | reportId |
| `/topic/interview/{id}/error` | 分析失败 | error |
| `/topic/user/{userId}/notifications` | HR 修正通知 | reportId, message |

---

## 数据库设计

### Platform Schema（公共平台）

| 表名 | 说明 |
|------|------|
| `sys_tenant` | 租户表 |
| `sys_user` | 用户表 |
| `sys_role` | 角色表 |
| `sys_permission` | 权限表 |
| `sys_user_role` | 用户角色关联 |
| `sys_role_permission` | 角色权限关联 |
| `sys_subscription` | 订阅计划 |

### Tenant Schema（每租户独立）

| 表名 | 说明 |
|------|------|
| `t_interview` | 面试记录 |
| `t_evaluation` | 逐条评估 |
| `t_report` | 复盘报告（AI原始 + HR修正后） |
| `t_interview_session` | 面试会话（邀请码） |
| `t_knowledge_base` | 知识库 |
| `t_knowledge_doc` | 知识库文档 |
| `knowledge_chunk` | 文档片段（向量检索） |
| `evaluation_template` | 评估模板 |
| `audit_log` | 操作日志 |

---

## 项目结构

```
backend_springai/
├── pom.xml
├── src/main/java/com/interview/mentor/
│   ├── InterviewMentorApplication.java
│   ├── config/
│   │   ├── SecurityConfig.java          # Spring Security + JWT FilterChain
│   │   └── CorsConfig.java              # 跨域配置
│   ├── security/
│   │   ├── JwtTokenProvider.java         # JWT 生成/验证
│   │   ├── JwtAuthenticationFilter.java  # JWT 认证过滤器
│   │   └── CustomUserDetailsService.java # 用户详情加载
│   ├── tenant/
│   │   ├── TenantContext.java            # ThreadLocal 租户上下文
│   │   ├── TenantFilter.java            # 租户解析过滤器
│   │   └── TenantService.java           # 租户服务
│   ├── async/
│   │   └── AsyncConfig.java             # 线程池配置
│   ├── websocket/
│   │   ├── WebSocketConfig.java         # STOMP + SockJS
│   │   └── WsPushService.java           # 推送服务
│   ├── exception/
│   │   ├── BusinessException.java       # 业务异常
│   │   └── GlobalExceptionHandler.java  # 全局异常处理
│   ├── entity/                           # 18个实体类
│   ├── entity/dto/                       # 请求/响应 DTO
│   ├── mapper/                           # 12个Mapper接口
│   ├── service/                          # 6个Service（接口+实现）
│   └── controller/                       # 8个Controller
├── src/main/resources/
│   ├── application.yml                   # 应用配置
│   ├── schema-platform.sql              # 平台建表脚本
│   ├── schema-tenant.sql                # 租户建表脚本
│   └── mapper/                           # MyBatis XML
└── INTERVIEW-MVP-PLAN.html              # MVP 技术方案
```

---

## 快速开始

### 环境要求

- JDK 17+
- MySQL 8.0+
- Maven 3.8+

### 数据库初始化

```sql
-- 创建平台数据库
CREATE DATABASE platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE platform;
SOURCE schema-platform.sql;

-- 为每个租户执行（复制 schema-tenant.sql）
-- CREATE DATABASE tenant_1 ...;
-- USE tenant_1;
-- SOURCE schema-tenant.sql;
```

### 启动

```bash
cd backend_springai

# 配置环境变量
export MYSQL_PASSWORD=your-password
export JWT_SECRET=your-secret-key

# 编译运行
mvn spring-boot:run
```

服务默认运行在 `http://localhost:8080`

---

## 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `server.port` | 8080 | 服务端口 |
| `spring.datasource.url` | localhost:3306/platform | MySQL 连接 |
| `jwt.secret` | - | JWT 签名密钥 |
| `jwt.access-token-expiration` | 7200000 | accessToken 过期时间(ms) |
| `jwt.refresh-token-expiration` | 604800000 | refreshToken 过期时间(ms) |
| `python.ai.backend.url` | http://localhost:8000 | Python AI 后端地址 |
| `async.core-pool-size` | 4 | AI 分析线程池核心数 |
| `async.max-pool-size` | 8 | AI 分析线程池最大数 |
