/**
 * 面试完整记录实体（InterviewRecord）
 * 
 * 功能说明：
 * - 对应数据库面试记录表，持久化存储单次面试的完整数据
 * - 包含音频文件路径、ASR转写文本、对话列表、AI生成的复盘报告
 * - 由InterviewRecordService负责CRUD操作
 * 
 * 预留字段：
 * - id: 主键ID
 * - audioPath: 音频文件存储路径
 * - rawTranscript: ASR语音识别原始文本
 * - dialogueJson: 对话列表JSON字符串
 * - reportMarkdown: AI生成的复盘报告（Markdown格式）
 * - createdAt: 创建时间
 */
package com.ecommerce.backend_springai.entity;

public class InterviewRecord {
}
