/**
 * 单条对话实体（DialogueItem）
 * 
 * 功能说明：
 * - 表示面试过程中的一条对话记录
 * - 包含发言人角色（面试官/面试者）和对话内容文本
 * - 由DialogueParseNode从ASR转写文本中解析生成
 * - 作为AgentState的一部分在工作流节点间传递
 * 
 * 预留字段：
 * - role: 发言人角色（interviewer / candidate）
 * - content: 对话内容文本
 */
package com.ecommerce.backend_springai.entity;

public class DialogueItem {
}
