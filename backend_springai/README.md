# InterviewMentorAI — Java 业务后端

> Spring Boot 3.2.5 + Java 17 业务后端

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Java | 17 | 运行环境 |
| Spring Boot | 3.2.5 | Web 框架 |
| Spring Security | 6.x | JWT 认证 |
| MyBatis-Plus | 3.5.6 | ORM + 分页 |
| MySQL | 8.0+ | 数据库 |
| JWT (jjwt) | 0.12.5 | Token 生成/解析 |
| WebSocket (STOMP+SockJS) | - | 实时推送 |
| Lombok | - | 简化实体 |

## 项目结构

```
backend_springai/
├── pom.xml
└── src/main/java/com/interview/mentor/
    ├── InterviewMentorApplication.java
    ├── config/           # SecurityConfig / MyBatisPlusConfig / CorsConfig
    ├── security/         # JWT 认证 (Provider / Filter / UserDetailsService / AuthUser)
    ├── controller/       # 5 个 Controller (Auth / User / Interview / Report / Knowledge)
    ├── service/          # 5 个 Service 接口
    ├── service/impl/     # 5 个 Service 实现 + AiAnalysisRunner
    ├── entity/           # 7 个实体
    ├── entity/dto/       # 请求/响应 DTO
    ├── mapper/           # 6 个 Mapper 接口
    ├── client/           # Python AI 后端调用
    ├── websocket/        # STOMP 推送服务
    ├── async/            # 异步线程池
    └── exception/        # 统一异常处理
```

## API 端点（23 个）

| 模块 | 端点数 | 路径前缀 | 说明 |
|------|--------|----------|------|
| Auth | 3 | `/auth/*` | 登录/注册/刷新Token |
| User | 3 | `/user/*` | 个人信息查看/修改/改密码 |
| Interview | 5 | `/interview/*` | 创建面试/上传音频/详情/列表 |
| Report | 3 | `/report/*` | 评估列表/报告详情/报告列表 |
| Knowledge | 6 | `/knowledge/*` | 知识库CRUD/搜索 |
| Stats | 3 | `/report/*` | 统计/日志/健康检查 |

## 数据库（7 张表）

`sys_user`, `t_interview`, `t_evaluation`, `t_report`, `t_knowledge_document`, `audit_log`, `evaluation_template`

## 快速开始

```bash
# 初始化数据库
mysql -u root -p -e "CREATE DATABASE interview_mentor DEFAULT CHARSET utf8mb4;"
mysql -u root -p interview_mentor < src/main/resources/schema.sql

# 配置环境变量
export MYSQL_PASSWORD=your-password
export JWT_SECRET=your-secret-key

# 启动
mvn spring-boot:run
```
