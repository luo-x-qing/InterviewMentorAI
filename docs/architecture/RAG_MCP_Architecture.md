# InterviewMentorAI RAG + MCP + Skill 架构说明

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        InterviewMentorAI AI 后端架构                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │   数据源     │    │   文档转换   │    │   RAG系统    │    │  MCP层    │  │
│  │  PDF/Word    │───→│  doc_converter│───→│  分块/向量化  │───→│ 上下文调度 │  │
│  │  HTML/TXT    │    │  转换为MD    │    │  检索/重排   │    │ LLM增强   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └─────┬─────┘  │
│                                                                    │        │
│                                                                    ▼        │
│                                                          ┌──────────────┐   │
│                                                          │ agent_pipeline│   │
│                                                          │   业务流水线  │   │
│                                                          └──────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 二、核心模块说明

### 2.1 RAG系统（检索增强生成）

**作用**：通过检索知识库增强LLM的生成能力，减少幻觉，提供准确的面试评估。

**核心组件**：

| 文件 | 职责 | 说明 |
|------|------|------|
| `vector_db.py` | 向量数据库层 | SQLite + sqlite-vec，存储文本和向量 |
| `rag_service.py` | RAG业务层 | 分块、向量化、混合检索、重排序 |
| `rag_mcp.py` | MCP调度层 | 上下文组装、LLM增强调用 |
| `rag_api.py` | API接口层 | 知识库管理、检索调试接口 |

**数据流**：

```
知识库文件 → 分块 → 向量化 → 存储到SQLite
                              ↓
用户问题 → 向量化 → 混合检索 → 重排序 → 获取相关文档
                                          ↓
                              组装上下文 → 调用LLM评估
```

### 2.2 MCP层（模型上下文调度）

**作用**：统一封装「检索→上下文组装→LLM调用」链路，隔离检索与生成逻辑。

**职责**：
1. 调用 `rag_service` 执行完整检索链路（混合检索+重排）
2. 标准化拼接知识库参考上下文
3. 封装LLM调用逻辑，隔离检索与生成代码
4. 处理无检索结果降级、上下文超长截断
5. 统一日志记录和可观测性

**接口**：

```python
# 标准评估接口
rag_mcp.rag_enhance_evaluate(question, answer, use_hybrid=True, use_rerank=True)

# 上下文预览接口
rag_mcp.build_rag_context(retrieval_res)
rag_mcp.limit_context_length(raw_context)
```

### 2.3 Skill系统（文档转换）

**作用**：将不同格式的题库文档转换为RAG可读的Markdown格式。

**支持格式**：

| 格式 | 转换器 | 依赖 |
|------|--------|------|
| PDF | `pdf_to_md.py` | pdfplumber |
| Word (.docx/.doc) | `docx_to_md.py` | python-docx |
| HTML | `html_to_md.py` | beautifulsoup4 |
| TXT | `txt_to_md.py` | 无 |
| MD | 直接复制 | 无 |

**使用方式**：

```bash
# 转换单个文件
python app/services/doc_converter/convert.py \
    --input ./题库/Java面试题.pdf \
    --output ./data/rag_docs/

# 批量转换目录
python app/services/doc_converter/convert.py \
    --input ./题库/ \
    --output ./data/rag_docs/
```

**Agent执行流程**：

1. 读取 `skill.md` 了解转换规范
2. 检测文档格式
3. 调用 `convert.py` 执行转换
4. 验证转换结果
5. 运行 `rag_init.py` 入库

## 三、分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        分层架构图                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
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
│  │ - 分块/向量化      │      │ - 通用模型调用     │            │
│  │ - 混合检索/重排    │      │ - ASR/评估/报告    │            │
│  └────────────────────┘      └────────────────────┘            │
│              ↓                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2. 底层存储层（vector_db.py）                          │   │
│  │     - SQLite + sqlite-vec                               │   │
│  │     - 向量存储/检索，BM25检索                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│              ↓                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. 数据源层（data/rag_docs/）                          │   │
│  │     - 面试题库（MD格式）                                 │   │
│  │     - 标准答案/评估标准                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 四、文件结构

