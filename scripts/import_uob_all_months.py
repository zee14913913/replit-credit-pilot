#!/usr/bin/env python3
"""导入所有UOB月结单数据 - 100%准确验证"""

import sys
import os
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
from db.database import get_db

# UOB月结单文件（按月份顺序）
UOB_FILES = [
    'attached_assets/30-04-25_1760494366333.pdf',  # 2025年4月
    'attached_assets/31-05-25_1760494366334.pdf',  # 2025年5月
    'attached_assets/30-06-25_1760494366333.pdf',  # 2025年6月
    'attached_assets/31-07-25_1760494366334.pdf',  # 2025年7月
]

def import_uob_statement(file_path: str, customer_id: int = 7, account_id: int = 10):
    """导入单个UOB月结单并验证100%准确"""
    
    print(f'\n{"="*100}')
    print(f'处理文件: {file_path}')
    print(f'{"="*100}')
    
    # 解析PDF
    info, transactions = parse_savings_statement(file_path, bank_name='UOB')
    
    if not transactions:
        print(f'❌ 错误: 未提取到任何交易')
        return False
    
    # 验证数据准确性
    total_deposits = sum(t['amount'] for t in transactions if t['type'] == 'credit')
    total_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'debit')
    
    print(f'\n【解析结果】')
    print(f'  月结单日期: {info["statement_date"]}')
    print(f'  账号后4位: {info["account_last4"]}')
    print(f'  交易总数: {len(transactions)}笔')
    print(f'  总存款: RM {total_deposits:,.2f}')
    print(f'  总取款: RM {total_withdrawals:,.2f}')
    print(f'  最终余额: RM {transactions[-1].get("balance", 0):,.2f}')
    
    # 验证余额连续性
    print(f'\n【余额连续性验证】')
    prev_balance = 0
    # 提取期初余额
    for t in transactions:
        if t.get('balance'):
            if t['type'] == 'credit':
                prev_balance = t['balance'] - t['amount']
            else:
                prev_balance = t['balance'] + t['amount']
            break
    
    errors = 0
    for i, t in enumerate(transactions, 1):
        expected_balance = prev_balance + t['amount'] if t['type'] == 'credit' else prev_balance - t['amount']
        actual_balance = t.get('balance', 0)
        if abs(expected_balance - actual_balance) > 0.01:
            errors += 1
            if errors <= 3:
                print(f'  ❌ 第{i}笔余额错误: {t["date"]}, 预期={expected_balance:.2f}, 实际={actual_balance:.2f}')
        prev_balance = actual_balance
    
    if errors == 0:
        print(f'  ✅ 全部{len(transactions)}笔交易余额验证通过！')
    else:
        print(f'  ❌ {errors}笔交易存在余额错误，停止导入')
        return False
    
    # 写入数据库
    print(f'\n【写入数据库】')
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 插入月结单
        cursor.execute('''
            INSERT INTO savings_statements (
                savings_account_id, statement_date, file_path, file_type, 
                total_transactions, is_processed
            ) VALUES (?, ?, ?, 'PDF', ?, 1)
        ''', (account_id, info['statement_date'], file_path, len(transactions)))
        
        statement_id = cursor.lastrowid
        print(f'  ✅ 月结单ID: {statement_id}')
        
        # 插入所有交易
        for t in transactions:
            cursor.execute('''
                INSERT INTO savings_transactions (
                    savings_statement_id, transaction_date, description, 
                    amount, transaction_type, balance
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                statement_id,
                t['date'],
                t['description'],
                t['amount'],
                t['type'],
                t.get('balance', 0)
            ))
        
        conn.commit()
        print(f'  ✅ 已写入{len(transactions)}笔交易')
    
    print(f'\n✅✅✅ {info["statement_date"]} 导入成功，100%准确验证通过！')
    return True

def main():
    print('''
╔══════════════════════════════════════════════════════════════════════════╗
║        UOB ONE Account 全部月结单导入 - 100%准确验证系统                ║
╚══════════════════════════════════════════════════════════════════════════╝
    ''')
    
    success_count = 0
    failed_count = 0
    
    for file_path in UOB_FILES:
        if os.path.exists(file_path):
            if import_uob_statement(file_path):
                success_count += 1
            else:
                failed_count += 1
        else:
            print(f'\n❌ 文件不存在: {file_path}')
            failed_count += 1
    
    print(f'\n{"="*100}')
    print(f'【导入完成】')
    print(f'  ✅ 成功: {success_count}份月结单')
    print(f'  ❌ 失败: {failed_count}份月结单')
    print(f'{"="*100}')

if __name__ == '__main__':
    main()
