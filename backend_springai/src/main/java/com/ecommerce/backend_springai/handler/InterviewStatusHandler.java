/**
 * WebSocket处理器（InterviewStatusHandler）
 * 
 * 功能说明：
 * - 处理WebSocket连接和消息
 * - 支持客户端订阅特定面试记录的状态更新
 * - 推送AI处理进度给Flutter前端
 */
package com.ecommerce.backend_springai.handler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class InterviewStatusHandler extends TextWebSocketHandler {

    /**
     * 存储所有活跃的WebSocket连接
     * Key: interviewId, Value: WebSocketSession
     */
    private final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        log.info("WebSocket连接建立, sessionId={}", session.getId());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.info("收到WebSocket消息: {}", payload);
        
        // 客户端发送订阅消息格式: {"interviewId": "123"}
        if (payload.contains("interviewId")) {
            String interviewId = extractInterviewId(payload);
            if (interviewId != null) {
                sessions.put(interviewId, session);
                log.info("客户端订阅面试记录状态, interviewId={}, sessionId={}", interviewId, session.getId());
                session.sendMessage(new TextMessage("{\"type\":\"subscribed\",\"interviewId\":\"" + interviewId + "\"}"));
            }
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        // 移除断开的连接
        sessions.values().removeIf(s -> s.equals(session));
        log.info("WebSocket连接关闭, sessionId={}", session.getId());
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        log.error("WebSocket传输错误, sessionId={}", session.getId(), exception);
        sessions.values().removeIf(s -> s.equals(session));
    }

    /**
     * 推送状态更新给订阅了该interviewId的客户端
     * 
     * @param interviewId 面试记录ID
     * @param status 状态信息
     */
    public void sendStatusUpdate(String interviewId, String status) {
        WebSocketSession session = sessions.get(interviewId);
        if (session != null && session.isOpen()) {
            try {
                String message = String.format(
                    "{\"type\":\"status_update\",\"interviewId\":\"%s\",\"status\":\"%s\"}",
                    interviewId, status
                );
                session.sendMessage(new TextMessage(message));
                log.info("推送状态更新, interviewId={}, status={}", interviewId, status);
            } catch (IOException e) {
                log.error("推送状态更新失败, interviewId={}", interviewId, e);
            }
        }
    }

    /**
     * 推送报告给订阅了该interviewId的客户端
     * 
     * @param interviewId 面试记录ID
     * @param report 报告内容
     */
    public void sendReport(String interviewId, String report) {
        WebSocketSession session = sessions.get(interviewId);
        if (session != null && session.isOpen()) {
            try {
                // 转义JSON中的特殊字符
                String escapedReport = report.replace("\\", "\\\\").replace("\"", "\\\"");
                String message = String.format(
                    "{\"type\":\"report_ready\",\"interviewId\":\"%s\",\"report\":\"%s\"}",
                    interviewId, escapedReport
                );
                session.sendMessage(new TextMessage(message));
                log.info("推送报告, interviewId={}", interviewId);
            } catch (IOException e) {
                log.error("推送报告失败, interviewId={}", interviewId, e);
            }
        }
    }

    private String extractInterviewId(String payload) {
        // 简单的JSON解析，提取interviewId值
        String[] parts = payload.split(":");
        if (parts.length >= 2) {
            return parts[1].replaceAll("[^0-9]", "").trim();
        }
        return null;
    }
}
