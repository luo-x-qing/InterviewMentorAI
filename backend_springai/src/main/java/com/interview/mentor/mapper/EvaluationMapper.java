package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.Evaluation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Mapper
public interface EvaluationMapper extends BaseMapper<Evaluation> {

    /**
     * 查询面试的所有评估（按题目序号排序）
     */
    List<Evaluation> selectByInterviewId(@Param("interviewId") Long interviewId);

    /**
     * HR修正评估
     */
    int hrCorrectEvaluation(@Param("id") Long id,
                            @Param("hrScore") BigDecimal hrScore,
                            @Param("hrLevel") String hrLevel,
                            @Param("hrRemark") String hrRemark,
                            @Param("hrEditedBy") Long hrEditedBy);

    /**
     * 查询面试的评估统计
     */
    Map<String, Object> selectEvaluationStats(@Param("interviewId") Long interviewId);
}
