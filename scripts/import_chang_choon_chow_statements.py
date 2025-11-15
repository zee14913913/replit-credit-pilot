"""
批量导入CHANG CHOON CHOW的银行流水（KENG CHOW ELECTRICAL SERVICE）
使用INFINITE GZ系统自动识别和分类AI SMART TECH转账
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
import pdfplumber
from datetime import datetime
import re
from services.infinite_gz_processor import InfiniteGZProcessor


def get_db():
    """获取数据库连接"""
    return sqlite3.connect('db/smart_loan_manager.db')


def extract_transactions_from_pdf(pdf_path):
    """从PDF提取交易记录"""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            
            lines = text.split('\n')
            
            for line in lines:
                if re.match(r'^\d{2}/\d{2}', line):
                    parts = line.split()
                    
                    if len(parts) >= 4:
                        date_str = parts[0]
                        description = ' '.join(parts[1:-2])
                        
                        try:
                            debit = float(parts[-2].replace(',', ''))
                        except:
                            debit = 0
                        
                        try:
                            credit = float(parts[-1].replace(',', ''))
                        except:
                            credit = 0
                        
                        if credit > 0:
                            trans_type = 'credit'
                            amount = credit
                        elif debit > 0:
                            trans_type = 'debit'
                            amount = debit
                        else:
                            continue
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'type': trans_type,
                            'amount': amount
                        })
    
    return transactions


def process_statement(pdf_path, customer_id, account_number, bank_name, statement_month):
    """处理一个月结单"""
    print(f"\n处理月结单: {statement_month}")
    print(f"PDF: {pdf_path}")
    print("-" * 80)
    
    transactions = extract_transactions_from_pdf(pdf_path)
    print(f"提取到 {len(transactions)} 笔交易")
    
    processor = InfiniteGZProcessor()
    gz_transfers_found = 0
    
    conn = get_db()
    cursor = conn.cursor()
    
    account_last4 = account_number[-4:]
    
    cursor.execute('''
        SELECT id FROM savings_accounts 
        WHERE customer_id = ? AND account_number_last4 = ?
    ''', (customer_id, account_last4))
    
    account = cursor.fetchone()
    
    if not account:
        print("❌ 储蓄账户不存在，正在创建...")
        cursor.execute('''
            INSERT INTO savings_accounts (
                customer_id, account_number_last4, bank_name, account_type, account_holder_name
            ) VALUES (?, ?, ?, 'Current Account-i', 'KENG CHOW ELECTRICAL SERVICE')
        ''', (customer_id, account_last4, bank_name))
        conn.commit()
        account_id = cursor.lastrowid
        print(f"✅ 创建账户 ID: {account_id}")
    else:
        account_id = account[0]
        print(f"✅ 找到账户 ID: {account_id}")
    
    cursor.execute('''
        INSERT INTO savings_statements (
            savings_account_id, statement_date, file_path, file_type, is_processed
        ) VALUES (?, ?, ?, 'PDF', 0)
    ''', (account_id, statement_month + '-01', pdf_path))
    
    statement_id = cursor.lastrowid
    conn.commit()
    print(f"✅ 创建账单记录 ID: {statement_id}")
    
    for trans in transactions:
        year = statement_month[:4]
        trans_date = f"{year}-{trans['date'].replace('/', '-')}"
        
        cursor.execute('''
            INSERT INTO savings_transactions (
                savings_statement_id, transaction_date, description, amount, transaction_type
            ) VALUES (?, ?, ?, ?, ?)
        ''', (statement_id, trans_date, trans['description'], trans['amount'], trans['type']))
        
        conn.commit()
        
        if trans['type'] == 'credit' and trans['amount'] > 0:
            result = processor.process_bank_transfer(
                customer_id=customer_id,
                transfer_date=trans_date,
                amount=trans['amount'],
                description=trans['description'],
                bank_name=bank_name
            )
            
            if result['is_gz_transfer']:
                gz_transfers_found += 1
                print(f"  ✅ GZ转账: {trans_date} | RM {trans['amount']:,.2f} | {result['transfer_purpose']}")
                print(f"     来源: {result['matched_account']['name']} ({result['matched_account']['bank']})")
    
    conn.close()
    
    print(f"\n📊 本月统计:")
    print(f"   总交易数: {len(transactions)}")
    print(f"   GZ转账数: {gz_transfers_found}")
    
    return gz_transfers_found


def main():
    """主函数"""
    customer_id = 10
    customer_name = "CHANG CHOON CHOW"
    account_number = "3984223427"
    bank_name = "Public Islamic Bank"
    
    pdf_files = [
        ('attached_assets/KC DEC 2024_1763186458174.pdf', '2024-12'),
        ('attached_assets/KC JAN 2025_1763186458175.pdf', '2025-01'),
        ('attached_assets/KC FEB 2025 _1763186458175.pdf', '2025-02'),
        ('attached_assets/KC MAR 2025_1763186458178.pdf', '2025-03'),
        ('attached_assets/KC APR 2025_1763186458172.pdf', '2025-04'),
        ('attached_assets/KC MAY 2025_1763186458178.pdf', '2025-05'),
        ('attached_assets/KC JUNE 2025_1763186458177.pdf', '2025-06'),
        ('attached_assets/KC JULY 2025_1763186458177.pdf', '2025-07'),
        ('attached_assets/KC AUG 2025_1763186458174.pdf', '2025-08'),
        ('attached_assets/KC SEPT 2024_1763186458179.pdf', '2024-09'),
        ('attached_assets/KC OCT  2024_1763186458179.pdf', '2024-10'),
        ('attached_assets/KC NOV 2024_1763186458179.pdf', '2024-11'),
    ]
    
    print("=" * 80)
    print(f"INFINITE GZ系统 - 批量导入{customer_name}银行流水")
    print(f"账户: KENG CHOW ELECTRICAL SERVICE ({account_number})")
    print("=" * 80)
    
    total_gz_transfers = 0
    
    for pdf_path, statement_month in pdf_files:
        if os.path.exists(pdf_path):
            gz_count = process_statement(
                pdf_path=pdf_path,
                customer_id=customer_id,
                account_number=account_number,
                bank_name=bank_name,
                statement_month=statement_month
            )
            total_gz_transfers += gz_count
        else:
            print(f"❌ 文件不存在: {pdf_path}")
    
    print("\n" + "=" * 80)
    print(f"🎉 批量导入完成！")
    print(f"   总GZ转账数: {total_gz_transfers}")
    print("=" * 80)
    
    processor = InfiniteGZProcessor()
    summary = processor.get_gz_os_balance_summary(customer_id)
    
    print(f"\n📊 GZ OS Balance汇总:")
    print(f"   Opening Balance: RM {summary['opening_balance']:,.2f}")
    print(f"   Total GZ Expenses: RM {summary['total_gz_expenses']:,.2f}")
    print(f"   Total GZ Payments: RM {summary['total_gz_payments']:,.2f}")
    print(f"   Closing Balance: RM {summary['closing_balance']:,.2f}")


if __name__ == '__main__':
    main()
