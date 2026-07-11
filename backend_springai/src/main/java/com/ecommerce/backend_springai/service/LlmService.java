/**
 * 大模型HTTP调用服务（LlmService）
 * 
 * 功能说明：
 * - 封装WebClient调用大模型API（如通义千问、GPT等）
 * - 负责发送Prompt提示词并接收大模型返回的分析结果
 * - 被AnswerEvaluateNode和ReportGenNode调用，执行AI分析任务
 * - 依赖WebClientConfig中配置的WebClient Bean
 * 
 * 预留方法：
 * - chat(String prompt): 发送Prompt获取大模型文本回复
 * - chatStream(String prompt): 流式调用大模型（SSE）
 */
package com.ecommerce.backend_springai.service;

public class LlmService {
}
