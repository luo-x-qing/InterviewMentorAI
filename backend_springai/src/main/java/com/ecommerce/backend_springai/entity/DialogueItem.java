/**
 * 单条对话实体（DialogueItem）
 * 
 * 功能说明：
 * - 表示面试过程中的一条对话记录
 * - 包含发言人角色（面试官/面试者）和对话内容文本
 * - 由DialogueParseNode从ASR转写文本中解析生成
 * - 作为AgentState的一部分在工作流节点间传递
 * 
 * 字段说明：
 * - speaker: 发言人角色（INTERVIEWER / CANDIDATE）
 * - content: 对话内容文本
 * - startTimeMs: 对话起始时间（毫秒）
 * - endTimeMs: 对话结束时间（毫秒）
 */
package com.ecommerce.backend_springai.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DialogueItem {
    
    /**
     * 发言人角色枚举
     * INTERVIEWER: 面试官
     * CANDIDATE: 面试者/候选人
     */
    public enum Speaker {
        INTERVIEWER,  // 面试官
        CANDIDATE     // 面试者
    }
    
    /**
     * 发言人角色
     * 值为 "INTERVIEWER" 或 "CANDIDATE"
     */
    private Speaker speaker;
    
    /**
     * 对话内容文本
     * 包含完整的发言内容
     */
    private String content;
    
    /**
     * 对话起始时间（毫秒）
     * 用于在音频中定位该段对话
     */
    private Long startTimeMs;
    
    /**
     * 对话结束时间（毫秒）
     * 用于在音频中定位该段对话
     */
    private Long endTimeMs;
}
