#!/usr/bin/env python3
"""验证已导入的储蓄账户数据准确性"""

import sys
sys.path.insert(0, '.')

from db.database import get_db

def verify_balance_accuracy():
    """验证余额准确性 - 每笔交易都应该有余额"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 检查余额完整性
        cursor.execute('''
            SELECT 
                sa.bank_name,
                sa.account_number_last4,
                ss.statement_date,
                COUNT(st.id) as total_txns,
                SUM(CASE WHEN st.balance IS NOT NULL THEN 1 ELSE 0 END) as with_balance,
                SUM(CASE WHEN st.balance IS NULL THEN 1 ELSE 0 END) as without_balance
            FROM savings_accounts sa
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            GROUP BY sa.bank_name, sa.account_number_last4, ss.statement_date
            ORDER BY sa.bank_name, ss.statement_date
        ''')
        
        print("="*100)
        print("余额提取准确性验证")
        print("="*100)
        
        total_txns = 0
        total_with_balance = 0
        
        for row in cursor.fetchall():
            bank, acct, date, txns, with_bal, without_bal = row
            pct = (with_bal / txns * 100) if txns > 0 else 0
            status = "✅" if pct == 100 else "⚠️ "
            
            print(f"{status} {bank:20s} | {acct:5s} | {date:15s} | {txns:>3} 笔 | 余额: {with_bal:>3}/{txns:<3} ({pct:>5.1f}%)")
            
            total_txns += txns
            total_with_balance += with_bal
        
        overall_pct = (total_with_balance / total_txns * 100) if total_txns > 0 else 0
        print("\n" + "="*100)
        print(f"总计: {total_txns} 笔交易, {total_with_balance} 笔有余额 ({overall_pct:.1f}%)")
        print("="*100)

def verify_transaction_types():
    """验证交易类型分类"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                sa.bank_name,
                st.transaction_type,
                COUNT(*) as count,
                SUM(st.amount) as total_amount
            FROM savings_accounts sa
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            GROUP BY sa.bank_name, st.transaction_type
            ORDER BY sa.bank_name, st.transaction_type
        ''')
        
        print("\n交易类型分类统计")
        print("="*100)
        
        for row in cursor.fetchall():
            bank, txn_type, count, total = row
            print(f"{bank:20s} | {txn_type:10s} | {count:>4} 笔 | 总额: RM {total:>12,.2f}")
        
        print("="*100)

def show_sample_transactions():
    """显示样本交易数据"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                sa.bank_name,
                sa.account_number_last4,
                st.transaction_date,
                st.description,
                st.transaction_type,
                st.amount,
                st.balance
            FROM savings_accounts sa
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            ORDER BY st.transaction_date DESC
            LIMIT 10
        ''')
        
        print("\n最近10笔交易样本")
        print("="*100)
        
        for row in cursor.fetchall():
            bank, acct, date, desc, txn_type, amount, balance = row
            bal_str = f"RM {balance:>10,.2f}" if balance else "N/A"
            print(f"{bank:15s} | {acct:5s} | {date:12s} | {txn_type:6s} | RM {amount:>10,.2f} | 余额: {bal_str}")
            print(f"  {desc[:90]}")
        
        print("="*100)

def main():
    print("\n" + "="*100)
    print("储蓄账户数据验证报告 - YEO CHEE WANG")
    print("="*100 + "\n")
    
    verify_balance_accuracy()
    verify_transaction_types()
    show_sample_transactions()
    
    print("\n✅ 数据验证完成！\n")

if __name__ == '__main__':
    main()
