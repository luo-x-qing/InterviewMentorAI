# InterviewMentorAI 文档中心

## 目录结构

```
docs/
├── README.md                           # 本文档索引
├── architecture/                       # 架构设计
│   └── AGENT-ARCHITECTURE.md           # ★ 现行：全 Agent 架构（多Agent协作/ML/RAG/MCP工具层/Coach模块）
├── recycle_bin/                        # ★ 回收站（陈旧的 Java/Python 双后端设计文档归档）
│   ├── README.md                       # 回收站说明
│   ├── architecture/                   # 旧架构设计（architecture.md / RAG_MCP_Architecture.md）
│   ├── plans/                          # 旧技术方案（MVP / 原型 / RAG 路线图）
│   └── vision/                         # 旧架构思维导图
├── adr/                                # 架构决策记录
│   └── 0001-tenant-isolation-row-level.md (已废弃)
├── api/                                # API 接口文档
│   └── api_document.md
├── reports/                            # 项目报告 & 评审
│   └── reviews/                        # 架构评审报告
├── learning/                           # 学习资料
│   ├── MISSION.md                      # 学习目标
│   ├── NOTES.md                        # 学习笔记
│   ├── RESOURCES.md                    # 学习资源
│   ├── interview_intro.md              # 面试讲解文稿
│   └── records/                        # 学习记录
├── dev/                                # 开发日志
│   ├── DEVELOPMENT-LOGA.md             # 全迭代开发日志
│   └── teaching-workspace-README.md    # 教学工作区说明
```

## 相关子项目文档

| 项目 | 文档 |
|------|------|
| Flutter 移动端 | [前端架构](../frontend_flutter/README.md) |
| Python Agent 后端 | [Python 后端架构](../backend_python/README.md) |
| 主项目文档 | [根 README](../README.md) |

## 现行架构 vs 旧架构

| 文档 | 状态 | 说明 |
|------|------|------|
| [架构设计](architecture/AGENT-ARCHITECTURE.md) | **现行** | 全 Agent 驱动（v3.0），无 Java |
| [回收站说明](recycle_bin/README.md) | 归档 | 旧 Java/Python 双后端方案（v2.x），不删除仅归档 |