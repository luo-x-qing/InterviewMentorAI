/**
 * AI Agent全局状态载体（AgentState）
 * 
 * 功能说明：
 * - 作为AI Agent工作流的全局上下文数据容器
 * - 在DialogueParseNode → AnswerEvaluateNode → ReportGenNode三个节点间传递数据
 * - 使用@Data注解自动生成getter/setter方法
 * 
 * 字段说明：
 * - rawTranscript: ASR语音识别输出的原始完整文本
 * - dialogueList: 经DialogueParseNode拆分后的对话列表（区分面试官/面试者）
 * - finalReport: 经ReportGenNode生成的最终Markdown格式复盘报告
 */
package com.ecommerce.backend_springai.service.agent;

import com.ecommerce.backend_springai.entity.DialogueItem;
import lombok.Data;
import java.util.ArrayList;
import java.util.List;

/**
 * AI Agent全局状态
 * 在多个节点之间传递上下文数据
 */
@Data
public class AgentState {
    // ASR识别原始完整文本
    private String rawTranscript;
    // 拆分后的对话列表【面试官/面试者区分】
    private List<DialogueItem> dialogueList = new ArrayList<>();
    // AI最终输出完整复盘Markdown报告
    private String finalReport;
}
