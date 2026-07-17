package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.interview.mentor.entity.Subscription;
import com.interview.mentor.entity.User;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.SubscriptionMapper;
import com.interview.mentor.mapper.UserMapper;
import com.interview.mentor.service.SubscriptionService;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

@Service
public class SubscriptionServiceImpl implements SubscriptionService {

    private final SubscriptionMapper subscriptionMapper;
    private final UserMapper userMapper;

    public SubscriptionServiceImpl(SubscriptionMapper subscriptionMapper,
                                   UserMapper userMapper) {
        this.subscriptionMapper = subscriptionMapper;
        this.userMapper = userMapper;
    }

    @Override
    public Subscription getCurrentSubscription(Long tenantId) {
        return subscriptionMapper.selectOne(
                new LambdaQueryWrapper<Subscription>()
                        .eq(Subscription::getTenantId, tenantId)
                        .eq(Subscription::getStatus, 1)
                        .orderByDesc(Subscription::getCreatedAt)
                        .last("LIMIT 1"));
    }

    @Override
    public boolean checkQuota(String quotaType, Long tenantId) {
        Subscription subscription = getCurrentSubscription(tenantId);
        if (subscription == null) {
            return false;
        }

        switch (quotaType) {
            case "users":
                long userCount = userMapper.selectCount(
                        new LambdaQueryWrapper<User>().eq(User::getTenantId, tenantId));
                return userCount < subscription.getMaxUsers();

            case "interviews":
                // TODO: 查询当月面试次数
                return true;

            case "knowledge_docs":
                // TODO: 查询知识库文档数
                return true;

            default:
                return false;
        }
    }

    @Override
    public Subscription upgradePlan(Long tenantId, String planName) {
        Subscription current = getCurrentSubscription(tenantId);
        if (current == null) {
            throw new BusinessException(404, "未找到当前订阅");
        }

        // 检查是否已经是更高等级
        int currentLevel = getPlanLevel(current.getPlanName());
        int newLevel = getPlanLevel(planName);
        if (newLevel <= currentLevel) {
            throw new BusinessException(400, "只能升级到更高等级的计划");
        }

        // 停用当前订阅
        current.setStatus(0);
        subscriptionMapper.updateById(current);

        // 创建新订阅
        Subscription newSubscription = new Subscription();
        newSubscription.setTenantId(tenantId);
        newSubscription.setPlanName(planName);
        newSubscription.setMaxUsers(getMaxUsers(planName));
        newSubscription.setMaxInterviewsMonth(getMaxInterviews(planName));
        newSubscription.setMaxKnowledgeDocs(getMaxKnowledgeDocs(planName));
        newSubscription.setStartDate(LocalDate.now());
        newSubscription.setEndDate(LocalDate.now().plusYears(1));
        newSubscription.setStatus(1);
        newSubscription.setCreatedAt(java.time.LocalDateTime.now());

        subscriptionMapper.insert(newSubscription);
        return newSubscription;
    }

    @Override
    public Map<String, Object> getSubscriptionStats(Long tenantId) {
        Subscription subscription = getCurrentSubscription(tenantId);
        Map<String, Object> stats = new HashMap<>();

        if (subscription != null) {
            stats.put("plan_name", subscription.getPlanName());
            stats.put("max_users", subscription.getMaxUsers());
            stats.put("max_interviews_month", subscription.getMaxInterviewsMonth());
            stats.put("max_knowledge_docs", subscription.getMaxKnowledgeDocs());
            stats.put("end_date", subscription.getEndDate());

            // 查询当前用量
            long userCount = userMapper.selectCount(
                    new LambdaQueryWrapper<User>().eq(User::getTenantId, tenantId));
            stats.put("current_users", userCount);
        }

        return stats;
    }

    private int getPlanLevel(String planName) {
        return switch (planName) {
            case "FREE" -> 0;
            case "BASIC" -> 1;
            case "PRO" -> 2;
            case "ENTERPRISE" -> 3;
            default -> -1;
        };
    }

    private int getMaxUsers(String planName) {
        return switch (planName) {
            case "FREE" -> 5;
            case "BASIC" -> 20;
            case "PRO" -> 100;
            case "ENTERPRISE" -> 999999;
            default -> 5;
        };
    }

    private int getMaxInterviews(String planName) {
        return switch (planName) {
            case "FREE" -> 50;
            case "BASIC" -> 200;
            case "PRO" -> 1000;
            case "ENTERPRISE" -> 999999;
            default -> 50;
        };
    }

    private int getMaxKnowledgeDocs(String planName) {
        return switch (planName) {
            case "FREE" -> 10;
            case "BASIC" -> 50;
            case "PRO" -> 500;
            case "ENTERPRISE" -> 999999;
            default -> 10;
        };
    }
}
