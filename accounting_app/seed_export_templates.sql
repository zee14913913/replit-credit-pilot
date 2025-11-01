-- ============================================================
-- 导出模板种子数据 - CSV Export Templates
-- 用途：预定义常用会计软件的导出格式
-- 支持：SQL Account, AutoCount, UBS
-- ============================================================

-- ============================================================
-- 1. SQL Account模板
-- ============================================================

-- SQL Account - General Ledger (总账)
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'SQL Account - General Ledger',
    'SQL Account',
    'general_ledger',
    '{"Date": "entry_date", "Account Code": "account_code", "Account Name": "account_name", "Description": "description", "Debit": "debit_amount", "Credit": "credit_amount", "Reference": "reference_number"}'::jsonb,
    ',',
    'DD/MM/YYYY',
    2,
    true,
    true,  -- 默认模板
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'SQL Account - General Ledger'
);

-- SQL Account - Journal Entry (分录)
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'SQL Account - Journal Entry',
    'SQL Account',
    'journal_entry',
    '{"Entry No": "entry_number", "Date": "entry_date", "Account": "account_code", "Debit": "debit_amount", "Credit": "credit_amount", "Description": "description", "Doc No": "reference_number"}'::jsonb,
    ',',
    'DD/MM/YYYY',
    2,
    true,
    false,
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'SQL Account - Journal Entry'
);

-- ============================================================
-- 2. AutoCount模板
-- ============================================================

-- AutoCount - General Ledger
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'AutoCount - General Ledger',
    'AutoCount',
    'general_ledger',
    '{"DocDate": "entry_date", "AccNo": "account_code", "Description": "description", "DR": "debit_amount", "CR": "credit_amount", "DocRef": "reference_number"}'::jsonb,
    ',',
    'YYYY-MM-DD',
    2,
    true,
    true,  -- AutoCount默认模板
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'AutoCount - General Ledger'
);

-- AutoCount - Trial Balance
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'AutoCount - Trial Balance',
    'AutoCount',
    'trial_balance',
    '{"Account Code": "account_code", "Account Name": "account_name", "Debit": "debit_balance", "Credit": "credit_balance"}'::jsonb,
    ',',
    'YYYY-MM-DD',
    2,
    true,
    false,
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'AutoCount - Trial Balance'
);

-- ============================================================
-- 3. UBS模板
-- ============================================================

-- UBS - General Ledger
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'UBS - General Ledger',
    'UBS',
    'general_ledger',
    '{"GL Date": "entry_date", "GL Code": "account_code", "Particulars": "description", "Debit Amt": "debit_amount", "Credit Amt": "credit_amount", "Doc Ref": "reference_number"}'::jsonb,
    ',',
    'DD-MM-YYYY',
    2,
    true,
    true,  -- UBS默认模板
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'UBS - General Ledger'
);

-- ============================================================
-- 4. Generic通用模板
-- ============================================================

-- Generic - General Ledger (标准格式)
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'Generic - General Ledger',
    'Generic',
    'general_ledger',
    '{"Date": "entry_date", "Account Code": "account_code", "Account Name": "account_name", "Description": "description", "Debit": "debit_amount", "Credit": "credit_amount", "Reference": "reference_number", "Entry Type": "entry_type"}'::jsonb,
    ',',
    'YYYY-MM-DD',
    2,
    true,
    true,  -- Generic默认模板
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'Generic - General Ledger'
);

-- Generic - Chart of Accounts (会计科目表)
INSERT INTO export_templates (
    company_id, template_name, software_name, export_type, column_mappings,
    delimiter, date_format, decimal_places, include_header, is_default, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'Generic - Chart of Accounts',
    'Generic',
    'chart_of_accounts',
    '{"Account Code": "account_code", "Account Name": "account_name", "Account Type": "account_type", "Description": "description", "Active": "is_active"}'::jsonb,
    ',',
    'YYYY-MM-DD',
    2,
    true,
    true,
    true
WHERE NOT EXISTS (
    SELECT 1 FROM export_templates 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND template_name = 'Generic - Chart of Accounts'
);

-- ============================================================
-- 统计信息
-- ============================================================

-- 查看插入的模板数量
SELECT 
    'Total Templates Inserted:' as info,
    COUNT(*) as count
FROM export_templates
WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT');

-- 按软件查看模板列表
SELECT 
    software_name,
    template_name,
    export_type,
    is_default
FROM export_templates
WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
ORDER BY software_name, export_type;
