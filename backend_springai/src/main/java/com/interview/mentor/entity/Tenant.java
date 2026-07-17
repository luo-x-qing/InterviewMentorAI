package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("sys_tenant")
public class Tenant {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String tenantName;
    private String schemaName;
    private String contactName;
    private String contactEmail;
    private Integer status;
    private Integer maxUsers;
    private Integer maxInterviewsMonth;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
