package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.service.ReportService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/report")
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @GetMapping("/interview/{interviewId}/evaluations")
    public Result<List<Evaluation>> getEvaluations(@PathVariable Long interviewId) {
        List<Evaluation> evaluations = reportService.getEvaluations(interviewId);
        return Result.success(evaluations);
    }

    @GetMapping("/interview/{interviewId}/report")
    public Result<Report> getReport(@PathVariable Long interviewId) {
        Report report = reportService.getReport(interviewId);
        return Result.success(report);
    }

    @GetMapping("/list")
    public Result<IPage<Report>> listReports(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        IPage<Report> result = reportService.listReports(new Page<>(page, size));
        return Result.success(result);
    }
}
