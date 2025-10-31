-- ============================================================
-- 银行贷款合规会计系统 - PostgreSQL 数据库建表脚本
-- 用途：将银行月结单转换为会计分录，生成银行贷款所需的财务报表
-- ============================================================

-- 1. 客户公司表（多租户核心表）
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    registration_number VARCHAR(100),
    tax_number VARCHAR(100),
    business_type VARCHAR(100),
    address TEXT,
    contact_person VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(100),
    fiscal_year_end VARCHAR(10) DEFAULT '12-31',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_companies_code ON companies(company_code);
CREATE INDEX idx_companies_status ON companies(status);

-- 2. 会计科目表（Chart of Accounts）
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(200) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'income', 'expense')),
    parent_id INTEGER REFERENCES chart_of_accounts(id),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, account_code)
);
CREATE INDEX idx_coa_company ON chart_of_accounts(company_id);
CREATE INDEX idx_coa_type ON chart_of_accounts(account_type);
CREATE INDEX idx_coa_parent ON chart_of_accounts(parent_id);

-- 3. 银行月结单导入表
CREATE TABLE IF NOT EXISTS bank_statements (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(100) NOT NULL,
    statement_month VARCHAR(7) NOT NULL,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    reference_number VARCHAR(100),
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2),
    matched BOOLEAN DEFAULT false,
    matched_journal_id INTEGER,
    auto_category VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_bank_statements_company ON bank_statements(company_id);
CREATE INDEX idx_bank_statements_date ON bank_statements(transaction_date);
CREATE INDEX idx_bank_statements_matched ON bank_statements(matched);
CREATE INDEX idx_bank_statements_month ON bank_statements(statement_month);

-- 4. 总账分录表（Journal Entries）
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    entry_number VARCHAR(50) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    entry_type VARCHAR(50) DEFAULT 'manual' CHECK (entry_type IN ('manual', 'auto', 'bank_import', 'invoice', 'payment', 'payroll', 'tax_adjustment')),
    reference_number VARCHAR(100),
    created_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'posted' CHECK (status IN ('draft', 'posted', 'reversed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_journal_entries_company ON journal_entries(company_id);
CREATE INDEX idx_journal_entries_date ON journal_entries(entry_date);
CREATE INDEX idx_journal_entries_type ON journal_entries(entry_type);

-- 5. 总账分录明细表（Journal Entry Lines）
CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES chart_of_accounts(id),
    description TEXT,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    line_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_journal_lines_entry ON journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_lines_account ON journal_entry_lines(account_id);

-- 6. 供应商表（Suppliers）
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_code VARCHAR(50) NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    payment_terms INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, supplier_code)
);
CREATE INDEX idx_suppliers_company ON suppliers(company_id);

-- 7. 采购发票表（Purchase Invoices）
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    paid_amount DECIMAL(15,2) DEFAULT 0,
    balance_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'unpaid' CHECK (status IN ('unpaid', 'partial', 'paid', 'overdue')),
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, invoice_number)
);
CREATE INDEX idx_purchase_invoices_company ON purchase_invoices(company_id);
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_invoices_date ON purchase_invoices(invoice_date);
CREATE INDEX idx_purchase_invoices_status ON purchase_invoices(status);

-- 8. 供应商付款表（Supplier Payments）
CREATE TABLE IF NOT EXISTS supplier_payments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    payment_number VARCHAR(100) NOT NULL,
    payment_date DATE NOT NULL,
    payment_amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, payment_number)
);
CREATE INDEX idx_supplier_payments_company ON supplier_payments(company_id);
CREATE INDEX idx_supplier_payments_supplier ON supplier_payments(supplier_id);
CREATE INDEX idx_supplier_payments_date ON supplier_payments(payment_date);

-- 9. 付款分配表（Payment Allocations）
CREATE TABLE IF NOT EXISTS payment_allocations (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES supplier_payments(id) ON DELETE CASCADE,
    invoice_id INTEGER NOT NULL REFERENCES purchase_invoices(id),
    allocated_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. 客户表（Customers - 应收账款）
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_code VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    credit_limit DECIMAL(15,2) DEFAULT 0,
    payment_terms INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, customer_code)
);
CREATE INDEX idx_customers_company ON customers(company_id);

