/**
 * Agent提示词模板类（AgentPromptTemplate）
 * 
 * 功能说明：
 * - 集中管理AI Agent各节点使用的Prompt提示词模板
 * - 避免提示词硬编码在业务逻辑中，便于统一维护和优化
 * - 支持变量占位符替换（如{dialogue}、{transcript}等）
 * 
 * 预留常量：
 * - DIALOGUE_PARSE_PROMPT: 对话拆分提示词模板
 * - ANSWER_EVALUATE_PROMPT: 回答点评提示词模板
 * - REPORT_GENERATE_PROMPT: 复盘报告生成提示词模板
 */
package com.ecommerce.backend_springai.service.agent.prompts;

public class AgentPromptTemplate {
}
