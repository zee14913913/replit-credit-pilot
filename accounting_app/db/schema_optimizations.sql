-- ============================================================
-- 系统优化补充 - 基于用户反馈的架构增强
-- 日期：2025-11-01
-- ============================================================

-- ============================================================
-- 1. 多租户隔离 - 文件路径唯一索引
-- ============================================================
CREATE UNIQUE INDEX IF NOT EXISTS ux_files_company_path
ON file_index (company_id, file_path);

COMMENT ON INDEX ux_files_company_path IS '确保不同公司不会访问到彼此的文件';

-- ============================================================
-- 2. 自动记账规则表（表驱动，可配置）
-- ============================================================
CREATE TABLE IF NOT EXISTS auto_posting_rules (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 规则信息
    rule_name VARCHAR(100) NOT NULL,
    rule_description TEXT,
    
    -- 匹配模式
    pattern TEXT NOT NULL,  -- 关键词，例如 'salary','gaji','epf','shopee'
    pattern_type VARCHAR(20) DEFAULT 'keyword',  -- 'keyword', 'regex', 'exact'
    
    -- 银行特定（可选）
    bank_name VARCHAR(100),  -- NULL表示适用所有银行
    
    -- 会计科目映射
    target_account_code VARCHAR(50) NOT NULL,
    posting_type VARCHAR(20) NOT NULL,  -- 'debit', 'credit', 'split'
    
    -- 税务标记
    tax_flag BOOLEAN DEFAULT FALSE,
    tax_rate DECIMAL(5,2),
    
    -- 优先级（数字越大越优先）
    priority INTEGER DEFAULT 0,
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    created_by VARCHAR(100),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_posting_rules_company ON auto_posting_rules(company_id);
CREATE INDEX IF NOT EXISTS idx_posting_rules_bank ON auto_posting_rules(bank_name);
CREATE INDEX IF NOT EXISTS idx_posting_rules_priority ON auto_posting_rules(priority DESC);

COMMENT ON TABLE auto_posting_rules IS '自动记账规则表 - 表驱动配置，支持不同银行和公司的自定义规则';

-- ============================================================
-- 3. CSV导出模板配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS export_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(50) NOT NULL,  -- 'journal_entry', 'invoice', 'aging'
    
    -- 模板说明
    description TEXT,
    target_system VARCHAR(100),  -- 'Generic', 'SQL Account', 'AutoCount', 'QuickBooks'
    
    -- 列配置（JSON数组）
    columns JSONB NOT NULL,  
    -- 示例: ["date","account_code","description","debit","credit","ref_no"]
    
    -- 列映射（JSON对象）
    column_mapping JSONB,
    -- 示例: {"date": "transaction_date", "account_code": "account", ...}
    
    -- 格式设置
    date_format VARCHAR(50) DEFAULT 'YYYY-MM-DD',
    decimal_places INTEGER DEFAULT 2,
    delimiter VARCHAR(10) DEFAULT ',',
    encoding VARCHAR(20) DEFAULT 'UTF-8',
    include_header BOOLEAN DEFAULT TRUE,
    
    -- 状态
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_export_templates_type ON export_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_export_templates_target ON export_templates(target_system);

COMMENT ON TABLE export_templates IS 'CSV导出模板配置 - 支持多种会计软件格式';

-- 插入默认模板
INSERT INTO export_templates (template_name, template_type, description, target_system, columns, column_mapping)
VALUES 
    ('generic_v1', 'journal_entry', 'Generic CSV format for journal entries', 'Generic', 
     '["date","account_code","description","debit","credit","reference"]'::jsonb,
     '{"date": "entry_date", "account_code": "account_code", "description": "description", "debit": "debit_amount", "credit": "credit_amount", "reference": "reference_no"}'::jsonb),
    
    ('sqlacc_v1', 'journal_entry', 'SQL Account compatible format', 'SQL Account',
     '["Date","Account","Description","Debit","Credit","Ref"]}]'::jsonb,
     '{"Date": "entry_date", "Account": "account_code", "Description": "description", "Debit": "debit_amount", "Credit": "credit_amount", "Ref": "reference_no"}'::jsonb),
    
    ('autocount_v1', 'journal_entry', 'AutoCount compatible format', 'AutoCount',
     '["DocDate","AccNo","Description","DrAmt","CrAmt","DocNo"]}]'::jsonb,
     '{"DocDate": "entry_date", "AccNo": "account_code", "Description": "description", "DrAmt": "debit_amount", "CrAmt": "credit_amount", "DocNo": "reference_no"}'::jsonb)
ON CONFLICT (template_name) DO NOTHING;

-- ============================================================
-- 4. 增强 file_index 表 - 明确区分原件/成品
-- ============================================================
-- 已有字段，确保正确设置
ALTER TABLE file_index ADD COLUMN IF NOT EXISTS module VARCHAR(50);  -- 'bank', 'supplier', 'pos', 'reports', 'management'
ALTER TABLE file_index ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);

