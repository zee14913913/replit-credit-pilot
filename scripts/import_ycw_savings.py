#!/usr/bin/env python3
"""
导入YEO CHEE WANG所有储蓄账户数据到数据库
包含4个账户：2个OCBC，1个UOB，1个Maybank Islamic
"""

import sys
import os
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
from db.database import get_db
from datetime import datetime
import hashlib

# YEO CHEE WANG的所有账户文件
ACCOUNTS = {
    'OCBC_712-261484-1': {
        'bank': 'OCBC',
        'account_name': 'YEO CHEE WANG',
        'files': [
            'attached_assets/712-261484-1 Jan 24.pdf',
            'attached_assets/712-261484-1 Feb 24.pdf',
            'attached_assets/712-261484-1 Mar 24.pdf',
            'attached_assets/712-261484-1 Apr 24.pdf',
            'attached_assets/712-261484-1 May 24.pdf',
            'attached_assets/712-261484-1 Jun 24.pdf',
            'attached_assets/712-261484-1 Jul 24.pdf',
            'attached_assets/712-261484-1 Aug 24.pdf',
            'attached_assets/712-261484-1 Sep 24.pdf',
            'attached_assets/712-261484-1 Oct 24.pdf',
            'attached_assets/712-261484-1 Nov 24.pdf',
            'attached_assets/712-261484-1 Dec 24.pdf',
            'attached_assets/712-261484-1 Jan 25.pdf',
            'attached_assets/712-261484-1 Feb 25.pdf',
            'attached_assets/712-261484-1 Mar 25.pdf',
            'attached_assets/712-261484-1 Apr 25.pdf',
            'attached_assets/712-261484-1 May 25.pdf',
            'attached_assets/712-261484-1 Jun 25.pdf',
            'attached_assets/712-261484-1 Jul 25.pdf',
        ]
    },
    'OCBC_712-261489-2': {
        'bank': 'OCBC',
        'account_name': 'TEO YOK CHU & YEO CHEE WANG',
        'files': [
            'attached_assets/712-261489-2 Jul 22.pdf',
            'attached_assets/712-261489-2 Aug 22.pdf',
            'attached_assets/712-261489-2 Sep 22.pdf',
            'attached_assets/712-261489-2 Oct 22.pdf',
            'attached_assets/712-261489-2 Nov 22.pdf',
            'attached_assets/712-261489-2 Dec 22.pdf',
            'attached_assets/712-261489-2 Jan 23.pdf',
            'attached_assets/712-261489-2 Feb 23.pdf',
            'attached_assets/712-261489-2 Mar 23.pdf',
            'attached_assets/712-261489-2 Apr 23.pdf',
            'attached_assets/712-261489-2 May 23.pdf',
            'attached_assets/712-261489-2 Jun 23.pdf',
            'attached_assets/712-261489-2 Jul 23.pdf',
            'attached_assets/712-261489-2 Aug 23.pdf',
            'attached_assets/712-261489-2 Sep 23.pdf',
            'attached_assets/712-261489-2 Oct 23.pdf',
            'attached_assets/712-261489-2 Nov 23.pdf',
            'attached_assets/712-261489-2 Dec 23.pdf',
            'attached_assets/712-261489-2 Jan 24.pdf',
            'attached_assets/712-261489-2 Feb 24.pdf',
            'attached_assets/712-261489-2 Mar 24.pdf',
            'attached_assets/712-261489-2 Apr 24.pdf',
            'attached_assets/712-261489-2 May 24.pdf',
            'attached_assets/712-261489-2 Jun 24.pdf',
            'attached_assets/712-261489-2 Jul 24.pdf',
            'attached_assets/712-261489-2 Aug 24.pdf',
            'attached_assets/712-261489-2 Sep 24.pdf',
            'attached_assets/712-261489-2 Oct 24.pdf',
            'attached_assets/712-261489-2 Nov 24.pdf',
            'attached_assets/712-261489-2 Dec 24.pdf',
            'attached_assets/712-261489-2 Jan 25.pdf',
            'attached_assets/712-261489-2 Feb 25.pdf',
            'attached_assets/712-261489-2 Jul 25.pdf',
        ]
    },
    'UOB_914-316-184-2': {
        'bank': 'UOB',
        'account_name': 'YEO CHEE WANG',
        'files': [
            'attached_assets/31-12-24_1760494388344.pdf',
            'attached_assets/31-01-25_1760494366333.pdf',
            'attached_assets/28-02-25_1760494366331.pdf',
            'attached_assets/31-03-25_1760494366333.pdf',
            'attached_assets/30-04-25_1760494366333.pdf',
            'attached_assets/31-05-25_1760494366334.pdf',
            'attached_assets/30-06-25_1760494366333.pdf',
            'attached_assets/31-07-25_1760494366334.pdf',
        ]
    },
    'Maybank_3470': {
        'bank': 'Maybank Islamic',
        'account_name': 'YEO CHEE WANG',
        'files': [
            'attached_assets/Maybank Islamic 3470 Feb 24.pdf',
            'attached_assets/Maybank Islamic 3470 Mar 24.pdf',
            'attached_assets/Maybank Islamic 3470 Apr 24.pdf',
            'attached_assets/Maybank Islamic 3470 May 24.pdf',
            'attached_assets/Maybank Islamic 3470 Jun 24.pdf',
            'attached_assets/Maybank Islamic 3470 Jul 24.pdf',
            'attached_assets/Maybank Islamic 3470 Aug 24.pdf',
            'attached_assets/Maybank Islamic 3470 Sep 24.pdf',
            'attached_assets/Maybank Islamic 3470 Oct 24.pdf',
            'attached_assets/Maybank Islamic 3470 Nov 24.pdf',
            'attached_assets/Maybank Islamic 3470 Dec 24.pdf',
            'attached_assets/Maybank Islamic 3470 Jan 25.pdf',
            'attached_assets/Maybank Islamic 3470 Feb 25.pdf',
            'attached_assets/Maybank Islamic 3470 Mar 25.pdf',
            'attached_assets/Maybank Islamic 3470 Apr 25.pdf',
            'attached_assets/Maybank Islamic 3470 May 25.pdf',
            'attached_assets/Maybank Islamic 3470 Jun 25.pdf',
            'attached_assets/Maybank Islamic 3470 Jul 25.pdf',
        ]
    }
}

