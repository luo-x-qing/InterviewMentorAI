package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewSession;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.service.InterviewSessionService;
import com.interview.mentor.tenant.TenantContext;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/session")
public class InterviewSessionController {

    private final InterviewSessionService sessionService;

    public InterviewSessionController(InterviewSessionService sessionService) {
        this.sessionService = sessionService;
    }

    /**
     * HR创建面试会话
     */
    @PostMapping("/create")
    public Result<InterviewSession> createSession(@RequestBody Map<String, String> request) {
        Long tenantId = TenantContext.getTenantId();
        // TODO: 从 Authentication 获取 hrUserId
        Long hrUserId = null;

        InterviewSession session = sessionService.createSession(
                request.get("title"),
                tenantId,
                hrUserId,
                request.get("candidateName"),
                request.get("candidatePhone")
        );
        return Result.success(session);
    }

    /**
     * 候选人通过邀请码查看面试会话（公开接口）
     */
    @GetMapping("/code/{code}")
    public Result<InterviewSession> getSessionByCode(@PathVariable String code) {
        InterviewSession session = sessionService.getSessionByCode(code);
        return Result.success(session);
    }

    /**
     * 检查邀请码是否有效（公开接口）
     */
    @GetMapping("/code/{code}/valid")
    public Result<Boolean> checkCodeValid(@PathVariable String code) {
        boolean valid = sessionService.isCodeValid(code);
        return Result.success(valid);
    }

    /**
     * HR查看自己创建的会话列表
     */
    @GetMapping("/list")
    public Result<IPage<InterviewSession>> listSessions(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long tenantId = TenantContext.getTenantId();
        // TODO: 从 Authentication 获取 hrUserId
        Long hrUserId = null;

        IPage<InterviewSession> result = sessionService.listSessions(
                new Page<>(page, size), tenantId, hrUserId);
        return Result.success(result);
    }
}