COMMENT ON COLUMN file_index.file_type IS 'original=上传的原始文件, generated=系统生成的文件';
COMMENT ON COLUMN file_index.module IS '模块分类：bank, supplier, pos, reports, management';
COMMENT ON COLUMN file_index.related_entity_id IS '关联的业务实体ID（可反查原始PDF）';

-- ============================================================
-- 5. 定时任务执行记录表（幂等性控制）
-- ============================================================
CREATE TABLE IF NOT EXISTS task_runs (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    run_date DATE NOT NULL,
    
    -- 执行信息
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    
    -- 结果
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    details JSONB,
    error_message TEXT,
    
    -- 触发信息
    triggered_by VARCHAR(100),  -- 'scheduler', 'manual', 'api'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 幂等性约束：同一任务同一天只能跑一次
    CONSTRAINT unique_task_run UNIQUE (task_name, run_date)
);

CREATE INDEX IF NOT EXISTS idx_task_runs_date ON task_runs(run_date);
CREATE INDEX IF NOT EXISTS idx_task_runs_status ON task_runs(status);

COMMENT ON TABLE task_runs IS '定时任务执行记录 - 幂等性控制，防止重复执行';

-- ============================================================
-- 6. 增强 processing_logs 表 - 更详细的错误追踪
-- ============================================================
ALTER TABLE processing_logs ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);
ALTER TABLE processing_logs ADD COLUMN IF NOT EXISTS error_stage VARCHAR(50);
-- error_stage: 'upload', 'parse', 'ocr', 'mapping', 'posting', 'validation'
ALTER TABLE processing_logs ADD COLUMN IF NOT EXISTS related_file_id INTEGER REFERENCES file_index(id);

COMMENT ON COLUMN processing_logs.original_filename IS '原始文件名，方便排查问题';
COMMENT ON COLUMN processing_logs.error_stage IS '失败阶段：upload/parse/ocr/mapping/posting';
COMMENT ON COLUMN processing_logs.related_file_id IS '关联的文件索引ID';

-- ============================================================
-- 7. 增强 pending_documents 表 - 详细失败原因
-- ============================================================
ALTER TABLE pending_documents ADD COLUMN IF NOT EXISTS failure_stage VARCHAR(50);
-- 'ocr_failed', 'layout_unsupported', 'bank_template_unknown', 'data_incomplete'

COMMENT ON COLUMN pending_documents.failure_stage IS '具体失败阶段，前端可据此提示用户';

-- ============================================================
-- 8. 增强 management_reports 表 - 数据质量指标
-- ============================================================
ALTER TABLE management_reports ADD COLUMN IF NOT EXISTS data_freshness DATE;
ALTER TABLE management_reports ADD COLUMN IF NOT EXISTS source_modules JSONB;
-- 示例: {"bank": true, "pos": true, "supplier": true, "manual": false}
ALTER TABLE management_reports ADD COLUMN IF NOT EXISTS estimated_revenue_gap DECIMAL(15,2);

COMMENT ON COLUMN management_reports.data_freshness IS '报表基于的最后数据日期';
COMMENT ON COLUMN management_reports.source_modules IS '本期包含的数据来源模块';
COMMENT ON COLUMN management_reports.estimated_revenue_gap IS '因未匹配可能遗漏的收入估算';

-- ============================================================
-- 9. 创建视图：未匹配项目汇总（给Management Report用）
-- ============================================================
CREATE OR REPLACE VIEW vw_unreconciled_summary AS
SELECT 
    company_id,
    COUNT(*) as total_unreconciled,
    SUM(CASE WHEN file_type = 'bank-statement' THEN 1 ELSE 0 END) as bank_unreconciled,
    SUM(CASE WHEN file_type = 'supplier-invoice' THEN 1 ELSE 0 END) as supplier_unreconciled,
    SUM(CASE WHEN file_type = 'pos-report' THEN 1 ELSE 0 END) as pos_unreconciled,
    MAX(upload_date) as latest_unreconciled_date
