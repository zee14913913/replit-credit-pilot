
-- ============================================================
-- Infinite GZ 系统数据库 Schema 设计
-- 用途：信用卡账单管理、交易分类、月结算、贷款评估
-- 数据库：SQLite
-- 创建日期：2025-11-21
-- ============================================================

-- ============================================================
-- 1. 用户信息表 (users)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- 用户姓名
    ic_number TEXT UNIQUE,                       -- 身份证号码
    phone TEXT,                                  -- 手机号码
    email TEXT UNIQUE,                           -- 邮箱
    company_name TEXT,                           -- 公司名称
    role TEXT DEFAULT 'customer' CHECK(role IN ('customer', 'admin', 'accountant', 'viewer')),
    
    -- 财务评估指标
    ctos_score INTEGER,                          -- CTOS 信用评分 (0-1000)
    dsr REAL,                                    -- Debt Service Ratio 债务偿还比率
    monthly_income REAL DEFAULT 0,               -- 月收入
    
    -- 系统字段
    password_hash TEXT,                          -- 加密密码
    is_active INTEGER DEFAULT 1,                 -- 账户状态 (1=活跃, 0=停用)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_ic_number ON users(ic_number);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- 2. 信用卡账户表 (credit_cards)
-- ============================================================
CREATE TABLE IF NOT EXISTS credit_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    
    -- 卡片信息
    bank_name TEXT NOT NULL,                     -- 银行名称
    card_number_last4 TEXT NOT NULL,             -- 卡号后4位
    card_full_number TEXT,                       -- 完整卡号（加密存储）
    card_type TEXT,                              -- 卡片类型 (Visa/MasterCard/AmEx)
    
    -- 额度信息
    credit_limit REAL DEFAULT 0,                 -- 信用额度
    available_credit REAL DEFAULT 0,             -- 可用额度
    
    -- 账单日期配置
    statement_cutoff_day INTEGER,                -- 账单日（每月几号）
    payment_due_day INTEGER,                     -- 到期日（每月几号）
    min_payment_rate REAL DEFAULT 0.05,          -- 最低还款比例 (5%)
    
    -- 积分配置
    points_balance REAL DEFAULT 0,               -- 当前积分余额
    
    -- 系统字段
    is_active INTEGER DEFAULT 1,                 -- 卡片状态 (1=活跃, 0=停用)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_credit_cards_user ON credit_cards(user_id);
CREATE INDEX idx_credit_cards_bank ON credit_cards(bank_name);

-- ============================================================
-- 3. 账单主表 (statements)
-- ============================================================
CREATE TABLE IF NOT EXISTS statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    card_id INTEGER NOT NULL,                    -- 信用卡ID外键
    
    -- 账单信息
    statement_date TEXT NOT NULL,                -- 账单日期 (YYYY-MM-DD)
    due_date TEXT NOT NULL,                      -- 到期日期
    statement_month TEXT NOT NULL,               -- 账单月份 (YYYY-MM)
    
    -- 金额信息
    previous_balance REAL DEFAULT 0,             -- 上期余额
    total_spent REAL DEFAULT 0,                  -- 本期总支出
    total_payment REAL DEFAULT 0,                -- 本期总还款
    total_amount REAL NOT NULL,                  -- 全额应还
    min_payment REAL NOT NULL,                   -- 最低还款额
    current_balance REAL DEFAULT 0,              -- 当前余额
    
    -- 积分信息
    points_earned REAL DEFAULT 0,                -- 本期赚取积分
    
    -- 文件信息
    upload_filename TEXT,                        -- 上传的PDF文件名
    file_path TEXT,                              -- 文件存储路径
    file_type TEXT,                              -- 文件类型 (pdf/csv/excel)
    
    -- 解析状态
    parse_status TEXT DEFAULT 'pending' CHECK(parse_status IN ('pending', 'parsed', 'failed', 'verified')),
    validation_score REAL DEFAULT 0,             -- 验证置信度 (0-1)
    inconsistencies TEXT,                        -- 不一致项记录(JSON格式)
    
    -- 确认状态
    is_confirmed INTEGER DEFAULT 0,              -- 用户确认状态 (0=未确认, 1=已确认)
    confirmed_by TEXT,                           -- 确认人
    confirmed_at TIMESTAMP,                      -- 确认时间
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES credit_cards(id) ON DELETE CASCADE,
    UNIQUE(card_id, statement_month)             -- 同一张卡每月只能有一份账单
);

