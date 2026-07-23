package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("t_interview")
public class InterviewRecord {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long tenantId;
    private String title;
    private Long userId;
    private String jobRole;
    private Long createdBy;
    private Long candidateId;
    private String audioFileId;
    private String audioFilePath;
    private Integer durationSeconds;
    private String source;
    private String status;
    private String rawTranscript;
    private String dialogueJson;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
