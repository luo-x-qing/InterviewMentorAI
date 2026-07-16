/**
 * WebSocket配置类（WebSocketConfig）
 * 
 * 功能说明：
 * - 启用WebSocket支持
 * - 注册WebSocket端点 /ws
 * - 允许跨域连接
 */
package com.ecommerce.backend_springai.config;

import com.ecommerce.backend_springai.handler.InterviewStatusHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final InterviewStatusHandler statusHandler;

    public WebSocketConfig(InterviewStatusHandler statusHandler) {
        this.statusHandler = statusHandler;
    }

    @Override
    public void registerWebSocketHandlers(@NonNull WebSocketHandlerRegistry registry) {
        registry.addHandler(statusHandler, "/ws")
                .setAllowedOrigins("*");
    }
}
