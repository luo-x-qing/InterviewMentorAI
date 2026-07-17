package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("t_knowledge_base")
public class KnowledgeBase {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long tenantId;
    private String name;
    private String description;
    private String type;
    private Integer docCount;
    private String status;
    private Long createdBy;
    private LocalDateTime createdAt;
}
