/**
 * 音频上传请求DTO（AudioUploadReq）
 * 
 * 功能说明：
 * - 封装Flutter前端上传音频文件的请求参数
 * - 作为AudioController接口的入参
 * - 遵循DTO模式，与前端数据解耦
 * 
 * 字段说明：
 * - audioFile: 音频文件，支持wav, mp3, m4a格式
 * - title: 面试标题（可选），如"Java面试模拟"
 * - userId: 用户ID（可选），用于关联用户
 * - durationSeconds: 音频时长（可选），由前端传入
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
     * 音频文件
     * 支持格式: wav, mp3, m4a
     * 大小限制: 200MB，可在application.yml中配置
     */
    private MultipartFile audioFile;
    
    /**
     * 面试标题（可选）
     * 用于在记录列表中显示，如不传则使用文件名
     */
    private String title;
    
    /**
     * 用户ID（可选）
     * 用于关联用户，如不传则不关联
     */
    private Long userId;
    
    /**
     * 音频时长（秒，可选）
     * 由前端获取音频时长后传入
     */
    private Integer durationSeconds;
}
