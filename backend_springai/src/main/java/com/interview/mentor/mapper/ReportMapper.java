package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.Report;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface ReportMapper extends BaseMapper<Report> {

    @Select("SELECT * FROM t_report WHERE interview_id = #{interviewId} LIMIT 1")
    Report selectByInterviewId(@Param("interviewId") Long interviewId);
}
