package com.interview.mentor.service;

import com.interview.mentor.client.PythonAiClient;
import com.interview.mentor.client.PythonAiException;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.resp.AnalysisResult;
import com.interview.mentor.mapper.InterviewRecordMapper;
import com.interview.mentor.service.impl.AiAnalysisRunner;
import com.interview.mentor.websocket.WsPushService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

/**
 * AiAnalysisRunner 编排逻辑单元测试：验证成功链路（调 client → 回写 → 状态/推送）
 * 与失败链路（异常 → 置 FAILED → 推送失败）。用 mock 隔离，不起真实端口。
 */
class AiAnalysisRunnerTest {

    private InterviewRecordMapper interviewMapper;
    private WsPushService wsPushService;
    private PythonAiClient pythonAiClient;
    private ReportService reportService;
    private AiAnalysisRunner runner;

    @BeforeEach
    void setUp() {
        interviewMapper = mock(InterviewRecordMapper.class);
        wsPushService = mock(WsPushService.class);
        pythonAiClient = mock(PythonAiClient.class);
        reportService = mock(ReportService.class);
        runner = new AiAnalysisRunner(interviewMapper, wsPushService, pythonAiClient, reportService);
    }

    private InterviewRecord record() {
        InterviewRecord r = new InterviewRecord();
        r.setId(7L);
        r.setAudioFilePath("/data/audio/x.wav");
        return r;
    }

    @Test
    @DisplayName("成功链路：调 analyze → 回写 → 置 COMPLETED → 推送完成")
    void successPath() {
        AnalysisResult result = new AnalysisResult();
        result.setStatus("COMPLETED");
        when(pythonAiClient.analyze(7L, "/data/audio/x.wav")).thenReturn(result);

        InterviewRecord rec = record();
        runner.run(rec);

        verify(pythonAiClient).analyze(7L, "/data/audio/x.wav");
        verify(reportService).saveAnalysisResult(7L, result);
        verify(interviewMapper).updateById(rec);
        verify(wsPushService).pushAnalysisComplete(7L, null);
        verify(wsPushService, never()).pushAnalysisFailed(anyLong(), any());
        assertEquals("COMPLETED", rec.getStatus());
    }

    @Test
    @DisplayName("失败链路：analyze 抛异常 → 置 FAILED → 推送失败，不回写")
    void failurePath() {
        when(pythonAiClient.analyze(anyLong(), any()))
                .thenThrow(new PythonAiException("Python 500"));

        InterviewRecord rec = record();
        runner.run(rec);

        verify(reportService, never()).saveAnalysisResult(anyLong(), any());
        verify(wsPushService).pushAnalysisFailed(eq(7L), anyString());
        verify(wsPushService, never()).pushAnalysisComplete(anyLong(), any());
        assertEquals("FAILED", rec.getStatus());
    }
}