CREATE INDEX idx_statements_user ON statements(user_id);
CREATE INDEX idx_statements_card ON statements(card_id);
CREATE INDEX idx_statements_month ON statements(statement_month);
CREATE INDEX idx_statements_status ON statements(parse_status);

-- ============================================================
-- 4. 交易明细表 (transactions)
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,               -- 账单ID外键
    
    -- 交易信息
    transaction_date TEXT NOT NULL,              -- 交易日期 (YYYY-MM-DD)
    description TEXT NOT NULL,                   -- 交易描述
    merchant TEXT,                               -- 商户名称
    
    -- 金额信息
    debit_amount REAL DEFAULT 0,                 -- 支出金额 (DR)
    credit_amount REAL DEFAULT 0,                -- 收入金额 (CR)
    
    -- Infinite GZ 分类核心字段
    classification TEXT CHECK(classification IN ('Owner', 'GZ')),  -- 账户归属分类
    transaction_type TEXT CHECK(transaction_type IN ('Expense', 'Payment')),  -- 交易类型
    
    -- 详细分类
    transaction_subtype TEXT,                    -- 子类型 (supplier_debit, shop_debit, 3rd_party_credit, etc.)
    supplier_name TEXT,                          -- 供应商名称（如果是供应商消费）
    supplier_fee REAL DEFAULT 0,                 -- 供应商手续费 (1%)
    
    -- 付款人信息
    payment_user TEXT,                           -- 付款人 (Owner/GZ/Third Party)
    
    -- AI分类
    category TEXT,                               -- AI自动分类
    category_confidence REAL DEFAULT 0,          -- 分类置信度 (0-1)
    
    -- 积分
    points_earned REAL DEFAULT 0,                -- 该笔交易赚取积分
    
    -- 处理状态
    is_processed INTEGER DEFAULT 0,              -- 是否已处理 (0=未处理, 1=已处理)
    notes TEXT,                                  -- 备注
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (statement_id) REFERENCES statements(id) ON DELETE CASCADE
);

CREATE INDEX idx_transactions_statement ON transactions(statement_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_classification ON transactions(classification);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_supplier ON transactions(supplier_name);

-- ============================================================
-- 5. 月结算表 (settlements)
-- ============================================================
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    
    -- 结算期间
    settlement_month TEXT NOT NULL,              -- 结算月份 (YYYY-MM)
    
    -- Owner's Account 流水账
    owner_previous_balance REAL DEFAULT 0,       -- Owner上期余额
    owner_expenses REAL DEFAULT 0,               -- Owner's Expenses (Owner消费)
    owner_payments REAL DEFAULT 0,               -- Owner's Payment (Owner还款)
    owner_outstanding_balance REAL DEFAULT 0,    -- Owner's OS Bal (Owner欠款余额)
    
    -- GZ's Account 流水账
    gz_previous_balance REAL DEFAULT 0,          -- GZ上期余额
    gz_expenses REAL DEFAULT 0,                  -- GZ's Expenses (GZ消费)
    gz_payments REAL DEFAULT 0,                  -- GZ's Payment (GZ还款)
    gz_outstanding_balance REAL DEFAULT 0,       -- GZ's OS Bal (GZ欠款余额)
    
    -- 供应商费用
    total_supplier_fee REAL DEFAULT 0,           -- 1% 供应商手续费总额
    
    -- 优化节省
    optimization_savings REAL DEFAULT 0,         -- 优化节省总额
    platform_commission REAL DEFAULT 0,          -- 平台分成 (50%)
    customer_savings REAL DEFAULT 0,             -- 客户节省 (50%)
    
    -- 积分
    total_points_earned REAL DEFAULT 0,          -- 本月赚取积分总额
    
    -- 状态
    settlement_status TEXT DEFAULT 'draft' CHECK(settlement_status IN ('draft', 'confirmed', 'paid', 'cancelled')),
    
    -- 报告文件
    report_pdf_path TEXT,                        -- 生成的PDF报告路径
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,                      -- 确认时间
    paid_at TIMESTAMP,                           -- 支付时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, settlement_month)            -- 每个用户每月只能有一份结算
);

