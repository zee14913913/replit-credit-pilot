#!/usr/bin/env python3
"""
数据清理脚本：
1. 只保留LEE E KAI客户的数据
2. 删除其他客户的statements记录
3. 识别并删除重复的PDF文件
4. 保留原始PDF文件
"""
import sqlite3
import os
import shutil
from datetime import datetime

def cleanup_keep_lee_only():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 1. 查找LEE E KAI客户ID
    cursor.execute("SELECT id, name, customer_code FROM customers WHERE name LIKE '%LEE E KAI%' OR customer_code LIKE '%LEE_EK%'")
    lee_customer = cursor.fetchone()
    
    if not lee_customer:
        print("❌ 未找到LEE E KAI客户！")
        conn.close()
        return
    
    lee_id, lee_name, lee_code = lee_customer
    print("=" * 120)
    print(f"找到LEE E KAI客户: ID={lee_id}, 姓名={lee_name}, 客户编号={lee_code}")
    print("=" * 120)
    
    # 2. 查找LEE E KAI的credit_cards
    cursor.execute("SELECT id, bank_name FROM credit_cards WHERE customer_id = ?", (lee_id,))
    lee_cards = cursor.fetchall()
    lee_card_ids = [card[0] for card in lee_cards]
    
    print(f"\nLEE E KAI的信用卡数量: {len(lee_cards)}")
    for card_id, bank_name in lee_cards:
        print(f"  - Card ID {card_id}: {bank_name}")
    
    # 3. 查找LEE E KAI的statements
    if lee_card_ids:
        placeholders = ','.join(['?' for _ in lee_card_ids])
        cursor.execute(f"SELECT id, file_path, statement_date, created_at FROM statements WHERE card_id IN ({placeholders})", lee_card_ids)
        lee_statements = cursor.fetchall()
        print(f"\nLEE E KAI的对账单数量: {len(lee_statements)}")
        for stmt_id, file_path, stmt_date, created_at in lee_statements:
            print(f"  - Statement ID {stmt_id}: {stmt_date}, 创建于 {created_at}")
    else:
        lee_statements = []
        print("\nLEE E KAI没有对账单记录")
    
    # 4. 统计要删除的其他客户数据
    cursor.execute("SELECT COUNT(*) FROM statements WHERE card_id NOT IN (SELECT id FROM credit_cards WHERE customer_id = ?)", (lee_id,))
    other_statements_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM credit_cards WHERE customer_id != ?", (lee_id,))
    other_cards_count = cursor.fetchone()[0]
    
    print(f"\n将要删除的记录:")
    print(f"  - 其他客户的对账单: {other_statements_count}条")
    print(f"  - 其他客户的信用卡: {other_cards_count}张")
    
    # 5. 确认删除（自动执行）
    print("\n" + "=" * 120)
    print("开始清理...")
    print("=" * 120)
    
    # 删除其他客户的statements
    cursor.execute("""
        DELETE FROM statements 
        WHERE card_id IN (
            SELECT id FROM credit_cards WHERE customer_id != ?
        )
    """, (lee_id,))
    deleted_statements = cursor.rowcount
    print(f"✅ 已删除 {deleted_statements} 条其他客户的对账单记录")
    
    # 删除其他客户的credit_cards
    cursor.execute("DELETE FROM credit_cards WHERE customer_id != ?", (lee_id,))
    deleted_cards = cursor.rowcount
    print(f"✅ 已删除 {deleted_cards} 张其他客户的信用卡记录")
    
    # 6. 识别并删除重复的PDF文件
    print("\n" + "=" * 120)
    print("扫描并清理重复的PDF文件...")
    print("=" * 120)
    
    # 获取所有客户目录
    customers_dir = 'static/uploads/customers'
    if os.path.exists(customers_dir):
        for customer_folder in os.listdir(customers_dir):
            customer_path = os.path.join(customers_dir, customer_folder)
            if os.path.isdir(customer_path):
                # 保留LEE E KAI的文件夹
                if customer_folder == lee_code or 'LEE' in customer_folder.upper():
                    print(f"✓  保留LEE E KAI的文件夹: {customer_folder}")
                    continue
                
                # 删除其他客户的文件夹
                try:
                    shutil.rmtree(customer_path)
                    print(f"🗑️  已删除客户文件夹: {customer_folder}")
                except Exception as e:
                    print(f"❌ 删除失败 {customer_folder}: {str(e)}")
    
    # 7. 识别LEE E KAI文件夹中的重复PDF
    lee_folder_candidates = [lee_code, f"LEE_EK_009", "LEE_E_KAI"]
    lee_folder = None
    for candidate in lee_folder_candidates:
        path = os.path.join(customers_dir, candidate)
        if os.path.exists(path):
            lee_folder = path
            break
    
    if lee_folder:
        print(f"\n扫描LEE E KAI文件夹: {lee_folder}")
        # 收集所有PDF文件
        pdf_files = {}
        for root, dirs, files in os.walk(lee_folder):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    
                    # 使用文件名作为key识别重复
                    if file in pdf_files:
                        # 发现重复文件
                        existing_path, existing_size = pdf_files[file]
                        if file_size == existing_size:
                            # 大小相同，删除当前文件（保留第一个）
                            os.remove(file_path)
                            print(f"🗑️  删除重复PDF: {file_path}")
                        else:
                            print(f"⚠️  发现同名但大小不同的文件: {file} ({file_size} vs {existing_size})")
                    else:
                        pdf_files[file] = (file_path, file_size)
        
        print(f"✅ LEE E KAI文件夹中保留 {len(pdf_files)} 个唯一PDF文件")
    else:
        print("⚠️  未找到LEE E KAI的文件夹")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 120)
    print("清理完成！")
    print("=" * 120)
    print(f"✅ 数据库已清理，仅保留LEE E KAI的 {len(lee_statements)} 条对账单记录")
    print(f"✅ 文件系统已清理，仅保留LEE E KAI的PDF文件")
    print("=" * 120)

if __name__ == '__main__':
    cleanup_keep_lee_only()
