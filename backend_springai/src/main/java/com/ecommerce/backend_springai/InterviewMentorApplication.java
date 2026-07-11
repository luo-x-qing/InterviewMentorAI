/**
 * InterviewMentorAI Spring Boot 启动类
 * 
 * 功能说明：
 * - 启动Spring Boot应用，自动装配所有组件
 * - 通过@MapperScan扫描repository包下的MyBatis Mapper接口
 * - 作为整个后端服务的入口，集成AI面试复盘功能
 */
package com.ecommerce.backend_springai;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.ecommerce.backend_springai.repository")
public class InterviewMentorApplication {

    /**
     * 应用程序主入口方法
     * 
     * @param args 命令行启动参数
     */
    public static void main(String[] args) {
        SpringApplication.run(InterviewMentorApplication.class, args);
    }
}