```
backend_python/
├── app/
│   ├── services/
│   │   ├── rag_service.py          # RAG业务层
│   │   ├── rag_mcp.py              # MCP调度层
│   │   ├── llm_client.py          # LLM通用层
│   │   ├── agent_pipeline.py       # 业务流水线
│   │   └── doc_converter/          # 文档转换Skill
│   │       ├── skill.md            # Skill说明
│   │       ├── convert.py          # 统一转换入口
│   │       └── scripts/            # 转换脚本
│   │           ├── pdf_to_md.py
│   │           ├── docx_to_md.py
│   │           ├── html_to_md.py
│   │           └── txt_to_md.py
│   ├── core/
│   │   ├── vector_db.py            # 向量数据库层
│   │   └── config.py               # 配置管理
│   ├── api/
│   │   ├── rag_api.py              # RAG API接口
│   │   └── analysis.py             # 分析API接口
│   └── models/
│       └── schemas.py              # 数据模型
├── data/
│   ├── rag_docs/                   # 知识库目录
│   │   ├── 通用评估标准.md
│   │   ├── 技术难点标准答案.md
│   │   ├── Java面试题库/
│   │   ├── Python面试题库/
│   │   └── 系统设计面试题.md
│   └── embedding_cache.json        # 向量缓存
├── scripts/
│   └── rag_init.py                 # 离线入库脚本
└── tests/
    └── test_rag_eval.py            # RAG测试脚本
```

## 五、核心流程

### 5.1 离线知识库构建

```bash
# 1. 准备题库文档（放入data/rag_docs/）
# 2. 如有非MD格式文档，先转换
python app/services/doc_converter/convert.py \
    --input ./题库/ \
    --output ./data/rag_docs/

# 3. 执行入库（分块→向量化→存储）
python scripts/rag_init.py
```

**入库流程**：

```
读取MD文件 → 分块（500字符，重叠100） → 调用DashScope生成向量
                                           ↓
                              存入SQLite（rag_docs + rag_vectors表）
```

### 5.2 在线RAG评估

```
用户问题 → rag_mcp.rag_enhance_evaluate()
                │
                ├─→ rag_service.retrieve_by_question()
                │       ├─→ 向量检索（语义相似）
                │       ├─→ BM25检索（关键词匹配）
                │       └─→ 加权融合（0.7:0.3）
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
| `/api/v1/rag/knowledge/import` | POST | 导入知识库 |
| `/api/v1/rag/retrieve` | POST | 检索调试 |
| `/api/v1/rag/chunks/preview` | POST | 分块预览 |
| `/api/v1/rag/knowledge/stats` | GET | 统计信息 |
| `/api/v1/rag/knowledge/clear` | DELETE | 清空知识库 |
| `/api/v1/rag/mcp/eval-test` | POST | MCP评估测试 |
| `/api/v1/rag/mcp/context-preview` | POST | MCP上下文预览 |

## 六、配置说明

### 6.1 环境变量（.env）

```bash
# DashScope API
DASHSCOPE_API_KEY=your_api_key

# RAG配置
EMBEDDING_MODEL=text-embedding-v3
RAG_TOP_K=3
RAG_THRESHOLD=0.6
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```

### 6.2 RAG参数调优

| 参数 | 默认值 | 说明 | 调优建议 |
|------|--------|------|----------|
| `chunk_size` | 500 | 分块大小（字符） | 越大语义越完整，但检索精度下降 |
| `chunk_overlap` | 100 | 分块重叠 | 保持上下文连贯 |
| `rag_top_k` | 3 | 返回文档数 | 影响上下文丰富度 |
| `rag_similar_threshold` | 0.6 | 相似度阈值 | 越高越严格 |
| `vector_weight` | 0.7 | 向量检索权重 | 语义检索为主 |
| `bm25_weight` | 0.3 | BM25权重 | 关键词补充 |

## 七、扩展指南

### 7.1 新增文档格式

1. 在 `doc_converter/scripts/` 创建新转换器
2. 在 `convert.py` 注册新格式
3. 更新 `skill.md` 说明

### 7.2 新增检索策略

1. 在 `vector_db.py` 实现检索方法
2. 在 `rag_service.py` 集成新策略
3. 更新 `rag_mcp.py` 调用逻辑

### 7.3 新增评估维度

1. 在 `llm_client.py` 修改评估Prompt
2. 在 `schemas.py` 扩展评估结果字段
3. 在 `agent_pipeline.py` 处理新字段

## 八、依赖说明

```txt
# RAG核心依赖
numpy==1.26
sqlite-vec==0.1.6
rank-bm25==0.2.2

# 文档转换依赖
PyPDF2>=3.0.0
pdfplumber>=0.9.0
python-docx>=1.0.0
beautifulsoup4>=4.12.0

# 可选：重排序依赖
sentence-transformers>=2.2.0
```

## 九、测试

```bash
# RAG检索测试
python tests/test_rag_eval.py

# API测试
curl -X POST http://localhost:8000/api/v1/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "Java HashMap底层原理", "top_k": 3}'

# MCP测试
curl -X POST http://localhost:8000/api/v1/rag/mcp/eval-test \
  -H "Content-Type: application/json" \
  -d '{"question": "Java HashMap底层原理", "answer": "基于数组+链表实现"}'
```
