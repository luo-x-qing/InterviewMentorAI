package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.resp.AnalysisResult;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.EvaluationMapper;
import com.interview.mentor.mapper.ReportMapper;
import com.interview.mentor.service.ReportService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class ReportServiceImpl implements ReportService {

    private static final Logger log = LoggerFactory.getLogger(ReportServiceImpl.class);

    private final EvaluationMapper evaluationMapper;
    private final ReportMapper reportMapper;

    public ReportServiceImpl(EvaluationMapper evaluationMapper,
                             ReportMapper reportMapper) {
        this.evaluationMapper = evaluationMapper;
        this.reportMapper = reportMapper;
    }

    @Override
    @Transactional
    public void saveAnalysisResult(Long interviewId, AnalysisResult result) {
        List<AnalysisResult.EvaluationItem> items =
                result.getEvaluations() != null ? result.getEvaluations() : List.of();

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

        Report report = reportMapper.selectByInterviewId(interviewId);
        boolean isNew = report == null;
        if (isNew) {
            report = new Report();
            report.setInterviewId(interviewId);
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
    public Report getReport(Long interviewId) {
        Report report = reportMapper.selectByInterviewId(interviewId);
        if (report == null) {
            throw new BusinessException(404, "报告不存在");
        }
        return report;
    }

    @Override
    public IPage<Report> listReports(Page<Report> page) {
        LambdaQueryWrapper<Report> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(Report::getCreatedAt);
        return reportMapper.selectPage(page, wrapper);
    }
}
