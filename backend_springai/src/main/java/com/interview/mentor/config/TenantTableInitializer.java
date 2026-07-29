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

@Component
@DependsOn("dataSource")
@ConditionalOnProperty(name = "app.tables.auto-init", havingValue = "true", matchIfMissing = true)
public class TenantTableInitializer {

    private static final Logger log = LoggerFactory.getLogger(TenantTableInitializer.class);
    private final DataSource dataSource;

    public TenantTableInitializer(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @PostConstruct
    public void initTables() {
        try (Connection conn = dataSource.getConnection()) {
            ClassPathResource resource = new ClassPathResource("schema.sql");
            log.info("正在执行建表脚本: schema.sql");
            ScriptUtils.executeSqlScript(conn, resource);
            log.info("建表初始化完成（IF NOT EXISTS 保证幂等）");
        } catch (Exception e) {
            log.warn("建表初始化失败（可能已存在或数据库未就绪）: {}", e.getMessage());
        }
    }
}
