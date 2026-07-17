package com.interview.mentor.service;

import com.interview.mentor.entity.Subscription;

import java.util.Map;

public interface SubscriptionService {

    /**
     * 获取租户当前订阅
     */
    Subscription getCurrentSubscription(Long tenantId);

    /**
     * 检查配额是否足够
     * @param quotaType 配额类型：users/interviews/knowledge_docs
     * @param tenantId 租户ID
     * @return 是否足够
     */
    boolean checkQuota(String quotaType, Long tenantId);

    /**
     * 升级订阅计划
     */
    Subscription upgradePlan(Long tenantId, String planName);

    /**
     * 获取订阅统计信息
     */
    Map<String, Object> getSubscriptionStats(Long tenantId);
}
