package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.User;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.mapper.UserMapper;
import com.interview.mentor.tenant.TenantContext;
import com.interview.mentor.tenant.TenantService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/tenant")
public class TenantController {

    private final TenantService tenantService;
    private final UserMapper userMapper;

    public TenantController(TenantService tenantService, UserMapper userMapper) {
        this.tenantService = tenantService;
        this.userMapper = userMapper;
    }

    /**
     * 创建租户（仅平台管理员）
     */
    @PostMapping("/create")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public Result<Map<String, Object>> createTenant(@RequestBody Map<String, String> request) {
        var tenant = tenantService.createTenant(
                request.get("tenantName"),
                request.get("contactName"),
                request.get("contactEmail"));
        return Result.success(Map.of(
                "id", tenant.getId(),
                "tenantName", tenant.getTenantName(),
                "schemaName", tenant.getSchemaName()));
    }

    /**
     * 查看租户成员列表
     */
    @GetMapping("/members")
    @PreAuthorize("hasAnyRole('PLATFORM_ADMIN', 'TENANT_ADMIN')")
    public Result<IPage<User>> listMembers(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long tenantId = TenantContext.getTenantId();
        Page<User> pageParam = new Page<>(page, size);
        IPage<User> result = userMapper.selectPage(pageParam,
                new LambdaQueryWrapper<User>()
                        .eq(User::getTenantId, tenantId)
                        .orderByDesc(User::getCreatedAt));

        // 脱敏密码
        result.getRecords().forEach(u -> u.setPassword(null));
        return Result.success(result);
    }

    /**
     * 邀请成员加入租户
     */
    @PostMapping("/invite")
    @PreAuthorize("hasAnyRole('PLATFORM_ADMIN', 'TENANT_ADMIN')")
    public Result<Void> inviteMember(@RequestBody Map<String, String> request) {
        // TODO: 发送邀请邮件/短信，创建待接受的邀请记录
        // MVP阶段简化：直接返回成功
        return Result.success();
    }
}
