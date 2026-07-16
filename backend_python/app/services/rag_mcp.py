"""
RAG-MCP 模型上下文调度层
统一封装：检索上下文组装 + LLM增强调用
隔离RAG检索逻辑与LLM生成逻辑，标准化RAG调用链路
"""
import logging
from typing import Optional
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.models.schemas import RagRetrievalResult

logger = logging.getLogger(__name__)

class RagMCP:
    def __init__(self):
        self.rag = rag_service
        self.llm = llm_service

    def build_rag_context(self, retrieval_res: RagRetrievalResult) -> str:
        """MCP专属：标准化拼接检索参考上下文"""
        if not retrieval_res.docs:
            return ""
        
        context_blocks = ["===== 面试知识库参考资料（仅依据以下内容作答）=====\n"]
        for idx, doc in enumerate(retrieval_res.docs):
            block = f"""【参考{idx+1}】
文档来源：{doc.source}
匹配相似度：{round(doc.score, 2)}
原文内容：
{doc.content}
---------------------------------------
"""
            context_blocks.append(block)
        return "\n".join(context_blocks)

    def limit_context_length(self, raw_context: str, max_chars: int = 1800) -> str:
        """MCP优化：截断超长上下文，避免超出LLM窗口"""
        if len(raw_context) <= max_chars:
            return raw_context
        logger.warning(f"知识库上下文过长，截断至{max_chars}字符")
        return raw_context[:max_chars] + "\n【内容过长，已截断】"

    def rag_enhance_evaluate(
        self,
        question: str,
        answer: str,
        use_hybrid: bool = True,
        use_rerank: bool = True
    ) -> str:
        """
        MCP对外标准接口：RAG增强面试问答评估
        完整链路：检索→上下文构建→长度截断→调用LLM评估
        """
        # 1. 执行全套RAG检索（混合检索+重排）
        retrieval_res = self.rag.retrieve_by_question(
            interview_question=question,
            use_hybrid=use_hybrid,
            use_rerank=use_rerank
        )
        logger.info(f"[MCP] 问题：{question}，检索命中文档数：{len(retrieval_res.docs)}")

        # 2. 标准化组装参考上下文
        raw_ref = self.build_rag_context(retrieval_res)
        # 3. 上下文窗口截断优化
        final_ref = self.limit_context_length(raw_ref)

        # 4. 调用LLM，传入增强上下文
        llm_response = self.llm.evaluate_answer(
            question=question,
            answer=answer,
            ref_text=final_ref
        )
        return llm_response

# 全局单例MCP实例
rag_mcp = RagMCP()