CREATE INDEX idx_settlements_user ON settlements(user_id);
CREATE INDEX idx_settlements_month ON settlements(settlement_month);
CREATE INDEX idx_settlements_status ON settlements(settlement_status);

-- ============================================================
-- 6. 供应商列表 (suppliers)
-- ============================================================
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 供应商信息
    supplier_name TEXT UNIQUE NOT NULL,          -- 供应商标准名称
    supplier_aliases TEXT,                       -- 别名列表 (JSON数组)
    supplier_category TEXT,                      -- 分类 (7SL主要供应商/Shop/Utilities)
    
    -- 费用配置
    fee_percentage REAL DEFAULT 1.0,             -- 手续费比例 (默认1%)
    is_active INTEGER DEFAULT 1,                 -- 状态 (1=启用, 0=停用)
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);
CREATE INDEX idx_suppliers_category ON suppliers(supplier_category);

-- ============================================================
-- 7. 提醒记录表 (reminders)
-- ============================================================
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    
    -- 提醒信息
    reminder_type TEXT NOT NULL CHECK(reminder_type IN ('payment_due', 'statement_upload', 'settlement', 'custom')),
    reminder_content TEXT NOT NULL,              -- 提醒内容
    
    -- 时间配置
    scheduled_time TIMESTAMP NOT NULL,           -- 预定发送时间
    sent_at TIMESTAMP,                           -- 实际发送时间
    
    -- 发送状态
    send_status TEXT DEFAULT 'pending' CHECK(send_status IN ('pending', 'sent', 'failed', 'cancelled')),
    send_channel TEXT CHECK(send_channel IN ('email', 'sms', 'in_app', 'all')),  -- 发送渠道
    
    -- 关联实体
    related_entity_type TEXT,                    -- 关联实体类型 (statement/settlement/card)
    related_entity_id INTEGER,                   -- 关联实体ID
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_reminders_user ON reminders(user_id);
CREATE INDEX idx_reminders_type ON reminders(reminder_type);
CREATE INDEX idx_reminders_status ON reminders(send_status);
CREATE INDEX idx_reminders_scheduled ON reminders(scheduled_time);

-- ============================================================
-- 8. 合同签约表 (contracts)
-- ============================================================
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    
    -- 合同信息
    contract_type TEXT NOT NULL CHECK(contract_type IN ('service_agreement', 'optimization_proposal', 'payment_on_behalf', 'other')),
    contract_number TEXT UNIQUE NOT NULL,        -- 合同编号
    contract_content TEXT NOT NULL,              -- 合同内容 (HTML/Markdown)
    
    -- 签署信息
    signed_at TIMESTAMP,                         -- 签署时间
    signature_image_path TEXT,                   -- 签名图片路径
    ip_address TEXT,                             -- 签署IP地址
    
    -- 合同状态
    contract_status TEXT DEFAULT 'draft' CHECK(contract_status IN ('draft', 'pending_signature', 'signed', 'expired', 'terminated')),
    
    -- 有效期
    effective_date TEXT,                         -- 生效日期
    expiration_date TEXT,                        -- 到期日期
    
    -- 文件路径
    pdf_path TEXT,                               -- 合同PDF文件路径
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_contracts_user ON contracts(user_id);
CREATE INDEX idx_contracts_type ON contracts(contract_type);
CREATE INDEX idx_contracts_status ON contracts(contract_status);
CREATE INDEX idx_contracts_number ON contracts(contract_number);

