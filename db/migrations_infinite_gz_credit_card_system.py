"""
INFINITE GZ 信用卡系统 - 完整数据库迁移
按照INFINITE GZ信用卡系统开发任务书（Final版）规范
包含：月度账单交易表、Supplier表、GZ银行白名单、积分表、协议表等
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

def create_infinite_gz_credit_card_tables():
    """创建INFINITE GZ信用卡系统所需的所有数据表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("INFINITE GZ 信用卡系统 - 数据库迁移")
    print("=" * 80)
    
    # ========== 1. 月度账单交易明细表 ==========
    # 任务书第4节：每张信用卡账单的逐行交易记录（1:1原样复刻）
    print("\n[1/8] 创建月度账单交易明细表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_statement_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            statement_month TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            card_last4 TEXT NOT NULL,
            
            -- 原始账单字段（1:1复刻，不得修改）
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            record_type TEXT NOT NULL CHECK(record_type IN ('spend', 'payment', 'fee', 'adjustment')),
            source_doc_type TEXT NOT NULL CHECK(source_doc_type IN ('CC Statement', 'Bank Statement', 'Transfer Slip')),
            
            -- 系统分类字段（任务书第5节）
            expense_owner TEXT CHECK(expense_owner IN ('Owner''s Expenses', 'GZ''s Expenses', NULL)),
            payment_type TEXT CHECK(payment_type IN ('Owner Payment', 'GZ Direct', 'GZ Indirect', NULL)),
            category TEXT CHECK(category IN ('Card Due Assist', 'Loan-Credit Assist', NULL)),
            
            -- 验证字段
            verified INTEGER DEFAULT 0,
            needs_review INTEGER DEFAULT 0,
            
            -- Supplier相关
            is_supplier_transaction INTEGER DEFAULT 0,
            supplier_name TEXT,
            supplier_fee REAL DEFAULT 0,
            supplier_invoice_id INTEGER,
            
            -- 元数据
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (supplier_invoice_id) REFERENCES supplier_invoices(id)
        )
    ''')
    
    # 创建索引加速查询
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_monthly_trans_customer 
        ON monthly_statement_transactions(customer_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_monthly_trans_statement 
        ON monthly_statement_transactions(statement_month, bank_name, card_last4)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_monthly_trans_supplier 
        ON monthly_statement_transactions(is_supplier_transaction, supplier_name)
    ''')
    print("✓ 月度账单交易明细表创建完成")
    
    # ========== 2. Supplier 白名单配置表 ==========
    # 任务书第5.1节：Supplier List
    print("\n[2/8] 创建Supplier配置表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL UNIQUE,
            supplier_category TEXT,
            fee_percentage REAL DEFAULT 0.01,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入默认Supplier List（任务书第5.1节）
    default_suppliers = [
        ('7sl', 'Business', 0.01, 1),
        ('Dinas', 'Business', 0.01, 1),
        ('Raub Syc Hainan', 'Business', 0.01, 1),
        ('Ai Smart Tech', 'Business', 0.01, 1),
        ('Huawei', 'Business', 0.01, 1),
        ('Pasar Raya', 'Business', 0.01, 1),
        ('Puchong Herbs', 'Business', 0.01, 1),
    ]
    
    for supplier_name, category, fee, is_active in default_suppliers:
        cursor.execute('''
            INSERT OR IGNORE INTO supplier_list (supplier_name, supplier_category, fee_percentage, is_active)
            VALUES (?, ?, ?, ?)
        ''', (supplier_name, category, fee, is_active))
    
    print("✓ Supplier配置表创建完成（默认7个Supplier）")
    
    # ========== 3. Supplier Invoice 表 ==========
    # 任务书第7节：每笔Supplier消费都必须生成Invoice
    print("\n[3/8] 创建Supplier Invoice表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            transaction_id INTEGER,
            
            supplier_name TEXT NOT NULL,
            invoice_number TEXT UNIQUE NOT NULL,
            invoice_date TEXT NOT NULL,
            statement_month TEXT NOT NULL,
            
            amount REAL NOT NULL,
            fee_percentage REAL DEFAULT 0.01,
            fee_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            
            card_last4 TEXT,
            bank_name TEXT,
            
            file_path TEXT,
            is_generated INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (transaction_id) REFERENCES monthly_statement_transactions(id)
        )
    ''')
    print("✓ Supplier Invoice表创建完成")
    
    # ========== 4. GZ 银行白名单 ==========
    # 任务书第16节：9个GZ银行账户
    print("\n[4/8] 创建GZ银行白名单表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gz_bank_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_holder_name TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            account_number_last4 TEXT,
            full_account_identifier TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入默认GZ银行账户（任务书第16节）
    default_gz_banks = [
        ('tan zee liang', 'GX bank', '', 'tan zee liang GX bank'),
        ('Yeo chee wang', 'MBB', '', 'Yeo chee wang MBB'),
        ('Yeo chee wang', 'GX bank', '', 'Yeo chee wang GX bank'),
        ('Yeo chee wang', 'UOB', '', 'Yeo chee wang UOB'),
        ('Yeo chee wang', 'OCBC', '', 'Yeo chee wang OCBC'),
        ('Teo yok chu & yeo chee wang', 'OCBC', '', 'Teo yok chu & yeo chee wang 联名 OCBC'),
        ('Infinite GZ Sdn Bhd', 'HLB', '', 'Infinite GZ Sdn Bhd HLB'),
        ('Ai Smart Tech', 'PBB bank', '', 'Ai Smart Tech PBB bank'),
        ('Ai Smart Tech', 'Alliance bank', '', 'Ai Smart Tech Alliance bank'),
    ]
    
    for holder, bank, last4, identifier in default_gz_banks:
        cursor.execute('''
            INSERT OR IGNORE INTO gz_bank_list (account_holder_name, bank_name, account_number_last4, full_account_identifier, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (holder, bank, last4, identifier))
    
    print("✓ GZ银行白名单表创建完成（默认9个账户）")
    
    # ========== 5. 积分追踪表 ==========
    # 任务书第14节：积分系统
    print("\n[5/8] 创建积分追踪表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS card_points_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            card_last4 TEXT NOT NULL,
            statement_month TEXT NOT NULL,
            
            points_earned REAL DEFAULT 0,
            points_redeemed REAL DEFAULT 0,
            points_adjustment REAL DEFAULT 0,
            points_total_after_month REAL DEFAULT 0,
            
            related_transactions TEXT,
            source_doc_type TEXT DEFAULT 'CreditCardStatement',
            verified INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id, card_last4, statement_month)
        )
    ''')
    print("✓ 积分追踪表创建完成")
    
    # ========== 6. 协议管理表 ==========
    # 任务书第15节：8类协议自动生成+E-Sign
    print("\n[6/8] 创建协议管理表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_agreements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            
            agreement_type TEXT NOT NULL CHECK(agreement_type IN (
                'Credit Card Management',
                'GZ Payment Direct',
                'GZ Payment Indirect',
                'Loan Agreement',
                'Supplier Invoice',
                'Points Acknowledgement',
                'PDPA',
                'Loan Application',
                'Financial Optimization'
            )),
            
            agreement_title TEXT NOT NULL,
            agreement_content TEXT NOT NULL,
            
            amount REAL,
            interest_rate REAL,
            repayment_terms TEXT,
            
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'signed', 'rejected', 'expired')),
            signed_date TIMESTAMP,
            signature_data TEXT,
            
            file_path TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("✓ 协议管理表创建完成")
    
    # ========== 7. Loan Outstanding 表 ==========
    # 任务书第11节：借贷系统（与信用卡无关）
    print("\n[7/8] 创建Loan Outstanding表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_outstanding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            
            loan_type TEXT NOT NULL CHECK(loan_type IN (
                'Build Profile',
                'Cash Flow Support',
                'Business Capital',
                'Investment',
                'Procurement',
                'Other'
            )),
            
            principal_amount REAL NOT NULL,
            interest_rate REAL NOT NULL,
            interest_type TEXT CHECK(interest_type IN ('Simple', 'Compound')),
            
            amount_repaid REAL DEFAULT 0,
            interest_accrued REAL DEFAULT 0,
            outstanding_balance REAL NOT NULL,
            
            disbursement_date TEXT NOT NULL,
            repayment_schedule TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'repaid', 'defaulted')),
            
            agreement_id INTEGER,
            transfer_slip_path TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (agreement_id) REFERENCES customer_agreements(id)
        )
    ''')
    print("✓ Loan Outstanding表创建完成")
    
    # ========== 8. GZ Transfer Records 表 ==========
    # 任务书第12节：Savings页面 - GZ→客户转账记录
    print("\n[8/8] 创建GZ转账记录表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gz_transfer_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            
            source_bank TEXT NOT NULL,
            destination_account TEXT NOT NULL,
            amount REAL NOT NULL,
            transfer_date TEXT NOT NULL,
            
            slip_file_path TEXT,
            
            purpose TEXT NOT NULL CHECK(purpose IN ('Card Due Assist', 'Loan-Credit Assist', 'Build Profile')),
            verified INTEGER DEFAULT 0,
            
            affects TEXT CHECK(affects IN ('GZ OS Balance', 'Loan Outstanding', 'None')),
            
            linked_statement_month TEXT,
            linked_loan_id INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (linked_loan_id) REFERENCES loan_outstanding(id)
        )
    ''')
    print("✓ GZ转账记录表创建完成")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ INFINITE GZ 信用卡系统数据库迁移完成！")
    print("=" * 80)
    print("\n数据表摘要：")
    print("  1. monthly_statement_transactions - 月度账单交易明细（1:1原样复刻）")
    print("  2. supplier_list - Supplier白名单（7个默认）")
    print("  3. supplier_invoices - Supplier Invoice自动生成")
    print("  4. gz_bank_list - GZ银行白名单（9个默认账户）")
    print("  5. card_points_history - 积分追踪系统")
    print("  6. customer_agreements - 8类协议管理+E-Sign")
    print("  7. loan_outstanding - 借贷系统（独立于信用卡）")
    print("  8. gz_transfer_records - GZ转账记录（用途判断）")
    print("\n系统已准备就绪，可开始实施分类引擎和OS Balance计算！")
    print("=" * 80)

if __name__ == '__main__':
    create_infinite_gz_credit_card_tables()
