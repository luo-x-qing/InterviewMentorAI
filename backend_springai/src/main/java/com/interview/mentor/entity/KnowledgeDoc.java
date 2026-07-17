package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("t_knowledge_doc")
public class KnowledgeDoc {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long knowledgeBaseId;
    private String title;
    private String originalFilename;
    private String filePath;
    private String fileType;
    private Integer chunkCount;
    private String status;
    private Long createdBy;
    private LocalDateTime createdAt;
}
