package com.interview.mentor.service;

import com.interview.mentor.entity.Evaluation;
import com.interview.mentor.entity.Report;
import com.interview.mentor.entity.dto.resp.AnalysisResult;
import com.interview.mentor.mapper.EvaluationMapper;
import com.interview.mentor.mapper.ReportMapper;
import com.interview.mentor.service.impl.ReportServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.math.BigDecimal;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * ReportService.saveAnalysisResult 回写逻辑的单元测试。
 * 用 Mockito mock 各 Mapper，聚焦派生字段计算与幂等 upsert —— 这是回写逻辑最易藏 bug 处。
 */
class ReportServiceSaveAnalysisTest {

    private EvaluationMapper evaluationMapper;
    private ReportMapper reportMapper;
    private ReportServiceImpl service;

    @BeforeEach
    void setUp() {
        evaluationMapper = mock(EvaluationMapper.class);
        reportMapper = mock(ReportMapper.class);
        service = new ReportServiceImpl(evaluationMapper, reportMapper);
    }

    private AnalysisResult resultWith(AnalysisResult.EvaluationItem... items) {
        AnalysisResult r = new AnalysisResult();
        r.setStatus("COMPLETED");
        r.setReport("# 复盘报告");
        r.setEvaluations(List.of(items));
        return r;
    }

    private AnalysisResult.EvaluationItem item(String level, int score) {
        AnalysisResult.EvaluationItem e = new AnalysisResult.EvaluationItem();
        e.setQuestion("Q");
        e.setAnswer("A");
        e.setLevel(level);
        e.setScore(score);
        return e;
    }

    @Test
    @DisplayName("新报告：计算均分/优秀数/薄弱数并 insert")
    void insertsNewReport_withDerivedFields() {
        when(reportMapper.selectByInterviewId(1L)).thenReturn(null); // 不存在 → insert

        service.saveAnalysisResult(1L, resultWith(
                item("PROFICIENT", 90),
                item("PROFICIENT", 80),
                item("WEAK", 40)));

        // 逐题评估：先删后批量插入 3 条
        verify(evaluationMapper).delete(any());
        verify(evaluationMapper, times(3)).insert(any(Evaluation.class));

        ArgumentCaptor<Report> captor = ArgumentCaptor.forClass(Report.class);
        verify(reportMapper).insert(captor.capture());
        verify(reportMapper, never()).updateById(any());

        Report saved = captor.getValue();
        assertEquals(1L, saved.getInterviewId());
        assertEquals(0, new BigDecimal("70.00").compareTo(saved.getAvgScore()), "均分=(90+80+40)/3=70.00");
        assertEquals(2, saved.getProficientCount(), "优秀数");
        assertEquals(1, saved.getWeakCount(), "薄弱数");
        assertEquals("# 复盘报告", saved.getReportMarkdown());
    }

    @Test
    @DisplayName("已存在报告：按 interviewId 更新而非新增")
    void updatesExistingReport() {
        Report existing = new Report();
        existing.setId(99L);
        existing.setInterviewId(1L);
        when(reportMapper.selectByInterviewId(1L)).thenReturn(existing);

        service.saveAnalysisResult(1L, resultWith(item("PROFICIENT", 100)));

        verify(reportMapper).updateById(existing);
        verify(reportMapper, never()).insert(any());
        assertEquals(0, new BigDecimal("100.00").compareTo(existing.getAvgScore()));
    }

    @Test
    @DisplayName("空评估：均分为 0，不 insert 评估")
    void emptyEvaluations_avgIsZero() {
        when(reportMapper.selectByInterviewId(1L)).thenReturn(null);
        AnalysisResult r = new AnalysisResult();
        r.setStatus("COMPLETED");
        r.setReport("空报告");
        r.setEvaluations(List.of());

        service.saveAnalysisResult(1L, r);

        verify(evaluationMapper, never()).insert(any());
        ArgumentCaptor<Report> captor = ArgumentCaptor.forClass(Report.class);
        verify(reportMapper).insert(captor.capture());
        assertEquals(0, BigDecimal.ZERO.compareTo(captor.getValue().getAvgScore()));
        assertEquals(0, captor.getValue().getProficientCount());
        assertEquals(0, captor.getValue().getWeakCount());
    }
}
