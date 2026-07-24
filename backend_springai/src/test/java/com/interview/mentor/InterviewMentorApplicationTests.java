package com.interview.mentor;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

/**
 * Spring Boot 上下文加载测试（需 MySQL 数据库）
 */
@SpringBootTest
class InterviewMentorApplicationTests {

    @Test
    void contextLoads() {
        // 验证 Spring 容器正常启动（含 Security / MyBatis-Plus / WebSocket）
    }
}
