-- ============================================
-- InterviewMentorAI 数据库表结构
-- 适配H2数据库语法
-- ============================================

-- 面试记录表
CREATE TABLE IF NOT EXISTS interview_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    audio_file_id VARCHAR(36) NOT NULL,
    audio_file_path VARCHAR(500) NOT NULL,
    duration_seconds INT,
    status VARCHAR(20) NOT NULL DEFAULT 'PROCESSING',
    raw_transcript TEXT,
    dialogue_json TEXT,
    report_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audio_file_id ON interview_record(audio_file_id);
CREATE INDEX IF NOT EXISTS idx_status ON interview_record(status);
CREATE INDEX IF NOT EXISTS idx_created_at ON interview_record(created_at);