def get_or_create_customer(cursor, customer_name):
    """获取或创建客户"""
    # 查找客户
    cursor.execute("""
        SELECT id FROM customers 
        WHERE name = ?
    """, (customer_name,))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # 创建新客户
    cursor.execute("""
        INSERT INTO customers (name, email, phone, monthly_income)
        VALUES (?, ?, ?, ?)
    """, (customer_name, f"{customer_name.lower().replace(' ', '.')}@example.com", '', 0))
    
    return cursor.lastrowid

def get_or_create_savings_account(cursor, customer_id, bank_name, account_last4, account_holder_name):
    """获取或创建储蓄账户"""
    # 查找账户
    cursor.execute("""
        SELECT id FROM savings_accounts
        WHERE customer_id = ? AND bank_name = ? AND account_number_last4 = ?
    """, (customer_id, bank_name, account_last4))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # 创建新账户
    cursor.execute("""
        INSERT INTO savings_accounts (customer_id, bank_name, account_number_last4, account_type, account_holder_name)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, bank_name, account_last4, 'Savings', account_holder_name))
    
    return cursor.lastrowid

def get_or_create_savings_statement(cursor, account_id, statement_date, file_path, total_transactions):
    """获取或创建对账单记录"""
    # 查找对账单
    cursor.execute("""
        SELECT id FROM savings_statements
        WHERE savings_account_id = ? AND statement_date = ?
    """, (account_id, statement_date))
    
    result = cursor.fetchone()
    if result:
        return result[0], True  # 返回ID和是否已存在标志
    
    # 创建新对账单
    cursor.execute("""
        INSERT INTO savings_statements (savings_account_id, statement_date, file_path, file_type, total_transactions, is_processed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (account_id, statement_date, file_path, 'PDF', total_transactions, 1))
    
    return cursor.lastrowid, False  # 返回ID和是否已存在标志

def main():
    print("=" * 100)
    print("导入YEO CHEE WANG家族所有储蓄账户数据")
    print("=" * 100)
    
    total_files = 0
    total_transactions = 0
    total_skipped = 0
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for account_key, account_data in ACCOUNTS.items():
            bank_name = account_data['bank']
            account_name = account_data['account_name']
            files = account_data['files']
            
            print(f"\n{'='*100}")
            print(f"📁 账户: {account_key}")
            print(f"   银行: {bank_name}")
            print(f"   户名: {account_name}")
            print(f"   文件数: {len(files)}")
            print(f"{'='*100}\n")
            
            # 获取或创建客户
            customer_id = get_or_create_customer(cursor, account_name)
            
            for file_path in files:
                if not os.path.exists(file_path):
                    print(f"❌ 文件不存在: {file_path}")
                    continue
                
                try:
                    # 解析对账单
                    info, transactions = parse_savings_statement(file_path, bank_name=bank_name)
                    
                    if not info['account_last4']:
                        print(f"⚠️  无法提取账号: {file_path}")
                        continue
                    
                    # 获取或创建储蓄账户
                    account_id = get_or_create_savings_account(
                        cursor, 
                        customer_id, 
                        bank_name, 
                        info['account_last4'],
                        account_name
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
                        print(f"⏭️  已存在: {os.path.basename(file_path)} ({info['statement_date']}) - 跳过")
                        total_skipped += len(transactions)
                        continue
                    
                    # 插入交易
                    inserted = 0
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
                        inserted += 1
                    
                    total_files += 1
                    total_transactions += inserted
                    
                    balance_info = f"{sum(1 for t in transactions if t.get('balance') is not None)}/{len(transactions)}"
                    print(f"✅ {os.path.basename(file_path):<50} | {info['statement_date']:<15} | {inserted:>3} 笔交易 | 余额: {balance_info}")
                    
                except Exception as e:
                    print(f"❌ 错误: {file_path} - {e}")
                    import traceback
                    traceback.print_exc()
        
        conn.commit()
    
    print(f"\n{'='*100}")
    print(f"✅ 导入完成！")
    print(f"   • {total_files} 个对账单已处理")
    print(f"   • {total_transactions} 笔新交易已导入")
    print(f"   • {total_skipped} 笔交易已存在（跳过）")
    print(f"{'='*100}")

if __name__ == '__main__':
    main()
