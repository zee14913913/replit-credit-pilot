-- ============================================================
-- 规则引擎种子数据 - 银行导入自动记账规则
-- 用途：将原硬编码MATCHING_RULES迁移到数据库表驱动
-- 来源：accounting_app/services/bank_matcher.py
-- ============================================================

-- 注意：这些规则针对DEFAULT公司（company_code='DEFAULT'）
-- 生产环境中，每个公司应有独立的规则集

-- ============================================================
-- 1. 工资支付规则（优先级10-40，最高优先级）
-- ============================================================

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '工资支付 - Payout',
    'bank_import',
    'payout',
    false,  -- 关键字匹配
    10,     -- 最高优先级
    'salary_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '工资支付 - Payout'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '工资支付 - Infinite.GZ',
    'bank_import',
    'infinite.gz',
    false,
    20,
    'salary_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '工资支付 - Infinite.GZ'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '工资支付 - Salary',
    'bank_import',
    'salary',
    false,
    30,
    'salary_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '工资支付 - Salary'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '工资支付 - Gaji',
    'bank_import',
    'gaji',
    false,
    40,
    'salary_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '工资支付 - Gaji'
);

-- ============================================================
-- 2. 法定缴纳规则（优先级50-100）
-- ============================================================

-- EPF (雇员公积金)
INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'EPF缴纳 - KWSP',
    'bank_import',
    'kumpulan wang simpanan pekerja',
    false,
    50,
    'epf_payable',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = 'EPF缴纳 - KWSP'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'EPF缴纳 - KWSP缩写',
    'bank_import',
    'kwsp',
    false,
    60,
    'epf_payable',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = 'EPF缴纳 - KWSP缩写'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'EPF缴纳 - EPF',
    'bank_import',
    'epf',
    false,
    70,
    'epf_payable',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = 'EPF缴纳 - EPF'
);

-- SOCSO (社会保险)
INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'SOCSO缴纳 - PERKESO',
    'bank_import',
    'pertubuhan keselamatan sosial',
    false,
    80,
    'socso_payable',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = 'SOCSO缴纳 - PERKESO'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'SOCSO缴纳 - Perkeso',
    'bank_import',
    'perkeso',
    false,
    90,
    'socso_payable',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = 'SOCSO缴纳 - Perkeso'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    'SOCSO缴纳 - SOCSO',
    'bank_import',
    'socso',
    false,
    100,
    'socso_payable',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = 'SOCSO缴纳 - SOCSO'
);

-- ============================================================
-- 3. 支出类规则（优先级200-300）
-- ============================================================

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '租金支出 - Rental',
    'bank_import',
    'rental',
    false,
    200,
    'rent_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '租金支出 - Rental'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '租金支出 - Rent',
    'bank_import',
    'rent',
    false,
    210,
    'rent_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '租金支出 - Rent'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '水电支出 - Utilities',
    'bank_import',
    'utilities',
    false,
    220,
    'utilities_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '水电支出 - Utilities'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '水电支出 - Util',
    'bank_import',
    'util',
    false,
    230,
    'utilities_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '水电支出 - Util'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '采购支出 - Supplier',
    'bank_import',
    'supplier',
    false,
    240,
    'purchase_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '采购支出 - Supplier'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '采购支出 - Payment',
    'bank_import',
    'payment',
    false,
    250,
    'purchase_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '采购支出 - Payment'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '采购支出 - Stock',
    'bank_import',
    'stock',
    false,
    260,
    'purchase_expense',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '采购支出 - Stock'
);

-- ============================================================
-- 4. 收入类规则（优先级400-500）
-- ============================================================

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '服务收入 - Service',
    'bank_import',
    'service',
    false,
    400,
    'bank',
    'service_income',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '服务收入 - Service'
);

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '客户押金 - Deposit',
    'bank_import',
    'deposit',
    false,
    410,
    'bank',
    'deposit_income',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '客户押金 - Deposit'
);

-- ============================================================
-- 5. 其他规则（优先级900+，最低优先级）
-- ============================================================

INSERT INTO auto_posting_rules (
    company_id, rule_name, source_type, pattern, is_regex, priority,
    debit_account_code, credit_account_code, is_active
)
SELECT 
    (SELECT id FROM companies WHERE company_code = 'DEFAULT'),
    '银行手续费 - Fee',
    'bank_import',
    'fee',
    false,
    900,
    'bank_charges',
    'bank',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM auto_posting_rules 
    WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
    AND rule_name = '银行手续费 - Fee'
);

-- ============================================================
-- 统计信息
-- ============================================================

-- 查看插入的规则数量
SELECT 
    'Total Rules Inserted:' as info,
    COUNT(*) as count
FROM auto_posting_rules
WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT');

-- 按优先级查看规则列表
SELECT 
    priority,
    rule_name,
    pattern,
    debit_account_code || ' -> ' || credit_account_code as accounting_entry
FROM auto_posting_rules
WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
ORDER BY priority ASC;
