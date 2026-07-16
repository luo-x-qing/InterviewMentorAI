/**
 * 单条对话实体（DialogueItem）
 * 
 * 功能说明：
 * - 表示面试过程中的一条对话记录
 * - 包含说话人角色（面试官/候选人）和对话内容文本
 * - 由DialogueParseNode从ASR转写文本中解析得出
 * 
 * 字段说明：
 * - speaker: 说话人角色，INTERVIEWER / CANDIDATE
 * - content: 对话内容文本
 * - startTimeMs: 对话开始时间戳（毫秒）
 * - endTimeMs: 对话结束时间戳（毫秒）
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
     * 说话人角色枚举
     * INTERVIEWER: 面试官
     * CANDIDATE: 候选人
     */
    public enum Speaker {
        INTERVIEWER,  // 面试官
        CANDIDATE     // 候选人
    }
    
    /**
     * 说话人角色
     * 取值为 "INTERVIEWER" 或 "CANDIDATE"
     */
    private Speaker speaker;
    
    /**
     * 对话内容文本
     * 由ASR识别后经过格式化的文本
     */
    private String content;
    
    /**
     * 对话开始时间戳（毫秒）
     * 从音频文件中提取的相对时间
     */
    private Long startTimeMs;
    
    /**
     * 对话结束时间戳（毫秒）
     * 从音频文件中提取的相对时间
     */
    private Long endTimeMs;
}
