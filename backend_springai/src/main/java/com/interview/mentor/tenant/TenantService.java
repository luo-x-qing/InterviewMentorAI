package com.interview.mentor.tenant;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.interview.mentor.entity.Tenant;
import com.interview.mentor.mapper.TenantMapper;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

/**
 * 租户服务 - 解析 tenantId 与 schemaName 映射
 */
@Service
public class TenantService {

    private final TenantMapper tenantMapper;

    public TenantService(TenantMapper tenantMapper) {
        this.tenantMapper = tenantMapper;
    }

    /**
     * 根据 username 解析所属 tenantId
     */
    public String resolveTenantIdByUsername(String username) {
        // TODO: 实际实现需要查 sys_user 表，MVP阶段先返回公共租户
        return "1";
    }

    /**
     * 根据 tenantId 解析 schemaName（带缓存）
     */
    @Cacheable(value = "tenantSchema", key = "#tenantId")
    public String resolveSchemaName(Long tenantId) {
        Tenant tenant = tenantMapper.selectById(tenantId);
        return tenant != null ? tenant.getSchemaName() : "platform";
    }

    /**
     * 创建新租户（平台管理员操作）
     */
    public Tenant createTenant(String tenantName, String contactName, String contactEmail) {
        String schemaName = "tenant_" + System.currentTimeMillis();
        Tenant tenant = new Tenant();
        tenant.setTenantName(tenantName);
        tenant.setSchemaName(schemaName);
        tenant.setContactName(contactName);
        tenant.setContactEmail(contactEmail);
        tenant.setStatus(1);
        tenant.setMaxUsers(10);
        tenant.setMaxInterviewsMonth(100);
        tenantMapper.insert(tenant);

        // TODO: 自动执行 schema-tenant.sql 为新租户建表
        // TODO: 初始化默认角色、权限、订阅

        return tenant;
    }
}
