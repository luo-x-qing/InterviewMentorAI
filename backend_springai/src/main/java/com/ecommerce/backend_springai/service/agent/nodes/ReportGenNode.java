/**
 * 复盘报告生成节点（ReportGenNode）
 * 
 * 功能说明：
 * - Agent工作流第三个（最终）处理节点
 * - 接收AnswerEvaluateNode的点评分析结果
 * - 调用LlmService，使用AgentPromptTemplate中的报告生成提示词
 * - 生成完整的Markdown格式面试复盘报告
 * - 包含：总体评价、各题点评、改进建议、综合评分等板块
 * - 将最终报告写入AgentState.finalReport
 * 
 * 预留方法：
 * - generate(AgentState state): 生成Markdown格式复盘报告
 */
package com.ecommerce.backend_springai.service.agent.nodes;

public class ReportGenNode {
}
