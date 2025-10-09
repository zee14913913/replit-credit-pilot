-- 扩展交易表，添加交易类型分类
ALTER TABLE transactions ADD COLUMN transaction_type TEXT DEFAULT 'debit'; -- 'debit' or 'credit'
ALTER TABLE transactions ADD COLUMN transaction_subtype TEXT; -- 'supplier_debit', 'shop_debit', 'others_debit', '3rd_party_credit', 'owner_credit'
ALTER TABLE transactions ADD COLUMN supplier_fee REAL DEFAULT 0; -- 1% fee for specific suppliers
ALTER TABLE transactions ADD COLUMN payment_user TEXT; -- Who made the payment
ALTER TABLE transactions ADD COLUMN is_processed INTEGER DEFAULT 0; -- Processing status

-- 信用卡积分追踪表
CREATE TABLE IF NOT EXISTS card_points_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    statement_id INTEGER NOT NULL,
    previous_points REAL DEFAULT 0,
    earned_points REAL DEFAULT 0,
    total_points REAL DEFAULT 0,
    statement_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);

-- 付款收据表
CREATE TABLE IF NOT EXISTS payment_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    receipt_file_path TEXT NOT NULL,
    payment_amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 供应商发票表
CREATE TABLE IF NOT EXISTS supplier_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    statement_id INTEGER NOT NULL,
    supplier_name TEXT NOT NULL,
    invoice_number TEXT UNIQUE NOT NULL,
    total_amount REAL NOT NULL,
    supplier_fee REAL NOT NULL,
    invoice_date TEXT NOT NULL,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);

-- 月度总结报告表
CREATE TABLE IF NOT EXISTS monthly_summary_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    month TEXT NOT NULL, -- Format: YYYY-MM
    total_debit REAL DEFAULT 0,
    total_credit REAL DEFAULT 0,
    supplier_debit REAL DEFAULT 0,
    shop_debit REAL DEFAULT 0,
    others_debit REAL DEFAULT 0,
    third_party_credit REAL DEFAULT 0,
    owner_credit REAL DEFAULT 0,
    total_supplier_fee REAL DEFAULT 0,
    total_points_earned REAL DEFAULT 0,
    report_pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 扩展提醒表，添加statement date提醒
CREATE TABLE IF NOT EXISTS statement_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    statement_date TEXT NOT NULL,
    reminder_date TEXT NOT NULL, -- statement_date + 3 days
    is_sent INTEGER DEFAULT 0,
    is_uploaded INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 扩展statements表，添加卡号全号
ALTER TABLE statements ADD COLUMN card_full_number TEXT;
ALTER TABLE statements ADD COLUMN points_earned REAL DEFAULT 0;

-- 特定供应商配置表
CREATE TABLE IF NOT EXISTS supplier_fee_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT UNIQUE NOT NULL,
    fee_percentage REAL DEFAULT 1.0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入7个特定供应商
INSERT OR IGNORE INTO supplier_fee_config (supplier_name, fee_percentage) VALUES
('7sl', 1.0),
('Dinas', 1.0),
('Raub Syc Hainan', 1.0),
('Ai Smart Tech', 1.0),
('Huawei', 1.0),
('Pasar Raya', 1.0),
('Puchong Herbs', 1.0);

-- Shop/Utilities供应商配置表
CREATE TABLE IF NOT EXISTS shop_utilities_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT 'shop',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入Shop/Utilities供应商
INSERT OR IGNORE INTO shop_utilities_config (supplier_name, category) VALUES
('Shopee', 'shop'),
('Lazada', 'shop'),
('TNB', 'utilities');
