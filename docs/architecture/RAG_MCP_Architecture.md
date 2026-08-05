# InterviewMentorAI RAG + MCP + Skill 架构说明

> 版本：v2.0（P1-P5 同步版）｜上次同步：2026-08-05
> 覆盖：结构化切面、幂等入库管道、混合检索调优、检索可观测、端到端演练

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        InterviewMentorAI AI 后端架构                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌───────┐  │
│  │   数据源     │    │  入库管道 Ingest  │    │   RAG系统    │    │ MCP层 │  │
│  │ 题库(MD/TXT) │───→│ 清洗→结构化切面    │───→│  混合检索/重排 │───→│上下文 │  │
│  │  PDF(规划中) │    │ →向量化→落库→自检  │    │  (权重+阈值)  │    │ 调度  │  │
│  └──────────────┘    └──────────────────┘    └──────────────┘    └───┬───┘  │
│                                                                      │      │
│                                                                      ▼      │
│                                                            ┌──────────────┐ │
│                                                            │ agent_pipeline││
│                                                            │   业务流水线  │ │
│                                                            └──────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 二、核心模块说明

### 2.1 入库管道（Ingest Pipeline）

**作用**：把题库从「文件」加工到「可检索」的单入口深度模块，统一走
`KnowledgeService.import_document(file_path)`，全程幂等、带自检、失败回滚。

**处理流水线**：

```
读取MD/TXT → 清洗(去噪+指纹) → 结构化切面(题目粒度) → 向量化 → 蓝绿替换落库 → 自检 → ImportReport
```

| 阶段 | 模块 | 说明 |
|------|------|------|
| 清洗 | `cleaning_service.py` | 去噪、规范化、内容指纹（MD5）去重 |
| 结构化切面 | `chunking_service.py` | 以**题目**为粒度切分，保留 `question_no`/`section`；超长答案按句/段二次切分 |
| 向量化 | `embedding_service.py` | DashScope text-embedding-v3，本地缓存 |
| 落库 | `vector_db.py` | SQLite + sqlite-vec，存储文本与向量 |
| 自检 | `knowledge_service.py` | stats 对账 + 前 2 块 BM25 抽样检索，失败则回滚该文件 |

**幂等语义**：

| 场景 | 行为 |
|------|------|
| 指纹未变 | `skipped`，不入库 |
| 指纹变更 | `updated`：新块先插入 → 按旧 doc_id 删除 → 更新指纹（蓝绿替换，整替换纳入回滚） |
| 0 题或自检失败 | 不入库 / 回滚，报告 `error` |
| 文件从磁盘消失 | `reconcile_directory()` 对账清理旧分块与指纹 |

**入库报告（ImportReport）**：识别题目数 / 分块数 / 向量数 / 去重数 / 自检结论 / 失败项。

### 2.2 RAG系统（检索增强生成）

**核心组件**：

| 文件 | 职责 |
|------|------|
| `vector_db.py` | 向量库层：向量检索、BM25 检索、混合检索（权重融合+阈值判定） |
| `rag_service.py` | RAG业务层：混合检索、默认重排、检索指标采集 |
| `reranker_service.py` | Cross-Encoder 重排，min-max 归一化 |
| `rag_mcp.py` | MCP调度层：上下文组装、LLM增强调用 |

**检索数据流**：

```
用户问题 → 向量化 → 向量检索(BM25并行) → 加权融合(0.7:0.3)
                              ↓
               阈值判定(任一路强命中放行) → 默认重排 → 采集metrics → 组装上下文 → LLM评估
```

**检索可观测（metrics）**：每次检索返回命中数、得分范围/均值、来源分布，随 API 响应暴露。

### 2.3 MCP层（模型上下文调度）

**职责**：
1. 调用 `rag_service` 执行完整检索链路（混合检索 + 默认重排）
2. 标准化拼接知识库参考上下文
3. 封装 LLM 调用逻辑，隔离检索与生成代码
4. 处理无检索结果降级、上下文超长截断（1800 字符）
5. 统一日志记录和可观测性

### 2.4 文档转换（规划中）

`doc_converter`（PDF/Word/HTML → Markdown）**尚未实现**。当前数据源仅支持
MD/TXT；`data/rag_docs/Java面试题库/` 下存在 1 份 PDF（2026-01-05 上传），
因无转换器而不可入库，待接入转换组件后补入。