-- ============================================================
-- 9. 贷款产品知识库 (loan_products)
-- ============================================================
CREATE TABLE IF NOT EXISTS loan_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 机构信息
    institution_name TEXT NOT NULL,              -- 金融机构名称
    institution_type TEXT CHECK(institution_type IN ('bank', 'fintech', 'credit_cooperative', 'other')),
    
    -- 产品信息
    product_name TEXT NOT NULL,                  -- 产品名称
    product_type TEXT CHECK(product_type IN ('personal_loan', 'sme_loan', 'housing_loan', 'car_loan', 'credit_card', 'other')),
    
    -- 利率信息
    interest_rate_min REAL,                      -- 最低利率 (%)
    interest_rate_max REAL,                      -- 最高利率 (%)
    interest_rate_type TEXT CHECK(interest_rate_type IN ('fixed', 'floating', 'hybrid')),
    
    -- 额度信息
    loan_amount_min REAL,                        -- 最低贷款额
    loan_amount_max REAL,                        -- 最高贷款额
    
    -- 期限信息
    loan_term_min INTEGER,                       -- 最短期限（月）
    loan_term_max INTEGER,                       -- 最长期限（月）
    
    -- 申请条件
    min_income REAL,                             -- 最低月收入要求
    min_ctos_score INTEGER,                      -- 最低CTOS评分
    max_dsr REAL,                                -- 最高DSR要求
    
    -- 产品特色
    features TEXT,                               -- 产品特色（JSON格式）
    fees TEXT,                                   -- 费用说明（JSON格式）
    
    -- 状态
    is_active INTEGER DEFAULT 1,                 -- 产品状态 (1=上架, 0=下架)
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP                   -- 最后验证日期
);

CREATE INDEX idx_loan_products_institution ON loan_products(institution_name);
CREATE INDEX idx_loan_products_type ON loan_products(product_type);
CREATE INDEX idx_loan_products_active ON loan_products(is_active);

-- ============================================================
-- 10. 税务记录表 (tax_records)
-- ============================================================
CREATE TABLE IF NOT EXISTS tax_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    
    -- 税务年度
    tax_year INTEGER NOT NULL,                   -- 税务年度
    
    -- 收入信息
    total_income REAL DEFAULT 0,                 -- 年度总收入
    employment_income REAL DEFAULT 0,            -- 就业收入
    business_income REAL DEFAULT 0,              -- 营业收入
    other_income REAL DEFAULT 0,                 -- 其他收入
    
    -- 扣除项
    total_deductions REAL DEFAULT 0,             -- 总扣除额
    epf_deduction REAL DEFAULT 0,                -- EPF扣除
    insurance_deduction REAL DEFAULT 0,          -- 保险扣除
    education_deduction REAL DEFAULT 0,          -- 教育扣除
    other_deductions REAL DEFAULT 0,             -- 其他扣除
    
    -- 应纳税额
    taxable_income REAL DEFAULT 0,               -- 应纳税收入
    tax_payable REAL DEFAULT 0,                  -- 应缴税额
    tax_paid REAL DEFAULT 0,                     -- 已缴税额
    tax_refund REAL DEFAULT 0,                   -- 退税额
    
    -- 状态
    tax_status TEXT DEFAULT 'draft' CHECK(tax_status IN ('draft', 'submitted', 'approved', 'rejected')),
    
    -- 文件
    tax_return_path TEXT,                        -- 报税表文件路径
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,                      -- 提交时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, tax_year)                    -- 每个用户每年只能有一份税务记录
);

CREATE INDEX idx_tax_records_user ON tax_records(user_id);
CREATE INDEX idx_tax_records_year ON tax_records(tax_year);
CREATE INDEX idx_tax_records_status ON tax_records(tax_status);

-- ============================================================
-- 11. 月度账本汇总表 (monthly_statements)
-- Infinite GZ Module 4 核心表：6个强制字段
-- ============================================================
CREATE TABLE IF NOT EXISTS monthly_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID外键
    card_id INTEGER NOT NULL,                    -- 信用卡ID外键
    statement_id INTEGER,                        -- 原始账单ID（可选）
    
    -- 月份信息
    statement_month TEXT NOT NULL,               -- YYYY-MM
    
    -- Module 4: 6个强制字段（100%准确度要求）
    total_spent REAL NOT NULL DEFAULT 0,         -- 字段1: 总支出
    total_fees REAL NOT NULL DEFAULT 0,          -- 字段2: 总费用（1% supplier fee）
    total_supplier_consumption REAL NOT NULL DEFAULT 0,  -- 字段3: 供应商消费总额
    total_customer_payment REAL NOT NULL DEFAULT 0,      -- 字段4: 客户付款总额
    total_revenue REAL NOT NULL DEFAULT 0,       -- 字段5: 总收入（fees + supplier consumption）
    total_refunds REAL NOT NULL DEFAULT 0,       -- 字段6: 退款总额
    
    -- 额外统计字段
    previous_balance REAL DEFAULT 0,             -- 上期余额
    current_balance REAL DEFAULT 0,              -- 当前余额
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES credit_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (statement_id) REFERENCES statements(id) ON DELETE SET NULL,
    UNIQUE(card_id, statement_month)
);

