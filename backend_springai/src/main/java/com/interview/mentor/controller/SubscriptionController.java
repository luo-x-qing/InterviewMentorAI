package com.interview.mentor.controller;

import com.interview.mentor.entity.Subscription;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.service.SubscriptionService;
import com.interview.mentor.tenant.TenantContext;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/subscription")
public class SubscriptionController {

    private final SubscriptionService subscriptionService;

    public SubscriptionController(SubscriptionService subscriptionService) {
        this.subscriptionService = subscriptionService;
    }

    /**
     * 获取当前订阅状态
     */
    @GetMapping("/current")
    public Result<Subscription> getCurrentSubscription() {
        Long tenantId = TenantContext.getTenantId();
        Subscription subscription = subscriptionService.getCurrentSubscription(tenantId);
        return Result.success(subscription);
    }

    /**
     * 获取订阅统计信息
     */
    @GetMapping("/stats")
    public Result<Map<String, Object>> getStats() {
        Long tenantId = TenantContext.getTenantId();
        Map<String, Object> stats = subscriptionService.getSubscriptionStats(tenantId);
        return Result.success(stats);
    }

    /**
     * 升级订阅计划
     */
    @PostMapping("/upgrade")
    public Result<Subscription> upgradePlan(@RequestBody Map<String, String> request) {
        Long tenantId = TenantContext.getTenantId();
        Subscription upgraded = subscriptionService.upgradePlan(tenantId, request.get("planName"));
        return Result.success(upgraded);
    }
}
