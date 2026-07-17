package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("sys_subscription")
public class Subscription {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long tenantId;
    private String planName;
    private Integer maxUsers;
    private Integer maxInterviewsMonth;
    private Integer maxKnowledgeDocs;
    private LocalDate startDate;
    private LocalDate endDate;
    private Integer status;
    private LocalDateTime createdAt;
}
