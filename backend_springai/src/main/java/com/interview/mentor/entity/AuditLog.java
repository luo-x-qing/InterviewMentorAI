package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("audit_log")
public class AuditLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long tenantId;
    private Long userId;
    private String action;
    private String resourceType;
    private Long resourceId;
    private String detailJson;
    private String ipAddress;
    private LocalDateTime createdAt;
}
