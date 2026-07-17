-- ============================================
-- InterviewMentorAI Platform Schema
-- MySQL 8.0+ 语法
-- ============================================
-- MySQL 初始化
CREATE DATABASE platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE platform;
SOURCE schema-platform.sql;
-- -------------------------------------------
-- 1. 租户表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_tenant (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_name     VARCHAR(100) NOT NULL COMMENT '企业/机构名称',
    schema_name     VARCHAR(50)  NOT NULL COMMENT '对应 MySQL schema 名',
    contact_name    VARCHAR(50)  NULL     COMMENT '联系人',
    contact_email   VARCHAR(100) NULL     COMMENT '联系邮箱',
    status          TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=正常 2=试用',
    max_users       INT          NOT NULL DEFAULT 10 COMMENT '最大成员数',
    max_interviews_month INT     NOT NULL DEFAULT 100 COMMENT '月最大面试次数',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_schema_name (schema_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户表';

-- 预置公共租户
INSERT IGNORE INTO sys_tenant (id, tenant_name, schema_name, status, max_users, max_interviews_month)
VALUES (1, '公共租户 (个人用户)', 'platform', 1, 999999, 999999);

-- -------------------------------------------
-- 2. 用户表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL COMMENT '用户名/手机号/邮箱',
    password        VARCHAR(255) NOT NULL COMMENT 'BCrypt 加密密码',
    nickname        VARCHAR(50)  NULL     COMMENT '显示昵称',
    email           VARCHAR(100) NULL     COMMENT '邮箱',
    phone           VARCHAR(20)  NULL     COMMENT '手机号',
    avatar_url      VARCHAR(500) NULL     COMMENT '头像地址',
    tenant_id       BIGINT       NOT NULL COMMENT '所属租户ID',
    status          TINYINT      NOT NULL DEFAULT 1 COMMENT '0=禁用 1=启用',
    last_login_at   DATETIME     NULL     COMMENT '最后登录时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_username (username),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- -------------------------------------------
-- 3. 角色表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_role (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_code       VARCHAR(30)  NOT NULL COMMENT '角色编码',
    role_name       VARCHAR(50)  NOT NULL COMMENT '角色名称',
    description     VARCHAR(200) NULL     COMMENT '描述',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 预置角色
INSERT IGNORE INTO sys_role (id, role_code, role_name, description) VALUES
(1, 'PLATFORM_ADMIN', '平台管理员', '管理所有租户、订阅计划、系统配置'),
(2, 'TENANT_ADMIN',   '租户管理员', '管理本租户成员、知识库、查看所有面试报告'),
(3, 'TENANT_MEMBER',  '租户成员',   '普通成员：HR/候选人');

-- -------------------------------------------
-- 4. 用户角色关联表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user_role (
    user_id         BIGINT NOT NULL,
    role_id         BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    INDEX idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- -------------------------------------------
-- 5. 权限表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_permission (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    perm_code       VARCHAR(50)  NOT NULL COMMENT '权限编码',
    perm_name       VARCHAR(100) NOT NULL COMMENT '权限名称',
    module          VARCHAR(30)  NULL     COMMENT '所属模块',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_perm_code (perm_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

-- 预置权限
INSERT IGNORE INTO sys_permission (perm_code, perm_name, module) VALUES
('interview:create',    '创建面试',     'interview'),
('interview:view',      '查看面试记录', 'interview'),
('interview:view_all',  '查看租户所有面试', 'interview'),
('report:view',         '查看评估报告', 'report'),
('report:edit',         '人工修正评估报告', 'report'),
('report:export',       '导出报告',     'report'),
('knowledge:manage',    '知识库管理',   'knowledge'),
('tenant:manage',       '租户管理',     'tenant'),
('member:manage',       '成员管理',     'tenant'),
('subscription:manage', '订阅管理',     'subscription');

-- -------------------------------------------
-- 6. 角色权限关联表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_role_permission (
    role_id         BIGINT NOT NULL,
    permission_id   BIGINT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    INDEX idx_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- 平台管理员: 所有权限
INSERT IGNORE INTO sys_role_permission (role_id, permission_id)
SELECT 1, id FROM sys_permission;

-- 租户管理员: 除 subscription:manage 外的所有权限
INSERT IGNORE INTO sys_role_permission (role_id, permission_id)
SELECT 2, id FROM sys_permission WHERE perm_code != 'subscription:manage';

-- 租户成员: 仅面试和查看权限
INSERT IGNORE INTO sys_role_permission (role_id, permission_id)
SELECT 3, id FROM sys_permission WHERE perm_code IN ('interview:create', 'interview:view', 'report:view');

-- -------------------------------------------
-- 7. 订阅计划表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_subscription (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id           BIGINT       NOT NULL COMMENT '租户ID',
    plan_name           VARCHAR(30)  NOT NULL COMMENT 'FREE/BASIC/PRO/ENTERPRISE',
    max_users           INT          NULL     COMMENT '最大用户数',
    max_interviews_month INT         NULL     COMMENT '月最大面试次数',
    max_knowledge_docs  INT          NULL     COMMENT '最大知识库文档数',
    start_date          DATE         NOT NULL COMMENT '订阅开始日期',
    end_date            DATE         NOT NULL COMMENT '订阅到期日期',
    status              TINYINT      NOT NULL DEFAULT 1 COMMENT '0=过期 1=生效',
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订阅计划表';

-- 公共租户默认订阅
INSERT IGNORE INTO sys_subscription (tenant_id, plan_name, max_users, max_interviews_month, max_knowledge_docs, start_date, end_date, status)
VALUES (1, 'FREE', 999999, 999999, 999999, '2026-01-01', '2099-12-31', 1);
