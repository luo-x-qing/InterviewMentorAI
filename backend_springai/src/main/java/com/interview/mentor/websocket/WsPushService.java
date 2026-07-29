package com.interview.mentor.websocket;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class WsPushService {

    private static final Logger log = LoggerFactory.getLogger(WsPushService.class);

    private final SimpMessagingTemplate messagingTemplate;

    public WsPushService(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    public void pushInterviewStatus(Long interviewId, String status, String message) {
        Map<String, Object> payload = Map.of(
                "type", "INTERVIEW_STATUS",
                "interviewId", interviewId,
                "status", status,
                "message", message,
                "timestamp", System.currentTimeMillis()
        );
        messagingTemplate.convertAndSend("/topic/interview/" + interviewId, payload);
    }

    public void pushAnalysisProgress(Long interviewId, int progress, String step) {
        Map<String, Object> payload = Map.of(
                "type", "ANALYSIS_PROGRESS",
                "interviewId", interviewId,
                "progress", progress,
                "step", step,
                "timestamp", System.currentTimeMillis()
        );
        messagingTemplate.convertAndSend("/topic/interview/" + interviewId + "/progress", payload);
    }

    public void pushAnalysisComplete(Long interviewId, Long reportId) {
        Map<String, Object> payload = Map.of(
                "type", "ANALYSIS_COMPLETE",
                "interviewId", interviewId,
                "reportId", reportId,
                "timestamp", System.currentTimeMillis()
        );
        messagingTemplate.convertAndSend("/topic/interview/" + interviewId + "/complete", payload);
    }

    public void pushAnalysisFailed(Long interviewId, String errorMessage) {
        Map<String, Object> payload = Map.of(
                "type", "ANALYSIS_FAILED",
                "interviewId", interviewId,
                "error", errorMessage,
                "timestamp", System.currentTimeMillis()
        );
        messagingTemplate.convertAndSend("/topic/interview/" + interviewId + "/error", payload);
    }

}
