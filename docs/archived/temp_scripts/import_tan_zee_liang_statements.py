#!/usr/bin/env python3
"""
Batch import Tan Zee Liang GX Bank statements (May 2024 - Sep 2025)
"""

import os
import sys
import sqlite3
from datetime import datetime
from ingest.savings_parser import parse_gxbank_savings

CUSTOMER_ID = 9
CUSTOMER_NAME = "Tan Zee Liang"
BANK_NAME = "GX Bank"
ACCOUNT_LAST4 = "8388"

PDF_FILES = [
    ("attached_assets/MAY 2024_1761108804252.pdf", "2024-05-31"),
    ("attached_assets/JUL 2024_1761108804252.pdf", "2024-07-31"),
    ("attached_assets/AUG 2024_1761108804251.pdf", "2024-08-31"),
    ("attached_assets/SEPT 2024_1761108804253.pdf", "2024-09-30"),
    ("attached_assets/OCT 2024_1761108804253.pdf", "2024-10-31"),
    ("attached_assets/NOV 2024_1761108804252.pdf", "2024-11-30"),
    ("attached_assets/DEC 2024_1761108804252.pdf", "2024-12-31"),
    ("attached_assets/JAN 2025_1761108804252.pdf", "2025-01-31"),
    ("attached_assets/FEB 2025_1761108804252.pdf", "2025-02-28"),
    ("attached_assets/MAR 2025_1761108804252.pdf", "2025-03-31"),
    ("attached_assets/APR 2025_1761108804251.pdf", "2025-04-30"),
    ("attached_assets/MAY 2025_1761108804252.pdf", "2025-05-31"),
    ("attached_assets/JULY 2025_1761108804252.pdf", "2025-07-31"),
    ("attached_assets/AUG 2025_1761108804251.pdf", "2025-08-31"),
    ("attached_assets/SEPT 2025_1761108804253.pdf", "2025-09-30"),
]

def get_or_create_savings_account(cursor, customer_id):
    cursor.execute("""
        SELECT id FROM savings_accounts 
        WHERE customer_id = ? AND bank_name = ? AND account_number_last4 = ?
    """, (customer_id, BANK_NAME, ACCOUNT_LAST4))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("""
        INSERT INTO savings_accounts (customer_id, bank_name, account_number_last4, created_at)
        VALUES (?, ?, ?, datetime('now'))
    """, (customer_id, BANK_NAME, ACCOUNT_LAST4))
    return cursor.lastrowid

def main():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    print("="*80)
    print(f"批量导入: {CUSTOMER_NAME} - {BANK_NAME} 储蓄账户月结单")
    print("="*80)
    
    account_id = get_or_create_savings_account(cursor, CUSTOMER_ID)
    print(f"\n储蓄账户ID: {account_id}")
    print(f"账户号码: {BANK_NAME} - {ACCOUNT_LAST4}\n")
    
    total_statements = 0
    total_transactions = 0
    total_credit = 0
    total_debit = 0
    
    for pdf_path, statement_date in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"⚠️  文件不存在: {pdf_path}")
            continue
        
        print(f"\n处理: {os.path.basename(pdf_path)}")
        print(f"月结单日期: {statement_date}")
        
        cursor.execute("""
            SELECT id FROM savings_statements 
            WHERE savings_account_id = ? AND statement_date = ?
        """, (account_id, statement_date))
        
        if cursor.fetchone():
            print(f"  ⚠️  该月结单已存在，跳过...")
            continue
        
        try:
            metadata, transactions = parse_gxbank_savings(pdf_path)
            result = {'transactions': transactions}
            
            cursor.execute("""
                INSERT INTO savings_statements 
                (savings_account_id, statement_date, file_path, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (account_id, statement_date, pdf_path))
            statement_id = cursor.lastrowid
            
            credit_count = 0
            debit_count = 0
            
            for txn in result['transactions']:
                cursor.execute("""
                    INSERT INTO savings_transactions 
                    (savings_statement_id, transaction_date, description, amount, transaction_type, 
                     customer_name_tag, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    statement_id,
                    txn['date'],
                    txn['description'],
                    txn['amount'],
                    txn['type'],
                    txn.get('counterparty')
                ))
                
                if txn['type'] == 'CREDIT':
                    credit_count += 1
                else:
                    debit_count += 1
            
            conn.commit()
            
            total_statements += 1
            total_transactions += len(result['transactions'])
            total_credit += credit_count
            total_debit += debit_count
            
            print(f"  ✅ 导入成功: {len(result['transactions'])} 笔交易")
            print(f"     Credit: {credit_count} | Debit: {debit_count}")
            
        except Exception as e:
            print(f"  ❌ 解析失败: {str(e)}")
            conn.rollback()
    
    conn.close()
    
    print("\n" + "="*80)
    print("📊 导入汇总")
    print("="*80)
    print(f"月结单数量: {total_statements}")
    print(f"交易总数: {total_transactions}")
    print(f"  - Credit (入账): {total_credit}")
    print(f"  - Debit (支出): {total_debit}")
    print("="*80)
    print("✅ 批量导入完成！")

if __name__ == '__main__':
    main()
