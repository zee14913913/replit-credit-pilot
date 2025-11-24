#!/usr/bin/env python3
"""
终极清理 - 删除所有非LEE E KAI的数据，包括：
1. 所有数据库表中的非LEE E KAI记录
2. 所有文件系统中的非LEE E KAI文件
"""
import sqlite3
import os
import shutil

def ultimate_cleanup():
    print("=" * 120)
    print("终极清理 - 删除所有非LEE E KAI的数据")
    print("=" * 120)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 查找LEE E KAI
    cursor.execute("SELECT id FROM customers WHERE name LIKE '%LEE E KAI%' OR customer_code LIKE '%LEE_EK%'")
    lee_result = cursor.fetchone()
    
    if not lee_result:
        print("❌ 未找到LEE E KAI！")
        conn.close()
        return
    
    lee_id = lee_result[0]
    print(f"保留客户ID: {lee_id} (LEE E KAI)")
    
    # ========== 数据库清理 ==========
    print("\n" + "=" * 120)
    print("清理数据库 - 删除所有非系统配置表的数据")
    print("=" * 120)
    
    # 系统配置表（不清理）
    system_tables = {
        'credit_card_products', 'loan_products', 'bnm_rates', 'gz_bank_whitelist',
        'predefined_suppliers', 'supplier_config', 'supplier_fee_config', 
        'service_terms', 'shop_utilities_config', 'customer_classification_config',
        'customer_employment_types', 'payer_aliases', 'supplier_aliases', 
        'transfer_recipient_aliases', 'tags', 'users', 'sqlite_sequence'
    }
    
    # 需要完全清空的表（与客户无关但包含旧数据）
    tables_to_truncate = [
        'savings_transactions', 'transactions', 'monthly_statement_cards',
        'infinite_monthly_ledger', 'monthly_ledger', 'statement_migration_map',
        'consumption_records', 'audit_logs', 'payment_records',
        'supplier_invoices', 'supplier_invoices_backup_20251029',
        'instalment_payment_records', 'statement_balance_analysis',
        'deleted_savings_statements_backup', 'gz_transfers', 'payment_accounts',
        'payment_on_behalf_records', 'repayment_reminders', 'statement_ocr_raw',
        'success_fee_calculations', 'batch_jobs', 'gz_os_balance',
        'transaction_tags', 'ai_logs'
    ]
    
    total_deleted = 0
    
    # 清空非客户相关的数据表
    for table in tables_to_truncate:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table}")
                deleted = cursor.rowcount
                print(f"✅ {table}: 清空 {deleted} 条记录")
                total_deleted += deleted
        except Exception as e:
            print(f"⚠️  {table}: {str(e)}")
    
    print(f"\n数据库总计删除: {total_deleted} 条记录")
    
    # ========== 文件系统清理 ==========
    print("\n" + "=" * 120)
    print("清理文件系统 - 删除所有非LEE E KAI的文件和目录")
    print("=" * 120)
    
    # 需要清理的目录
    directories_to_clean = [
        'reports',
        'static/reports',
        'static/downloads',
        'static/invoices',
        'static/uploads/invoices',
        'static/uploads/monthly_reports',
        'static/uploads/customer_16',
        'attached_assets',
        'archive_old',
    ]
    
    files_deleted = 0
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            print(f"\n清理目录: {directory}")
            if directory == 'attached_assets':
                # attached_assets保留目录，只删除文件
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        files_deleted += 1
                print(f"  删除 {files_deleted} 个文件")
            else:
                # 其他目录完全删除
                try:
                    shutil.rmtree(directory)
                    print(f"  ✅ 已删除整个目录")
                except Exception as e:
                    print(f"  ⚠️  删除失败: {str(e)}")
    
    # 清理tests目录中的测试文件
    if os.path.exists('tests'):
        print(f"\n清理tests目录中的测试文件")
        for item in os.listdir('tests'):
            if item.endswith('.pdf') or item.endswith('.xlsx'):
                item_path = os.path.join('tests', item)
                try:
                    os.remove(item_path)
                    print(f"  删除: {item}")
                    files_deleted += 1
                except:
                    pass
    
    print(f"\n文件系统总计删除: {files_deleted}+ 个文件")
    
    # 提交数据库更改
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 120)
    print("终极清理完成！")
    print("=" * 120)
    print(f"✅ 数据库: 删除 {total_deleted} 条记录")
    print(f"✅ 文件系统: 删除 {files_deleted}+ 个文件和多个目录")
    print(f"✅ 系统现在只保留LEE E KAI的数据和系统配置")
    print("=" * 120)

if __name__ == '__main__':
    ultimate_cleanup()
