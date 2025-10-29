#!/usr/bin/env python3
"""
修复supplier_invoices表约束：将statement_id改为可NULL
Fix supplier_invoices table constraints: Make statement_id nullable
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_db


def fix_supplier_invoices_constraints():
    """修复supplier_invoices表约束"""
    
    print("="*80)
    print("修复supplier_invoices表约束")
    print("="*80)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：创建新表（statement_id可为NULL）
        print("\n步骤1: 创建新表结构（statement_id可NULL）...")
        cursor.execute('''
            CREATE TABLE supplier_invoices_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                statement_id INTEGER,
                monthly_statement_id INTEGER,
                supplier_name TEXT NOT NULL,
                invoice_number TEXT UNIQUE NOT NULL,
                total_amount REAL NOT NULL,
                supplier_fee REAL NOT NULL,
                invoice_date TEXT NOT NULL,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (monthly_statement_id) REFERENCES monthly_statements(id)
            )
        ''')
        print("   ✅ 新表已创建")
        
        # 步骤2：复制现有数据（如果有）
        print("\n步骤2: 复制现有数据...")
        cursor.execute('SELECT COUNT(*) as cnt FROM supplier_invoices')
        old_count = cursor.fetchone()['cnt']
        
        if old_count > 0:
            cursor.execute('''
                INSERT INTO supplier_invoices_new
                (id, customer_id, statement_id, monthly_statement_id, supplier_name,
                 invoice_number, total_amount, supplier_fee, invoice_date, pdf_path, created_at)
                SELECT 
                    id, customer_id, statement_id, monthly_statement_id, supplier_name,
                    invoice_number, total_amount, supplier_fee, invoice_date, pdf_path, created_at
                FROM supplier_invoices
            ''')
            print(f"   ✅ 已复制 {old_count} 条记录")
        else:
            print("   ℹ️  旧表为空，无需复制")
        
        # 步骤3: 删除旧表
        print("\n步骤3: 删除旧表...")
        cursor.execute('DROP TABLE supplier_invoices')
        print("   ✅ 旧表已删除")
        
        # 步骤4: 重命名新表
        print("\n步骤4: 重命名新表...")
        cursor.execute('ALTER TABLE supplier_invoices_new RENAME TO supplier_invoices')
        print("   ✅ 新表已重命名为supplier_invoices")
        
        conn.commit()
        
        # 步骤5: 验证新表结构
        print("\n步骤5: 验证新表结构...")
        cursor.execute("PRAGMA table_info(supplier_invoices)")
        columns = cursor.fetchall()
        
        print("   新表结构:")
        for col in columns:
            null_str = "NULL" if col['notnull'] == 0 else "NOT NULL"
            default_str = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] else ""
            print(f"      - {col['name']}: {col['type']} {null_str} {default_str}")
        
        # 验证statement_id是否可NULL
        statement_id_col = [c for c in columns if c['name'] == 'statement_id'][0]
        if statement_id_col['notnull'] == 0:
            print("\n   ✅ statement_id 已改为可NULL")
        else:
            print("\n   ❌ statement_id 仍然是NOT NULL")
        
        print("\n" + "="*80)
        print("✅ 约束修复完成！")
        print("="*80)
        print("📊 总结:")
        print("   - statement_id: 可NULL（遗留字段）")
        print("   - monthly_statement_id: 可NULL（新字段）")
        print("   - 已迁移记录: {old_count} 条".format(old_count=old_count))
        print("="*80)


if __name__ == "__main__":
    fix_supplier_invoices_constraints()
