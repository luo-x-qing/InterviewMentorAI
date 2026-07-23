package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.req.HrCorrectionRequest;
import com.interview.mentor.entity.dto.resp.AnalysisResult;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.EvaluationMapper;
import com.interview.mentor.mapper.InterviewRecordMapper;
import com.interview.mentor.mapper.ReportMapper;
import com.interview.mentor.service.ReportService;
import com.interview.mentor.websocket.WsPushService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
public class ReportServiceImpl implements ReportService {

    private static final Logger log = LoggerFactory.getLogger(ReportServiceImpl.class);

    private final EvaluationMapper evaluationMapper;
    private final ReportMapper reportMapper;
    private final InterviewRecordMapper interviewMapper;
    private final WsPushService wsPushService;

    public ReportServiceImpl(EvaluationMapper evaluationMapper,
                             ReportMapper reportMapper,
                             InterviewRecordMapper interviewMapper,
                             WsPushService wsPushService) {
        this.evaluationMapper = evaluationMapper;
        this.reportMapper = reportMapper;
        this.interviewMapper = interviewMapper;
        this.wsPushService = wsPushService;
    }

    @Override
    @Transactional
    public void saveAnalysisResult(Long interviewId, AnalysisResult result) {
        List<AnalysisResult.EvaluationItem> items =
                result.getEvaluations() != null ? result.getEvaluations() : List.of();

        // 1. 批量回写逐题评估（tenant_id 由拦截器在请求线程上自动注入）
        //    幂等：先清掉该面试已有评估，避免重跑产生重复
        evaluationMapper.delete(new LambdaQueryWrapper<Evaluation>()
                .eq(Evaluation::getInterviewId, interviewId));

        int proficientCount = 0;
        int weakCount = 0;
        BigDecimal scoreSum = BigDecimal.ZERO;
        int scoredCount = 0;
        int questionIndex = 0;
        for (AnalysisResult.EvaluationItem item : items) {
            Evaluation evaluation = new Evaluation();
            evaluation.setInterviewId(interviewId);
            evaluation.setQuestionIndex(questionIndex++);
            evaluation.setQuestion(item.getQuestion());
            evaluation.setAnswer(item.getAnswer());
            if (item.getScore() != null) {
                BigDecimal score = BigDecimal.valueOf(item.getScore());
                evaluation.setAiScore(score);
                scoreSum = scoreSum.add(score);
                scoredCount++;
            }
            evaluation.setAiLevel(item.getLevel());
            evaluation.setAiStrengths(item.getStrengths());
            evaluation.setAiWeaknesses(item.getWeaknesses());
            evaluation.setAiCorrection(item.getCorrection());
            evaluation.setAiKnowledgePoints(item.getKnowledgePoints());
            evaluation.setCreatedAt(LocalDateTime.now());
            evaluationMapper.insert(evaluation);

            if ("PROFICIENT".equalsIgnoreCase(item.getLevel())) {
                proficientCount++;
            } else if ("WEAK".equalsIgnoreCase(item.getLevel())) {
                weakCount++;
            }
        }

        BigDecimal avgScore = scoredCount > 0
                ? scoreSum.divide(BigDecimal.valueOf(scoredCount), 2, java.math.RoundingMode.HALF_UP)
                : BigDecimal.ZERO;

        // 2. 回写复盘报告（按 interviewId 幂等：存在则更新）
        Report report = reportMapper.selectByInterviewId(interviewId);
        boolean isNew = report == null;
        if (isNew) {
            report = new Report();
            report.setInterviewId(interviewId);
            report.setHrEdited(0);
            report.setCreatedAt(LocalDateTime.now());
        }
        report.setReportMarkdown(result.getReport());
        report.setAvgScore(avgScore);
        report.setProficientCount(proficientCount);
        report.setWeakCount(weakCount);
        if (isNew) {
            reportMapper.insert(report);
        } else {
            reportMapper.updateById(report);
        }

        log.info("回写分析结果完成, interviewId={}, 评估条数={}, 均分={}, 优秀={}, 薄弱={}",
                interviewId, items.size(), avgScore, proficientCount, weakCount);
    }

    @Override
    public List<Evaluation> getEvaluations(Long interviewId) {
        return evaluationMapper.selectByInterviewId(interviewId);
    }

