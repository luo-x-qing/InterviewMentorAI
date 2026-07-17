package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.req.CreateInterviewRequest;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.service.InterviewService;
import com.interview.mentor.tenant.TenantContext;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/interview")
public class InterviewController {

    private final InterviewService interviewService;

    public InterviewController(InterviewService interviewService) {
        this.interviewService = interviewService;
    }

    /**
     * 创建面试记录
     */
    @PostMapping
    public Result<InterviewRecord> createInterview(
            @Valid @RequestBody CreateInterviewRequest request,
            Authentication authentication) {
        Long currentUserId = getCurrentUserId(authentication);
        InterviewRecord record = interviewService.createInterview(request, currentUserId);
        return Result.success(record);
    }

    /**
     * 上传音频并触发 AI 分析
     */
    @PostMapping("/{id}/audio")
    public Result<InterviewRecord> uploadAudio(
            @PathVariable Long id,
            @RequestParam("file") MultipartFile audioFile) {
        InterviewRecord record = interviewService.uploadAudio(id, audioFile);
        return Result.success(record);
    }

    /**
     * 查询面试记录详情
     */
    @GetMapping("/{id}")
    public Result<InterviewRecord> getInterview(@PathVariable Long id) {
        InterviewRecord record = interviewService.getInterview(id);
        return Result.success(record);
    }

    /**
     * 分页查询本租户所有面试（HR/管理员）
     */
    @GetMapping("/list")
    public Result<IPage<InterviewRecord>> listInterviews(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long tenantId = TenantContext.getTenantId();
        IPage<InterviewRecord> result = interviewService.listInterviews(
                new Page<>(page, size), tenantId);
        return Result.success(result);
    }

    /**
     * 分页查询候选人自己的面试列表
     */
    @GetMapping("/my")
    public Result<IPage<InterviewRecord>> listMyInterviews(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            Authentication authentication) {
        Long currentUserId = getCurrentUserId(authentication);
        IPage<InterviewRecord> result = interviewService.listMyInterviews(
                new Page<>(page, size), currentUserId);
        return Result.success(result);
    }

    private Long getCurrentUserId(Authentication authentication) {
        // 从 JWT Claims 中获取 userId，或从数据库查询
        // MVP 阶段简化处理：从 username 查数据库
        return null; // TODO: 实现完整逻辑
    }
}
