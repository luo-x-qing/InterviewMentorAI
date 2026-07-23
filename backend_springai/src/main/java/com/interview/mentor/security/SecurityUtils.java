package com.interview.mentor.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

/**
 * 安全上下文工具 —— 统一解析「当前用户」，取代各控制器散落的 {@code userId = null} TODO。
 */
public final class SecurityUtils {

    private SecurityUtils() {
    }

    /**
     * 当前登录用户ID；未认证或 principal 非 AuthUser 时返回 null。
     */
    public static Long currentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getPrincipal() instanceof AuthUser authUser) {
            return authUser.getUserId();
        }
        return null;
    }
}
