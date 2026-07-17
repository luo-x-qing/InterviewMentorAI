package com.interview.mentor.websocket;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * STOMP 推送服务
 * 用于向客户端推送异步任务状态更新
 */
@Service
public class WsPushService {

    private static final Logger log = LoggerFactory.getLogger(WsPushService.class);

    private final SimpMessagingTemplate messagingTemplate;

    public WsPushService(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * 推送面试状态更新
     * 客户端订阅: /topic/interview/{interviewId}
     */
    public void pushInterviewStatus(Long interviewId, String status, String message) {
        Map<String, Object> payload = Map.of(
                "type", "INTERVIEW_STATUS",
                "interviewId", interviewId,
                "status", status,
                "message", message,
                "timestamp", System.currentTimeMillis()
        );

        String destination = "/topic/interview/" + interviewId;
        messagingTemplate.convertAndSend(destination, payload);
        log.debug("推送面试状态: interviewId={}, status={}", interviewId, status);
    }

    /**
     * 推送 AI 分析进度
     * 客户端订阅: /topic/interview/{interviewId}/progress
     */
    public void pushAnalysisProgress(Long interviewId, int progress, String step) {
        Map<String, Object> payload = Map.of(
                "type", "ANALYSIS_PROGRESS",
                "interviewId", interviewId,
                "progress", progress,
                "step", step,
                "timestamp", System.currentTimeMillis()
        );

        String destination = "/topic/interview/" + interviewId + "/progress";
        messagingTemplate.convertAndSend(destination, payload);
        log.debug("推送分析进度: interviewId={}, progress={}%, step={}", interviewId, progress, step);
    }

    /**
     * 推送分析完成通知
     */
    public void pushAnalysisComplete(Long interviewId, Long reportId) {
        Map<String, Object> payload = Map.of(
                "type", "ANALYSIS_COMPLETE",
                "interviewId", interviewId,
                "reportId", reportId,
                "timestamp", System.currentTimeMillis()
        );

        String destination = "/topic/interview/" + interviewId + "/complete";
        messagingTemplate.convertAndSend(destination, payload);
        log.debug("推送分析完成: interviewId={}, reportId={}", interviewId, reportId);
    }

    /**
     * 推送分析失败通知
     */
    public void pushAnalysisFailed(Long interviewId, String errorMessage) {
        Map<String, Object> payload = Map.of(
                "type", "ANALYSIS_FAILED",
                "interviewId", interviewId,
                "error", errorMessage,
                "timestamp", System.currentTimeMillis()
        );

        String destination = "/topic/interview/" + interviewId + "/error";
        messagingTemplate.convertAndSend(destination, payload);
        log.debug("推送分析失败: interviewId={}, error={}", interviewId, errorMessage);
    }

    /**
     * 推送 HR 修正通知给候选人
     * 客户端订阅: /topic/user/{userId}/notifications
     */
    public void pushHrCorrectionNotification(Long userId, Long reportId, Long tenantId) {
        Map<String, Object> payload = Map.of(
                "type", "HR_CORRECTION",
                "reportId", reportId,
                "tenantId", tenantId,
                "message", "您的面试报告已被HR修正",
                "timestamp", System.currentTimeMillis()
        );

        String destination = "/topic/user/" + userId + "/notifications";
        messagingTemplate.convertAndSend(destination, payload);
        log.debug("推送HR修正通知: userId={}, reportId={}", userId, reportId);
    }
}
