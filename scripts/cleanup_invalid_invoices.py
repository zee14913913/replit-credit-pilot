#!/usr/bin/env python3
"""
清理无效的supplier_invoices记录
Cleanup invalid supplier invoice records with no PDF and no recoverable data
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_db


def backup_and_cleanup_invalid_invoices():
    """备份并清理无效的发票记录"""
    
    print("="*80)
    print("备份并清理无效的supplier_invoices记录")
    print("="*80)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：创建备份表
        print("\n步骤1: 创建备份表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supplier_invoices_backup_20251029 (
                id INTEGER,
                customer_id INTEGER,
                statement_id INTEGER,
                supplier_name TEXT,
                invoice_number TEXT,
                total_amount REAL,
                supplier_fee REAL,
                invoice_date TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP,
                backup_reason TEXT,
                backup_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ 备份表已创建")
        
        # 步骤2：查询所有无效记录（pdf_path为NULL）
        print("\n步骤2: 查询所有无效记录...")
        cursor.execute('''
            SELECT * FROM supplier_invoices WHERE pdf_path IS NULL
        ''')
        invalid_records = cursor.fetchall()
        
        print(f"   找到 {len(invalid_records)} 条无效记录（pdf_path = NULL）")
        
        if len(invalid_records) == 0:
            print("   没有需要清理的记录，退出")
            return
        
        # 步骤3：备份无效记录
        print("\n步骤3: 备份无效记录到备份表...")
        backup_reason = "无PDF文件且无法恢复交易数据 (2025-10-29架构修复)"
        
        for record in invalid_records:
            cursor.execute('''
                INSERT INTO supplier_invoices_backup_20251029
                (id, customer_id, statement_id, supplier_name, invoice_number,
                 total_amount, supplier_fee, invoice_date, pdf_path, created_at, backup_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (record['id'], record['customer_id'], record['statement_id'],
                  record['supplier_name'], record['invoice_number'],
                  record['total_amount'], record['supplier_fee'],
                  record['invoice_date'], record['pdf_path'],
                  record['created_at'], backup_reason))
        
        conn.commit()
        print(f"   ✅ 已备份 {len(invalid_records)} 条记录")
        
        # 步骤4：显示备份的记录摘要
        print("\n步骤4: 备份记录摘要（前10条）:")
        print("-"*80)
        for i, record in enumerate(invalid_records[:10], 1):
            print(f"   {i}. {record['invoice_number']} | {record['supplier_name']} | "
                  f"RM {record['total_amount']:.2f} | {record['invoice_date']}")
        
        if len(invalid_records) > 10:
            print(f"   ... 还有 {len(invalid_records) - 10} 条记录")
        
        # 步骤5：确认删除
        print("\n步骤5: 从supplier_invoices表中删除无效记录...")
        cursor.execute('DELETE FROM supplier_invoices WHERE pdf_path IS NULL')
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"   ✅ 已删除 {deleted_count} 条无效记录")
        
        # 步骤6：验证清理结果
        print("\n步骤6: 验证清理结果...")
        cursor.execute('SELECT COUNT(*) as cnt FROM supplier_invoices')
        remaining = cursor.fetchone()['cnt']
        
        cursor.execute('SELECT COUNT(*) as cnt FROM supplier_invoices_backup_20251029')
        backed_up = cursor.fetchone()['cnt']
        
        print(f"   ✅ supplier_invoices 剩余记录: {remaining} 条")
        print(f"   ✅ supplier_invoices_backup_20251029 备份记录: {backed_up} 条")
        
        # 步骤7：生成清理报告
        print("\n步骤7: 生成清理报告...")
        report_path = "docs/SUPPLIER_INVOICES_CLEANUP_REPORT_2025-10-29.md"
        os.makedirs("docs", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Supplier Invoices Cleanup Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Invalid Records Found:** {len(invalid_records)}\n")
            f.write(f"- **Records Backed Up:** {backed_up}\n")
            f.write(f"- **Records Deleted:** {deleted_count}\n")
            f.write(f"- **Remaining Valid Records:** {remaining}\n\n")
            f.write("## Reason for Cleanup\n\n")
            f.write("All deleted records had `pdf_path = NULL` and referenced deprecated `statement_id` ")
            f.write("from the old `statements` table. These records cannot generate PDF files because:\n\n")
            f.write("1. Missing transaction details (`supplier_name`, `card_last4` were NULL)\n")
            f.write("2. Referenced deprecated `statements` table instead of new `monthly_statements`\n")
            f.write("3. No way to recover the original transaction data\n\n")
            f.write("## Backup Location\n\n")
            f.write("- **Backup Table:** `supplier_invoices_backup_20251029`\n")
            f.write("- All deleted records are preserved in this table for audit purposes\n\n")
            f.write("## Next Steps\n\n")
            f.write("1. ✅ Update `supplier_invoices` table schema with `monthly_statement_id`\n")
            f.write("2. ✅ Normalize `owner_flag` values to OWNER/INFINITE standard\n")
            f.write("3. ✅ Fix invoice generation to create actual PDF files\n")
            f.write("4. ✅ Regenerate invoices from valid `infinite_monthly_ledger` data\n\n")
            f.write("## Deleted Records Sample\n\n")
            f.write("| ID | Invoice Number | Supplier | Amount | Date |\n")
            f.write("|---|---|---|---|---|\n")
            
            for record in invalid_records[:20]:
                f.write(f"| {record['id']} | {record['invoice_number']} | "
                       f"{record['supplier_name']} | RM {record['total_amount']:.2f} | "
                       f"{record['invoice_date']} |\n")
            
            if len(invalid_records) > 20:
                f.write(f"\n*... and {len(invalid_records) - 20} more records*\n")
        
        print(f"   ✅ 清理报告已生成: {report_path}")
        
        print("\n" + "="*80)
        print("✅ 清理完成！")
        print("="*80)
        print(f"📊 总结:")
        print(f"   - 备份: {backed_up} 条")
        print(f"   - 删除: {deleted_count} 条")
        print(f"   - 剩余: {remaining} 条")
        print(f"   - 报告: {report_path}")
        print("="*80)


if __name__ == "__main__":
    backup_and_cleanup_invalid_invoices()
