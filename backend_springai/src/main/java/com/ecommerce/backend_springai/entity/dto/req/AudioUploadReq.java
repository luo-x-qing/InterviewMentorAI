/**
 * 音频上传请求DTO（AudioUploadReq）
 * 
 * 功能说明：
 * - 封装Flutter前端上传音频文件的请求参数
 * - 作为AudioController接口的入参对象
 * - 采用DTO模式解耦前端请求与后端实体
 * 
 * 字段说明：
 * - audioFile: 上传的音频文件（MultipartFile）
 * - title: 面试标题（可选），如 "Java后端二面"
 * - userId: 用户ID（可选），当前版本可为空
 * - durationSeconds: 面试时长（可选），前端可预传
 */
package com.ecommerce.backend_springai.entity.dto.req;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AudioUploadReq {
    
    /**
     * 上传的音频文件
     * 支持格式：wav, mp3, m4a
     * 最大大小：200MB（由application.yml配置）
     */
    private MultipartFile audioFile;
    
    /**
     * 面试标题（可选）
     * 用于标识本次面试，如岗位名称、面试轮次等
     */
    private String title;
    
    /**
     * 用户ID（可选）
     * 当前版本可为空，后续用于用户关联
     */
    private Long userId;
    
    /**
     * 面试时长（秒，可选）
     * 前端可在上传时预传面试时长
     */
    private Integer durationSeconds;
}
