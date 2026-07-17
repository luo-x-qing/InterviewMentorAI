package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.req.CreateInterviewRequest;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.InterviewRecordMapper;
import com.interview.mentor.service.InterviewService;
import com.interview.mentor.tenant.TenantContext;
import com.interview.mentor.websocket.WsPushService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class InterviewServiceImpl implements InterviewService {

    private static final Logger log = LoggerFactory.getLogger(InterviewServiceImpl.class);

    private final InterviewRecordMapper interviewMapper;
    private final WsPushService wsPushService;

    @Value("${audio.storage.path:./data/audio}")
    private String audioStoragePath;

    @Value("${python.ai.backend.url:http://localhost:8000}")
    private String pythonBackendUrl;

    public InterviewServiceImpl(InterviewRecordMapper interviewMapper,
                                WsPushService wsPushService) {
        this.interviewMapper = interviewMapper;
        this.wsPushService = wsPushService;
    }

    @Override
    public InterviewRecord createInterview(CreateInterviewRequest request, Long currentUserId) {
        InterviewRecord record = new InterviewRecord();
        record.setTenantId(TenantContext.getTenantId());
        record.setUserId(request.getUserId() != null ? request.getUserId() : currentUserId);
        record.setAudioFileId(UUID.randomUUID().toString());
        record.setJobRole(request.getJobRole());
        record.setStatus("CREATED");
        record.setCreatedBy(currentUserId);
        record.setCreatedAt(LocalDateTime.now());
        record.setUpdatedAt(LocalDateTime.now());

        interviewMapper.insert(record);
        return record;
    }

    @Override
    public InterviewRecord uploadAudio(Long interviewId, MultipartFile audioFile) {
        InterviewRecord record = interviewMapper.selectById(interviewId);
        if (record == null) {
            throw new BusinessException(404, "面试记录不存在");
        }

        // 保存音频文件到磁盘
        String fileName = record.getAudioFileId() + getAudioExtension(audioFile.getOriginalFilename());
        Path filePath = Paths.get(audioStoragePath, fileName);
        try {
            Files.createDirectories(filePath.getParent());
            audioFile.transferTo(filePath.toFile());
        } catch (IOException e) {
            throw new BusinessException(500, "音频文件保存失败: " + e.getMessage());
        }

        // 更新记录
        record.setAudioFilePath(filePath.toString());
        record.setStatus("PROCESSING");
        record.setUpdatedAt(LocalDateTime.now());
        interviewMapper.updateById(record);

        // 推送状态：开始处理
        wsPushService.pushInterviewStatus(interviewId, "PROCESSING", "音频上传成功，开始AI分析");

        // 异步调用 Python AI 后端
        triggerAiAnalysis(record);

        return record;
    }

    @Override
    public InterviewRecord getInterview(Long interviewId) {
        InterviewRecord record = interviewMapper.selectById(interviewId);
        if (record == null) {
            throw new BusinessException(404, "面试记录不存在");
        }
        return record;
    }

    @Override
    public IPage<InterviewRecord> listInterviews(Page<InterviewRecord> page, Long tenantId) {
        return interviewMapper.selectPage(page,
                new LambdaQueryWrapper<InterviewRecord>()
                        .eq(InterviewRecord::getTenantId, tenantId)
                        .orderByDesc(InterviewRecord::getCreatedAt));
    }

    @Override
    public IPage<InterviewRecord> listMyInterviews(Page<InterviewRecord> page, Long userId) {
        return interviewMapper.selectPage(page,
                new LambdaQueryWrapper<InterviewRecord>()
                        .eq(InterviewRecord::getUserId, userId)
                        .orderByDesc(InterviewRecord::getCreatedAt));
    }

    /**
     * 异步调用 Python AI 后端进行分析
     */
    @Async("aiAnalysisExecutor")
    public void triggerAiAnalysis(InterviewRecord record) {
        try {
            log.info("开始异步调用 Python AI 后端, interviewId={}", record.getId());

            // 推送进度：开始分析
            wsPushService.pushAnalysisProgress(record.getId(), 0, "开始语音转文字");

            // 使用 RestClient 调用 Python 后端
            org.springframework.web.client.RestClient restClient =
                    org.springframework.web.client.RestClient.create(pythonBackendUrl);

            // 构建请求体
            java.util.Map<String, Object> requestBody = new java.util.HashMap<>();
            requestBody.put("audio_file_id", record.getAudioFileId());
            requestBody.put("audio_file_path", record.getAudioFilePath());

            // 推送进度：调用Python
            wsPushService.pushAnalysisProgress(record.getId(), 30, "调用AI模型分析中");

            // 调用 Python AI 接口
            String response = restClient.post()
                    .uri("/api/v1/analysis/analyze")
                    .header("Content-Type", "application/json")
                    .body(requestBody)
                    .retrieve()
                    .body(String.class);

            log.info("Python AI 分析完成, interviewId={}, response={}", record.getId(), response);

            // 推送进度：分析完成
            wsPushService.pushAnalysisProgress(record.getId(), 90, "生成评估报告");

            // 更新状态为完成
            record.setStatus("COMPLETED");
            record.setUpdatedAt(LocalDateTime.now());
            interviewMapper.updateById(record);

            // 推送完成通知
            wsPushService.pushAnalysisComplete(record.getId(), null);

        } catch (Exception e) {
            log.error("Python AI 分析失败, interviewId={}", record.getId(), e);
            record.setStatus("FAILED");
            record.setUpdatedAt(LocalDateTime.now());
            interviewMapper.updateById(record);

            // 推送失败通知
            wsPushService.pushAnalysisFailed(record.getId(), e.getMessage());
        }
    }

    private String getAudioExtension(String originalFilename) {
        if (originalFilename != null && originalFilename.contains(".")) {
            return originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        return ".wav";
    }
}
