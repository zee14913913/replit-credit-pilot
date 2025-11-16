-- ============================================================
-- 第三批次：批量管理功能数据库迁移
-- 用途：增量添加批量审核、审计日志相关字段
-- 创建时间：2025-11-16
-- ============================================================

-- 1. 在 credit_card_statements 表中新增字段（如果不存在）
ALTER TABLE credit_card_statements ADD COLUMN IF NOT EXISTS upload_status TEXT DEFAULT 'success';
ALTER TABLE credit_card_statements ADD COLUMN IF NOT EXISTS error_tag TEXT DEFAULT NULL;
ALTER TABLE credit_card_statements ADD COLUMN IF NOT EXISTS upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP;

-- 2. 在 transactions 表中新增字段（用于异常标记）
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS error_tag TEXT DEFAULT NULL;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS manual_verified BOOLEAN DEFAULT 0;

-- 3. 创建批量上传日志表（增量添加，不影响现有表）
CREATE TABLE IF NOT EXISTS batch_upload_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    batch_id TEXT NOT NULL,
    file_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    batch_action TEXT DEFAULT 'upload',
    status TEXT DEFAULT 'pending',
    reason TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- 4. 创建审计日志表（系统操作日志）
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_action TEXT NOT NULL,
    operator_email TEXT,
    operation_content TEXT,
    ip_address TEXT,
    status TEXT DEFAULT 'success',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. 在 customers 表中新增客户标签字段
ALTER TABLE customers ADD COLUMN IF NOT EXISTS tag_desc TEXT DEFAULT NULL;

-- ============================================================
-- 迁移完成
-- ============================================================
