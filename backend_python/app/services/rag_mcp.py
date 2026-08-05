"""
RAG-MCP 模型上下文调度层
统一封装：检索上下文组装 + LLM增强调用 + Agent 知识库工具
隔离RAG检索逻辑与LLM生成逻辑，标准化RAG调用链路
"""
import logging
from typing import Optional
from app.models.schemas import RagRetrievalResult, ImportReport

logger = logging.getLogger(__name__)

class RagMCP:
    def __init__(self, rag_service=None, prompt_service=None, knowledge_service=None):
        # 延迟导入，避免循环依赖
        if rag_service is None:
            from app.services.rag_service import RagService
            self.rag = RagService()
        else:
            self.rag = rag_service
            
        if prompt_service is None:
            from app.services.prompt_service import PromptService
            self.prompt_service = PromptService()
        else:
            self.prompt_service = prompt_service

        if knowledge_service is None:
            from app.services.knowledge_service import KnowledgeService
            self._knowledge_service = KnowledgeService()
        else:
            self._knowledge_service = knowledge_service

    def import_document(self, file_path: str, max_chunk_size: int = None) -> ImportReport:
        """Agent 工具：拖入题库入库（清洗→解析→切面→向量化→落库→自检）"""
        return self._knowledge_service.import_document(file_path, max_chunk_size)

    def delete_document(self, source: str) -> bool:
        """Agent 工具：删除某来源题库的全部分块与指纹"""
        return self._knowledge_service.delete_document(source)

    def reconcile_directory(self, root: str = None) -> int:
        """Agent 工具：目录对账，清理已消失文件的旧分块"""
        return self._knowledge_service.reconcile_directory(root)

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

    async def rag_enhance_evaluate(
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
        retrieval_res = await self.rag.retrieve_by_question(
            interview_question=question,
            use_hybrid=use_hybrid,
            use_rerank=use_rerank
        )
        logger.info(f"[MCP] 问题：{question}，检索命中文档数：{len(retrieval_res.docs)}")

        # 2. 标准化组装参考上下文
        raw_ref = self.build_rag_context(retrieval_res)
        # 3. 上下文窗口截断优化
        final_ref = self.limit_context_length(raw_ref)

        # 4. 调用PromptService，传入增强上下文
        llm_response = await self.prompt_service.evaluate_answer(
            question=question,
            answer=answer,
            ref_text=final_ref
        )
        return llm_response

