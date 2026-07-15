/**
 * AI分析结果响应DTO（AnalysisResp）
 * 
 * 功能说明：
 * - 封装后端AI分析完成后返回给Flutter前端的响应数据
 * - 包含复盘报告、对话分析结果等核心内容
 * - 作为AudioController接口的返回值对象
 * 
 * 字段说明：
 * - interviewId: 面试记录ID，用于后续查询
 * - status: 当前处理状态
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
     * 前端可使用此ID查询处理进度和结果
     */
    private Long interviewId;
    
    /**
     * 音频文件唯一标识
     * 用于关联原始音频文件
     */
    private String audioFileId;
    
    /**
     * 当前处理状态
     * PROCESSING / ASR_COMPLETED / DIALOGUE_PARSED / COMPLETED / FAILED
     */
    private String status;
    
    /**
     * 状态描述信息
     * 如 "音频上传成功，AI复盘流水线已启动"
     */
    private String message;
}
