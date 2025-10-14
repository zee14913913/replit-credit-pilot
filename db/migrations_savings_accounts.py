"""
储蓄账户追踪系统 - 数据库迁移
用于追踪通过储蓄账户帮客户预付的转账记录
支持按客户名字搜索并生成结算报告
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

def create_savings_tracking_tables():
    """创建储蓄账户追踪相关表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("创建储蓄账户追踪系统数据表...")
    print("=" * 80)
    
    # 1. 储蓄账户表 (Savings Accounts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            bank_name TEXT NOT NULL,
            account_number_last4 TEXT NOT NULL,
            account_type TEXT DEFAULT 'Savings',
            account_holder_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("✓ Created savings_accounts table (储蓄账户表)")
    
    # 2. 储蓄账单表 (Savings Statements)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            savings_account_id INTEGER NOT NULL,
            statement_date TEXT NOT NULL,
            file_path TEXT,
            file_type TEXT,
            total_transactions INTEGER DEFAULT 0,
            is_processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (savings_account_id) REFERENCES savings_accounts(id)
        )
    ''')
    print("✓ Created savings_statements table (储蓄账单表)")
    
    # 3. 储蓄交易记录表 (Savings Transactions) - 完整记录所有转账
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            savings_statement_id INTEGER NOT NULL,
            transaction_date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT,
            balance REAL,
            reference_number TEXT,
            customer_name_tag TEXT,
            is_prepayment INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (savings_statement_id) REFERENCES savings_statements(id)
        )
    ''')
    print("✓ Created savings_transactions table (储蓄交易记录表)")
    
    # 4. 创建索引以加速搜索
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_savings_transactions_description 
        ON savings_transactions(description)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_savings_transactions_customer_tag 
        ON savings_transactions(customer_name_tag)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_savings_transactions_date 
        ON savings_transactions(transaction_date)
    ''')
    print("✓ Created search indexes (搜索索引)")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 储蓄账户追踪系统数据表创建完成！")
    print("=" * 80)
    print("\n数据表说明：")
    print("  1. savings_accounts - 储蓄账户基本信息")
    print("  2. savings_statements - 储蓄账户月结单")
    print("  3. savings_transactions - 所有转账交易记录（可按客户名搜索）")
    print("\n支持银行：Maybank, GX Bank, HLB, CIMB, UOB, OCBC, Public Bank")
    print("=" * 80)

if __name__ == '__main__':
    create_savings_tracking_tables()
