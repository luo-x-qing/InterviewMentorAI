/**
 * ASR文本拆分对话节点（DialogueParseNode）
 * 
 * 功能说明：
 * - Agent工作流第一个处理节点
 * - 接收AsrService输出的原始转写文本（rawTranscript）
 * - 通过规则/大模型将无结构的ASR文本拆分为结构化对话列表
 * - 自动识别发言人角色（面试官interviewer / 面试者candidate）
 * - 将拆分结果写入AgentState.dialogueList
 * 
 * 预留方法：
 * - parse(AgentState state): 将原始文本拆分为对话列表
 */
package com.ecommerce.backend_springai.service.agent.nodes;

public class DialogueParseNode {
}
