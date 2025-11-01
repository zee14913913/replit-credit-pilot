-- ============================================================
-- Phase 1-1: 1:1原件保护表结构
-- 用途：确保所有上传文件无删减、无添加、无更改，1:1落库
-- ============================================================

-- 1. 原件元数据表（所有上传文件必存）
CREATE TABLE IF NOT EXISTS raw_documents (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,              -- 分块SHA256，避免大文件超时
    file_size BIGINT NOT NULL,             -- 文件大小（字节）
    storage_path TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT now(),
    uploaded_by INT,
    source_engine VARCHAR(20) NOT NULL,    -- flask | fastapi
    module VARCHAR(50) NOT NULL,           -- credit-card | bank | savings | pos | supplier | reports
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',  -- uploaded | parsed | failed | reconciled
    total_lines INT,                       -- PDF/CSV总行数
    parsed_lines INT,                      -- 成功解析行数
    reconciliation_status VARCHAR(20),     -- match | mismatch | pending
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_raw_documents_company ON raw_documents(company_id);
CREATE INDEX idx_raw_documents_hash ON raw_documents(file_hash);
CREATE INDEX idx_raw_documents_status ON raw_documents(status);
CREATE INDEX idx_raw_documents_module ON raw_documents(module);

COMMENT ON TABLE raw_documents IS '原件必存表：所有上传文件的元数据，不管能否解析都要写入';
COMMENT ON COLUMN raw_documents.file_hash IS '分块SHA256哈希，防止大文件超时';
COMMENT ON COLUMN raw_documents.total_lines IS 'PDF/CSV总行数（用于对账）';
COMMENT ON COLUMN raw_documents.parsed_lines IS '成功解析行数（用于对账）';
COMMENT ON COLUMN raw_documents.reconciliation_status IS '行数对账状态：match=一致可入账, mismatch=不一致进异常中心';

-- 2. 原始文本逐行记录表
CREATE TABLE IF NOT EXISTS raw_lines (
    id SERIAL PRIMARY KEY,
    raw_document_id INT NOT NULL REFERENCES raw_documents(id) ON DELETE CASCADE,
    line_no INT NOT NULL,                  -- 行号（1-based）
    page_no INT,                           -- 页码（PDF专用）
    raw_text TEXT NOT NULL,                -- 原始文本内容
    parser_version VARCHAR(50),            -- 解析器版本号
    is_parsed BOOLEAN DEFAULT FALSE,       -- 是否已解析
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_raw_lines_document ON raw_lines(raw_document_id);
CREATE INDEX idx_raw_lines_line_no ON raw_lines(raw_document_id, line_no);
CREATE UNIQUE INDEX idx_raw_lines_unique ON raw_lines(raw_document_id, line_no);

COMMENT ON TABLE raw_lines IS '逐行原文表：PDF/CSV的每一行原始内容，用于防虚构交易';
COMMENT ON COLUMN raw_lines.line_no IS '行号（从1开始），用于对账';
COMMENT ON COLUMN raw_lines.is_parsed IS '标记该行是否已成功解析成业务记录';

-- 3. 文件迁移日志表（旧路径→新路径）
CREATE TABLE IF NOT EXISTS migration_logs (
    id SERIAL PRIMARY KEY,
    company_id INT,
    src_path TEXT NOT NULL,                -- 原路径
    dest_path TEXT,                        -- 目标路径
    module VARCHAR(50),                    -- credit-card | bank | savings | pos | supplier
    batch_id VARCHAR(50),                  -- 批次ID（按公司/月份分批）
    run_at TIMESTAMP NOT NULL DEFAULT now(),
    run_by VARCHAR(100),                   -- 执行人
    status VARCHAR(20) NOT NULL,           -- success | failed | skipped
    error_message TEXT,
    file_hash TEXT,                        -- 迁移前后hash校验
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_migration_logs_company ON migration_logs(company_id);
CREATE INDEX idx_migration_logs_status ON migration_logs(status);
CREATE INDEX idx_migration_logs_batch ON migration_logs(batch_id);

COMMENT ON TABLE migration_logs IS '文件迁移日志表：记录旧路径到新路径的迁移过程，支持分批回滚';
COMMENT ON COLUMN migration_logs.batch_id IS '批次ID，格式：COMPANY-{company_id}-{YYYYMM}';
COMMENT ON COLUMN migration_logs.status IS 'success=成功, failed=失败可重跑, skipped=跳过';

-- 4. 创建视图：文件对账状态
CREATE OR REPLACE VIEW v_raw_document_reconciliation AS
SELECT 
    rd.id,
    rd.company_id,
    rd.file_name,
    rd.module,
    rd.total_lines,
    rd.parsed_lines,
    rd.reconciliation_status,
    COUNT(rl.id) as actual_raw_lines_count,
    CASE 
        WHEN COUNT(rl.id) = rd.total_lines AND rd.parsed_lines = rd.total_lines THEN 'MATCH'
        WHEN COUNT(rl.id) != rd.total_lines THEN 'RAW_LINES_MISMATCH'
        WHEN rd.parsed_lines < rd.total_lines THEN 'PARTIAL_PARSE'
        ELSE 'UNKNOWN'
    END as validation_status
FROM raw_documents rd
LEFT JOIN raw_lines rl ON rd.id = rl.raw_document_id
GROUP BY rd.id, rd.company_id, rd.file_name, rd.module, rd.total_lines, rd.parsed_lines, rd.reconciliation_status;

COMMENT ON VIEW v_raw_document_reconciliation IS '文件对账视图：自动检查total_lines vs raw_lines行数 vs parsed_lines';
