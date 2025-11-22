#!/usr/bin/env python3
"""
创建月度账本表 - 用于双轨财务计算系统
"""
import sqlite3
from datetime import datetime

def create_monthly_ledger_tables():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 1. 客户月度账本表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            month_start TEXT NOT NULL,
            statement_id INTEGER,
            previous_balance REAL DEFAULT 0,
            customer_spend REAL DEFAULT 0,
            customer_payments REAL DEFAULT 0,
            rolling_balance REAL DEFAULT 0,
            is_reconciled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (statement_id) REFERENCES statements(id),
            UNIQUE(card_id, month_start)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_monthly_ledger_card_month 
        ON monthly_ledger(card_id, month_start)
    ''')
    
    # 2. INFINITE月度账本表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS infinite_monthly_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            month_start TEXT NOT NULL,
            statement_id INTEGER,
            previous_balance REAL DEFAULT 0,
            infinite_spend REAL DEFAULT 0,
            supplier_fee REAL DEFAULT 0,
            infinite_payments REAL DEFAULT 0,
            rolling_balance REAL DEFAULT 0,
            transfer_count INTEGER DEFAULT 0,
            is_reconciled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (statement_id) REFERENCES statements(id),
            UNIQUE(card_id, month_start)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_infinite_monthly_ledger_card_month 
        ON infinite_monthly_ledger(card_id, month_start)
    ''')
    
    # 3. INFINITE转账记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS infinite_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            savings_transaction_id INTEGER,
            transfer_date TEXT NOT NULL,
            payer_name TEXT NOT NULL,
            payee_name TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            month_start TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (savings_transaction_id) REFERENCES savings_transactions(id)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_infinite_transfers_card_month 
        ON infinite_transfers(card_id, month_start)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_infinite_transfers_date 
        ON infinite_transfers(transfer_date)
    ''')
    
    # 4. 供应商别名配置表（用于识别INFINITE供应商）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            alias TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(alias)
        )
    ''')
    
    # 插入INFINITE供应商别名
    infinite_suppliers = [
        ('7SL', '7sl'),
        ('7SL', '7 sl'),
        ('7SL', 'seven sl'),
        ('DINAS', 'dinas'),
        ('RAUB SYC HAINAN', 'raub syc hainan'),
        ('RAUB SYC HAINAN', 'raub'),
        ('RAUB SYC HAINAN', 'hainan'),
        ('AI SMART TECH', 'ai smart tech'),
        ('AI SMART TECH', 'ai smart'),
        ('HUAWEI', 'huawei'),
        ('PASAR RAYA', 'pasar raya'),
        ('PASAR RAYA', 'pasar'),
        ('PUCHONG HERBS', 'puchong herbs'),
        ('PUCHONG HERBS', 'puchong')
    ]
    
    for supplier, alias in infinite_suppliers:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO supplier_aliases (supplier_name, alias, is_active)
                VALUES (?, ?, 1)
            ''', (supplier, alias))
        except:
            pass
    
    # 5. 付款人别名配置表（用于识别客户本名付款）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payer_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            payer_type TEXT NOT NULL,
            alias TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id, alias)
        )
    ''')
    
    # 插入Chang Choon Chow的付款人别名
    # customer_type: 'customer' = 客户本名, 'company' = 公司名
    customer_aliases = [
        (5, 'customer', 'CHANG CHOON CHOW'),
        (5, 'customer', 'chang choon chow'),
        (5, 'company', 'KENG CHOW'),
        (5, 'company', 'keng chow')
    ]
    
    for customer_id, payer_type, alias in customer_aliases:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO payer_aliases (customer_id, payer_type, alias, is_active)
                VALUES (?, ?, ?, 1)
            ''', (customer_id, payer_type, alias))
        except:
            pass
    
    # 6. 转账收款人别名表（用于识别INFINITE转账）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfer_recipient_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            recipient_name TEXT NOT NULL,
            alias TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id, alias)
        )
    ''')
    
    # 插入Chang Choon Chow的转账收款人别名
    transfer_recipients = [
        (5, 'CHANG CHOON CHOW', 'CHANG CHOON CHOW'),
        (5, 'CHANG CHOON CHOW', 'chang choon chow'),
        (5, 'KENG CHOW', 'KENG CHOW'),
        (5, 'KENG CHOW', 'keng chow'),
        (5, 'MAKAN DULU', 'MAKAN DULU'),
        (5, 'MAKAN DULU', 'makan dulu'),
        (5, 'LEE CHEE HWA', 'LEE CHEE HWA'),
        (5, 'LEE CHEE HWA', 'lee chee hwa'),
        (5, 'WING CHOW', 'WING CHOW'),
        (5, 'WING CHOW', 'wing chow')
    ]
    
    for customer_id, recipient_name, alias in transfer_recipients:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO transfer_recipient_aliases (customer_id, recipient_name, alias, is_active)
                VALUES (?, ?, ?, 1)
            ''', (customer_id, recipient_name, alias))
        except:
            pass
    
    conn.commit()
    conn.close()
    
    print("✅ 月度账本表创建成功！")
    print("\n创建的表：")
    print("  1. monthly_ledger - 客户月度账本")
    print("  2. infinite_monthly_ledger - INFINITE月度账本")
    print("  3. infinite_transfers - INFINITE转账记录")
    print("  4. supplier_aliases - 供应商别名配置")
    print("  5. payer_aliases - 付款人别名配置")
    print("  6. transfer_recipient_aliases - 转账收款人别名")

if __name__ == "__main__":
    create_monthly_ledger_tables()
