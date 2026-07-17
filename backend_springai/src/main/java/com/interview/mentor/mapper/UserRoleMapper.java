package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.UserRole;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserRoleMapper extends BaseMapper<UserRole> {

    @Select("SELECT r.role_code FROM sys_role r " +
            "INNER JOIN sys_user_role ur ON ur.role_id = r.id " +
            "WHERE ur.user_id = #{userId}")
    List<String> selectRoleCodesByUserId(@Param("userId") Long userId);

    @Delete("DELETE FROM sys_user_role WHERE user_id = #{userId}")
    int deleteByUserId(@Param("userId") Long userId);
}
