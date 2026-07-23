package com.interview.mentor.tenant;

import com.interview.mentor.security.JwtAuthenticationFilter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 租户上下文过滤器 —— 单一职责：建立并清理当前请求的 {@link TenantContext}。
 *
 * <p>必须排在 {@link JwtAuthenticationFilter} 之后：租户ID由认证过滤器从已验签 JWT
 * 的 tenantId claim 解析出、放入 request 属性，本过滤器再取出建立 ThreadLocal 上下文，
 * 并在请求结束时清理，防止线程复用导致的租户串号。
 *
 * <p>取代旧的 TenantFilter（其 @Order(HIGHEST_PRECEDENCE) 早于 Security、依赖尚未建立的
 * Authentication，且靠可伪造的 X-Tenant-ID header —— 租户身份现完全来自签名保护的 JWT）。
 */
@Component
public class TenantContextFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            Object tenantId = request.getAttribute(JwtAuthenticationFilter.TENANT_ID_ATTRIBUTE);
            if (tenantId instanceof Long id) {
                TenantContext.setTenantInfo(new TenantContext.TenantInfo(id));
            }
            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }
}
