package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.InterviewRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

@Mapper
public interface InterviewRecordMapper extends BaseMapper<InterviewRecord> {

    /**
     * 面试列表查询（带筛选条件）
     */
    List<Map<String, Object>> selectListWithUser(
            @Param("tenantId") Long tenantId,
            @Param("status") String status,
            @Param("jobRole") String jobRole,
            @Param("userId") Long userId);

    /**
     * 按状态统计
     */
    List<Map<String, Object>> selectStatusStats(@Param("tenantId") Long tenantId);

    /**
     * 按岗位统计
     */
    List<Map<String, Object>> selectJobRoleStats(@Param("tenantId") Long tenantId);

    /**
     * 查询面试总数
     */
    int selectCountByTenant(@Param("tenantId") Long tenantId);
}
