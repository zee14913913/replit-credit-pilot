-- 咨询预约请求表
CREATE TABLE IF NOT EXISTS consultation_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    suggestion_id INTEGER NOT NULL,
    preferred_contact_method TEXT DEFAULT 'meeting', -- 'meeting' or 'call'
    preferred_date TEXT,
    confirmed_date TEXT,
    meeting_location TEXT,
    customer_notes TEXT,
    outcome_notes TEXT,
    proceed_with_service INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (suggestion_id) REFERENCES financial_optimization_suggestions(id)
);

-- 服务合同表
CREATE TABLE IF NOT EXISTS service_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    suggestion_id INTEGER NOT NULL,
    consultation_request_id INTEGER,
    contract_number TEXT UNIQUE NOT NULL,
    service_type TEXT NOT NULL,
    total_savings REAL NOT NULL,
    our_fee_50_percent REAL NOT NULL,
    actual_payment_amount REAL DEFAULT 0,
    contract_file_path TEXT,
    customer_signed INTEGER DEFAULT 0,
    customer_signed_date TEXT,
    company_signed INTEGER DEFAULT 0,
    company_signed_date TEXT,
    status TEXT DEFAULT 'pending_signature', -- 'pending_signature', 'active', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (suggestion_id) REFERENCES financial_optimization_suggestions(id),
    FOREIGN KEY (consultation_request_id) REFERENCES consultation_requests(id)
);

-- 代付记录表
CREATE TABLE IF NOT EXISTS payment_on_behalf_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    card_id INTEGER,
    amount REAL NOT NULL,
    payment_type TEXT NOT NULL, -- 'bill_payment', 'balance_transfer'
    payment_date TEXT NOT NULL,
    notes TEXT,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES service_contracts(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id)
);

-- 扩展success_fee_calculations表（如果列不存在）
-- SQLite不支持ALTER TABLE ADD IF NOT EXISTS，所以这些会在Python中处理
