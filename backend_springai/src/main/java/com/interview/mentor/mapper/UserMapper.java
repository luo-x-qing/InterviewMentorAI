package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    @Select("SELECT r.role_code FROM sys_role r " +
            "INNER JOIN sys_user_role ur ON ur.role_id = r.id " +
            "WHERE ur.user_id = #{userId}")
    List<String> selectRoleCodesByUserId(@Param("userId") Long userId);

    @Select("SELECT p.perm_code FROM sys_permission p " +
            "INNER JOIN sys_role_permission rp ON rp.permission_id = p.id " +
            "INNER JOIN sys_user_role ur ON ur.role_id = rp.role_id " +
            "WHERE ur.user_id = #{userId}")
    List<String> selectPermCodesByUserId(@Param("userId") Long userId);
}
