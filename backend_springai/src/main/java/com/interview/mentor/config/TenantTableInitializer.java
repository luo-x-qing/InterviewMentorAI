package com.interview.mentor.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.DependsOn;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import jakarta.annotation.PostConstruct;
import java.sql.Connection;

/**
 * 租户表初始化器 —— 应用启动时自动执行 schema-tenant.sql 建表（幂等，使用 IF NOT EXISTS）。
 * <p>
 * 项目已从 schema-per-tenant 迁移到行级隔离（共享 schema + tenant_id 列），
 * 所有租户业务表只需创建一次。本初始化器确保启动后租户表已存在，
 * 消除手动执行 SQL 的部署步骤。
 * </p>
 */
@Component
@DependsOn("dataSource")
@ConditionalOnProperty(name = "tenant.tables.auto-init", havingValue = "true", matchIfMissing = true)
public class TenantTableInitializer {

    private static final Logger log = LoggerFactory.getLogger(TenantTableInitializer.class);
    private final DataSource dataSource;

    public TenantTableInitializer(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @PostConstruct
    public void initTenantTables() {
        try (Connection conn = dataSource.getConnection()) {
            ClassPathResource resource = new ClassPathResource("schema-tenant.sql");
            log.info("正在执行租户表初始化脚本: schema-tenant.sql");
            ScriptUtils.executeSqlScript(conn, resource);
            log.info("租户表初始化完成（IF NOT EXISTS 保证幂等）");
        } catch (Exception e) {
            log.warn("租户表初始化失败（可能已存在或数据库未就绪）: {}", e.getMessage());
        }
    }
}
