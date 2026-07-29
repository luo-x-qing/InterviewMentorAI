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

    List<Evaluation> selectByInterviewId(@Param("interviewId") Long interviewId);

    Map<String, Object> selectEvaluationStats(@Param("interviewId") Long interviewId);
}
