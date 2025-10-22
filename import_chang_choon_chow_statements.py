#!/usr/bin/env python3
"""
批量导入Chang Choon Chow的Alliance Bank信用卡月结单
支持自动识别客户、创建信用卡、解析交易记录
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# 添加ingest目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'ingest'))
from statement_parser import parse_alliance_statement

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_or_create_customer(cursor, name):
    """获取或创建客户记录"""
    cursor.execute("SELECT id FROM customers WHERE name = ?", (name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # 创建新客户
    cursor.execute("""
        INSERT INTO customers (name, email, phone)
        VALUES (?, ?, ?)
    """, (name, f"{name.lower().replace(' ', '.')}@example.com", "0123456789"))
    
    return cursor.lastrowid

def get_or_create_credit_card(cursor, customer_id, bank_name, card_last4, card_type="Alliance Bank Credit Card"):
    """获取或创建信用卡记录"""
    cursor.execute("""
        SELECT id FROM credit_cards 
        WHERE customer_id = ? AND card_number_last4 = ? AND bank_name = ?
    """, (customer_id, card_last4, bank_name))
    
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # 创建新信用卡
    cursor.execute("""
        INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, card_type, credit_limit)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, bank_name, card_last4, card_type, 30000.00))
    
    return cursor.lastrowid

def parse_statement_date_from_filename(filename):
    """从文件名解析月结单日期"""
    # 文件名格式: 12:01:2025_xxx.pdf 或 12:09:2024_xxx.pdf
    # 提取 MM:DD:YYYY
    parts = filename.split('_')[0].split(':')
    if len(parts) == 3:
        month, day, year = parts
        # 返回格式: YYYY-MM-DD
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return None

def main():
    """主函数"""
    print("="*80)
    print("批量导入: Chang Choon Chow - Alliance Bank 信用卡月结单")
    print("="*80)
    
    # PDF文件目录 - 只处理12开头的文件（Chang Choon Chow的月结单）
    pdf_dir = Path("attached_assets")
    pdf_files = sorted(pdf_dir.glob("12*.pdf"))
    
    if not pdf_files:
        print("❌ 未找到PDF文件")
        return
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取或创建客户
        customer_name = "CHANG CHOON CHOW"
        customer_id = get_or_create_customer(cursor, customer_name)
        print(f"\n客户ID: {customer_id} ({customer_name})")
        
        # 信用卡映射（卡号后4位 -> 卡类型）
        card_mapping = {
            "6432": ("VISA PLATINUM", "Alliance Bank"),
            "4514": ("YOU:NIQUE MASTERCARD", "Alliance Bank"),
            "3836": ("BALANCE TRANSFER", "Alliance Bank")
        }
        
        # 统计
        total_statements = 0
        total_transactions = 0
        failed_files = []
        
        # 处理每个PDF文件
        for pdf_file in pdf_files:
            print(f"\n处理: {pdf_file.name}")
            
            try:
                # 解析月结单日期
                statement_date = parse_statement_date_from_filename(pdf_file.name)
                if not statement_date:
                    print(f"  ⚠️  无法解析月结单日期，跳过")
                    continue
                
                print(f"  月结单日期: {statement_date}")
                
                # 解析PDF - 直接使用Alliance Bank解析器
                statement_info, transactions = parse_alliance_statement(str(pdf_file))
                
                if not statement_info:
                    statement_info = {'total': 0, 'card_last4': None}
                
                if not transactions:
                    print(f"  ⚠️  未找到交易记录，跳过")
                    continue
                
                print(f"  ✅ 解析成功: {len(transactions)} 笔交易")
                
                # Alliance Bank账单通常包含多张卡的交易
                # 暂时将所有交易分配到YOU:NIQUE MASTERCARD (4514)
                # 未来可以根据交易描述进一步区分
                card_last4 = '4514'  # YOU:NIQUE MASTERCARD
                card_txns = transactions
                
                # 为主卡创建月结单
                for _ in [1]:  # 只循环一次
                    if card_last4 not in card_mapping:
                        continue
                    
                    card_type, bank_name = card_mapping[card_last4]
                    
                    # 获取或创建信用卡
                    card_id = get_or_create_credit_card(
                        cursor, customer_id, bank_name, card_last4, card_type
                    )
                    
                    # 检查是否已存在该月结单
                    cursor.execute("""
                        SELECT id FROM statements 
                        WHERE card_id = ? AND statement_date = ?
                    """, (card_id, statement_date))
                    
                    if cursor.fetchone():
                        print(f"  ⚠️  卡 {card_last4} 的月结单已存在，跳过")
                        continue
                    
                    # 插入月结单记录
                    statement_total = statement_info.get('total', 0)
                    cursor.execute("""
                        INSERT INTO statements 
                        (card_id, statement_date, statement_total, file_path, file_type, 
                         validation_score, is_confirmed)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        card_id,
                        statement_date,
                        statement_total,
                        str(pdf_file),
                        'pdf',
                        100.0,  # 批量导入默认验证通过
                        1       # 自动确认
                    ))
                    
                    statement_id = cursor.lastrowid
                    total_statements += 1
                    
                    # 插入交易记录
                    purchase_count = 0
                    payment_count = 0
                    
                    for txn in card_txns:
                        # 判断交易类型
                        amount = txn.get('amount', 0)
                        txn_type = 'payment' if amount < 0 else 'purchase'
                        
                        cursor.execute("""
                            INSERT INTO transactions 
                            (statement_id, transaction_date, description, amount, 
                             category, transaction_type)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            statement_id,
                            txn.get('date'),
                            txn.get('description', ''),
                            abs(amount),
                            txn.get('category', 'Others'),
                            txn_type
                        ))
                        
                        if txn_type == 'payment':
                            payment_count += 1
                        else:
                            purchase_count += 1
                        
                        total_transactions += 1
                    
                    print(f"  ✅ 导入成功 - 卡{card_last4}: {len(card_txns)} 笔交易")
                    print(f"     Purchase: {purchase_count} | Payment: {payment_count}")
                
            except Exception as e:
                print(f"  ❌ 解析失败: {str(e)}")
                failed_files.append(pdf_file.name)
                continue
        
        # 提交事务
        conn.commit()
        
        # 打印汇总
        print("\n" + "="*80)
        print("📊 导入汇总")
        print("="*80)
        print(f"月结单数量: {total_statements}")
        print(f"交易总数: {total_transactions}")
        
        if failed_files:
            print(f"\n失败文件 ({len(failed_files)}):")
            for f in failed_files:
                print(f"  - {f}")
        
        print("\n✅ 批量导入完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 导入失败: {str(e)}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
