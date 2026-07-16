/**
 * 音频上传控制器（AudioController）
 * 
 * 功能说明：
 * - 接收Flutter前端上传的音频文件（wav/mp3/m4a格式）
 * - 将音频文件保存到服务器指定目录，生成唯一文件标识
 * - 创建面试记录
 * - 异步调用Python AI后端进行语音识别和分析
 * 
 * 接口说明：
 * - POST /api/audio/upload - 上传音频文件并创建面试记录
 */
package com.ecommerce.backend_springai.controller;

import com.ecommerce.backend_springai.entity.InterviewRecord;
import com.ecommerce.backend_springai.entity.dto.resp.AnalysisResp;
import com.ecommerce.backend_springai.handler.InterviewStatusHandler;
import com.ecommerce.backend_springai.service.InterviewRecordService;
import com.ecommerce.backend_springai.util.FileUtil;
import com.ecommerce.backend_springai.util.ResultUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/audio")
public class AudioController {
    
    /**
     * 音频文件存储路径
     */
    @Value("${audio.storage.path:./data/audio}")
    private String audioStoragePath;
    
    /**
     * Python AI 后端地址
     */
    @Value("${python.ai.backend.url:http://localhost:8000}")
    private String pythonBackendUrl;
    
    /**
     * 面试记录服务
     */
    private final InterviewRecordService recordService;
    
    /**
     * HTTP 客户端
     */
    private final RestTemplate restTemplate;
    
    /**
     * WebSocket状态推送处理器
     */
    private final InterviewStatusHandler statusHandler;
    
    /**
     * 构造函数注入依赖
     */
    public AudioController(InterviewRecordService recordService, RestTemplate restTemplate, InterviewStatusHandler statusHandler) {
        this.recordService = recordService;
        this.restTemplate = restTemplate;
        this.statusHandler = statusHandler;
    }
    
    /**
     * 上传音频文件并创建面试记录
     * 
     * 处理流程：
     * 1. 验证文件格式和大小
     * 2. 生成唯一文件标识
     * 3. 保存音频文件到本地磁盘
     * 4. 创建面试记录
     * 5. 异步调用Python AI后端进行分析
     * 6. 返回处理状态给Flutter前端
     */
    @PostMapping("/upload")
    public ResultUtil<AnalysisResp> uploadAudio(
            @RequestParam("file") MultipartFile audioFile,
            @RequestParam(value = "title", required = false) String title,
            @RequestParam(value = "userId", required = false) Long userId,
            @RequestParam(value = "durationSeconds", required = false) Integer durationSeconds) {
        
        log.info("收到音频上传请求: fileName={}, fileSize={}", 
                audioFile.getOriginalFilename(), audioFile.getSize());
        
        // 1. 验证文件格式和大小
        if (audioFile.isEmpty()) {
            return ResultUtil.fail(400, "音频文件不能为空");
        }
        
        String originalFilename = audioFile.getOriginalFilename();
        if (originalFilename == null || !isAudioFileValid(originalFilename)) {
            return ResultUtil.fail(400, "不支持的音频格式，请上传 wav/mp3/m4a 格式的音频");
        }
        
        long maxSize = 200 * 1024 * 1024; // 200MB
        if (audioFile.getSize() > maxSize) {
            return ResultUtil.fail(413, "音频文件过大，最大支持200MB");
        }
        
        try {
            // 2. 生成唯一文件标识
            String audioFileId = java.util.UUID.randomUUID().toString();
            String newFileName = FileUtil.generateFileName(originalFilename);
            
            log.info("生成文件标识: audioFileId={}, newFileName={}", audioFileId, newFileName);
            
            // 3. 保存音频文件到本地磁盘
            FileUtil.makeDir(audioStoragePath);
            Path filePath = Paths.get(audioStoragePath, newFileName);
            audioFile.transferTo(new java.io.File(filePath.toString()));
            log.info("音频文件保存成功, path={}", filePath.toAbsolutePath());
            
            // 4. 创建面试记录
            InterviewRecord record = InterviewRecord.builder()
                    .audioFileId(audioFileId)
                    .audioFilePath(filePath.toAbsolutePath().toString())
                    .durationSeconds(durationSeconds)
                    .build();
            
            record = recordService.createRecord(record);
            log.info("面试记录创建成功, id={}", record.getId());
            
            // 5. 异步调用Python AI后端
            final Long interviewId = record.getId();
            final String audioFilePathStr = filePath.toAbsolutePath().toString();
            
            new Thread(() -> {
                try {
                    callPythonBackend(interviewId, audioFilePathStr);
                } catch (Exception e) {
                    log.error("调用Python AI后端失败, interviewId={}", interviewId, e);
                    recordService.markFailed(interviewId, e.getMessage());
                }
            }, "ai-pipeline-" + interviewId).start();
            
            // 6. 返回处理状态给Flutter前端
            AnalysisResp resp = AnalysisResp.builder()
                    .interviewId(record.getId())
                    .audioFileId(audioFileId)
                    .status("PROCESSING")
                    .message("音频上传成功，正在进行AI分析处理，请稍后查看结果")
                    .build();
            
            return ResultUtil.success(resp);
            
        } catch (IOException e) {
            log.error("音频文件保存失败", e);
            return ResultUtil.fail(500, "音频文件保存失败: " + e.getMessage());
        } catch (Exception e) {
            log.error("音频上传处理异常", e);
            return ResultUtil.fail(500, "服务器内部错误: " + e.getMessage());
        }
    }
    
    /**
     * 调用Python AI后端进行分析
     */
    private void callPythonBackend(Long interviewId, String audioFilePath) {
        log.info("调用Python AI后端: interviewId={}", interviewId);
        
        // 推送处理状态给Flutter前端
        statusHandler.sendStatusUpdate(String.valueOf(interviewId), "PROCESSING");
        
        String url = pythonBackendUrl + "/api/v1/analysis/analyze";
        
        Map<String, Object> request = new HashMap<>();
        request.put("interview_id", interviewId);
        request.put("audio_file_path", audioFilePath);
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);
        
        ResponseEntity<?> response = restTemplate.postForEntity(url, entity, Object.class);
        
        if (response.getStatusCode().is2xxSuccessful() && response.getBody() instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> body = (Map<String, Object>) response.getBody();
            if (body != null && "COMPLETED".equals(body.get("status"))) {
                log.info("Python AI分析完成: interviewId={}", interviewId);
                // 更新面试记录报告
                String report = (String) body.get("report");
                if (report != null) {
                    recordService.updateReport(interviewId, report);
                    // 推送报告给Flutter前端
                    statusHandler.sendReport(String.valueOf(interviewId), report);
                }
            }
        } else {
            throw new RuntimeException("Python AI后端调用失败: " + response.getStatusCode());
        }
    }
    
    /**
     * 验证音频文件格式
     */
    private boolean isAudioFileValid(String filename) {
        String lowerFilename = filename.toLowerCase();
        return lowerFilename.endsWith(".wav") 
            || lowerFilename.endsWith(".mp3") 
            || lowerFilename.endsWith(".m4a");
    }
}
