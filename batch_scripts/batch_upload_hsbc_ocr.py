#!/usr/bin/env python3
"""
HSBC OCR批量上传工具 - 处理扫描PDF账单
"""
import sys
import os
import glob
sys.path.insert(0, '.')

from parsers.hsbc_ocr_parser import HSBCOCRParser
import sqlite3
from datetime import datetime
import re

def batch_upload_hsbc_statements():
    """批量上传HSBC账单"""
    
    # 获取所有HSBC PDF文件
    pdf_files = sorted(glob.glob("attached_assets/*Statement*.pdf"))
    
    print("="*80)
    print(f" HSBC OCR批量处理 - 共 {len(pdf_files)} 个账单")
    print("="*80)
    
    parser = HSBCOCRParser()
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 获取HSBC卡ID
    cursor.execute("""
        SELECT c.id, cu.name 
        FROM credit_cards c
        JOIN customers cu ON c.customer_id = cu.id
        WHERE c.bank_name = 'HSBC' AND cu.name = 'Chang Choon Chow'
    """)
    card_info = cursor.fetchone()
    
    if not card_info:
        print("❌ 未找到Chang Choon Chow的HSBC信用卡")
        conn.close()
        return
    
    card_id = card_info[0]
    customer_name = card_info[1]
    
    print(f"\n客户: {customer_name}")
    print(f"卡片ID: {card_id}")
    print(f"\n开始OCR处理...\n")
    
    total_statements = 0
    total_transactions = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"[{i}/{len(pdf_files)}] 处理: {filename}")
        
        try:
            # OCR解析
            print(f"    🔄 OCR识别中...")
            result = parser.parse_statement(pdf_path)
            
            if not result['statement_date']:
                print(f"    ⚠️  无法识别账单日期，跳过")
                continue
            
            stmt_date = result['statement_date']
            stmt_total = result['statement_total']
            transactions = result['transactions']
            
            print(f"    ✅ 识别成功: {stmt_date} | 交易 {len(transactions)} 笔 | 总额 RM {stmt_total:,.2f}")
            
            # 检查账单是否已存在
            cursor.execute("""
                SELECT id FROM statements 
                WHERE card_id = ? AND statement_date = ?
            """, (card_id, stmt_date))
            
            existing = cursor.fetchone()
            
            if existing:
                print(f"    ℹ️  账单已存在，跳过")
                continue
            
            # 插入账单
            cursor.execute("""
                INSERT INTO statements (card_id, statement_date, due_date, statement_total)
                VALUES (?, ?, ?, ?)
            """, (card_id, stmt_date, stmt_date, stmt_total))
            
            statement_id = cursor.lastrowid
            
            # 插入交易
            for txn in transactions:
                # 构建完整日期
                txn_date = txn['date']
                # 从账单日期获取年份
                stmt_year = stmt_date[:4]
                
                # 转换日期格式 "15 May" -> "2025-05-15"
                try:
                    txn_datetime = datetime.strptime(f"{txn_date} {stmt_year}", '%d %b %Y')
                    full_date = txn_datetime.strftime('%Y-%m-%d')
                except:
                    full_date = stmt_date
                
                cursor.execute("""
                    INSERT INTO transactions (statement_id, transaction_date, description, amount, transaction_type, category)
                    VALUES (?, ?, ?, ?, ?, 'Uncategorized')
                """, (statement_id, full_date, txn['description'], txn['amount'], txn['type']))
            
            conn.commit()
            total_statements += 1
            total_transactions += len(transactions)
            print(f"    💾 已保存账单 (ID: {statement_id})")
            
        except Exception as e:
            print(f"    ❌ 处理失败: {e}")
            continue
    
    conn.close()
    
    print(f"\n{'='*80}")
    print(f" 批量上传完成")
    print(f"{'='*80}")
    print(f"  成功上传: {total_statements} 个账单")
    print(f"  交易总数: {total_transactions} 笔")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    batch_upload_hsbc_statements()
