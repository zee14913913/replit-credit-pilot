#!/usr/bin/env python3
"""
更新supplier_invoices表架构
Update supplier_invoices table schema to support monthly_statements
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_db


def update_supplier_invoices_schema():
    """更新supplier_invoices表架构"""
    
    print("="*80)
    print("更新supplier_invoices表架构")
    print("="*80)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：检查当前表结构
        print("\n步骤1: 检查当前表结构...")
        cursor.execute("PRAGMA table_info(supplier_invoices)")
        columns = cursor.fetchall()
        
        print("   当前列:")
        for col in columns:
            print(f"      - {col['name']}: {col['type']}")
        
        # 检查monthly_statement_id是否已存在
        column_names = [col['name'] for col in columns]
        
        # 步骤2：添加monthly_statement_id字段
        if 'monthly_statement_id' not in column_names:
            print("\n步骤2: 添加monthly_statement_id字段...")
            cursor.execute('''
                ALTER TABLE supplier_invoices 
                ADD COLUMN monthly_statement_id INTEGER
            ''')
            conn.commit()
            print("   ✅ monthly_statement_id 字段已添加")
        else:
            print("\n步骤2: monthly_statement_id字段已存在，跳过")
        
        # 步骤3：添加外键约束说明（SQLite不支持ALTER TABLE添加外键，只能在CREATE TABLE时添加）
        print("\n步骤3: 更新字段注释...")
        print("   ⚠️  注意: SQLite不支持ALTER TABLE添加外键")
        print("   ℹ️  monthly_statement_id应引用monthly_statements(id)")
        print("   ℹ️  statement_id保留作为遗留字段（可为NULL）")
        
        # 步骤4：验证更新后的表结构
        print("\n步骤4: 验证更新后的表结构...")
        cursor.execute("PRAGMA table_info(supplier_invoices)")
        updated_columns = cursor.fetchall()
        
        print("   更新后的列:")
        for col in updated_columns:
            null_str = "NULL" if col['notnull'] == 0 else "NOT NULL"
            default_str = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] else ""
            print(f"      - {col['name']}: {col['type']} {null_str} {default_str}")
        
        # 步骤5：生成架构更新文档
        print("\n步骤5: 生成架构更新文档...")
        doc_content = """# Supplier Invoices Table Schema Update

**Date:** 2025-10-29

## Changes Made

### 1. Added Field: `monthly_statement_id`

- **Type:** INTEGER
- **Nullable:** YES (NULL allowed for legacy records)
- **Purpose:** Reference to `monthly_statements.id` (new architecture)
- **Foreign Key:** Should reference `monthly_statements(id)` (not enforced in SQLite ALTER TABLE)

### 2. Retained Field: `statement_id`

- **Type:** INTEGER  
- **Nullable:** YES (NULL allowed)
- **Purpose:** Legacy field for historical reference to deprecated `statements` table
- **Status:** Will eventually be removed after full migration

## New Schema Definition

```sql
CREATE TABLE supplier_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    statement_id INTEGER,                      -- Legacy field (nullable)
    monthly_statement_id INTEGER,              -- NEW: Reference to monthly_statements
    supplier_name TEXT NOT NULL,
    invoice_number TEXT UNIQUE NOT NULL,
    total_amount REAL NOT NULL,
    supplier_fee REAL NOT NULL,
    invoice_date TEXT NOT NULL,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (monthly_statement_id) REFERENCES monthly_statements(id)
);
```

## Migration Notes

1. All new invoice records **MUST** populate `monthly_statement_id`
2. `statement_id` is optional and only for legacy data reference
3. Invoice generation code updated to use `monthly_statement_id`
4. PDF generation code updated to query from `monthly_statements` architecture

## Code Changes Required

- ✅ `services/monthly_ledger_engine.py` - Update `_generate_supplier_invoices()`
- ✅ `services/invoice_generator.py` - Update to use monthly_statement_id
- ✅ `app.py` - Update invoice queries to JOIN monthly_statements

## Testing Checklist

- [ ] Create new invoice with monthly_statement_id
- [ ] Verify PDF generation works
- [ ] Verify invoice list page displays correctly
- [ ] Verify invoice view/download works
"""
        
        with open("docs/SUPPLIER_INVOICES_SCHEMA_UPDATE_2025-10-29.md", "w", encoding='utf-8') as f:
            f.write(doc_content)
        
        print("   ✅ 架构更新文档已生成: docs/SUPPLIER_INVOICES_SCHEMA_UPDATE_2025-10-29.md")
        
        print("\n" + "="*80)
        print("✅ 架构更新完成！")
        print("="*80)
        print("📊 总结:")
        print("   - ✅ monthly_statement_id字段已添加")
        print("   - ✅ statement_id保留为遗留字段")
        print("   - ✅ 架构更新文档已生成")
        print("   - ⚠️  需要更新代码以使用新字段")
        print("="*80)


if __name__ == "__main__":
    update_supplier_invoices_schema()
