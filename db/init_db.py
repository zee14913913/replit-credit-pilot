import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            monthly_income REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            card_number_last4 TEXT NOT NULL,
            card_type TEXT,
            credit_limit REAL DEFAULT 0,
            due_date INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # ⚠️ DEPRECATED TABLE: statements
    # 此表已废弃，仅保留用于历史数据查询
    # 新系统请使用: monthly_statements (月度账单合并表)
    # Deprecated: This table is kept only for historical data reference
    # New system uses: monthly_statements (consolidated monthly statements)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            statement_date TEXT NOT NULL,
            statement_total REAL NOT NULL,
            file_path TEXT,
            file_type TEXT,
            validation_score REAL DEFAULT 0,
            is_confirmed INTEGER DEFAULT 0,
            inconsistencies TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER NOT NULL,
            transaction_date TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            category TEXT,
            category_confidence REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (statement_id) REFERENCES statements(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repayment_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            amount_due REAL,
            reminder_sent_7days INTEGER DEFAULT 0,
            reminder_sent_3days INTEGER DEFAULT 0,
            reminder_sent_1day INTEGER DEFAULT 0,
            is_paid INTEGER DEFAULT 0,
            paid_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            monthly_income REAL NOT NULL,
            total_monthly_repayments REAL NOT NULL,
            dsr REAL NOT NULL,
            max_loan_amount REAL,
            loan_term_months INTEGER,
            interest_rate REAL,
            monthly_installment REAL,
            evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # ⚠️ REMOVED: banking_news table (News Management feature deprecated)
    # 已删除: banking_news 表（新闻管理功能已废弃）
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bnm_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rate_type TEXT NOT NULL,
            rate_value REAL NOT NULL,
            effective_date TEXT NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            description TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {DB_PATH}")

if __name__ == "__main__":
    init_database()
