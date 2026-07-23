package com.interview.mentor.tenant;

import net.sf.jsqlparser.expression.LongValue;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 租户行级隔离处理器的单元测试 —— 隔离决策的测试面。
 * 纯单元测试，不依赖 Spring 上下文或数据库。
 */
class TenantLineHandlerImplTest {

    private final TenantLineHandlerImpl handler = new TenantLineHandlerImpl();

    @AfterEach
    void tearDown() {
        // 防止 ThreadLocal 污染后续用例
        TenantContext.clear();
    }

    @Test
    @DisplayName("上下文有租户时，业务表参与过滤")
    void tenantTable_isFiltered_whenContextPresent() {
        TenantContext.setTenantInfo(new TenantContext.TenantInfo(42L));

        assertFalse(handler.ignoreTable("t_interview"), "业务表应参与租户过滤");
        assertEquals(42L, ((LongValue) handler.getTenantId()).getValue(), "应注入当前租户ID");
    }

    @Test
    @DisplayName("上下文为空时，所有表都跳过过滤（保住登录期 sys_user 查询）")
    void allTables_areIgnored_whenContextAbsent() {
        // 不设置 TenantContext，模拟登录/认证期

        assertTrue(handler.ignoreTable("sys_user"), "登录期查 sys_user 必须跳过，否则被 tenant_id=null 打死");
        assertTrue(handler.ignoreTable("t_interview"), "上下文为空时业务表也应跳过");
    }

    @Test
    @DisplayName("全局表始终在忽略名单中")
    void globalTables_areAlwaysIgnored() {
        TenantContext.setTenantInfo(new TenantContext.TenantInfo(1L));

        assertTrue(handler.ignoreTable("sys_tenant"));
        assertTrue(handler.ignoreTable("sys_role"));
        assertTrue(handler.ignoreTable("sys_user_role"));
        assertTrue(handler.ignoreTable("sys_permission"));
        assertTrue(handler.ignoreTable("sys_role_permission"));
    }

    @Test
    @DisplayName("知识库文档表跳过过滤，以保留「私有 OR 公共」跨租户可见性")
    void knowledgeDocument_isIgnored_forPublicVisibility() {
        TenantContext.setTenantInfo(new TenantContext.TenantInfo(7L));

        assertTrue(handler.ignoreTable("t_knowledge_document"),
                "公共文档需跨租户可见，不能被单一 tenant_id 过滤");
    }

    @Test
    @DisplayName("忽略名单大小写不敏感")
    void ignoreTable_isCaseInsensitive() {
        TenantContext.setTenantInfo(new TenantContext.TenantInfo(1L));

        assertTrue(handler.ignoreTable("SYS_TENANT"));
        assertTrue(handler.ignoreTable("T_Knowledge_Document"));
    }

    @Test
    @DisplayName("租户列名固定为 tenant_id")
    void tenantColumn_isTenantId() {
        assertEquals("tenant_id", handler.getTenantIdColumn());
    }
}
