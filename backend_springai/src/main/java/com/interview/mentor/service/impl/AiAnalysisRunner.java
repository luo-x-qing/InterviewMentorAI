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

/**
 * AI 分析异步执行器 —— 独立 bean，使 {@code @Async} 真正生效。
 *
 * <p>此前分析逻辑写在 InterviewServiceImpl 内，被同类的 uploadAudio 以 this 自调用，
 * Spring AOP 代理对自调用不生效，导致分析实际同步阻塞在上传请求线程上。
 * 抽到独立 bean 后，InterviewServiceImpl 跨 bean 调用 {@link #run}，代理生效，分析真正后台异步执行。
 *
 * <p>异步线程不继承请求线程的 {@code TenantContext}（ThreadLocal），
 * 由 AsyncConfig 的 TaskDecorator 负责传播，保证回写 insert 时拦截器能填 tenant_id。
 */
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

    /**
     * 后台异步执行一次面试分析：调 Python → 回写报告与评估 → 更新状态 → WS 推送。
     */
    @Async("aiAnalysisExecutor")
    public void run(InterviewRecord record) {
        try {
            log.info("开始调用 Python AI 后端, interviewId={}", record.getId());

            wsPushService.pushAnalysisProgress(record.getId(), 0, "开始语音转文字");
            wsPushService.pushAnalysisProgress(record.getId(), 30, "调用AI模型分析中");

            // 经适配器调用 Python 分析接口（HTTP 细节封装在 PythonAiClient 之后）
            AnalysisResult result = pythonAiClient.analyze(record.getId(), record.getAudioFilePath());

            wsPushService.pushAnalysisProgress(record.getId(), 90, "生成评估报告");

            // 回写分析结果（复盘报告 + 逐题评估），tenant_id 由 TaskDecorator 传播的上下文注入
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
