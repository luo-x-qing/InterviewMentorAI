package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("t_interview_session")
public class InterviewSession {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long tenantId;
    private String title;
    private Long createdBy;
    private String inviteCode;
    private String candidateName;
    private String candidatePhone;
    private Long interviewId;
    private String status;
    private LocalDateTime expireAt;
    private LocalDateTime createdAt;
}
