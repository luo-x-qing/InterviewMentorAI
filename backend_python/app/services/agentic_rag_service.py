"""
Agentic RAG 答案合成服务（LangChain 标准化组件 + LangGraph 状态图编排）

分层：
- LangChain：提供标准化检索组件（RagRetriever，BaseRetriever/Document）
- LangGraph：编排 检索→扩展→评估→（重查）→合成 的复杂流转

图结构：
    retrieve ─▶ expand ─▶ assess ─┬─(相关/超限/无法改写)─▶ finalize
                                  └─(全不相关)───────────▶ re_query ─▶ retrieve

解决两个痛点：
1. 答案被截断：检索只命中超长题目的首块（如「（1/6）」），
   expand 节点按（来源, 题号）拉取同一题的全部块并拼接成完整答案。
2. 无关候选：assess 节点用「相似度阈值 + 关键词重合」离线规则过滤低相关候选，
   全部不相关时经 re_query 二次检索（最多 max_iterations 轮）。
"""
import logging
import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, TypedDict

import jieba

# 项目目录依赖优先：langchain/langgraph 下载在 backend_python/lib（sitecustomize 兜底）
_PROJECT_LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "lib")
_PROJECT_LIB = os.path.abspath(_PROJECT_LIB)
if os.path.isdir(_PROJECT_LIB) and _PROJECT_LIB not in sys.path:
    sys.path.insert(0, _PROJECT_LIB)

from app.models.schemas import RagCandidate, RagDoc, RagAnswerResult

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import PrivateAttr

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)

# 块标题解析：{source} · 题{no} {title}（{index}/{total}）
_CHUNK_TITLE_RE = re.compile(r"^(.+?) · 题(\d+) (.+?)(?:（(\d+)/(\d+)）)?$")

# assess 相关度判定用中文停用词（问题里的虚词不计入关键词重合）
_STOPWORDS = {
    "这个", "那个", "什么", "如何", "怎么", "为什么", "哪些", "一个", "一下",
    "的", "了", "是", "在", "有", "与", "和", "或", "中", "请", "介绍", "说说",
    "解释", "简述", "详细", "简单", "区别", "原理", "吗", "呢", "吧", "啊",
}


class RagRetriever(BaseRetriever):
    """LangChain 标准化检索组件：封装混合检索 + 重排，输出 Document

    供 LangGraph 工作流的 retrieve 节点调用；外部亦可作为标准 Retriever 复用。
    """

    top_k: int = 6
    _rag: Any = PrivateAttr()

    def __init__(self, rag_service, top_k: int = 6):
        super().__init__(top_k=top_k)
        self._rag = rag_service

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        res = await self._rag.retrieve_by_question(query, use_hybrid=True, use_rerank=True)
        return [
            Document(
                page_content=d.content,
                metadata={
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "source": d.source,
                    "question_no": d.question_no,
                    "section": d.section,
                    "score": d.score,
                },
            )
            for d in res.docs
        ]

    def _get_relevant_documents(self, query: str) -> List[Document]:  # pragma: no cover - 仅兼容同步调用
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._aget_relevant_documents(query))


def parse_chunk_title(title: str) -> Optional[dict]:
    """解析块标题 → {source, question_no, title, index, total}；无法解析返回 None"""
    m = _CHUNK_TITLE_RE.match(title)
    if not m:
        return None
    source, qno, qtitle, index, total = m.groups()
    return {
        "source": source,
        "question_no": qno,
        "title": qtitle,
        "index": int(index) if index else None,
        "total": int(total) if total else None,
    }


class _State(TypedDict, total=False):
    question: str
    last_query: str
    docs: List[RagDoc]
    candidates: List[dict]
    iteration: int
    log: List[str]
    result: RagAnswerResult


