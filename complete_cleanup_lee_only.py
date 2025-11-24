#!/usr/bin/env python3
"""
彻底清理：删除除了LEE E KAI之外的所有数据
包括：customers、credit_cards、statements、transactions、savings、loans等所有表
以及所有文件系统中的数据
"""
import sqlite3
import os
import shutil

def complete_cleanup():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 查找LEE E KAI
    cursor.execute("SELECT id, name, customer_code FROM customers WHERE name LIKE '%LEE E KAI%' OR customer_code LIKE '%LEE_EK%'")
    lee_customer = cursor.fetchone()
    
    if not lee_customer:
        print("❌ 未找到LEE E KAI！停止清理")
        conn.close()
        return
    
    lee_id = lee_customer[0]
    print("=" * 120)
    print(f"保留客户: {lee_customer[1]} (ID: {lee_id}, 客户编号: {lee_customer[2]})")
    print("=" * 120)
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n数据库中的表: {len(all_tables)}个")
    
    # 定义需要清理的表及其customer关联字段
    tables_to_clean = {
        'statements': 'card_id IN (SELECT id FROM credit_cards WHERE customer_id != ?)',
        'transactions': 'card_id IN (SELECT id FROM credit_cards WHERE customer_id != ?)',
        'credit_cards': 'customer_id != ?',
        'savings_accounts': 'customer_id != ?',
        'savings_statements': 'account_id IN (SELECT id FROM savings_accounts WHERE customer_id != ?)',
        'savings_transactions': 'account_id IN (SELECT id FROM savings_accounts WHERE customer_id != ?)',
        'loans': 'customer_id != ?',
        'loan_evaluations': 'customer_id != ?',
        'monthly_statements': 'customer_id != ?',
        'monthly_statement_cards': 'monthly_statement_id IN (SELECT id FROM monthly_statements WHERE customer_id != ?)',
        'receipts': 'customer_id != ?',
        'payment_receipts': 'customer_id != ?',
        'payment_schedules': 'customer_id != ?',
        'card_payment_schedules': 'card_id IN (SELECT id FROM credit_cards WHERE customer_id != ?)',
        'financial_health_scores': 'customer_id != ?',
        'financial_anomalies': 'customer_id != ?',
        'financial_optimization_suggestions': 'customer_id != ?',
        'card_recommendations': 'customer_id != ?',
        'monthly_reports': 'customer_id != ?',
        'account_baselines': 'customer_id != ?',
        'customer_accounts': 'customer_id != ?',
        'user_customers': 'customer_id != ?',
        'customer_sessions': 'customer_id != ?',
        'customer_logins': 'customer_id != ?',
        'ctos_applications': 'customer_id != ?',
        'risk_consents': 'customer_id != ?',
    }
    
    total_deleted = 0
    
    print("\n" + "=" * 120)
    print("开始清理数据库...")
    print("=" * 120)
    
    for table, condition in tables_to_clean.items():
        if table in all_tables:
            try:
                # 先查询要删除的数量
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {condition}", (lee_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # 执行删除
                    cursor.execute(f"DELETE FROM {table} WHERE {condition}", (lee_id,))
                    deleted = cursor.rowcount
                    print(f"✅ {table}: 删除 {deleted} 条记录")
                    total_deleted += deleted
            except Exception as e:
                print(f"⚠️  {table}: {str(e)}")
    
    # 删除customers表中的其他客户
    cursor.execute("SELECT COUNT(*) FROM customers WHERE id != ?", (lee_id,))
    other_customers_count = cursor.fetchone()[0]
    
    if other_customers_count > 0:
        cursor.execute("DELETE FROM customers WHERE id != ?", (lee_id,))
        deleted = cursor.rowcount
        print(f"✅ customers: 删除 {deleted} 个其他客户")
        total_deleted += deleted
    
    print(f"\n总计删除: {total_deleted} 条记录")
    
    # 清理文件系统
    print("\n" + "=" * 120)
    print("清理文件系统...")
    print("=" * 120)
    
    # 清理static/uploads目录
    uploads_dirs = [
        'static/uploads/customers',
        'static/uploads/receipts',
        'static/uploads/loans',
        'static/uploads/savings',
    ]
    
    for upload_dir in uploads_dirs:
        if os.path.exists(upload_dir):
            # 删除所有内容
            for item in os.listdir(upload_dir):
                item_path = os.path.join(upload_dir, item)
                # 保留LEE相关的文件夹
                if 'LEE' in item.upper() or 'LEE_EK' in item:
                    print(f"✓  保留: {item_path}")
                    continue
                
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"🗑️  删除文件夹: {item_path}")
                else:
                    os.remove(item_path)
                    print(f"🗑️  删除文件: {item_path}")
    
    # 清理attached_assets（如果有）
    if os.path.exists('attached_assets'):
        print(f"\n扫描 attached_assets...")
        for item in os.listdir('attached_assets'):
            item_path = os.path.join('attached_assets', item)
            if 'LEE' in item.upper():
                print(f"✓  保留: {item_path}")
                continue
            
            if os.path.isfile(item_path) and item.endswith('.pdf'):
                os.remove(item_path)
                print(f"🗑️  删除: {item_path}")
    
    # 提交数据库更改
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 120)
    print("彻底清理完成！")
    print("=" * 120)
    print(f"✅ 数据库: 删除 {total_deleted} 条记录，仅保留LEE E KAI")
    print(f"✅ 文件系统: 已清理所有非LEE E KAI的文件")
    print("=" * 120)

if __name__ == '__main__':
    complete_cleanup()
