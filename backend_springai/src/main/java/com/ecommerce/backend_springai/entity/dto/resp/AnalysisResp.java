/**
 * AI分析处理响应DTO（AnalysisResp）
 * 
 * 功能说明：
 * - 封装音频上传后返回给Flutter前端的响应数据
 * - 包含面试记录ID、处理状态等关键信息
 * - 供AudioController接口使用
 * 
 * 字段说明：
 * - interviewId: 面试记录ID，前端用于后续查询
 * - audioFileId: 音频文件唯一标识
 * - status: 处理状态
 * - message: 状态描述信息
 */
package com.ecommerce.backend_springai.entity.dto.resp;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResp {
    
    /**
     * 面试记录ID
     * 用于前端后续查询处理状态和结果
     */
    private Long interviewId;
    
    /**
     * 音频文件唯一标识
     * 用于关联上传的音频文件
     */
    private String audioFileId;
    
    /**
     * 处理状态
     * PROCESSING / ASR_COMPLETED / DIALOGUE_PARSED / COMPLETED / FAILED
     */
    private String status;
    
    /**
     * 状态描述信息
     * 如 "音频上传成功，正在进行AI分析处理"
     */
    private String message;
}
