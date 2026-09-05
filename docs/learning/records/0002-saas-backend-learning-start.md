# Python Agent 后端学习起点（原 Java 后端学习）

> **2026-09-05 更新**：项目已由「Java/Python 双后端」迁移至「全 Agent 驱动的 Python 单后端」，`backend_springai/`（Java）代码已删除归档。本学习记录已由「学习 Java 后端设计逻辑」调整为「学习 Python Agent 后端设计逻辑」，Java 相关内容仅作历史留档。

用户希望学习 InterviewMentorAI 项目的后端设计逻辑。这是一个系统性学习目标，需要从架构概念到具体实现逐步掌握。

## 学习背景（现状 v3.1）

当前项目已完成后端重构，采用纯 Python 单后端承载全部能力：
- Python FastAPI 单后端（业务 + AI + Agent 编排）
- 多 Agent 协作（LangGraph 状态图：ASR / 说话人分离 / RAG检索 / 评估 / 报告）
- RAG 知识库检索（Embedding + BM25 + Reranker）
- MCP 工具层（auth / interview / report / knowledge / coach）
- Coach Agent（AI 辅助面试：会话状态机 + 画像 + 难度自适应）
- SQLite 单库（原 MySQL schema 等价迁移）
- WebSocket 原生实时推送（替代原 STOMP）

> 历史：原 Java 后端（Spring Boot 3.2.5 + Java 17，JWT 认证、MyBatis-Plus、STOMP 推送）已迁移至回收站，不再承担运行职责。完整说明见 [回收站](../../recycle_bin/README.md)。

## 学习目标

1. 理解 FastAPI 项目结构与业务分层
2. 理解多 Agent 状态图（LangGraph）编排原理
3. 理解 RAG 检索链路（向量 / BM25 / 重排）
4. 掌握 MCP 工具层的设计与调用约定
5. 掌握 Coach 会话状态机与画像更新
6. 能够独立实现新 Agent 并接入编排层

## 学习路径

### 第一阶段：架构概念
- FastAPI 项目结构与单后端定位
- 全 Agent 架构总览（多 Agent 协作 / ML / RAG / MCP）

### 第二阶段：多 Agent 编排
- LangGraph 状态图与 Agent 状态传递
- 每个 Agent 的职责与调用边界

### 第三阶段：RAG 与知识库
- 向量检索 / BM25 混合检索 / Reranker
- 入库管道与离线测试

### 第四阶段：MCP 工具层
- 工具协议与 `call_tool` 调用约定
- 工具注册与权限边界

### 第五阶段：Coach 会话
- 会话状态机与难度自适应
- 画像更新与选题策略

### 第六阶段：总结与实战
- 整体架构回顾与新增 Agent 实战练习

## 相关资源

- [Agent 架构设计（现行）](../../architecture/AGENT-ARCHITECTURE.md)
- [Python 后端架构](../../../backend_python/README.md)
- [MVP 技术方案（已归档）](../../recycle_bin/plans/INTERVIEW-MVP-PLAN.html)
- [RAG 学习课程](./0001-rag-learning-start.md)
