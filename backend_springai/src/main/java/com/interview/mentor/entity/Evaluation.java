package com.interview.mentor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("t_evaluation")
public class Evaluation {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long tenantId;
    private Long interviewId;
    private Integer questionIndex;
    private String question;
    private String answer;
    private BigDecimal aiScore;
    private String aiLevel;
    private String aiStrengths;
    private String aiWeaknesses;
    private String aiCorrection;
    private String aiKnowledgePoints;
    private BigDecimal hrScore;
    private String hrLevel;
    private String hrRemark;
    private Long hrEditedBy;
    private LocalDateTime hrEditedAt;
    private LocalDateTime createdAt;
}
