#!/usr/bin/env python3
"""
自动扫描并导入所有储蓄账户对账单
智能识别银行和账户，无需手动指定文件名
"""

import sys
import os
import glob
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
from db.database import get_db
from datetime import datetime
import pdfplumber

def detect_bank_type(file_path):
    """检测银行类型"""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text()
            
            if 'OCBC' in text:
                return 'OCBC'
            elif 'UOB' in text or 'ONE Account' in text:
                return 'UOB'
            elif 'Maybank Islamic' in text:
                return 'Maybank Islamic'
            elif 'Maybank' in text:
                return 'Maybank'
            elif 'Public Bank' in text:
                return 'Public Bank'
            elif 'Hong Leong' in text:
                return 'Hong Leong Bank'
            elif 'Alliance' in text:
                return 'Alliance Bank'
            elif 'CIMB' in text:
                return 'CIMB'
            elif 'GX Bank' in text or 'GXBank' in text:
                return 'GX Bank'
    except:
        pass
    
    return 'Unknown'

def get_or_create_customer(cursor, customer_name):
    """获取或创建客户"""
    cursor.execute("SELECT id FROM customers WHERE name = ?", (customer_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("""
        INSERT INTO customers (name, email, phone, monthly_income)
        VALUES (?, ?, ?, ?)
    """, (customer_name, f"{customer_name.lower().replace(' ', '.')}@example.com", '', 0))
    return cursor.lastrowid

def get_or_create_savings_account(cursor, customer_id, bank_name, account_last4, account_holder_name):
    """获取或创建储蓄账户"""
    cursor.execute("""
        SELECT id FROM savings_accounts
        WHERE customer_id = ? AND bank_name = ? AND account_number_last4 = ?
    """, (customer_id, bank_name, account_last4))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("""
        INSERT INTO savings_accounts (customer_id, bank_name, account_number_last4, account_type, account_holder_name)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, bank_name, account_last4, 'Savings', account_holder_name))
    return cursor.lastrowid

def get_or_create_savings_statement(cursor, account_id, statement_date, file_path, total_transactions):
    """获取或创建对账单记录"""
    cursor.execute("""
        SELECT id FROM savings_statements
        WHERE savings_account_id = ? AND statement_date = ?
    """, (account_id, statement_date))
    
    result = cursor.fetchone()
    if result:
        return result[0], True
    
    cursor.execute("""
        INSERT INTO savings_statements (savings_account_id, statement_date, file_path, file_type, total_transactions, is_processed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (account_id, statement_date, file_path, 'PDF', total_transactions, 1))
    return cursor.lastrowid, False

# 映射账户名称（从对账单提取到规范的客户名）
CUSTOMER_NAME_MAPPING = {
    'YEO CHEE WANG': 'YEO CHEE WANG',
    'TEO YOK CHU': 'TEO YOK CHU & YEO CHEE WANG',
    'TEO YOK CHU & YEO CHEE WANG': 'TEO YOK CHU & YEO CHEE WANG',
    'YCW': 'YEO CHEE WANG',
}

def extract_customer_name_from_statement(file_path, bank_name):
    """从对账单提取客户名"""
    import pdfplumber
    try:
        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text()
            
            # 不同银行的客户名提取逻辑
            if bank_name == 'OCBC':
                for line in text.split('\n'):
                    if 'Account Name' in line or 'Nama Akaun' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            name = parts[1].strip().split()[0:4]
                            name_str = ' '.join(name).strip()
                            return CUSTOMER_NAME_MAPPING.get(name_str, name_str)
            
            elif bank_name == 'UOB':
                # UOB默认为YEO CHEE WANG
                return 'YEO CHEE WANG'
            
            elif bank_name == 'Maybank Islamic':
                # Maybank默认为YEO CHEE WANG
                return 'YEO CHEE WANG'
    
    except:
        pass
    
    return 'YEO CHEE WANG'  # 默认客户

def main():
    print("=" * 100)
    print("自动扫描并导入所有储蓄账户对账单")
    print("=" * 100)
    
    # 扫描所有PDF文件
    pdf_files = glob.glob('attached_assets/*.pdf')
    print(f"\n找到 {len(pdf_files)} 个PDF文件\n")
    
    total_files = 0
    total_transactions = 0
    total_skipped = 0
    bank_stats = {}
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for file_path in sorted(pdf_files):
            try:
                # 检测银行类型
                bank_name = detect_bank_type(file_path)
                
                # 只处理储蓄账户（OCBC, UOB, Maybank Islamic）
                if bank_name not in ['OCBC', 'UOB', 'Maybank Islamic']:
                    continue
                
                # 解析对账单
                info, transactions = parse_savings_statement(file_path, bank_name=bank_name)
                
                if not info['account_last4'] or not info['statement_date']:
                    continue
                
                # 提取客户名
                customer_name = extract_customer_name_from_statement(file_path, bank_name)
                
                # 获取或创建客户
                customer_id = get_or_create_customer(cursor, customer_name)
                
                # 获取或创建储蓄账户
                account_id = get_or_create_savings_account(
                    cursor,
                    customer_id,
                    bank_name,
                    info['account_last4'],
                    customer_name
                )
                
                # 获取或创建对账单记录
                statement_id, already_exists = get_or_create_savings_statement(
                    cursor,
                    account_id,
                    info['statement_date'],
                    file_path,
                    len(transactions)
                )
                
                if already_exists:
                    total_skipped += len(transactions)
                    continue
                
                # 插入交易
                for txn in transactions:
                    cursor.execute("""
                        INSERT INTO savings_transactions (
                            savings_statement_id, transaction_date, description,
                            amount, transaction_type, balance
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        statement_id,
                        txn['date'],
                        txn['description'],
                        txn['amount'],
                        txn['type'],
                        txn.get('balance')
                    ))
                
                total_files += 1
                total_transactions += len(transactions)
                
                # 统计各银行数据
                if bank_name not in bank_stats:
                    bank_stats[bank_name] = {'files': 0, 'transactions': 0}
                bank_stats[bank_name]['files'] += 1
                bank_stats[bank_name]['transactions'] += len(transactions)
                
                balance_pct = sum(1 for t in transactions if t.get('balance') is not None) / len(transactions) * 100 if transactions else 0
                print(f"✅ {bank_name:20s} | {info['account_last4']:5s} | {info['statement_date']:15s} | {len(transactions):>3} 笔 | {balance_pct:>5.1f}% 余额 | {os.path.basename(file_path)}")
                
            except Exception as e:
                # 静默跳过非储蓄账户文件
                pass
        
        conn.commit()
    
    print(f"\n{'='*100}")
    print(f"✅ 导入完成！")
    print(f"   总计:")
    print(f"   • {total_files} 个对账单已处理")
    print(f"   • {total_transactions} 笔新交易已导入")
    print(f"   • {total_skipped} 笔交易已存在（跳过）")
    
    if bank_stats:
        print(f"\n   各银行统计:")
        for bank, stats in sorted(bank_stats.items()):
            print(f"   • {bank:20s}: {stats['files']:>2} 个对账单, {stats['transactions']:>4} 笔交易")
    
    print(f"{'='*100}")

if __name__ == '__main__':
    main()
