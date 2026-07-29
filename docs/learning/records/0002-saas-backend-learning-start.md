# Java 业务后端学习起点

> **2026-07-29 更新**：项目已从 SaaS 多租户架构简化为纯个人用户模式，移除了所有多租户/RBAC/Subscription 概念。本学习记录已同步调整。

用户希望学习 InterviewMentorAI 项目的 Java 后端设计逻辑。这是一个系统性学习目标，需要从架构概念到具体实现逐步掌握。

## 学习背景

当前项目已完成 Java 后端的 Phase 1-3 重建：
- Spring Boot 3.2.5 + Java 17
- 单库单 schema 纯个人模式（无多租户）
- JWT 双 Token 认证
- 5 个业务模块（23 个 API）
- 异步调用 Python AI 后端
- STOMP WebSocket 实时推送

## 学习目标

1. 理解 Spring Boot 3 + Java 17 的基础设施搭建
2. 理解 JWT 双 Token 认证的工作原理
3. 理解 MyBatis-Plus ORM 和数据库设计
4. 掌握异步调用和 WebSocket 推送机制
5. 理解 RESTful API 设计和 Controller 层实现
6. 能够独立实现业务逻辑模块
7. 能够串联整体架构，进行实战开发

## 学习路径

### 第一阶段：架构概念（课程 1-2）
- Spring Boot 3 + Java 17 基础设施
- 单库单 schema 设计模式

### 第二阶段：安全（课程 3-4）
- JWT 双 Token 认证
- Spring Security 集成

### 第三阶段：数据与持久化（课程 5）
- MyBatis-Plus 与数据库设计

### 第四阶段：异步与实时（课程 6）
- 异步调用与 WebSocket 推送

### 第五阶段：API 与业务（课程 7-8）
- RESTful API 设计与 Controller 层
- 业务逻辑实现（核心模块串联）

### 第六阶段：总结与实战（课程 9）
- 整体架构回顾与实战练习

## 相关资源

- [Java 后端架构文档](../../../backend_springai/README.md)
- [MVP 技术方案](../../plans/INTERVIEW-MVP-PLAN.html)
- [RAG 学习课程](./0001-rag-learning-start.md)
