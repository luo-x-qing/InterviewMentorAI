# 回收站（Recycle Bin）

> 存放已被新方案取代的陈旧设计/架构文档。**不删除，仅归档保留**，以便追溯历史决策。

## 归档说明

- **归档时间**：2026-09-05
- **归档原因**：项目由「Java/Python 双后端」架构转向「全 Agent 驱动」架构（多 Agent 协作 + 机器学习 + RAG），相关旧架构设计文档统一移入本目录。
- **新方案入口**：`docs/architecture/AGENT-ARCHITECTURE.md`

## 目录结构

```
recycle_bin/
├── README.md                              # 本说明文件
├── architecture/
│   ├── architecture.md                    # 旧整体架构（Java+Python 双后端）
│   └── RAG_MCP_Architecture.md            # 旧 RAG + MCP 架构
├── plans/
│   ├── INTERVIEW-MVP-PLAN.html            # 旧 MVP 技术方案（Java 核心）
│   ├── interview-assistant.html           # 旧产品原型
│   └── rag-optimization-roadmap.html      # 旧 RAG 优化路线
└── vision/
    ├── MINDMAP.html                       # 旧架构思维导图（可视化）
    └── MINDMAP.md                         # 旧架构思维导图（文本）
```

## 说明

> 原 Java 业务后端代码（`backend_springai/`）已随架构迁移删除，仅保留上述设计文档作历史追溯。现行代码位于 `backend_python/`（Python 单后端）。若需回退查看旧架构如何运转，参见上方文档。
