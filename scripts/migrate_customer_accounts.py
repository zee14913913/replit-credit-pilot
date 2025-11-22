import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from datetime import datetime

def migrate_customer_accounts():
    """
    创建customer_accounts表并迁移现有数据
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        print("🔧 创建 customer_accounts 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                account_type TEXT NOT NULL CHECK(account_type IN ('personal', 'company')),
                account_name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                bank_name TEXT,
                is_primary BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_accounts_customer_id ON customer_accounts(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_accounts_type ON customer_accounts(customer_id, account_type)')
        
        conn.commit()
        print("✅ customer_accounts 表创建成功")
        
        print("\n📦 迁移现有账户数据...")
        cursor.execute('''
            SELECT id, personal_account_name, personal_account_number,
                   company_account_name, company_account_number
            FROM customers
        ''')
        
        customers = cursor.fetchall()
        migrated_count = 0
        
        for customer in customers:
            customer_id = customer[0]
            personal_name = customer[1]
            personal_number = customer[2]
            company_name = customer[3]
            company_number = customer[4]
            
            if personal_name and personal_number:
                cursor.execute('''
                    SELECT COUNT(*) FROM customer_accounts 
                    WHERE customer_id = ? AND account_type = 'personal' AND account_number = ?
                ''', (customer_id, personal_number))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO customer_accounts (customer_id, account_type, account_name, account_number, is_primary)
                        VALUES (?, 'personal', ?, ?, 1)
                    ''', (customer_id, personal_name, personal_number))
                    migrated_count += 1
                    print(f"  ✓ 客户 #{customer_id}: 私人账户 {personal_name}")
                else:
                    print(f"  ⊘ 客户 #{customer_id}: 私人账户已存在，跳过")
            
            if company_name and company_number:
                cursor.execute('''
                    SELECT COUNT(*) FROM customer_accounts 
                    WHERE customer_id = ? AND account_type = 'company' AND account_number = ?
                ''', (customer_id, company_number))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO customer_accounts (customer_id, account_type, account_name, account_number, is_primary)
                        VALUES (?, 'company', ?, ?, 1)
                    ''', (customer_id, company_name, company_number))
                    migrated_count += 1
                    print(f"  ✓ 客户 #{customer_id}: 公司账户 {company_name}")
                else:
                    print(f"  ⊘ 客户 #{customer_id}: 公司账户已存在，跳过")
        
        conn.commit()
        print(f"\n✅ 成功迁移 {migrated_count} 个账户记录")
        
        cursor.execute('SELECT COUNT(*) FROM customer_accounts')
        total = cursor.fetchone()[0]
        print(f"📊 customer_accounts 表总记录数: {total}")

if __name__ == '__main__':
    print("=" * 60)
    print("客户账户表迁移脚本")
    print("=" * 60)
    migrate_customer_accounts()
    print("\n🎉 迁移完成！")
