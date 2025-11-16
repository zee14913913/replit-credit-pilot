-- 012_raw_statement_complete_storage.sql
-- 实现账单100%无遗漏解析和原件同步存储
-- 版本: V2025.11
-- 功能: 所有账单行（包括汇总、标题、异常）全部保存，通过original_line_type区分

BEGIN;

-- =============================================================================
-- 1. 原始账单行表 raw_bank_statement
-- 存储所有账单原文，包括明细行、汇总行、标题行、备注行、异常行
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw_bank_statement (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 账单文件标识
    file_id VARCHAR(64) NOT NULL,  -- 账单文件唯一ID
    account_id VARCHAR(32) NOT NULL,  -- 账户卡号/ID
    
    -- 原始行信息
    line_number INTEGER NOT NULL CHECK (line_number >= 1),  -- 账单原始行号（从1开始）
    original_line TEXT NOT NULL CHECK (length(original_line) > 0 AND length(original_line) <= 2000),  -- 账单原文
    
    -- 行类型分类
    original_line_type VARCHAR(20) NOT NULL CHECK (
        original_line_type IN ('detail', 'summary', 'remark', 'header', 'error', 'footer', 'blank')
    ),  -- detail=明细行, summary=汇总行, remark=备注, header=标题, error=异常, footer=页脚, blank=空行
    
    -- 结构化数据
    parsed_json TEXT,  -- JSON格式的结构化数据
    
    -- 解析状态
    parse_status VARCHAR(10) NOT NULL DEFAULT 'pending' CHECK (
        parse_status IN ('success', 'fail', 'manual_edit', 'pending')
    ),
    parse_error_msg TEXT CHECK (length(parse_error_msg) <= 2000),  -- 解析错误信息
    
    -- 审计信息
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    user_modified_by VARCHAR(64) CHECK (user_modified_by IS NULL OR user_modified_by GLOB '[A-Za-z][A-Za-z0-9_-]*'),  -- 手动修订操作者
    
    -- 索引优化
    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id) ON DELETE CASCADE
);

-- 创建索引提高查询性能
CREATE INDEX IF NOT EXISTS idx_raw_statement_file ON raw_bank_statement(file_id);
CREATE INDEX IF NOT EXISTS idx_raw_statement_account ON raw_bank_statement(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_statement_type ON raw_bank_statement(original_line_type);
CREATE INDEX IF NOT EXISTS idx_raw_statement_status ON raw_bank_statement(parse_status);

-- =============================================================================
-- 2. 扩展transactions表：添加原始行类型和溯源字段
-- =============================================================================

-- 为transactions表添加新字段（如果不存在）
-- SQLite不支持ALTER TABLE ADD COLUMN IF NOT EXISTS，需要重建表

CREATE TABLE IF NOT EXISTS transactions_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT,
    customer_id INTEGER,
    card_id INTEGER,
    statement_id INTEGER,
    
    -- 原有字段
    transaction_date TEXT,
    description TEXT,
    amount REAL,
    transaction_type TEXT,
    category TEXT,
    merchant_category TEXT,
    
    -- Supplier相关字段
    is_supplier BOOLEAN DEFAULT 0,
    supplier_name TEXT,
    supplier_fee REAL,
    is_merchant_fee BOOLEAN DEFAULT 0,
    fee_reference_id INTEGER,
    is_fee_split BOOLEAN DEFAULT 0,
    
    -- 🆕 新增字段：原始行类型和溯源
    raw_statement_id INTEGER,  -- 关联raw_bank_statement.id，支持溯源
    original_line_type VARCHAR(20) DEFAULT 'detail' CHECK (
        original_line_type IN ('detail', 'summary', 'remark', 'header', 'error', 'footer', 'blank')
    ),
    
    -- 🆕 验证和修订状态
    verify_status VARCHAR(20) DEFAULT 'unverified' CHECK (
        verify_status IN ('verified', 'unverified', 'manual_pending', 'error')
    ),
    
    -- 审计信息
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (statement_id) REFERENCES monthly_statements(id),
    FOREIGN KEY (fee_reference_id) REFERENCES transactions(id),
    FOREIGN KEY (raw_statement_id) REFERENCES raw_bank_statement(id)
);

-- =============================================================================
-- 3. 账户配置表 account_config（如果不存在）
-- =============================================================================

CREATE TABLE IF NOT EXISTS account_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id VARCHAR(32) NOT NULL UNIQUE,  -- 账户ID
    bank_type VARCHAR(50) NOT NULL CHECK (
        bank_type IN ('CIMB', 'Maybank', 'Public Bank', 'RHB', 'Hong Leong', 'AmBank', 
                      'Alliance', 'HSBC', 'UOB', 'OCBC', 'GX Bank', 'Others')
    ),
    owner_name VARCHAR(100) NOT NULL,
    account_no VARCHAR(32),
    status VARCHAR(10) DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'hidden')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 4. 审计日志扩展：记录所有原始行的修订操作
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw_statement_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_statement_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'CREATE', 'UPDATE', 'DELETE', 'MANUAL_EDIT'
    old_value TEXT,  -- JSON格式的修改前数据
    new_value TEXT,  -- JSON格式的修改后数据
    modified_by VARCHAR(64),
    modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (raw_statement_id) REFERENCES raw_bank_statement(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_raw_statement ON raw_statement_audit_logs(raw_statement_id);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON raw_statement_audit_logs(action_type);

-- =============================================================================
-- 5. 数据迁移说明
-- =============================================================================

-- 迁移现有transactions数据到transactions_v2（如果需要）
-- 注意：实际执行时需要先备份数据，然后逐步迁移

-- INSERT INTO transactions_v2 
-- SELECT *, NULL, 'detail', 'unverified', created_at, updated_at
-- FROM transactions;

-- DROP TABLE transactions;
-- ALTER TABLE transactions_v2 RENAME TO transactions;

COMMIT;

-- =============================================================================
-- 使用说明
-- =============================================================================
-- 1. 所有账单上传后，先逐行插入raw_bank_statement表
-- 2. 解析器识别行类型（detail/summary/remark等），设置original_line_type
-- 3. 明细行（detail）解析后插入transactions表，同时记录raw_statement_id
-- 4. 汇总行（summary）、标题行（header）等仅存储在raw_bank_statement，不插入transactions
-- 5. 所有手动修订操作记录到raw_statement_audit_logs
-- 6. 前端可通过raw_statement_id溯源到原始账单行
