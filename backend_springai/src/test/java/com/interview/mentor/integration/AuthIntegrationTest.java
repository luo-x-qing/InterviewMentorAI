package com.interview.mentor.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.interview.mentor.entity.dto.req.LoginRequest;
import com.interview.mentor.entity.dto.req.RegisterRequest;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Auth 认证链路 E2E 集成测试
 * <p>
 * 使用 H2 内存数据库 + 真实 Spring Security 过滤器链，验证：
 * 1. 注册 → 返回 JWT + userInfo
 * 2. 登录 → 返回 JWT + userInfo
 * 3. 携带 Token 访问受保护接口
 * 4. 无 Token 访问受保护接口返回 401/403
 * 5. Token 刷新
 * </p>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
@DisplayName("Auth 认证链路集成测试（需 MySQL）")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class AuthIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private static String accessToken;
    private static String refreshToken;
    private static final String TEST_USERNAME = "e2e_test_user_" + System.currentTimeMillis();
    private static final String TEST_PASSWORD = "test123456";

    @Test
    @Order(1)
    @DisplayName("1. 注册新用户 → 返回 JWT + 用户信息")
    void register() throws Exception {
        RegisterRequest req = new RegisterRequest();
        req.setUsername(TEST_USERNAME);
        req.setPassword(TEST_PASSWORD);
        req.setNickname("E2E测试用户");
        req.setEmail("e2e@test.com");
        req.setPhone("13800138000");

        String resp = mockMvc.perform(post("/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.data.refreshToken").isNotEmpty())
                .andExpect(jsonPath("$.data.userInfo.username").value(TEST_USERNAME))
                .andExpect(jsonPath("$.data.userInfo.nickname").value("E2E测试用户"))
                .andReturn()
                .getResponse()
                .getContentAsString();

        // 提取 Token 供后续测试使用
        Map<String, Object> body = objectMapper.readValue(resp, Map.class);
        Map<String, Object> data = (Map<String, Object>) body.get("data");
        accessToken = (String) data.get("accessToken");
        refreshToken = (String) data.get("refreshToken");

        Assertions.assertNotNull(accessToken, "accessToken 不应为空");
        Assertions.assertNotNull(refreshToken, "refreshToken 不应为空");
    }

    @Test
    @Order(2)
    @DisplayName("2. 已注册用户登录 → 返回 JWT")
    void login() throws Exception {
        LoginRequest req = new LoginRequest();
        req.setUsername(TEST_USERNAME);
        req.setPassword(TEST_PASSWORD);

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.data.userInfo.username").value(TEST_USERNAME));
    }

    @Test
    @Order(3)
    @DisplayName("3. 错误密码登录 → 返回 401")
    void loginWithWrongPassword() throws Exception {
        LoginRequest req = new LoginRequest();
        req.setUsername(TEST_USERNAME);
        req.setPassword("wrong_password");

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @Order(4)
    @DisplayName("4. 携带有效 Token 访问受保护接口 → 200")
    void accessProtectedEndpointWithValidToken() throws Exception {
        Assertions.assertNotNull(accessToken, "需先执行注册测试");

        mockMvc.perform(get("/user/profile")
                        .header("Authorization", "Bearer " + accessToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.username").value(TEST_USERNAME));
    }

    @Test
    @Order(5)
    @DisplayName("5. 无 Token 访问受保护接口 → 401/403")
    void accessProtectedEndpointWithoutToken() throws Exception {
        mockMvc.perform(get("/user/profile"))
                .andExpect(status().is4xxClientError());
    }

    @Test
    @Order(6)
    @DisplayName("6. Token 刷新 → 返回新 accessToken")
    void refreshTokenFlow() throws Exception {
        Assertions.assertNotNull(refreshToken, "需先执行注册测试");

        mockMvc.perform(post("/auth/refresh")
                        .param("refreshToken", refreshToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.accessToken").isNotEmpty());
    }

    @Test
    @Order(7)
    @DisplayName("7. 面试列表接口（需认证 + 租户上下文）→ 200")
    void accessInterviewListWithValidToken() throws Exception {
        Assertions.assertNotNull(accessToken, "需先执行注册测试");

        mockMvc.perform(get("/interview/list")
                        .header("Authorization", "Bearer " + accessToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}
