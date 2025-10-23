"""
Add verification_status field to savings_statements table
用于100%准确性验证系统
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

def add_verification_status_field():
    """添加验证状态字段到savings_statements表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("Adding verification_status field to savings_statements...")
    print("=" * 80)
    
    try:
        cursor.execute('''
            ALTER TABLE savings_statements 
            ADD COLUMN verification_status TEXT DEFAULT 'pending'
        ''')
        print("✓ Added verification_status field (可选值: pending, verified, discrepancy)")
        
        cursor.execute('''
            ALTER TABLE savings_statements 
            ADD COLUMN verified_by TEXT
        ''')
        print("✓ Added verified_by field (记录验证人)")
        
        cursor.execute('''
            ALTER TABLE savings_statements 
            ADD COLUMN verified_at TIMESTAMP
        ''')
        print("✓ Added verified_at field (记录验证时间)")
        
        cursor.execute('''
            ALTER TABLE savings_statements 
            ADD COLUMN discrepancy_notes TEXT
        ''')
        print("✓ Added discrepancy_notes field (记录差异说明)")
        
        conn.commit()
        print("\n✅ Verification fields added successfully!")
        print("=" * 80)
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ Verification fields already exist, skipping...")
        else:
            raise e
    finally:
        conn.close()

if __name__ == '__main__':
    add_verification_status_field()
