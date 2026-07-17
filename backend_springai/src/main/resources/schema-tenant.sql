-- ============================================
-- InterviewMentorAI Tenant Schema
-- MySQL 8.0+ 语法（每个租户执行一次）
-- ============================================

-- -------------------------------------------
-- 1. 面试记录表 (原 interview_record → t_interview)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_interview (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       BIGINT       NOT NULL COMMENT '租户ID',
    title           VARCHAR(200) NULL     COMMENT '面试标题',
    created_by      BIGINT       NOT NULL COMMENT '创建者ID（HR或候选人自己）',
    candidate_id    BIGINT       NULL     COMMENT '候选人用户ID',
    audio_file_id   VARCHAR(36)  NULL     COMMENT '音频文件唯一ID',
    audio_file_path VARCHAR(500) NULL     COMMENT '音频文件路径',
    duration_seconds INT         NULL     COMMENT '音频时长（秒）',
    source          VARCHAR(20)  NOT NULL DEFAULT 'SELF' COMMENT 'SELF=自主录音 HR_INVITE=HR邀请',
    status          VARCHAR(20)  NOT NULL DEFAULT 'CREATED' COMMENT 'CREATED/PROCESSING/COMPLETED/FAILED',
    raw_transcript  LONGTEXT     NULL     COMMENT '原始语音转文字',
    dialogue_json   LONGTEXT     NULL     COMMENT '对话JSON（清洗后）',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_candidate_id (candidate_id),
    INDEX idx_created_by (created_by),
    INDEX idx_status (status),
    INDEX idx_source (source),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='面试记录表';

-- -------------------------------------------
-- 2. 评估表 (逐条评估，方案核心表)
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
    hr_score        DECIMAL(5,2) NULL     COMMENT 'HR修正分数',
    hr_level        VARCHAR(20)  NULL     COMMENT 'HR修正等级',
    hr_remark       TEXT         NULL     COMMENT 'HR评语',
    hr_edited_by    BIGINT       NULL     COMMENT 'HR修正者ID',
    hr_edited_at    DATETIME     NULL     COMMENT 'HR修正时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_interview_id (interview_id),
    INDEX idx_question_index (question_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评估表（逐条评估）';

-- -------------------------------------------
-- 3. 复盘报告表 (AI原始 + HR修正后 双版本)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_report (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    interview_id    BIGINT       NOT NULL COMMENT '面试记录ID(UNIQUE)',
    report_markdown LONGTEXT     NULL     COMMENT 'AI生成的原始报告(Markdown)',
    final_markdown  LONGTEXT     NULL     COMMENT 'HR修正后的最终报告(Markdown)',
    avg_score       DECIMAL(5,2) NULL     COMMENT '综合平均分',
    proficient_count INT         NULL     COMMENT '优秀题数',
    weak_count      INT          NULL     COMMENT '薄弱题数',
    hr_edited       TINYINT      NOT NULL DEFAULT 0 COMMENT '是否经过HR修正 0=否 1=是',
    hr_edited_by    BIGINT       NULL     COMMENT 'HR修正者ID',
    hr_edited_at    DATETIME     NULL     COMMENT 'HR修正时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_interview_id (interview_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复盘报告表';

-- -------------------------------------------
-- 4. 面试会话表 (HR邀请码机制)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_interview_session (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       BIGINT       NOT NULL COMMENT '租户ID',
    title           VARCHAR(200) NOT NULL COMMENT '面试会话标题',
    created_by      BIGINT       NOT NULL COMMENT 'HR创建者ID',
    invite_code     VARCHAR(8)   NOT NULL COMMENT '邀请码(6位大写字母)',
    candidate_name  VARCHAR(50)  NULL     COMMENT '候选人姓名',
    candidate_phone VARCHAR(20)  NULL     COMMENT '候选人手机号',
    interview_id    BIGINT       NULL     COMMENT '关联面试记录ID（候选人完成录音后填入）',
    status          VARCHAR(20)  NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING=待录音 COMPLETED=已完成 EXPIRED=已过期',
    expire_at       DATETIME     NULL     COMMENT '邀请码过期时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_invite_code (invite_code),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_created_by (created_by),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='面试会话表（HR邀请码）';

-- -------------------------------------------
-- 5. 知识库表 (两层结构: 知识库 → 文档)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS t_knowledge_base (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       BIGINT       NOT NULL COMMENT '租户ID',
    name            VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description     VARCHAR(500) NULL     COMMENT '描述',
    type            VARCHAR(30)  NOT NULL COMMENT 'job_description/interview_guide/reference_answer',
    doc_count       INT          NOT NULL DEFAULT 0 COMMENT '文档数量',
    status          VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    created_by      BIGINT       NULL     COMMENT '创建者ID',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

CREATE TABLE IF NOT EXISTS t_knowledge_doc (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    knowledge_base_id   BIGINT       NOT NULL COMMENT '所属知识库ID',
    title               VARCHAR(200) NOT NULL COMMENT '文档标题',
    original_filename   VARCHAR(200) NULL     COMMENT '原始文件名',
    file_path           VARCHAR(500) NOT NULL COMMENT '存储路径',
    file_type           VARCHAR(20)  NOT NULL COMMENT 'pdf/docx/txt/md',
    chunk_count         INT          NOT NULL DEFAULT 0 COMMENT '切片数量',
    status              VARCHAR(20)  NOT NULL DEFAULT 'UPLOADED' COMMENT 'UPLOADED/INDEXING/READY/FAILED',
    created_by          BIGINT       NULL     COMMENT '上传者ID',
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_knowledge_base_id (knowledge_base_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档表';

-- -------------------------------------------
-- 6. 知识库文档片段表 (RAG向量检索)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_chunk (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    document_id     BIGINT       NOT NULL COMMENT '关联文档ID',
    tenant_id       BIGINT       NOT NULL COMMENT '租户ID',
    chunk_index     INT          NOT NULL COMMENT '片段序号',
    chunk_text      TEXT         NOT NULL COMMENT '片段文本',
    token_count     INT          NULL     COMMENT 'Token数量',
    embedding_id    VARCHAR(100) NULL     COMMENT '向量存储ID',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_document_id (document_id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_embedding_id (embedding_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档片段表';

-- -------------------------------------------
-- 7. 评估模板表（可选，MVP后扩展）
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS evaluation_template (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       BIGINT       NULL     COMMENT 'NULL=平台公共模板',
    template_name   VARCHAR(100) NOT NULL COMMENT '模板名称',
    job_role        VARCHAR(50)  NOT NULL COMMENT '适用岗位',
    dimensions_json TEXT         NOT NULL COMMENT '评分维度JSON',
    weight_json     TEXT         NULL     COMMENT '权重配置JSON',
    is_public       TINYINT      NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_job_role (job_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评估模板表';

-- -------------------------------------------
-- 8. 操作日志表（审计）
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       BIGINT       NULL     COMMENT '租户ID',
    user_id         BIGINT       NULL     COMMENT '操作者ID',
    action          VARCHAR(50)  NOT NULL COMMENT '操作类型',
    resource_type   VARCHAR(50)  NULL     COMMENT '资源类型',
    resource_id     BIGINT       NULL     COMMENT '资源ID',
    detail_json     TEXT         NULL     COMMENT '操作详情JSON',
    ip_address      VARCHAR(50)  NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';
