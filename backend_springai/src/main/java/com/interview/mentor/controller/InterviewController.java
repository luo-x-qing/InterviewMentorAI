package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.req.CreateInterviewRequest;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.security.SecurityUtils;
import com.interview.mentor.service.InterviewService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/interview")
public class InterviewController {

    private final InterviewService interviewService;

    public InterviewController(InterviewService interviewService) {
        this.interviewService = interviewService;
    }

    @PostMapping
    public Result<InterviewRecord> createInterview(
            @Valid @RequestBody CreateInterviewRequest request) {
        Long currentUserId = SecurityUtils.currentUserId();
        InterviewRecord record = interviewService.createInterview(request, currentUserId);
        return Result.success(record);
    }

    @PostMapping("/{id}/audio")
    public Result<InterviewRecord> uploadAudio(
            @PathVariable Long id,
            @RequestParam("file") MultipartFile audioFile) {
        InterviewRecord record = interviewService.uploadAudio(id, audioFile);
        return Result.success(record);
    }

    @GetMapping("/{id}")
    public Result<InterviewRecord> getInterview(@PathVariable Long id) {
        InterviewRecord record = interviewService.getInterview(id);
        return Result.success(record);
    }

    @GetMapping("/list")
    public Result<IPage<InterviewRecord>> listInterviews(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        IPage<InterviewRecord> result = interviewService.listInterviews(
                new Page<>(page, size));
        return Result.success(result);
    }

    @GetMapping("/my")
    public Result<IPage<InterviewRecord>> listMyInterviews(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long currentUserId = SecurityUtils.currentUserId();
        IPage<InterviewRecord> result = interviewService.listMyInterviews(
                new Page<>(page, size), currentUserId);
        return Result.success(result);
    }
}
