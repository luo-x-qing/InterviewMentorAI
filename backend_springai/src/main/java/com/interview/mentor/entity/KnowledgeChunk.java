package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("knowledge_chunk")
public class KnowledgeChunk {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long documentId;
    private Long tenantId;
    private Integer chunkIndex;
    private String chunkText;
    private Integer tokenCount;
    private String embeddingId;
    private LocalDateTime createdAt;
}
