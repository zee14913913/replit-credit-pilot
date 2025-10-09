-- 扩展交易表，添加使用人和用途字段
ALTER TABLE transactions ADD COLUMN user_name TEXT; -- 使用人 / 付款人
ALTER TABLE transactions ADD COLUMN purpose TEXT; -- 用于 / 付款于
ALTER TABLE transactions ADD COLUMN belongs_to TEXT DEFAULT 'customer'; -- 'customer' or 'gz'

-- 客户自定义分类配置表
CREATE TABLE IF NOT EXISTS customer_classification_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    category_type TEXT NOT NULL, -- 'debit' or 'credit'
    keywords TEXT, -- JSON array of keywords
    auto_assign_to TEXT DEFAULT 'customer', -- 'customer' or 'gz'
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    UNIQUE(customer_id, category_name)
);

-- 账单余额分析表
CREATE TABLE IF NOT EXISTS statement_balance_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    
    -- 客户部分
    customer_previous_balance REAL DEFAULT 0,
    customer_debit_total REAL DEFAULT 0,
    customer_credit_total REAL DEFAULT 0,
    customer_balance REAL DEFAULT 0, -- previous_balance + debit - credit
    
    -- GZ部分
    gz_debit_total REAL DEFAULT 0,
    gz_credit_total REAL DEFAULT 0,
    gz_balance REAL DEFAULT 0, -- gz_debit - gz_credit
    
    -- 手续费
    merchant_fee_total REAL DEFAULT 0,
    
    -- 总计
    statement_total REAL DEFAULT 0,
    
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 扩展statements表
ALTER TABLE statements ADD COLUMN previous_balance REAL DEFAULT 0;
ALTER TABLE statements ADD COLUMN due_date TEXT;
