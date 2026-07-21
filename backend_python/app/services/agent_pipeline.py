"""
Agent 流水线服务
编排 LLM 语音识别 -> 说话人分离 -> 回答评估 -> 报告生成 的完整流程
"""
import asyncio
import json
import logging
from typing import List


from app.models.schemas import (
    AgentState,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatus,
    DialogueItem,
    EvaluationLevel,
    EvaluationResult,
    Speaker,
)

logger = logging.getLogger(__name__)


#Python 约定俗成：def _func() 私有方法，只能类内部调用，外部禁止直接调用。
class AgentPipeline:
    """AI Agent 流水线"""

    #初始化
    def __init__(self, prompt_service=None, rag_mcp=None):
        # 延迟导入，避免循环依赖
        if prompt_service is None:
            from app.services.prompt_service import PromptService
            self.prompt_service = PromptService()
        else:
            self.prompt_service = prompt_service
            
        if rag_mcp is None:
            from app.services.rag_mcp import RagMCP
            self.rag_mcp = RagMCP()
        else:
            self.rag_mcp = rag_mcp
    
    #外部接口收到请求之后，调用执行，启动整条链路
    async def run(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        执行完整的 Agent 流水线
        
        Args:
            request: 分析请求
            
        Returns:
            分析响应
        """
        logger.info(f"========== AI Agent流水线启动 ==========")
        logger.info(f"interview_id={request.interview_id}, audio_path={request.audio_file_path}")
        
        try:
            # 初始化状态：AgentState是全局状态容器，用于在流水线各步骤之间传递数据
            state = AgentState(
                interview_id=request.interview_id,
                audio_file_path=request.audio_file_path
            )
            logger.info("[Step 1] 初始化AgentState完成")
            
            # Step 1: 语音识别 - 将音频转为文字
            logger.info("[Step 2] 开始语音识别")
            state.raw_transcript = await self.prompt_service.transcribe_interview(request.audio_file_path)
            logger.info(f"[Step 2] 语音识别完成, text_length={len(state.raw_transcript)}")
            
            # Step 2: 说话人分离 - 解析对话结构
            logger.info("[Step 3] 开始说话人分离")
            state.dialogue_list = await self._parse_dialogue(state)
            logger.info(f"[Step 3] 说话人分离完成, dialogue_count={len(state.dialogue_list)}")
            
            # Step 3: 回答评估 - 评估面试者表现
            logger.info("[Step 4] 开始回答评估")
            state.evaluation_list = await self._evaluate_answers(state)
            logger.info(f"[Step 4] 回答评估完成, evaluation_count={len(state.evaluation_list)}")
            
            # Step 4: 生成复盘报告
            logger.info("[Step 5] 开始生成复盘报告")
            state.final_report = await self._generate_report(state)
            logger.info(f"[Step 5] 复盘报告生成完成, report_length={len(state.final_report)}")
            
            # 流水线完成
            logger.info("========== AI Agent流水线完成 ==========")
            
            return AnalysisResponse(
                status=AnalysisStatus.COMPLETED,
                interview_id=request.interview_id,
                report=state.final_report,
                evaluations=state.evaluation_list
            )
            
        except Exception as e:
            logger.error(f"========== AI Agent流水线异常 ==========", exc_info=True)
            return AnalysisResponse(
                status=AnalysisStatus.FAILED,
                interview_id=request.interview_id,
                error=str(e)
            )
    
    # 说话人分离,输出结构化数组 dialogue_list
    async def _parse_dialogue(self, state: AgentState) -> List[DialogueItem]:
        """
        说话人分离
        使用 LLM 分析对话语义，区分面试官和面试者
        """
        response = await self.prompt_service.parse_dialogue(state.raw_transcript)
        
        # 解析JSON响应
        try:
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
            
            dialogue_data = json.loads(json_str)
            
            dialogue_list = []
            for item in dialogue_data:
                # 根据 speaker 字段判断身份
                if item["speaker"] == "面试官":
                    speaker = Speaker.INTERVIEWER
                else:
                    speaker = Speaker.CANDIDATE
                    
                dialogue_list.append(DialogueItem(
                    speaker=speaker,
                    content=item["content"]
                ))
            
            return dialogue_list
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"解析对话分离结果失败: {e}")
            return self._fallback_dialogue_parse(state.raw_transcript)
    
    #增加降级兜底函数_fallback_dialogue_parse，避免LLM解析失败导致整个流水线中断
    def _fallback_dialogue_parse(self, transcript: str) -> List[DialogueItem]:
        """备用的简单对话解析"""
        lines = transcript.strip().split("\n")
        dialogue_list = []
        for line in lines:
            if line.strip():
                if line.startswith("面试官"):
                    speaker = Speaker.INTERVIEWER
                else:
                    speaker = Speaker.CANDIDATE
                dialogue_list.append(DialogueItem(
                    speaker=speaker,
                    content=line.strip()
                ))
        return dialogue_list
    
    # 每组问答调用LLM进行评估，返回EvaluationResult列表
    async def _evaluate_answers(self, state: AgentState) -> List[EvaluationResult]:
        """
        回答评估
        并发评估所有问答对，利用 asyncio.gather 提升 LLM 调用吞吐
        """
        # 找出所有问答对
        pairs = []
        current_question = None
        current_answer = None
        
        for item in state.dialogue_list:
            if item.speaker == Speaker.INTERVIEWER:
                if current_question and current_answer:
                    pairs.append((current_question, current_answer))
                current_question = item.content
                current_answer = None
            else:
                current_answer = item.content
        
        if current_question and current_answer:
            pairs.append((current_question, current_answer))
        
        if not pairs:
            return []
        
        # 并发执行所有评估
        results = await asyncio.gather(
            *(self._evaluate_single(q, a) for q, a in pairs),
            return_exceptions=True
        )
        
        evaluation_list = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"并发评估任务异常: {r}")
            elif r is not None:
                evaluation_list.append(r)
        
        return evaluation_list
    
    async def _evaluate_single(self, question: str, answer: str) -> EvaluationResult:
        """评估单个问答对"""
        try:
            # 仅调用MCP层，不再直接操作rag_service
            response = await self.rag_mcp.rag_enhance_evaluate(
                question=question,
                answer=answer,
                use_hybrid=True,
                use_rerank=True
            )
            
            # 原有JSON解析逻辑完全不变
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
            data = json.loads(json_str)
            return EvaluationResult(
                question=question,
                answer=answer,
                score=data.get("score", 0),
                level=EvaluationLevel(data.get("level", "WEAK")),
                strengths=data.get("strengths", ""),
                weaknesses=data.get("weaknesses", ""),
                correction=data.get("correction", ""),
                knowledge_points=data.get("knowledge_points", "")
            )
        except Exception as e:
            logger.error(f"评估问答失败: {e}")
            return None

    
    # 把前面所有问答的评估结果汇总成一份复盘报告喂给LLM生成最终报告
    async def _generate_report(self, state: AgentState) -> str:
        """
        生成复盘报告
        """
        # 将评估结果格式化为文本
        evaluations_text = ""
        for i, eval_result in enumerate(state.evaluation_list, 1):
            evaluations_text += f"""
问题{i}: {eval_result.question}
回答: {eval_result.answer}
得分: {eval_result.score}/100
等级: {eval_result.level.value}
优点: {eval_result.strengths}
不足: {eval_result.weaknesses}
修正: {eval_result.correction}
知识点: {eval_result.knowledge_points}
---
"""
        
        # 调用 LLM 生成报告
        return await self.prompt_service.generate_report(evaluations_text)

