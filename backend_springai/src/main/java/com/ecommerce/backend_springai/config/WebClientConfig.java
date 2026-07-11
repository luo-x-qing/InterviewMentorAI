/**
 * WebClient 全局配置类（WebClientConfig）
 * 
 * 功能说明：
 * - 注册WebClient Bean，用于响应式HTTP调用
 * - 配置最大内存缓冲区为10MB，支持大文件/大响应体传输
 * - 主要服务于LlmService，用于调用大模型API接口
 */
package com.ecommerce.backend_springai.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    /**
     * 创建并配置WebClient实例
     * 
     * @param builder WebClient构建器，Spring自动注入
     * @return 配置好内存限制的WebClient实例
     */
    @Bean
    public WebClient webClient(WebClient.Builder builder) {
        return builder
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024))
                .build();
    }
}
