/**
 * Web MVC 通用配置类（WebConfig）
 * 
 * 功能说明：
 * - 实现WebMvcConfigurer接口，提供Spring MVC扩展点
 * - 预留静态资源映射、格式化器等扩展接口
 * - 当前为空实现，可根据业务需求扩展
 */
package com.ecommerce.backend_springai.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    // 目前为空实现，可根据业务需求扩展
}
