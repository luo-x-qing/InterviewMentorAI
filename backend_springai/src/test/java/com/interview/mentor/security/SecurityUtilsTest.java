package com.interview.mentor.security;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.context.SecurityContextHolder;

import static org.junit.jupiter.api.Assertions.*;

/**
 * SecurityUtils.currentUserId 单元测试 —— 取代各控制器 userId=null 的核心解析点。
 */
class SecurityUtilsTest {

    @AfterEach
    void tearDown() {
        SecurityContextHolder.clearContext();
    }

    @Test
    @DisplayName("principal 为 AuthUser 时返回其 userId")
    void returnsUserId_whenAuthUserPrincipal() {
        AuthUser principal = new AuthUser(123L, "alice", "pwd", AuthorityUtils.NO_AUTHORITIES);
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities()));

        assertEquals(123L, SecurityUtils.currentUserId());
    }

    @Test
    @DisplayName("未认证时返回 null")
    void returnsNull_whenNoAuthentication() {
        assertNull(SecurityUtils.currentUserId());
    }

    @Test
    @DisplayName("principal 非 AuthUser 时返回 null（不抛异常）")
    void returnsNull_whenPrincipalNotAuthUser() {
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("plain-string", null, AuthorityUtils.NO_AUTHORITIES));

        assertNull(SecurityUtils.currentUserId());
    }
}
