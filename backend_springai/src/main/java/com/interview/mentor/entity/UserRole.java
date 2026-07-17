package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("sys_user_role")
public class UserRole {

    private Long userId;
    private Long roleId;
}
