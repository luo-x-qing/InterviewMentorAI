package com.interview.mentor.tenant;

/**
 * 多租户上下文 - 基于 ThreadLocal 存储当前请求的租户信息
 */
public class TenantContext {

    private static final ThreadLocal<TenantInfo> CURRENT_TENANT = new ThreadLocal<>();

    public static void setTenantInfo(TenantInfo info) {
        CURRENT_TENANT.set(info);
    }

    public static TenantInfo getTenantInfo() {
        return CURRENT_TENANT.get();
    }

    public static Long getTenantId() {
        TenantInfo info = CURRENT_TENANT.get();
        return info != null ? info.getTenantId() : null;
    }

    public static void clear() {
        CURRENT_TENANT.remove();
    }

    public static class TenantInfo {
        private final Long tenantId;

        public TenantInfo(Long tenantId) {
            this.tenantId = tenantId;
        }

        public Long getTenantId() {
            return tenantId;
        }
    }
}
