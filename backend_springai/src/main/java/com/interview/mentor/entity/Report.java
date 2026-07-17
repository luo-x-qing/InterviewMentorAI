package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("t_report")
public class Report {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long interviewId;
    private String reportMarkdown;
    private String finalMarkdown;
    private BigDecimal avgScore;
    private Integer proficientCount;
    private Integer weakCount;
    private Integer hrEdited;
    private Long hrEditedBy;
    private LocalDateTime hrEditedAt;
    private LocalDateTime createdAt;
}
