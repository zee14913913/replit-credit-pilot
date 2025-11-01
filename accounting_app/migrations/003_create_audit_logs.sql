-- Phase 1-4: 创建审计日志表
-- 执行日期: 2025-01-XX
-- 目的: 追踪所有敏感操作（导出、删除、修改规则、手工分录），确保合规性

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    user_id INTEGER,  -- 预留：关联users表
    username VARCHAR(100),  -- 操作人姓名或邮箱
    action_type VARCHAR(50) NOT NULL,  -- export, delete, rule_change, manual_entry, file_upload, config_change
    entity_type VARCHAR(50),  -- bank_statement, invoice, auto_posting_rule, journal_entry, file, etc.
    entity_id INTEGER,  -- 被操作实体的ID
    description TEXT NOT NULL,  -- 操作描述
    reason TEXT,  -- 操作原因（手工改账必须填写）
    ip_address VARCHAR(45),  -- IP地址（IPv4/IPv6）
    user_agent TEXT,  -- 浏览器UA
    request_method VARCHAR(10),  -- GET, POST, PUT, DELETE
    request_path VARCHAR(500),  -- API路径
    old_value JSONB,  -- 修改前的值（JSON格式）
    new_value JSONB,  -- 修改后的值（JSON格式）
    success BOOLEAN DEFAULT TRUE,  -- 操作是否成功
    error_message TEXT,  -- 失败时的错误信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_action_type CHECK (
        action_type IN ('export', 'delete', 'rule_change', 'manual_entry', 'file_upload', 
                       'config_change', 'batch_import', 'reconciliation', 'period_close', 'restore')
    )
);

-- 创建索引提升查询性能
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_action ON audit_logs(company_id, action_type);

-- 复合索引（常见查询模式）
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_lookup ON audit_logs(entity_type, entity_id);

-- 验证迁移结果
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'audit_logs'
    ) THEN
        RAISE EXCEPTION 'Migration failed: audit_logs table not created';
    END IF;
END $$;

-- 迁移完成
COMMENT ON TABLE audit_logs IS 'Phase 1-4: 审计日志表，追踪所有敏感操作';
COMMENT ON COLUMN audit_logs.reason IS '手工改账/删除操作必须填写原因，其他操作可选';
COMMENT ON COLUMN audit_logs.old_value IS 'JSONB格式存储修改前的值，方便审计和回滚';
COMMENT ON COLUMN audit_logs.new_value IS 'JSONB格式存储修改后的值';