## 三、分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        分层架构图                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  5. 业务流水线层（agent_pipeline.py）                   │   │
│  │     - 编排完整分析流程                                   │   │
│  │     - 仅依赖MCP层                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  4. MCP调度层（rag_mcp.py）                             │   │
│  │     - 检索+上下文组装+LLM调用                            │   │
│  │     - 统一入口，隔离检索与生成                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│              ↓                              ↓                    │
│  ┌────────────────────┐      ┌────────────────────┐            │
│  │ 3. RAG工具层       │      │ 3. LLM通用层       │            │
│  │ （rag_service.py） │      │ （llm_client.py） │            │
│  │ - 混合检索/重排    │      │ - 通用模型调用     │            │
│  │ - metrics采集      │      │ - ASR/评估/报告    │            │
│  └────────────────────┘      └────────────────────┘            │
│              ↓                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2. 底层存储层（vector_db.py）                          │   │
│  │     - SQLite + sqlite-vec                               │   │
│  │     - 向量存储/检索，BM25检索，混合检索                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│              ↓                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. 入库管道 + 数据源层                                 │   │
│  │     - knowledge_service 幂等入库（清洗/切面/自检）       │   │
│   │     - data/rag_docs/（13 份 MD 题库 + 1 份 PDF 待转换）  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 四、文件结构

```
backend_python/
├── app/
│   ├── services/
│   │   ├── knowledge_service.py     # 入库管道单入口（import/delete/reconcile/self-check）
│   │   ├── cleaning_service.py      # 清洗 + 内容指纹
│   │   ├── chunking_service.py      # 结构化切面（题目粒度）
│   │   ├── embedding_service.py     # 向量化（缓存）
│   │   ├── reranker_service.py      # 重排（min-max 归一化）
│   │   ├── rag_service.py           # RAG业务层（混合检索/重排/metrics）
│   │   ├── rag_mcp.py               # MCP调度层（含 import_document/delete_document 工具）
│   │   ├── llm_client.py            # LLM通用层
│   │   ├── prompt_service.py        # 提示词编排
│   │   └── agent_pipeline.py        # 业务流水线
│   ├── core/
│   │   ├── vector_db.py             # 向量库层（向量/BM25/混合检索）
│   │   └── config.py                # 配置管理
│   ├── api/
│   │   ├── knowledge_api.py         # 知识库生命周期接口
│   │   ├── retrieval_api.py         # 检索调试接口
│   │   ├── mcp_debug_api.py         # MCP调试接口
│   │   └── analysis.py              # 分析API接口
│   └── models/
│       └── schemas.py               # 数据模型（含 ImportReport / RetrievalMetrics）
├── data/
│   ├── rag_docs/                    # 知识库目录（13 份 MD）
│   └── embedding_cache.json         # 向量缓存
├── scripts/
│   └── rag_init.py                  # 离线入库脚本（走 import_document 单入口 + 对账）
└── tests/
    ├── test_import_pipeline.py      # 入库管道测试（幂等/替换/回滚/自检）
    ├── test_cleaning_service.py     # 清洗测试
    ├── test_chunking_service.py     # 切面测试
    ├── test_vector_db.py            # 向量库测试
    ├── test_rag_service.py          # 检索配置测试
    ├── test_reranker_service.py     # 重排测试
    ├── test_knowledge_api.py        # 知识库 API 测试
    ├── test_api_routes.py           # 分析 API 测试
    ├── rag_e2e_check.py             # 端到端演练（T5.2，伪 embedding）
    └── rag_eval_script.py           # 检索质量评估（T4.3 基线门禁）
```

## 五、核心流程

### 5.1 离线知识库构建

```bash
# 全量入库（幂等：未变更跳过，变更蓝绿替换，自检失败回滚）
python scripts/rag_init.py
```

入库管道内部流程：

```
读取文件 → 内容指纹比对
        ├─ 未变 → skipped
        └─ 变更/新增 → 清洗 → 结构化切面 → 向量化 → 新块落库
                       → 删除旧块（仅变更）→ 更新指纹 → 自检 → passed / 失败回滚
```

### 5.2 在线RAG评估

```
用户问题 → rag_mcp.rag_enhance_evaluate()
                │
                ├─→ rag_service.retrieve_by_question()
                │       ├─→ 向量检索 + BM25检索
                │       ├─→ 加权融合（vector 0.7 : bm25 0.3，BM25 归一化）
                │       ├─→ 阈值判定（任一路强命中放行，阈值 0.25）
                │       ├─→ 默认重排（RAG_USE_RERANK=true）
                │       └─→ 采集 metrics（命中数/得分/来源分布）
                │
                ├─→ rag_mcp.build_rag_context()
                │       └─→ 组装参考上下文
                │
                ├─→ rag_mcp.limit_context_length()
                │       └─→ 截断超长内容（1800字符）
                │
                └─→ llm_client.evaluate_answer()
                        └─→ LLM生成评估结果
```