class AgenticRagService:
    """Agentic RAG：langgraph 状态图编排 检索→扩展→评估→（重查）→合成"""

    def __init__(
        self,
        retrieve_fn: Optional[Callable[[str], Any]] = None,
        question_chunks_fn: Optional[Callable[[str, str], List[RagDoc]]] = None,
        max_iterations: int = 2,
        related_score_threshold: float = 0.6,
        min_keyword_hits: int = 1,
        stitch_overlap: int = 60,
    ):
        if retrieve_fn is None:
            from app.services.rag_service import RagService
            self._rag = RagService(top_k=6, threshold=0.25)
            self._retriever = RagRetriever(self._rag)
            retrieve_fn = self._retrieve_default
        if question_chunks_fn is None:
            self._question_chunks_fn = self._question_chunks_default
        else:
            self._question_chunks_fn = question_chunks_fn
        self._retrieve_fn = retrieve_fn
        self.max_iterations = max_iterations
        self.related_score_threshold = related_score_threshold
        self.min_keyword_hits = min_keyword_hits
        self.stitch_overlap = stitch_overlap
        self._graph = self._build_graph()

    # ---------- 默认依赖实现 ----------

    async def _retrieve_default(self, query: str) -> List[RagDoc]:
        """经 LangChain 标准化检索组件（RagRetriever）取回候选块"""
        docs = await self._retriever.ainvoke(query)
        return [
            RagDoc(
                doc_id=int(d.metadata.get("doc_id", 0)),
                title=d.metadata.get("title", ""),
                content=d.page_content,
                source=d.metadata.get("source", ""),
                question_no=d.metadata.get("question_no", ""),
                section=d.metadata.get("section", ""),
                score=float(d.metadata.get("score", 0.0)),
            )
            for d in docs
        ]

    def _question_chunks_default(self, source: str, question_no: str) -> List[RagDoc]:
        """从向量库拉取同一题的全部块（按 doc_id 有序）"""
        rows = self._rag.vector_db.conn.execute(
            "SELECT doc_id, title, content FROM rag_docs WHERE source=? AND question_no=? ORDER BY doc_id",
            (source, question_no),
        ).fetchall()
        return [
            RagDoc(doc_id=r[0], title=r[1], content=r[2], source=source, question_no=question_no)
            for r in rows
        ]

    # ---------- 图节点 ----------

    async def _retrieve(self, state: _State) -> dict:
        query = state.get("last_query", state["question"])
        docs = await self._retrieve_fn(query)
        state["log"].append(f"[retrieve] 检索「{query}」命中 {len(docs)} 块")
        return {"docs": docs}

    def _expand(self, state: _State) -> dict:
        """按（来源, 题号）聚合同一题的块，拼接为完整答案"""
        groups: Dict[tuple, dict] = {}
        for doc in state["docs"]:
            key = (doc.source, doc.question_no)
            if not doc.question_no:
                continue
            if key not in groups:
                groups[key] = {"blocks": [], "score": doc.score, "title": doc.title}
            g = groups[key]
            g["blocks"].append(doc)
            g["score"] = max(g["score"], doc.score)
        candidates = []
        for (source, qno), g in groups.items():
            parsed = parse_chunk_title(g["title"])
            blocks = self._question_chunks_fn(source, qno) or g["blocks"]
            ordered = self._order_blocks(blocks)
            full_answer = self._stitch([b.content for b in ordered])
            candidates.append({
                "source": source,
                "question_no": qno,
                "title": parsed["title"] if parsed else g["title"],
                "score": g["score"],
                "full_answer": full_answer,
                "related": False,
            })
        state["log"].append(f"[expand] 聚合成 {len(candidates)} 个候选题目")
        return {"candidates": candidates}

    def _assess(self, state: _State) -> dict:
        """离线规则相关性判定：相似度达标 且 与问题共享关键词"""
        for c in state["candidates"]:
            c["related"] = self._is_related(state["question"], c)
        n_related = sum(1 for c in state["candidates"] if c["related"])
        state["log"].append(f"[assess] 相关候选 {n_related}/{len(state['candidates'])}")
        return {}

    def _re_query(self, state: _State) -> dict:
        """改写问题（核心关键词）后二次检索"""
        new_query = self._rewrite(state["question"])
        state["log"].append(f"[re_query] 改写为「{new_query}」")
        return {"last_query": new_query, "iteration": state["iteration"] + 1}

    def _finalize(self, state: _State) -> dict:
        candidates = [
            RagCandidate(
                source=c["source"],
                question_no=c["question_no"],
                title=c["title"],
                score=c["score"],
                full_answer=c["full_answer"],
                related=c["related"],
            )
            for c in state["candidates"]
        ]
        candidates.sort(key=lambda c: (c.related, c.score), reverse=True)
        status = "answered" if any(c.related for c in candidates) else "no_match"
        return {"result": RagAnswerResult(
            question=state["question"],
            candidates=candidates,
            status=status,
            iterations=state["iteration"] + 1,
            log=state["log"],
        )}

    # ---------- 图路由 ----------

    def _route(self, state: _State) -> str:
        if state["iteration"] >= self.max_iterations:
            return "finalize"
        if any(c["related"] for c in state["candidates"]):
            return "finalize"
        if self._rewrite(state["question"]) == state["question"]:
            return "finalize"
        return "re_query"

    # ---------- 规则工具 ----------

    @staticmethod
    def _order_blocks(blocks: List[RagDoc]) -> List[RagDoc]:
        """块按标题中的块序号排序；解析失败按 doc_id 兜底"""
        def key(b: RagDoc):
            p = parse_chunk_title(b.title)
            if p and p["index"]:
                return (0, p["index"])
            return (1, b.doc_id)
        return sorted(blocks, key=key)

    def _stitch(self, contents: List[str]) -> str:
        """按块顺序拼接，去掉相邻块之间的公共重叠尾巴"""
        if not contents:
            return ""
        text = contents[0]
        limit = self.stitch_overlap
        for part in contents[1:]:
            max_overlap = min(limit, len(text), len(part))
            k = 0
            for i in range(max_overlap, 0, -1):
                if text[-i:] == part[:i]:
                    k = i
                    break
            if k:
                part = part[k:].lstrip("\n")
            text += "\n" + part
        return text.strip()

    def _is_related(self, question: str, candidate: dict) -> bool:
        if candidate["score"] < self.related_score_threshold:
            return False
        words = self._keywords(question)
        if not words:
            return False
        hits = sum(1 for w in words if w in candidate["full_answer"])
        return hits >= self.min_keyword_hits

    @staticmethod
    def _keywords(text: str) -> List[str]:
        return [w.strip() for w in jieba.cut(text)
                if w.strip() and w.strip() not in _STOPWORDS and not w.strip().isdigit()]

    def _rewrite(self, question: str) -> str:
        """问题改写：抽取核心关键词作为检索词；无改进时原样返回"""
        words = self._keywords(question)
        if not words:
            return question
        return " ".join(words)

    # ---------- 图构建 ----------

    def _build_graph(self):
        g = StateGraph(_State)
        g.add_node("retrieve", self._retrieve)
        g.add_node("expand", self._expand)
        g.add_node("assess", self._assess)
        g.add_node("re_query", self._re_query)
        g.add_node("finalize", self._finalize)
        g.add_edge(START, "retrieve")
        g.add_edge("retrieve", "expand")
        g.add_edge("expand", "assess")
        g.add_conditional_edges("assess", self._route, {
            "re_query": "re_query", "finalize": "finalize",
        })
        g.add_edge("re_query", "retrieve")
        g.add_edge("finalize", END)
        return g.compile()

    # ---------- 对外入口 ----------

    async def answer(self, question: str) -> RagAnswerResult:
        """图工作流执行入口：检索→扩展→评估→（重查）→合成"""
        state = await self._graph.ainvoke({
            "question": question,
            "last_query": question,
            "iteration": 0,
            "log": [],
            "docs": [],
            "candidates": [],
        })
        return state["result"]

    def close(self):
        """清理资源"""
        if getattr(self, "_rag", None) is not None:
            self._rag.close()
