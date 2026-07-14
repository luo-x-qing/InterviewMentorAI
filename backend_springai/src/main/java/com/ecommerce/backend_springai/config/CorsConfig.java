/**
 * 跨域配置类（CorsConfig）
 * 
 * 功能说明：
 * - 配置全局CORS（跨域资源共享）策略
 * - 允许Flutter前端（Android/Web）跨域访问后端接口
 * - 支持GET、POST、PUT、DELETE、OPTIONS请求方法
 * - 允许携带凭证（Cookie），预检请求缓存1小时
 */
package com.ecommerce.backend_springai.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.lang.NonNull;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class CorsConfig implements WebMvcConfigurer {

    /**
     * 添加跨域映射规则
     * 
     * @param registry CORS注册表，用于配置跨域策略
     */
    @Override
    public void addCorsMappings(@NonNull CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowCredentials(true)
                .maxAge(3600);
    }
}
