/**
 * 面试记录实体（InterviewRecord）
 * 
 * 功能说明：
 * - 对应数据库面试记录表，持久化存储面试相关数据
 * - 包含音频文件路径、ASR转写文本、对话列表、AI生成的评估报告
 * - 由InterviewRecordService提供CRUD操作
 * 
 * 字段说明：
 * - id: 主键ID，自增生成
 * - audioFileId: 音频文件的唯一标识（UUID）
 * - audioFilePath: 音频文件在服务器的存储路径
 * - durationSeconds: 音频时长（秒）
 * - status: 处理状态，反映AI处理进度
 * - rawTranscript: ASR语音识别输出的原始文本
 * - dialogueJson: 解析后的结构化对话JSON
 * - reportJson: AI生成的评估报告JSON
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
     * 处理状态枚举，反映AI处理进度
     */
    public enum Status {
        PROCESSING,           // 处理中，等待AI分析
        ASR_COMPLETED,        // 语音识别完成
        DIALOGUE_PARSED,      // 对话解析完成
        EVALUATION_COMPLETED, // 评估报告生成完成
        COMPLETED,            // 处理完成，报告可查看
        FAILED                // 处理失败
    }
    
    /**
     * 主键ID，自增生成
     */
    @TableId(type = IdType.AUTO)
    private Long id;
    
    /**
     * 音频文件的唯一标识（UUID）
     * 用于Flutter前端关联音频文件
     */
    private String audioFileId;
    
    /**
     * 音频文件在服务器的存储路径
     * 由AudioController上传时保存
     */
    private String audioFilePath;
    
    /**
     * 音频时长（秒）
     * 由AudioController上传时传入
     */
    private Integer durationSeconds;
    
    /**
     * 处理状态
     * 反映AI处理进度
     */
    private Status status;
    
    /**
     * ASR语音识别输出的原始文本
     * 由Whisper模型识别后存储
     */
    private String rawTranscript;
    
    /**
     * 解析后的结构化对话JSON
     * 由DialogueParseNode解析生成对话列表
     */
    private String dialogueJson;
    
    /**
     * AI生成的评估报告JSON
     * 由ReportGenNode生成面试评估报告
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
     * 每次更新记录时自动填充
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
