package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("sys_role_permission")
public class RolePermission {

    private Long roleId;
    private Long permissionId;
}
