/**
 * 回答点评分析节点（AnswerEvaluateNode）
 * 
 * 功能说明：
 * - Agent工作流第二个处理节点
 * - 接收DialogueParseNode拆分后的对话列表
 * - 调用LlmService将对话内容发送给大模型，对面试者每条回答进行专业点评
 * - 分析维度包括：回答完整性、技术深度、表达逻辑、改进建议等
 * - 将点评结果写回AgentState供ReportGenNode使用
 * 
 * 预留方法：
 * - evaluate(AgentState state): 对对话列表进行AI点评分析
 */
package com.ecommerce.backend_springai.service.agent.nodes;

public class AnswerEvaluateNode {
}
