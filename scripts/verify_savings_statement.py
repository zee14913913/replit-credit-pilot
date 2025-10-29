#!/usr/bin/env python3
"""
储蓄账户月结单双重人工验证工具
用途：将系统记录与PDF原件并排显示，逐行对比验证100%准确性
"""

import sys
import sqlite3
from typing import List, Dict

def verify_savings_statement(statement_id: int):
    """验证指定账单的所有交易记录"""
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            ss.id,
            ss.statement_date,
            ss.total_transactions,
            ss.file_path,
            ss.verification_status,
            sa.bank_name,
            sa.account_number_last4,
            sa.account_holder_name,
            c.name as customer_name
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE ss.id = ?
    ''', (statement_id,))
    
    stmt = cursor.fetchone()
    
    if not stmt:
        print(f"❌ 找不到账单ID: {statement_id}")
        conn.close()
        return False
    
    cursor.execute('''
        SELECT 
            id,
            transaction_date,
            description,
            amount,
            transaction_type,
            balance
        FROM savings_transactions
        WHERE savings_statement_id = ?
        ORDER BY id
    ''', (statement_id,))
    
    transactions = cursor.fetchall()
    
    print("=" * 120)
    print("🔍 储蓄账户月结单 - 双重人工验证系统")
    print("=" * 120)
    print()
    print(f"📋 账单信息：")
    print(f"   账单ID:        {stmt['id']}")
    print(f"   客户名称:      {stmt['customer_name']} ({stmt['account_holder_name']})")
    print(f"   银行账户:      {stmt['bank_name']} ****{stmt['account_number_last4']}")
    print(f"   账单日期:      {stmt['statement_date']}")
    print(f"   PDF路径:       {stmt['file_path']}")
    print(f"   验证状态:      {stmt['verification_status']}")
    print(f"   记录交易数:    {stmt['total_transactions']} 笔")
    print(f"   系统交易数:    {len(transactions)} 笔")
    print()
    
    if stmt['total_transactions'] != len(transactions):
        print(f"⚠️  警告：记录交易数与系统交易数不一致！")
        print()
    
    print("=" * 120)
    print("📊 交易记录详细对比表（请与PDF原件逐行核对）")
    print("=" * 120)
    print()
    print(f"{'序号':>4} | {'交易日期':12} | {'描述（Description）':60} | {'类型':4} | {'金额（Amount）':>12} | {'余额（Balance）':>12}")
    print("-" * 120)
    
    total_credit = 0
    total_debit = 0
    
    for i, txn in enumerate(transactions, 1):
        txn_type = txn['transaction_type']
        amount = txn['amount']
        balance = txn['balance'] if txn['balance'] else 0
        
        if txn_type == 'credit':
            total_credit += amount
        elif txn_type == 'debit':
            total_debit += amount
        
        type_label = 'CR' if txn_type == 'credit' else 'DR'
        
        print(f"{i:4d} | {txn['transaction_date']:12} | {txn['description'][:60]:60} | {type_label:4s} | RM {amount:>10,.2f} | RM {balance:>10,.2f}")
    
    print("=" * 120)
    print()
    print(f"💰 财务汇总：")
    print(f"   Total Credit (入账):  RM {total_credit:>12,.2f}")
    print(f"   Total Debit (出账):   RM {total_debit:>12,.2f}")
    print(f"   期末余额（最后一笔）:  RM {transactions[-1]['balance']:>12,.2f}")
    print()
    print("=" * 120)
    print()
    print("📝 人工验证步骤（必须完成）：")
    print()
    print("   第一遍验证：")
    print("   1. 打开PDF原件：static/uploads/" + stmt['file_path'])
    print("   2. 从第1笔交易开始，逐行对比：")
    print("      - 序号是否一致")
    print("      - 交易日期是否一致")
    print("      - 描述内容是否一致（100%准确，一字不差）")
    print("      - 金额是否一致")
    print("      - 类型（CR/DR）是否一致")
    print("      - 余额是否一致")
    print("   3. 在纸上记录：第1遍验证通过 ✓")
    print()
    print("   第二遍验证：")
    print("   4. 再次从第1笔交易开始，重新逐行对比一遍")
    print("   5. 特别注意描述是否有遗漏、多字、错字")
    print("   6. 在纸上记录：第2遍验证通过 ✓")
    print()
    print("   标记为已验证：")
    print(f"   7. 确认两遍验证都通过后，运行以下命令：")
    print(f"      python3 scripts/mark_statement_verified.py {statement_id}")
    print()
    print("=" * 120)
    print()
    
    conn.close()
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 scripts/verify_savings_statement.py <statement_id>")
        print()
        print("示例: python3 scripts/verify_savings_statement.py 207")
        sys.exit(1)
    
    statement_id = int(sys.argv[1])
    verify_savings_statement(statement_id)
