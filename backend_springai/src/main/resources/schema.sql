-- ============================================
-- InterviewMentorAI Schema
-- MySQL 8.0+ 单库单schema
-- ============================================
CREATE DATABASE IF NOT EXISTS interview_mentor DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- -------------------------------------------
-- 1. 用户表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL COMMENT '用户名',
    password        VARCHAR(255) NOT NULL COMMENT 'BCrypt 加密密码',
    nickname        VARCHAR(50)  NULL     COMMENT '显示昵称',
    email           VARCHAR(100) NULL     COMMENT '邮箱',
    phone           VARCHAR(20)  NULL     COMMENT '手机号',
    avatar_url      VARCHAR(500) NULL     COMMENT '头像地址',
    status          TINYINT      NOT NULL DEFAULT 1 COMMENT '0=禁用 1=启用',
    last_login_at   DATETIME     NULL     COMMENT '最后登录时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- -------------------------------------------
-- 2. 面试记录表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_interview (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200) NULL     COMMENT '面试标题',
    user_id         BIGINT       NULL     COMMENT '用户ID',
    job_role        VARCHAR(100) NULL     COMMENT '应聘岗位',
    created_by      BIGINT       NOT NULL COMMENT '创建者ID',
    audio_file_id   VARCHAR(36)  NULL     COMMENT '音频文件唯一ID',
    audio_file_path VARCHAR(500) NULL     COMMENT '音频文件路径',
    duration_seconds INT         NULL     COMMENT '音频时长（秒）',
    status          VARCHAR(20)  NOT NULL DEFAULT 'CREATED' COMMENT 'CREATED/PROCESSING/COMPLETED/FAILED',
    raw_transcript  LONGTEXT     NULL     COMMENT '原始语音转文字',
    dialogue_json   LONGTEXT     NULL     COMMENT '对话JSON',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='面试记录表';

-- -------------------------------------------
-- 3. 评估表（逐条评估）
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_evaluation (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    interview_id    BIGINT       NOT NULL COMMENT '面试记录ID',
    question_index  INT          NOT NULL COMMENT '题目序号',
    question        TEXT         NOT NULL COMMENT '题目内容',
    answer          TEXT         NULL     COMMENT '候选人回答',
    ai_score        DECIMAL(5,2) NULL     COMMENT 'AI评分(0-100)',
    ai_level        VARCHAR(20)  NULL     COMMENT '优秀/良好/一般/较差',
    ai_strengths    TEXT         NULL     COMMENT 'AI识别的优点',
    ai_weaknesses   TEXT         NULL     COMMENT 'AI识别的不足',
    ai_correction   TEXT         NULL     COMMENT 'AI建议的改进答案',
    ai_knowledge_points TEXT     NULL     COMMENT '相关知识点',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_interview_id (interview_id),
    INDEX idx_question_index (question_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评估表';

-- -------------------------------------------
-- 4. 复盘报告表
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_report (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    interview_id    BIGINT       NOT NULL COMMENT '面试记录ID(UNIQUE)',
    report_markdown LONGTEXT     NULL     COMMENT 'AI生成的原始报告(Markdown)',
    avg_score       DECIMAL(5,2) NULL     COMMENT '综合平均分',
    proficient_count INT         NULL     COMMENT '优秀题数',
    weak_count      INT          NULL     COMMENT '薄弱题数',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_interview_id (interview_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复盘报告表';

-- -------------------------------------------
-- 5. 知识库文档表（原序号6）
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_knowledge_document (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200) NOT NULL COMMENT '文档标题',
    content         LONGTEXT     NULL     COMMENT '文档内容',
    doc_type        VARCHAR(50)  NULL     COMMENT '文档类型',
    job_role        VARCHAR(50)  NULL     COMMENT '适用岗位',
    tags            VARCHAR(500) NULL     COMMENT '标签(逗号分隔)',
    is_public       TINYINT      NOT NULL DEFAULT 0 COMMENT '0=私有 1=公开',
    embedding_status TINYINT     NOT NULL DEFAULT 0 COMMENT '0=待向量化 1=向量化中 2=完成',
    uploaded_by     BIGINT       NULL     COMMENT '上传者ID',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_type (doc_type),
    INDEX idx_job_role (job_role),
    INDEX idx_is_public (is_public),
    INDEX idx_uploaded_by (uploaded_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档表';

-- -------------------------------------------
-- 6. 操作日志表（审计，原序号7）
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT       NULL     COMMENT '操作者ID',
    action          VARCHAR(50)  NOT NULL COMMENT '操作类型',
    resource_type   VARCHAR(50)  NULL     COMMENT '资源类型',
    resource_id     BIGINT       NULL     COMMENT '资源ID',
    detail_json     TEXT         NULL     COMMENT '操作详情JSON',
    ip_address      VARCHAR(50)  NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- -------------------------------------------
-- 7. 评估模板表（预留扩展，原序号8）
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS evaluation_template (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    template_name   VARCHAR(100) NOT NULL COMMENT '模板名称',
    job_role        VARCHAR(50)  NOT NULL COMMENT '适用岗位',
    dimensions_json TEXT         NOT NULL COMMENT '评分维度JSON',
    weight_json     TEXT         NULL     COMMENT '权重配置JSON',
    is_public       TINYINT      NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_job_role (job_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评估模板表';
