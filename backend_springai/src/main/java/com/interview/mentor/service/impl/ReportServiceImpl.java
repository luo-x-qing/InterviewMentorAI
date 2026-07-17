package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.req.HrCorrectionRequest;
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
        // 通过面试记录关联查询
        LambdaQueryWrapper<Report> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(Report::getCreatedAt);
        return reportMapper.selectPage(page, wrapper);
    }

    @Override
    public Map<String, Object> getTenantStats(Long tenantId) {
        // 简化实现：返回基本统计
        long totalReports = reportMapper.selectCount(null);
        java.util.HashMap<String, Object> stats = new java.util.HashMap<>();
        stats.put("total_reports", totalReports);
        stats.put("avg_score", BigDecimal.ZERO);
        stats.put("hr_edited_count", 0);
        return stats;
    }

    @Override
    public IPage<Map<String, Object>> listPendingHrReview(Page<Map<String, Object>> page, Long tenantId) {
        // 查询未修正的报告
        LambdaQueryWrapper<Report> wrapper = new LambdaQueryWrapper<Report>()
                .eq(Report::getHrEdited, 0)
                .orderByDesc(Report::getCreatedAt);

        IPage<Report> reportPage = reportMapper.selectPage(page, wrapper);

        // 转换为Map
        Page<Map<String, Object>> result = new Page<>(reportPage.getCurrent(), reportPage.getSize(), reportPage.getTotal());
        result.setRecords(reportPage.getRecords().stream().map(r -> {
            java.util.HashMap<String, Object> map = new java.util.HashMap<>();
            map.put("id", r.getId());
            map.put("interview_id", r.getInterviewId());
            map.put("avg_score", r.getAvgScore());
            map.put("created_at", r.getCreatedAt());
            return map;
        }).toList());

        return result;
    }
}
