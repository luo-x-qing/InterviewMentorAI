package com.interview.mentor.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * JWT 租户 claim 往返测试 —— 验证租户身份随签名保护的 token 传播。
 * 纯单元测试，直接构造 JwtTokenProvider，不依赖 Spring。
 */
class JwtTokenProviderTenantTest {

    private JwtTokenProvider provider;

    @BeforeEach
    void setUp() {
        // 256 位以上密钥，满足 HMAC-SHA 要求
        String secret = "InterviewMentorAI-Test-Secret-Key-At-Least-256-Bits-Long-XXXX";
        provider = new JwtTokenProvider(secret, 3600_000L, 604800_000L);
    }

    private Authentication authFor(String username) {
        UserDetails userDetails = new User(username, "pwd", AuthorityUtils.NO_AUTHORITIES);
        Authentication auth = mock(Authentication.class);
        when(auth.getPrincipal()).thenReturn(userDetails);
        return auth;
    }

    @Test
    @DisplayName("写入 tenantId 的 token 能被解析回同一租户")
    void tenantId_roundTrips() {
        String token = provider.generateAccessToken(authFor("alice"), 99L);

        assertTrue(provider.validateToken(token));
        assertEquals("alice", provider.getUsernameFromToken(token));
        assertEquals(99L, provider.getTenantIdFromToken(token));
    }

    @Test
    @DisplayName("未写入 tenantId 时解析返回 null，而非报错")
    void tenantId_isNull_whenNotProvided() {
        String token = provider.generateAccessToken(authFor("bob"));

        assertTrue(provider.validateToken(token));
        assertNull(provider.getTenantIdFromToken(token));
    }

    @Test
    @DisplayName("被篡改的 token 验签失败（租户身份不可伪造）")
    void tamperedToken_failsValidation() {
        String token = provider.generateAccessToken(authFor("carol"), 5L);
        String tampered = token.substring(0, token.length() - 4) + "AAAA";

        assertFalse(provider.validateToken(tampered));
    }
}
