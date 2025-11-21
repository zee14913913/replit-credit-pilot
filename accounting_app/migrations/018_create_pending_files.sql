
-- ============================================================
-- Phase 1-11: 文件上传确认系统
-- 用途：防止客户文件混乱，所有上传先进入待确认队列
-- 创建时间：2025-11-21
-- ============================================================

CREATE TABLE IF NOT EXISTS pending_files (
    id SERIAL PRIMARY KEY,
    
    -- 文件基本信息
    original_filename VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    
    -- OCR提取的信息
    extracted_customer_name VARCHAR(200),
    extracted_ic_number VARCHAR(50),
    extracted_bank VARCHAR(100),
    extracted_period VARCHAR(7),  -- YYYY-MM
    extracted_card_last4 VARCHAR(4),
    extracted_account_number VARCHAR(100),
    
    -- 匹配结果
    matched_customer_id INTEGER REFERENCES users(id),
    matched_company_id INTEGER REFERENCES companies(id),
    match_confidence DECIMAL(5,2),  -- 0-100
    match_reason TEXT,
    
    -- 验证状态
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending: 待确认
    -- matched: 自动匹配成功
    -- mismatch: 匹配失败需人工确认
    -- confirmed: 已确认可处理
    -- rejected: 已拒绝
    
    -- 确认信息
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    rejected_reason TEXT,
    notes TEXT,
    
    -- 处理状态
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    
    -- 关联信息
    raw_document_id INTEGER REFERENCES raw_documents(id),
    file_index_id INTEGER REFERENCES file_index(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_pending_files_status ON pending_files(verification_status);
CREATE INDEX IF NOT EXISTS idx_pending_files_customer ON pending_files(matched_customer_id);
CREATE INDEX IF NOT EXISTS idx_pending_files_uploaded ON pending_files(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_pending_files_processed ON pending_files(is_processed);

-- 约束
ALTER TABLE pending_files ADD CONSTRAINT chk_verification_status 
    CHECK (verification_status IN ('pending', 'matched', 'mismatch', 'confirmed', 'rejected'));

-- 自动更新时间戳
CREATE OR REPLACE FUNCTION update_pending_files_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pending_files_timestamp
    BEFORE UPDATE ON pending_files
    FOR EACH ROW
    EXECUTE FUNCTION update_pending_files_timestamp();

-- 注释
COMMENT ON TABLE pending_files IS 'Phase 1-11: 文件上传确认队列，防止客户文件混乱';
COMMENT ON COLUMN pending_files.verification_status IS '验证状态：pending/matched/mismatch/confirmed/rejected';
COMMENT ON COLUMN pending_files.match_confidence IS '匹配置信度 0-100，>80自动确认';
