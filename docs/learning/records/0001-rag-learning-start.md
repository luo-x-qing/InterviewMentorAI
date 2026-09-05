# RAG学习起点

> **2026-09-05 现状更新**：本记录为历史起点快照。当前项目已迁移为 Python 单后端（多 Agent + RAG + MCP），下方「当前项目状态」为当时（2026-07）情况。RAG 已落地于 `backend_python`（混合检索 + 重排 + Agentic RAG），详见 [Agent 架构设计](../../architecture/AGENT-ARCHITECTURE.md)。

用户希望学习RAG（检索增强生成）技术，并应用于InterviewMentorAI项目。这是一个中长期学习目标，需要先掌握通用RAG原理，再应用于具体项目。

用户选择了"两者都学"的学习路径，表明他们希望：
1. 掌握RAG的通用原理和实现方法
2. 将RAG技术集成到现有的InterviewMentorAI项目中

当前项目状态（历史快照，2026-07）：
- 纯LLM推理模式，没有RAG功能
- 双后端架构（Java + Python）
- 需要保持现有架构不变，逐步添加RAG功能

学习重点：
- RAG核心概念和工作流程
- 文档分块和向量嵌入技术
- 检索策略和优化方法
- 在InterviewMentorAI项目中的具体实现