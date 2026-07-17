package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.InterviewSession;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface InterviewSessionMapper extends BaseMapper<InterviewSession> {

    @Select("SELECT * FROM t_interview_session WHERE invite_code = #{code} LIMIT 1")
    InterviewSession selectByInviteCode(@Param("code") String code);
}
