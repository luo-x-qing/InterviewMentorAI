/**
 * 面试完整记录实体（InterviewRecord）
 * 
 * 功能说明：
 * - 对应数据库面试记录表，持久化存储单次面试的完整数据
 * - 包含音频文件路径、ASR转写文本、对话列表、AI生成的复盘报告
 * - 由InterviewRecordService负责CRUD操作
 * 
 * 字段说明：
 * - id: 主键ID（自增）
 * - audioFileId: 音频文件唯一标识（UUID）
 * - audioFilePath: 音频文件存储路径
 * - durationSeconds: 面试时长（秒）
 * - status: 流水线处理状态
 * - rawTranscript: ASR语音识别原始文本
 * - dialogueJson: 对话列表JSON字符串
 * - reportJson: AI生成的复盘报告JSON
 * - createdAt: 创建时间
 * - updatedAt: 更新时间
 */
package com.ecommerce.backend_springai.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("interview_record")
public class InterviewRecord {
    
    /**
     * 流水线处理状态枚举
     */
    public enum Status {
        PROCESSING,           // 流水线执行中
        ASR_COMPLETED,        // 语音转文字完成
        DIALOGUE_PARSED,      // 说话人分离完成
        EVALUATION_COMPLETED, // 回答评估完成
        COMPLETED,            // 复盘报告生成完毕
        FAILED                // 执行失败
    }
    
    /**
     * 主键ID（自增）
     */
    @TableId(type = IdType.AUTO)
    private Long id;
    
    /**
     * 音频文件唯一标识（UUID）
     * 用于前端查询和文件关联
     */
    private String audioFileId;
    
    /**
     * 音频文件存储路径
     * 服务端本地存储的绝对路径
     */
    private String audioFilePath;
    
    /**
     * 面试时长（秒）
     * 从音频文件中提取或由前端传入
     */
    private Integer durationSeconds;
    
    /**
     * 流水线处理状态
     * 记录当前AI处理进度
     */
    private Status status;
    
    /**
     * ASR语音识别原始文本
     * Whisper识别输出的完整文本
     */
    private String rawTranscript;
    
    /**
     * 对话列表JSON字符串
     * DialogueParseNode输出的结构化对话数据
     */
    private String dialogueJson;
    
    /**
     * AI生成的复盘报告JSON
     * ReportGenNode输出的完整复盘报告
     */
    private String reportJson;
    
    /**
     * 创建时间
     * 音频上传时自动填充
     */
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
    
    /**
     * 更新时间
     * 每次状态更新时自动填充
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