FROM pending_documents
WHERE parse_status IN ('pending', 'failed', 'partial')
  AND is_active = TRUE
GROUP BY company_id;

COMMENT ON VIEW vw_unreconciled_summary IS 'Management Report用 - 未匹配项目统计';

-- ============================================================
-- 10. 插入默认自动记账规则（示例）
-- ============================================================
INSERT INTO auto_posting_rules (company_id, rule_name, pattern, bank_name, target_account_code, posting_type, priority)
VALUES 
    -- Maybank规则
    (1, 'Salary Income', 'salary|gaji|wages', 'Maybank', '4001', 'credit', 100),
    (1, 'EPF Deduction', 'epf|kwsp', 'Maybank', '2101', 'credit', 90),
    (1, 'Shopee Sales', 'shopee|lazada|grab', NULL, '1200', 'debit', 80),
    
    -- 通用规则
    (1, 'Supplier Payment', 'payment|bayaran', NULL, '2001', 'debit', 70),
    (1, 'Customer Receipt', 'receipt|terima', NULL, '1100', 'debit', 70),
    (1, 'Bank Charges', 'bank charge|fee|commission', NULL, '6101', 'debit', 60)
ON CONFLICT DO NOTHING;

-- ============================================================
-- 11. 创建函数：检查任务是否今天已执行
-- ============================================================
CREATE OR REPLACE FUNCTION check_task_run_today(p_task_name VARCHAR, p_run_date DATE DEFAULT CURRENT_DATE)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM task_runs 
        WHERE task_name = p_task_name 
          AND run_date = p_run_date
          AND status IN ('running', 'completed')
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_task_run_today IS '检查任务今天是否已执行（幂等性检查）';

-- ============================================================
-- 12. 创建函数：记录任务开始
-- ============================================================
CREATE OR REPLACE FUNCTION start_task_run(
    p_task_name VARCHAR, 
    p_triggered_by VARCHAR DEFAULT 'manual'
) RETURNS INTEGER AS $$
DECLARE
    v_run_id INTEGER;
BEGIN
    INSERT INTO task_runs (task_name, run_date, status, start_time, triggered_by)
    VALUES (p_task_name, CURRENT_DATE, 'running', CURRENT_TIMESTAMP, p_triggered_by)
    ON CONFLICT (task_name, run_date) 
    DO UPDATE SET 
        status = 'running',
        start_time = CURRENT_TIMESTAMP,
        triggered_by = EXCLUDED.triggered_by
    RETURNING id INTO v_run_id;
    
    RETURN v_run_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION start_task_run IS '开始任务执行，返回run_id';

-- ============================================================
-- 13. 创建函数：记录任务完成
-- ============================================================
CREATE OR REPLACE FUNCTION complete_task_run(
    p_run_id INTEGER,
    p_status VARCHAR,
    p_records_processed INTEGER DEFAULT 0,
    p_records_failed INTEGER DEFAULT 0,
    p_details JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE task_runs 
    SET 
        status = p_status,
        end_time = CURRENT_TIMESTAMP,
        duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time)),
        records_processed = p_records_processed,
        records_failed = p_records_failed,
        details = p_details,
        error_message = p_error_message
    WHERE id = p_run_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION complete_task_run IS '完成任务执行，记录结果';

-- ============================================================
-- 14. 触发器：更新updated_at时间戳
-- ============================================================
CREATE TRIGGER update_auto_posting_rules_updated_at 
BEFORE UPDATE ON auto_posting_rules 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_export_templates_updated_at 
BEFORE UPDATE ON export_templates 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 15. 权限建议（可选）
-- ============================================================
-- 如果需要创建只读用户，可以用这个：
-- CREATE ROLE readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly_user;

-- ============================================================
-- 完成！
-- ============================================================

SELECT '✅ 系统优化SQL执行完成！新增：
- auto_posting_rules（规则表驱动）
- export_templates（多模板支持）
- task_runs（幂等性控制）
- vw_unreconciled_summary（未匹配项视图）
- 幂等性检查函数
- 增强的错误追踪字段
' as status;
