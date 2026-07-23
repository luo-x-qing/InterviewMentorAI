package com.interview.mentor.async;

import com.interview.mentor.tenant.TenantContext;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

@Configuration
@EnableAsync
public class AsyncConfig {

    @Value("${async.core-pool-size:4}")
    private int corePoolSize;

    @Value("${async.max-pool-size:8}")
    private int maxPoolSize;

    @Value("${async.queue-capacity:50}")
    private int queueCapacity;

    @Value("${async.thread-name-prefix:ai-analysis-}")
    private String threadNamePrefix;

    @Value("${async.keep-alive-seconds:60}")
    private int keepAliveSeconds;

    @Bean("aiAnalysisExecutor")
    public Executor aiAnalysisExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(corePoolSize);
        executor.setMaxPoolSize(maxPoolSize);
        executor.setQueueCapacity(queueCapacity);
        executor.setThreadNamePrefix(threadNamePrefix);
        executor.setKeepAliveSeconds(keepAliveSeconds);
        executor.setRejectedExecutionHandler(
                new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        // 传播 TenantContext 到异步线程：否则回写 insert 时拿不到租户，tenant_id 会为 null（见 ADR-0001）
        executor.setTaskDecorator(tenantContextDecorator());
        executor.initialize();
        return executor;
    }

    /**
     * 提交时捕获当前请求线程的租户ID，在池线程执行前恢复、执行后清理。
     */
    private org.springframework.core.task.TaskDecorator tenantContextDecorator() {
        return runnable -> {
            Long tenantId = TenantContext.getTenantId();
            return () -> {
                if (tenantId != null) {
                    TenantContext.setTenantInfo(new TenantContext.TenantInfo(tenantId));
                }
                try {
                    runnable.run();
                } finally {
                    TenantContext.clear();
                }
            };
        };
    }
}
