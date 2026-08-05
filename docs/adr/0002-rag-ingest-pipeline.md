---
status: accepted
---

# RAG 入库与检索管道：题目级结构化模型 + 单入口深度模块 + 幂等对账 + 自检闭环

## 背景

P0 基线（2026-08-05）证实：`interview.db` 中 `rag_docs` 为 0 行，知识库从未入库，RAG 检索召回率 0%。入库仅靠手动脚本 `rag_init.py` / `POST /knowledge/import`，固定 500 字符切分会把一道题拦腰切断；检索接口（`use_rerank=False`）与评估链路（`use_rerank=True`）行为不一致；`RAG_THRESHOLD=0.01` 近似不过滤，混合检索权重 0.7/0.3 硬编码。

## 决策

本次目标架构一次性定死以下五项，作为后续 P1-P5 实现的锚点，防止后期漂移：

1. **题目为一等概念**。入库、清洗、切面、检索、评估均以「一道完整题目的 Q-A」为基本单位，而非任意文本块。解析出结构化题目（问题 / 标准答案 / 评估要点 + 溯源元数据）；检索命中即返回完整题目作为参考上下文。

2. **单入口深度模块**。入库收敛为单一接口 `import_document(path) -> ImportReport`，内部编排 清洗 → 解析 → 题目级切面 → 向量化 → 落库 → 自检。HTTP 接口与 Agent 内部调用共用同一入口；**否决 watchdog 目录监听**（引入常驻进程，与测试/部署并发冲突），Agent 自治通过调用该入口实现。

3. **幂等 + 生命周期**。`rag_documents` 文档级元数据表记录文件指纹与状态；重复导入跳过、变更文件替换其分块、目录对账删除已消失文件的旧分块。**否决**仅指纹去重（旧分块残留）与全量重建（大题库成本高）。

4. **检索统一默认行为**。检索接口与评估链路统一 `use_hybrid=True` + `use_rerank=True`；向量/BM25 权重、阈值、top_k 全部入 config 可调。**否决**接口默认关重排的两套行为并存。

5. **自检闭环**。入库后自动执行：stats 对账（题目/分块/向量数）+ 抽样检索自测；不一致则回滚该文件并输出错误入库报告。Agent 以「入库 + 自证」闭环运行，失败不静默。

## 后果

- 数据模型变更：新增 `rag_documents` 元数据表；`rag_docs` 增加题目级字段（question_no / section）；`rag_vectors` 不变。
- 分块策略不再固定 500 字符，改以题目为粒度（超长答案按句/段边界二次切分）。
- 新增 `cleaning_service`（清洗 + 结构解析 + 指纹）；改造 `chunking_service`、`knowledge_service`、`vector_db`、`rag_mcp`、`knowledge_api`、`config`。
- 现有 `tests/rag_eval_script.py` 的检索语义随之变化，需同步；存量 103 用例保持通过。
- 边界不变：不触碰 Java 后端 `t_knowledge_document` CRUD、不换底层模型、不改前端、不引入多租户。
