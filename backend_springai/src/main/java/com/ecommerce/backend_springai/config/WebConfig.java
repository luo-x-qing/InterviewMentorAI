/**
 * Web MVC 通用配置类（WebConfig）
 * 
 * 功能说明：
 * - 实现WebMvcConfigurer接口，提供Spring MVC扩展点
 * - 预留静态资源映射、拦截器等配置入口
 * - 当前为空实现，后续可根据需求扩展
 */
package com.ecommerce.backend_springai.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    // 后续如需静态资源、拦截器在此扩展
}
