package com.interview.mentor.tenant;

import com.interview.mentor.entity.Subscription;
import com.interview.mentor.entity.Tenant;
import com.interview.mentor.mapper.SubscriptionMapper;
import com.interview.mentor.mapper.TenantMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;

/**
 * 租户服务 - 租户创建与管理
 * <p>
 * 项目已从 schema-per-tenant 迁移到行级隔离（共享 schema + tenant_id），
 * 租户业务表由 {@link com.interview.mentor.config.TenantTableInitializer} 启动时统一创建。
 * 本服务负责租户记录的创建及关联资源（订阅）的初始化。
 * </p>
 */
@Service
public class TenantService {

    private static final Logger log = LoggerFactory.getLogger(TenantService.class);

    private final TenantMapper tenantMapper;
    private final SubscriptionMapper subscriptionMapper;

    public TenantService(TenantMapper tenantMapper, SubscriptionMapper subscriptionMapper) {
        this.tenantMapper = tenantMapper;
        this.subscriptionMapper = subscriptionMapper;
    }

    /**
     * 创建新租户（平台管理员操作），同时初始化默认 FREE 订阅。
     *
     * @param tenantName   租户名称（企业/机构名）
     * @param contactName  联系人姓名
     * @param contactEmail 联系人邮箱
     * @return 创建完成的租户实体（含自增 ID）
     */
    @Transactional
    public Tenant createTenant(String tenantName, String contactName, String contactEmail) {
        // 1. 创建租户记录
        Tenant tenant = new Tenant();
        tenant.setTenantName(tenantName);
        tenant.setContactName(contactName);
        tenant.setContactEmail(contactEmail);
        tenant.setStatus(1);
        tenant.setMaxUsers(10);
        tenant.setMaxInterviewsMonth(100);
        tenantMapper.insert(tenant);

        log.info("租户创建成功: id={}, name={}", tenant.getId(), tenantName);

        // 2. 初始化默认 FREE 订阅
        Subscription sub = new Subscription();
        sub.setTenantId(tenant.getId());
        sub.setPlanName("FREE");
        sub.setMaxUsers(tenant.getMaxUsers());
        sub.setMaxInterviewsMonth(tenant.getMaxInterviewsMonth());
        sub.setMaxKnowledgeDocs(100);
        sub.setStartDate(LocalDate.now());
        sub.setEndDate(LocalDate.of(2099, 12, 31));
        sub.setStatus(1);
        subscriptionMapper.insert(sub);

        log.info("租户 {} 默认 FREE 订阅初始化完成", tenant.getId());

        return tenant;
    }
}
