/**
 * 面试记录Mapper接口（InterviewRecordMapper）
 * 
 * 功能说明：
 * - MyBatis Mapper接口，负责面试记录的数据库操作
 * - 继承BaseMapper，无需编写CRUD方法
 * - 由@MapperScan自动扫描注册为Spring Bean
 * - 供InterviewRecordService调用
 * 
 * 继承方法：
 * - insert(): 插入记录
 * - selectById(): 按ID查询
 * - selectList(): 查询列表
 * - updateById(): 更新记录
 * - deleteById(): 删除记录
 */
package com.ecommerce.backend_springai.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ecommerce.backend_springai.entity.InterviewRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface InterviewRecordMapper extends BaseMapper<InterviewRecord> {
    // 继承BaseMapper即可获得CRUD方法
    // 如需自定义SQL，可在此添加@Select注解或XML映射文件
}
