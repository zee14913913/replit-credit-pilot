"""
客户收款账户字段迁移
用于记录GZ可能转账给客户的2个收款账户
支持GZ's Payment (Indirect)的精准匹配和结算
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

def add_customer_receiving_account_fields():
    """在customers表添加2个收款账户字段"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("添加客户收款账户字段（用于GZ转账匹配）...")
    print("=" * 80)
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(customers)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # 添加收款账户1
        if 'receiving_account_1' not in existing_columns:
            cursor.execute('''
                ALTER TABLE customers 
                ADD COLUMN receiving_account_1 TEXT DEFAULT NULL
            ''')
            print("✓ Added receiving_account_1 field (收款账户1)")
        else:
            print("⊙ receiving_account_1 already exists (字段已存在)")
        
        # 添加收款账户2
        if 'receiving_account_2' not in existing_columns:
            cursor.execute('''
                ALTER TABLE customers 
                ADD COLUMN receiving_account_2 TEXT DEFAULT NULL
            ''')
            print("✓ Added receiving_account_2 field (收款账户2)")
        else:
            print("⊙ receiving_account_2 already exists (字段已存在)")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ 客户收款账户字段添加完成！")
        print("=" * 80)
        print("\n字段说明：")
        print("  • receiving_account_1 - 收款账户1（账户持有人名称 + 银行简称）")
        print("  • receiving_account_2 - 收款账户2（账户持有人名称 + 银行简称）")
        print("\n用途：")
        print("  • 用于匹配INFINITE GZ BANK LIST的转账记录")
        print("  • 计算GZ's Payment (Indirect)时精准识别客户收款账户")
        print("  • 支持Receipts和Invoices验证所有消费/付款交易")
        print("\n示例格式：")
        print("  • CHEOK JUN YOON - Maybank")
        print("  • INFINITE GZ SDN BHD - Hong Leong Bank")
        print("=" * 80)
        
    except sqlite3.Error as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_customer_receiving_account_fields()
