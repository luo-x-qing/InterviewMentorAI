package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.resp.AnalysisResult;

import java.util.List;

public interface ReportService {

    void saveAnalysisResult(Long interviewId, AnalysisResult result);

    List<Evaluation> getEvaluations(Long interviewId);

    Report getReport(Long interviewId);

    IPage<Report> listReports(Page<Report> page);
}
