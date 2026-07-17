package com.interview.mentor.tenant;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 多租户过滤器 - 从 JWT 或请求头解析 tenantId 并设置到 TenantContext
 * 优先级最高，在所有 Filter 之前执行
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TenantFilter extends OncePerRequestFilter {

    private static final String TENANT_HEADER = "X-Tenant-ID";
    private final TenantService tenantService;

    public TenantFilter(TenantService tenantService) {
        this.tenantService = tenantService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            // 1. 尝试从请求头获取 tenantId
            String tenantIdStr = request.getHeader(TENANT_HEADER);

            // 2. 如果没有请求头，从 JWT 中的 Authentication 获取
            if (tenantIdStr == null || tenantIdStr.isBlank()) {
                Authentication auth = SecurityContextHolder.getContext().getAuthentication();
                if (auth != null && auth.getPrincipal() instanceof String username) {
                    tenantIdStr = tenantService.resolveTenantIdByUsername(username);
                }
            }

            // 3. 设置租户上下文
            if (tenantIdStr != null && !tenantIdStr.isBlank()) {
                Long tenantId = Long.parseLong(tenantIdStr);
                String schemaName = tenantService.resolveSchemaName(tenantId);
                TenantContext.setTenantInfo(new TenantContext.TenantInfo(tenantId, schemaName));
            } else {
                // 默认使用公共租户
                TenantContext.setTenantInfo(new TenantContext.TenantInfo(1L, "platform"));
            }

            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getServletPath();
        return path.startsWith("/auth/") || path.equals("/actuator/health");
    }
}