    @Override
    @Transactional
    public Evaluation correctEvaluation(Long evaluationId,
                                         HrCorrectionRequest request,
                                         Long hrUserId) {
        Evaluation evaluation = evaluationMapper.selectById(evaluationId);
        if (evaluation == null) {
            throw new BusinessException(404, "评估不存在");
        }

        evaluationMapper.hrCorrectEvaluation(
                evaluationId,
                request.getScore(),
                request.getLevel(),
                request.getRemark(),
                hrUserId);

        log.info("HR修正评估完成, evaluationId={}, hrUserId={}, score={}",
                evaluationId, hrUserId, request.getScore());

        return evaluationMapper.selectById(evaluationId);
    }

    @Override
    public Report getReport(Long interviewId) {
        Report report = reportMapper.selectByInterviewId(interviewId);
        if (report == null) {
            throw new BusinessException(404, "报告不存在");
        }
        return report;
    }

    @Override
    @Transactional
    public Report correctReport(Long interviewId, String finalMarkdown, Long hrUserId) {
        Report report = reportMapper.selectByInterviewId(interviewId);
        if (report == null) {
            throw new BusinessException(404, "报告不存在");
        }

        report.setFinalMarkdown(finalMarkdown);
        report.setHrEdited(1);
        report.setHrEditedBy(hrUserId);
        report.setHrEditedAt(LocalDateTime.now());

        reportMapper.updateById(report);

        // 推送 HR 修正通知给候选人
        InterviewRecord interview = interviewMapper.selectById(interviewId);
        if (interview != null && interview.getCandidateId() != null) {
            wsPushService.pushHrCorrectionNotification(
                    interview.getCandidateId(), report.getId(), interview.getTenantId());
        }

        log.info("HR修正报告完成, interviewId={}, hrUserId={}", interviewId, hrUserId);
        return report;
    }

    @Override
    public IPage<Report> listReports(Page<Report> page, Long tenantId) {
        // 租户过滤由 TenantLineInnerInterceptor 自动注入，Service 层无需再手写 tenant_id 条件
        LambdaQueryWrapper<Report> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(Report::getCreatedAt);
        return reportMapper.selectPage(page, wrapper);
    }

    @Override
    public Map<String, Object> getTenantStats(Long tenantId) {
        // 所有查询均由拦截器自动限定在当前租户内，统计不再跨租户
        long totalReports = reportMapper.selectCount(null);
        long hrEditedCount = reportMapper.selectCount(
                new LambdaQueryWrapper<Report>().eq(Report::getHrEdited, 1));

        List<Report> reports = reportMapper.selectList(
                new LambdaQueryWrapper<Report>().isNotNull(Report::getAvgScore));
        BigDecimal avgScore = BigDecimal.ZERO;
        if (!reports.isEmpty()) {
            BigDecimal sum = reports.stream()
                    .map(Report::getAvgScore)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            avgScore = sum.divide(BigDecimal.valueOf(reports.size()), 2, java.math.RoundingMode.HALF_UP);
        }

        java.util.HashMap<String, Object> stats = new java.util.HashMap<>();
        stats.put("total_reports", totalReports);
        stats.put("avg_score", avgScore);
        stats.put("hr_edited_count", hrEditedCount);
        return stats;
    }

    @Override
    public IPage<Map<String, Object>> listPendingHrReview(Page<Map<String, Object>> page, Long tenantId) {
        // 租户过滤由拦截器自动注入
        LambdaQueryWrapper<Report> wrapper = new LambdaQueryWrapper<Report>()
                .eq(Report::getHrEdited, 0)
                .orderByDesc(Report::getCreatedAt);

        Page<Report> reportPageParam = new Page<>(page.getCurrent(), page.getSize());
        IPage<Report> reportPage = reportMapper.selectPage(reportPageParam, wrapper);

        Page<Map<String, Object>> result = new Page<>(reportPage.getCurrent(), reportPage.getSize(), reportPage.getTotal());
        java.util.List<Map<String, Object>> records = new java.util.ArrayList<>();
        for (Report r : reportPage.getRecords()) {
            java.util.Map<String, Object> map = new java.util.HashMap<>();
            map.put("id", r.getId());
            map.put("interview_id", r.getInterviewId());
            map.put("avg_score", r.getAvgScore());
            map.put("created_at", r.getCreatedAt());
            records.add(map);
        }
        result.setRecords(records);

        return result;
    }
}
