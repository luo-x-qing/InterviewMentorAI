/**
 * 应用配置类
 * 提供 RestTemplate 等 Bean 定义
 */
package com.ecommerce.backend_springai.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

@Configuration
public class AppConfig {
    
    /**
     * RestTemplate 配置
     * 用于调用 Python AI 后端
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
