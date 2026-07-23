---
status: accepted
---

# 多租户隔离采用共享 schema + 行级 tenant_id，而非 schema-per-tenant

## 决策

backend_springai 的多租户隔离采用**单库共享 schema + 每表 `tenant_id` 列 + 行级过滤**，由 MyBatis-Plus 的 `TenantLineInnerInterceptor` 在 SQL 层自动注入 `WHERE tenant_id = ?`。租户身份写入 JWT claim，请求经 `TenantContextFilter` 建立 `TenantContext`（ThreadLocal），拦截器从中取值。**明确否决 schema-per-tenant（每租户独立 schema/库 + 动态数据源路由）。**

## 背景与理由

代码库此前同时携带两种范式的碎片：`TenantContext`/`TenantService` 维护 `schemaName`（schema 隔离迹象），但所有实体又都带 `tenant_id` 列并靠手写 `.eq(tenantId)` 过滤（行级隔离迹象），而真正的 schema 切换动作从不存在——`schemaName` 是死值，`schema-tenant.sql` 从不为新租户执行，只有单一 datasource。

选择行级隔离的理由：与既有事实一致（每表已有 `tenant_id`、单 datasource），改动最小；隔离逻辑可下沉到单一拦截器成为深模块，消除各 Service 手写过滤的遗漏（正是一处跨租户数据泄漏的根因）。schema-per-tenant 需要落地建库自动化、按租户管理连接池、复杂迁移，等于推翻现状重做，其更强的物理隔离对当前 MVP 阶段不构成必要收益。

## 后果

- 隔离正确性依赖「查询时 `TenantContext` 已建立」这一前提。约定：**上下文为空则拦截器跳过过滤**（保住登录/认证期对 `sys_user` 的查询）。
- 无 `tenant_id` 列的全局表（`sys_tenant`/`sys_role`/`sys_permission`/关联表）及需跨租户可见的 `t_knowledge_document` 进拦截器忽略名单。
- 异步线程（如未来修复 `@Async` 后的 AI 分析回写）不会自动继承 ThreadLocal 上下文，需配套 TaskDecorator 传播——留待后续候选处理。
