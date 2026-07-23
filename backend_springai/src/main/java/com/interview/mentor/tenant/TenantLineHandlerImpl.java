package com.interview.mentor.tenant;

import com.baomidou.mybatisplus.extension.plugins.handler.TenantLineHandler;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.expression.LongValue;

import java.util.Set;

/**
 * 租户行级隔离处理器 —— 租户隔离的核心决策点，也是测试面。
 *
 * <p>从 {@link TenantContext} 取当前租户ID，为带 tenant_id 的表自动注入过滤条件。
 * 两条正确性约定见 {@code ignoreTable}。
 */
public class TenantLineHandlerImpl implements TenantLineHandler {

    /**
     * 不参与租户行级过滤的表：
     * - 全局表（无 tenant_id 列或天然跨租户）与关联表
     * - t_knowledge_document：保留 Service 层「私有 OR 公共」可见性逻辑
     */
    static final Set<String> IGNORE_TENANT_TABLES = Set.of(
            "sys_tenant",
            "sys_role",
            "sys_user_role",
            "sys_permission",
            "sys_role_permission",
            "t_knowledge_doc",
            "t_knowledge_document"
    );

    private static final String TENANT_COLUMN = "tenant_id";

    @Override
    public Expression getTenantId() {
        Long tenantId = TenantContext.getTenantId();
        // 上下文为空时返回 0；配合 ignoreTable 已跳过，不会真正拼入 SQL
        return new LongValue(tenantId != null ? tenantId : 0L);
    }

    @Override
    public String getTenantIdColumn() {
        return TENANT_COLUMN;
    }

    @Override
    public boolean ignoreTable(String tableName) {
        // 上下文为空（登录/系统流程）一律跳过，避免 tenant_id = null/0 误伤登录
        if (TenantContext.getTenantId() == null) {
            return true;
        }
        return IGNORE_TENANT_TABLES.contains(tableName.toLowerCase());
    }
}
