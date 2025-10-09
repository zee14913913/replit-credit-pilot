#!/usr/bin/env python3
"""
Apply schema extensions for enhanced credit card management
"""

import sqlite3
from pathlib import Path

def apply_extensions():
    """Apply all schema extensions"""
    
    db_path = Path("db/smart_loan_manager.db")
    
    print(f"Applying schema extensions to: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add columns to transactions table
    print("\n📋 Extending transactions table...")
    
    columns_to_add = [
        ('transaction_type', 'TEXT DEFAULT "debit"'),
        ('transaction_subtype', 'TEXT'),
        ('supplier_fee', 'REAL DEFAULT 0'),
        ('payment_user', 'TEXT'),
        ('is_processed', 'INTEGER DEFAULT 0')
    ]
    
    for col_name, col_def in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE transactions ADD COLUMN {col_name} {col_def}')
            print(f"  ✓ Added {col_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"  → {col_name} already exists")
            else:
                print(f"  ✗ Error adding {col_name}: {e}")
    
    # Add columns to statements table
    print("\n📋 Extending statements table...")
    
    statements_columns = [
        ('card_full_number', 'TEXT'),
        ('points_earned', 'REAL DEFAULT 0')
    ]
    
    for col_name, col_def in statements_columns:
        try:
            cursor.execute(f'ALTER TABLE statements ADD COLUMN {col_name} {col_def}')
            print(f"  ✓ Added {col_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"  → {col_name} already exists")
            else:
                print(f"  ✗ Error adding {col_name}: {e}")
    
    # Create card_points_tracker table
    print("\n📊 Creating card_points_tracker table...")
    cursor.execute('''
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
        )
    ''')
    print("  ✓ card_points_tracker table created")
    
    # Create payment_receipts table
    print("\n📄 Creating payment_receipts table...")
    cursor.execute('''
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
        )
    ''')
    print("  ✓ payment_receipts table created")
    
    # Create supplier_invoices table
    print("\n🧾 Creating supplier_invoices table...")
    cursor.execute('''
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
        )
    ''')
    print("  ✓ supplier_invoices table created")
    
    # Create monthly_summary_reports table
    print("\n📊 Creating monthly_summary_reports table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_summary_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            month TEXT NOT NULL,
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
        )
    ''')
    print("  ✓ monthly_summary_reports table created")
    
    # Create statement_reminders table
    print("\n⏰ Creating statement_reminders table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statement_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            statement_date TEXT NOT NULL,
            reminder_date TEXT NOT NULL,
            is_sent INTEGER DEFAULT 0,
            is_uploaded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (statement_id) REFERENCES statements(id),
            FOREIGN KEY (card_id) REFERENCES credit_cards(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("  ✓ statement_reminders table created")
    
    # Create supplier_fee_config table
    print("\n⚙️ Creating supplier_fee_config table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_fee_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT UNIQUE NOT NULL,
            fee_percentage REAL DEFAULT 1.0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("  ✓ supplier_fee_config table created")
    
    # Insert 7 specific suppliers
    print("\n🏪 Inserting supplier fee configurations...")
    suppliers = [
        '7sl', 'Dinas', 'Raub Syc Hainan', 
        'Ai Smart Tech', 'Huawei', 'Pasar Raya', 'Puchong Herbs'
    ]
    
    for supplier in suppliers:
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO supplier_fee_config (supplier_name, fee_percentage) VALUES (?, ?)',
                (supplier, 1.0)
            )
            print(f"  ✓ Added {supplier}")
        except Exception as e:
            print(f"  ✗ Error adding {supplier}: {e}")
    
    # Create shop_utilities_config table
    print("\n🛒 Creating shop_utilities_config table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_utilities_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'shop',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("  ✓ shop_utilities_config table created")
    
    # Insert Shop/Utilities suppliers
    print("\n🛍️ Inserting shop/utilities configurations...")
    shop_utilities = [
        ('Shopee', 'shop'),
        ('Lazada', 'shop'),
        ('TNB', 'utilities')
    ]
    
    for name, category in shop_utilities:
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO shop_utilities_config (supplier_name, category) VALUES (?, ?)',
                (name, category)
            )
            print(f"  ✓ Added {name} ({category})")
        except Exception as e:
            print(f"  ✗ Error adding {name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Schema extensions applied successfully!")
    print("\n📋 Summary of new tables:")
    print("  • card_points_tracker - 追踪信用卡积分")
    print("  • payment_receipts - 付款收据管理")
    print("  • supplier_invoices - 供应商发票")
    print("  • monthly_summary_reports - 月度总结报告")
    print("  • statement_reminders - 账单上传提醒")
    print("  • supplier_fee_config - 供应商费用配置")
    print("  • shop_utilities_config - Shop/Utilities配置")

if __name__ == "__main__":
    apply_extensions()
