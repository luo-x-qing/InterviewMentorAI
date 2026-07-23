package com.interview.mentor.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.TenantLineInnerInterceptor;
import com.interview.mentor.tenant.TenantLineHandlerImpl;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis-Plus 拦截器配置。
 *
 * <p>租户隔离沉为深模块：{@link TenantLineInnerInterceptor} 配合
 * {@link TenantLineHandlerImpl} 在 SQL 层自动为带 tenant_id 的表追加
 * {@code WHERE tenant_id = ?}，Service 层无需再手写过滤。
 *
 * <p>顺带注册分页插件，修复原本缺失导致的内存假分页。
 */
@Configuration
public class MyBatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();

        // 1. 租户行级隔离（必须先于分页插件）
        interceptor.addInnerInterceptor(new TenantLineInnerInterceptor(new TenantLineHandlerImpl()));

        // 2. 分页插件（修复原本缺失导致的内存假分页）
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));

        return interceptor;
    }
}
