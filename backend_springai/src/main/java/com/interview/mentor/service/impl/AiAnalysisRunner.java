package com.interview.mentor.service.impl;

import com.interview.mentor.client.PythonAiClient;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.resp.AnalysisResult;
import com.interview.mentor.mapper.InterviewRecordMapper;
import com.interview.mentor.service.ReportService;
import com.interview.mentor.websocket.WsPushService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class AiAnalysisRunner {

    private static final Logger log = LoggerFactory.getLogger(AiAnalysisRunner.class);

    private final InterviewRecordMapper interviewMapper;
    private final WsPushService wsPushService;
    private final PythonAiClient pythonAiClient;
    private final ReportService reportService;

    public AiAnalysisRunner(InterviewRecordMapper interviewMapper,
                            WsPushService wsPushService,
                            PythonAiClient pythonAiClient,
                            ReportService reportService) {
        this.interviewMapper = interviewMapper;
        this.wsPushService = wsPushService;
        this.pythonAiClient = pythonAiClient;
        this.reportService = reportService;
    }

    @Async("aiAnalysisExecutor")
    public void run(InterviewRecord record) {
        try {
            log.info("开始调用 Python AI 后端, interviewId={}", record.getId());

            wsPushService.pushAnalysisProgress(record.getId(), 0, "开始语音转文字");
            wsPushService.pushAnalysisProgress(record.getId(), 30, "调用AI模型分析中");

            AnalysisResult result = pythonAiClient.analyze(record.getId(), record.getAudioFilePath());

            wsPushService.pushAnalysisProgress(record.getId(), 90, "生成评估报告");

            reportService.saveAnalysisResult(record.getId(), result);

            record.setStatus("COMPLETED");
            record.setUpdatedAt(LocalDateTime.now());
            interviewMapper.updateById(record);

            wsPushService.pushAnalysisComplete(record.getId(), null);

        } catch (Exception e) {
            log.error("Python AI 分析失败, interviewId={}", record.getId(), e);
            record.setStatus("FAILED");
            record.setUpdatedAt(LocalDateTime.now());
            interviewMapper.updateById(record);

            wsPushService.pushAnalysisFailed(record.getId(), e.getMessage());
        }
    }
}
