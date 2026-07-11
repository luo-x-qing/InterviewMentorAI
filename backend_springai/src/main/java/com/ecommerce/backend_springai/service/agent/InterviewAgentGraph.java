/**
 * AI Agent调度主入口（InterviewAgentGraph）
 * 
 * 功能说明：
 * - 串联所有Agent处理节点，定义工作流执行顺序
 * - 工作流：DialogueParseNode → AnswerEvaluateNode → ReportGenNode
 * - 负责初始化AgentState并驱动整个AI分析流程
 * - 被AudioController调用，作为音频上传后的核心处理入口
 * 
 * 预留方法：
 * - run(String audioPath): 执行完整Agent工作流，返回最终报告
 */
package com.ecommerce.backend_springai.service.agent;

public class InterviewAgentGraph {
}
