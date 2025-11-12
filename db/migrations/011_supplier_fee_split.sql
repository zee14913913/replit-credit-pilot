-- 011_supplier_fee_split.sql
-- 手续费独立计入 Owner 的数据库架构升级

BEGIN;

-- transactions：拆分手续费所需字段（SQLite版本）
-- 注意：SQLite不支持ALTER COLUMN，使用ADD COLUMN IF NOT EXISTS

-- 检查并添加新字段
CREATE TABLE IF NOT EXISTS transactions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT,
    customer_id INTEGER,
    card_id INTEGER,
    statement_id INTEGER,
    transaction_date TEXT,
    description TEXT,
    amount REAL,
    transaction_type TEXT,
    category TEXT,
    merchant_category TEXT,
    is_supplier BOOLEAN DEFAULT 0,
    supplier_name TEXT,
    supplier_fee REAL,
    is_merchant_fee BOOLEAN DEFAULT 0,
    fee_reference_id INTEGER,
    is_fee_split BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (statement_id) REFERENCES monthly_statements(id),
    FOREIGN KEY (fee_reference_id) REFERENCES transactions(id)
);

-- 如果transactions表已存在，检查是否需要迁移
-- （实际执行时需要判断表结构）

COMMIT;