-- 11. 销售发票表（Sales Invoices）
CREATE TABLE IF NOT EXISTS sales_invoices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    received_amount DECIMAL(15,2) DEFAULT 0,
    balance_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'unpaid' CHECK (status IN ('unpaid', 'partial', 'paid', 'overdue')),
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    auto_generated BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, invoice_number)
);
CREATE INDEX idx_sales_invoices_company ON sales_invoices(company_id);
CREATE INDEX idx_sales_invoices_customer ON sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_date ON sales_invoices(invoice_date);
CREATE INDEX idx_sales_invoices_status ON sales_invoices(status);

-- 12. 客户收款表（Customer Receipts）
CREATE TABLE IF NOT EXISTS customer_receipts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    receipt_number VARCHAR(100) NOT NULL,
    receipt_date DATE NOT NULL,
    receipt_amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, receipt_number)
);
CREATE INDEX idx_customer_receipts_company ON customer_receipts(company_id);
CREATE INDEX idx_customer_receipts_customer ON customer_receipts(customer_id);
CREATE INDEX idx_customer_receipts_date ON customer_receipts(receipt_date);

-- 13. 收款分配表（Receipt Allocations）
CREATE TABLE IF NOT EXISTS receipt_allocations (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL REFERENCES customer_receipts(id) ON DELETE CASCADE,
    invoice_id INTEGER NOT NULL REFERENCES sales_invoices(id),
    allocated_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. 财务报表映射表（用于P&L和Balance Sheet）
CREATE TABLE IF NOT EXISTS financial_report_mapping (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES chart_of_accounts(id),
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN ('pnl', 'balance_sheet')),
    report_section VARCHAR(100) NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_report_mapping_company ON financial_report_mapping(company_id);
CREATE INDEX idx_report_mapping_account ON financial_report_mapping(account_id);

-- 15. 员工表（Employees - 用于工资分录）
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_code VARCHAR(50) NOT NULL,
    employee_name VARCHAR(200) NOT NULL,
    position VARCHAR(100),
    department VARCHAR(100),
    ic_number VARCHAR(50),
    epf_number VARCHAR(50),
    socso_number VARCHAR(50),
    basic_salary DECIMAL(15,2) DEFAULT 0,
    hire_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, employee_code)
);
CREATE INDEX idx_employees_company ON employees(company_id);

-- 16. 工资表（Payroll Runs）
CREATE TABLE IF NOT EXISTS payroll_runs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    payroll_number VARCHAR(100) NOT NULL,
    payroll_month VARCHAR(7) NOT NULL,
    payment_date DATE NOT NULL,
    total_gross DECIMAL(15,2) DEFAULT 0,
    total_epf_employer DECIMAL(15,2) DEFAULT 0,
    total_epf_employee DECIMAL(15,2) DEFAULT 0,
    total_socso DECIMAL(15,2) DEFAULT 0,
    total_net DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'posted', 'paid')),
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, payroll_number)
);
CREATE INDEX idx_payroll_runs_company ON payroll_runs(company_id);
CREATE INDEX idx_payroll_runs_month ON payroll_runs(payroll_month);

-- 17. 工资明细表（Payroll Items）
CREATE TABLE IF NOT EXISTS payroll_items (
    id SERIAL PRIMARY KEY,
    payroll_run_id INTEGER NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    basic_salary DECIMAL(15,2) NOT NULL,
    allowances DECIMAL(15,2) DEFAULT 0,
    overtime DECIMAL(15,2) DEFAULT 0,
    gross_salary DECIMAL(15,2) NOT NULL,
    epf_employee DECIMAL(15,2) DEFAULT 0,
    epf_employer DECIMAL(15,2) DEFAULT 0,
    socso DECIMAL(15,2) DEFAULT 0,
    income_tax DECIMAL(15,2) DEFAULT 0,
    other_deductions DECIMAL(15,2) DEFAULT 0,
    net_salary DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_payroll_items_run ON payroll_items(payroll_run_id);
CREATE INDEX idx_payroll_items_employee ON payroll_items(employee_id);

-- 18. 税务调整表（Tax Adjustments - 用于生成银行版报表）
CREATE TABLE IF NOT EXISTS tax_adjustments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    adjustment_period VARCHAR(7) NOT NULL,
    account_id INTEGER REFERENCES chart_of_accounts(id),
    description TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('add', 'deduct')),
    category VARCHAR(100),
    reason TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_tax_adjustments_company ON tax_adjustments(company_id);
