package com.interview.mentor.tenant;

import com.interview.mentor.entity.Tenant;
import com.interview.mentor.mapper.TenantMapper;
import org.springframework.stereotype.Service;

/**
 * 租户服务 - 租户创建与管理
 */
@Service
public class TenantService {

    private final TenantMapper tenantMapper;

    public TenantService(TenantMapper tenantMapper) {
        this.tenantMapper = tenantMapper;
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
