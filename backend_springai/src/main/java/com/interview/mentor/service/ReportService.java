package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.req.HrCorrectionRequest;
import com.interview.mentor.entity.dto.resp.AnalysisResult;

import java.util.List;
import java.util.Map;

public interface ReportService {

    /**
     * 回写 Python AI 分析结果：写复盘报告 + 逐题评估。
     * 报告按 interviewId 幂等（存在则更新），派生字段（均分/优秀数/薄弱数）由本方法计算。
     */
    void saveAnalysisResult(Long interviewId, AnalysisResult result);

    /**
     * 获取面试的评估列表
     */
    List<Evaluation> getEvaluations(Long interviewId);

    /**
     * HR修正单条评估
     */
    Evaluation correctEvaluation(Long evaluationId, HrCorrectionRequest request, Long hrUserId);

    /**
     * 获取复盘报告（优先返回HR修正后的finalMarkdown）
     */
    Report getReport(Long interviewId);

    /**
     * HR修正报告内容
     */
    Report correctReport(Long interviewId, String finalMarkdown, Long hrUserId);

    /**
     * 分页查询本租户所有报告
     */
    IPage<Report> listReports(Page<Report> page, Long tenantId);

    /**
     * 租户报告统计
     */
    Map<String, Object> getTenantStats(Long tenantId);

    /**
     * 查询待 HR 修正的报告列表
     */
    IPage<Map<String, Object>> listPendingHrReview(Page<Map<String, Object>> page, Long tenantId);
}
