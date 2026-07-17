package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.req.HrCorrectionRequest;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.service.ReportService;
import com.interview.mentor.tenant.TenantContext;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/report")
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    /**
     * 获取面试评估列表
     */
    @GetMapping("/interview/{interviewId}/evaluations")
    public Result<List<Evaluation>> getEvaluations(@PathVariable Long interviewId) {
        List<Evaluation> evaluations = reportService.getEvaluations(interviewId);
        return Result.success(evaluations);
    }

    /**
     * HR修正单条评估
     */
    @PutMapping("/evaluation/{id}/correct")
    public Result<Evaluation> correctEvaluation(
            @PathVariable Long id,
            @Valid @RequestBody HrCorrectionRequest request) {
        // TODO: 从 Authentication 获取 hrUserId
        Long hrUserId = null;
        Evaluation corrected = reportService.correctEvaluation(id, request, hrUserId);
        return Result.success(corrected);
    }

    /**
     * 获取复盘报告
     */
    @GetMapping("/interview/{interviewId}/report")
    public Result<Report> getReport(@PathVariable Long interviewId) {
        Report report = reportService.getReport(interviewId);
        return Result.success(report);
    }

    /**
     * HR修正报告内容
     */
    @PutMapping("/interview/{interviewId}/report")
    public Result<Report> correctReport(
            @PathVariable Long interviewId,
            @RequestBody Map<String, String> request) {
        // TODO: 从 Authentication 获取 hrUserId
        Long hrUserId = null;
        Report corrected = reportService.correctReport(interviewId, request.get("finalMarkdown"), hrUserId);
        return Result.success(corrected);
    }

    /**
     * 分页查询报告列表
     */
    @GetMapping("/list")
    public Result<IPage<Report>> listReports(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long tenantId = TenantContext.getTenantId();
        IPage<Report> result = reportService.listReports(
                new Page<>(page, size), tenantId);
        return Result.success(result);
    }

    /**
     * 租户报告统计
     */
    @GetMapping("/stats")
    public Result<Map<String, Object>> getStats() {
        Long tenantId = TenantContext.getTenantId();
        Map<String, Object> stats = reportService.getTenantStats(tenantId);
        return Result.success(stats);
    }

    /**
     * 查询待 HR 修正的报告
     */
    @GetMapping("/pending-review")
    public Result<IPage<Map<String, Object>>> listPendingReview(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long tenantId = TenantContext.getTenantId();
        IPage<Map<String, Object>> result = reportService.listPendingHrReview(
                new Page<>(page, size), tenantId);
        return Result.success(result);
    }
}