### 5.3 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/knowledge/import` | POST | 导入知识库（file_paths 缺省则扫描全目录，幂等） |
| `/knowledge/reconcile` | POST | 目录对账，清理已消失题库 |
| `/knowledge/stats` | GET | 统计信息 |
| `/knowledge/clear` | DELETE | 清空知识库 |
| `/knowledge/{source}` | DELETE | 文档级删除（T3.2） |
| `/retrieval/retrieve` | POST | 检索调试（含 metrics） |
| `/retrieval/chunks/preview` | POST | 分块预览 |
| `/mcp/eval-test` | POST | MCP评估测试 |
| `/mcp/context-preview` | POST | MCP上下文预览 |
| `/api/v1/analysis/analyze` | POST | 完整面试分析 |
| `/api/v1/analysis/health` | GET | 健康检查 |

## 六、配置说明

### 6.1 环境变量（.env）

```bash
# DashScope API
DASHSCOPE_API_KEY=your_api_key

# RAG配置
EMBEDDING_MODEL=text-embedding-v3
RAG_TOP_K=3
RAG_THRESHOLD=0.25
RAG_VECTOR_WEIGHT=0.7
RAG_BM25_WEIGHT=0.3
RAG_USE_RERANK=true
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```

### 6.2 RAG参数调优

| 参数 | 默认值 | 说明 | 调优建议 |
|------|--------|------|----------|
| `chunk_size` | 500 | 分块大小（字符，结构化切面 max） | 越大语义越完整，但检索精度下降 |
| `chunk_overlap` | 100 | 分块重叠 | 保持上下文连贯 |
| `rag_top_k` | 3 | 返回文档数 | 影响上下文丰富度 |
| `rag_similar_threshold` | 0.25 | 混合检索阈值（任一通道强命中放行） | 越高越严格 |
| `rag_vector_weight` | 0.7 | 向量检索权重 | 语义检索为主 |
| `rag_bm25_weight` | 0.3 | BM25权重 | 关键词补充 |
| `rag_use_rerank` | true | 是否默认重排 | 关闭时跳过 reranker，速度更快 |

## 七、扩展指南

### 7.1 新增文档格式

1. 实现文档转换（PDF/Word/HTML → MD），当前 `doc_converter` 为规划中
2. 转换产物统一放入 `data/rag_docs/`
3. 通过 `scripts/rag_init.py` 幂等入库（入库管道不感知源格式）

### 7.2 新增检索策略

1. 在 `vector_db.py` 实现检索方法
2. 在 `rag_service.py` 集成新策略（权重/阈值入参化）
3. 更新 `rag_mcp.py` 调用逻辑

### 7.3 新增评估维度

1. 在 `llm_client.py` 修改评估Prompt
2. 在 `schemas.py` 扩展评估结果字段
3. 在 `agent_pipeline.py` 处理新字段

## 八、依赖说明

```txt
# RAG核心依赖（已使用）
numpy==1.26
sqlite-vec==0.1.6
rank-bm25==0.2.2
jieba>=0.42.1            # 中文分词

# 重排序依赖（已使用）
sentence-transformers>=3.0.0

# 文档转换依赖（规划中，doc_converter 未落地）
pdfplumber>=0.10.0
python-docx>=1.0.0
beautifulsoup4>=4.12.0
```

## 九、测试与演练

```bash
# 全量单元测试（基线：155 passed + 6 存量 error，见下）
python -m pytest tests/ -q

# RAG 端到端演练（T5.2：临时库 + 伪 embedding，12 项全 PASS）
python tests/rag_e2e_check.py

# 检索质量评估（T4.3：命中率对比 P0 空库基线 0%，跌破基线 exit 1）
python tests/rag_eval_script.py

# API测试
curl -X POST http://localhost:8000/knowledge/import \
  -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/retrieval/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "Java HashMap底层原理", "top_k": 3}'
```

> 已知存量问题：`tests/test_knowledge_e2e.py` 6 个用例报 error，源于其直接构造
> `LlmClient.__init__()` 的旧接口不匹配，与本次 RAG 改动无关，列为独立跟进项。