CREATE INDEX idx_monthly_statements_user ON monthly_statements(user_id);
CREATE INDEX idx_monthly_statements_card ON monthly_statements(card_id);
CREATE INDEX idx_monthly_statements_month ON monthly_statements(statement_month);

-- ============================================================
-- 初始化供应商数据
-- ============================================================
INSERT OR IGNORE INTO suppliers (supplier_name, supplier_category, fee_percentage, supplier_aliases) VALUES
('7SL', '7SL主要供应商', 1.0, '["7sl", "7SL TECH", "7SL SDN BHD"]'),
('Dinas Raub', '7SL主要供应商', 1.0, '["DINAS", "DINAS RAUB"]'),
('SYC Hainan', '7SL主要供应商', 1.0, '["RAUB SYC HAINAN", "SYC HAINAN"]'),
('Ai Smart Tech', '7SL主要供应商', 1.0, '["AI SMART", "AI SMART TECH SDN BHD"]'),
('HUAWEI', '7SL主要供应商', 1.0, '["HUAWEI", "HUAWEI TECHNOLOGY"]'),
('Pasar Raya', '7SL主要供应商', 1.0, '["PASAR RAYA"]'),
('Puchong Herbs', '7SL主要供应商', 1.0, '["PUCHONG HERBS"]'),
('Shopee', 'Shop', 0, '["SHOPEE", "SHOPEE MALAYSIA"]'),
('Lazada', 'Shop', 0, '["LAZADA", "LAZADA MALAYSIA"]'),
('TNB', 'Utilities', 0, '["TNB", "TENAGA NASIONAL"]');

-- ============================================================
-- 初始化管理员账户（密码：admin123，需要后续hash）
-- ============================================================
INSERT OR IGNORE INTO users (name, email, role, is_active) VALUES
('System Administrator', 'admin@infinitegz.com', 'admin', 1);

-- ============================================================
-- 数据完整性检查视图
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_statement_summary AS
SELECT 
    s.id,
    s.statement_month,
    u.name as user_name,
    cc.bank_name,
    cc.card_number_last4,
    s.total_amount,
    s.min_payment,
    s.parse_status,
    s.is_confirmed,
    COUNT(t.id) as transaction_count,
    SUM(CASE WHEN t.classification = 'Owner' THEN t.debit_amount ELSE 0 END) as owner_expenses,
    SUM(CASE WHEN t.classification = 'GZ' THEN t.debit_amount ELSE 0 END) as gz_expenses,
    SUM(CASE WHEN t.classification = 'Owner' THEN t.credit_amount ELSE 0 END) as owner_payments,
    SUM(CASE WHEN t.classification = 'GZ' THEN t.credit_amount ELSE 0 END) as gz_payments
FROM statements s
JOIN users u ON s.user_id = u.id
JOIN credit_cards cc ON s.card_id = cc.id
LEFT JOIN transactions t ON s.id = t.statement_id
GROUP BY s.id;

-- ============================================================
-- 完成提示
-- ============================================================
-- 数据库初始化完成！
-- 包含 11 个核心表 + 1 个汇总视图
-- 支持完整的 Infinite GZ 业务流程：
-- 1. 用户管理
-- 2. 信用卡账户管理
-- 3. 账单解析与验证
-- 4. 交易分类（Owner/GZ）
-- 5. 月度结算
-- 6. 供应商管理
-- 7. 提醒系统
-- 8. 合同签约
-- 9. 贷款产品知识库
-- 10. 税务记录
-- 11. 月度汇总（Module 4）
-- ============================================================
