package com.interview.mentor.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.interview.mentor.entity.Tenant;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TenantMapper extends BaseMapper<Tenant> {
}