CREATE INDEX idx_tax_adjustments_period ON tax_adjustments(adjustment_period);

-- 19. 自动发票规则表（Auto Invoice Rules）
CREATE TABLE IF NOT EXISTS auto_invoice_rules (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    rule_name VARCHAR(200) NOT NULL,
    invoice_description TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    frequency VARCHAR(20) DEFAULT 'monthly' CHECK (frequency IN ('monthly', 'quarterly', 'yearly')),
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_auto_invoice_rules_company ON auto_invoice_rules(company_id);

-- ============================================================
-- 初始化默认会计科目（简化版马来西亚会计准则）
-- ============================================================
COMMENT ON TABLE chart_of_accounts IS '会计科目表 - 支持5大类：资产、负债、权益、收入、费用';
COMMENT ON TABLE bank_statements IS '银行月结单导入 - 核心数据源';
COMMENT ON TABLE journal_entries IS '总账分录 - 所有会计记录的核心';
COMMENT ON TABLE suppliers IS '供应商管理 - 用于Suppliers Aging报表';
COMMENT ON TABLE customers IS '客户管理 - 用于应收账款台账';
COMMENT ON TABLE tax_adjustments IS '税务调整 - 生成银行贷款报表时的合法调整';

-- ============================================================
-- 默认会计科目种子数据（Standard Chart of Accounts）
-- 这些科目代码与bank_matcher.py的自动匹配逻辑对应
-- ============================================================

-- 插入默认公司（如果不存在）
INSERT INTO companies (company_code, company_name, registration_number, status)
VALUES ('DEFAULT', '默认公司 (Default Company)', 'DEMO001', 'active')
ON CONFLICT (company_code) DO NOTHING;

-- 为DEFAULT公司创建会计科目（使用动态company_id查询）
-- ASSET 资产类
INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'bank', '银行存款 (Bank)', 'asset', '公司银行账户余额'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'bank' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'accounts_receivable', '应收账款 (Accounts Receivable)', 'asset', '客户欠款'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'accounts_receivable' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

-- LIABILITY 负债类
INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'accounts_payable', '应付账款 (Accounts Payable)', 'liability', '供应商欠款'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'accounts_payable' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'epf_payable', 'EPF应付款 (EPF Payable)', 'liability', '雇员公积金'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'epf_payable' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'socso_payable', 'SOCSO应付款 (SOCSO Payable)', 'liability', '社会保险'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'socso_payable' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

-- EXPENSE 费用类
INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'salary_expense', '工资支出 (Salary Expense)', 'expense', '员工工资'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'salary_expense' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'rent_expense', '租金支出 (Rent Expense)', 'expense', '办公室或仓库租金'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'rent_expense' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'utilities_expense', '水电支出 (Utilities Expense)', 'expense', '水费、电费、网费等'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'utilities_expense' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'purchase_expense', '采购支出 (Purchase Expense)', 'expense', '供应商采购'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'purchase_expense' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'bank_charges', '银行手续费 (Bank Charges)', 'expense', '银行服务费、转账费等'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'bank_charges' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

-- INCOME 收入类
INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'service_income', '服务收入 (Service Income)', 'income', '提供服务所得收入'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'service_income' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'sales_income', '销售收入 (Sales Income)', 'income', '产品销售收入'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'sales_income' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

INSERT INTO chart_of_accounts (company_id, account_code, account_name, account_type, description)
SELECT (SELECT id FROM companies WHERE company_code = 'DEFAULT'), 'deposit_income', '客户押金 (Customer Deposit)', 'income', '客户预付款项'
WHERE NOT EXISTS (
    SELECT 1 FROM chart_of_accounts c 
    WHERE c.account_code = 'deposit_income' 
    AND c.company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
);

-- ============================================================
-- 完成提示
-- ============================================================

-- ============================================================
-- 初始化完成
-- 默认会计科目已准备就绪
-- ============================================================
