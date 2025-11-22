#!/usr/bin/env python3
"""生成储蓄账户财务报告"""

import sys
sys.path.insert(0, '.')

from db.database import get_db
from datetime import datetime
from collections import defaultdict

def generate_monthly_summary():
    """按月汇总财务数据"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.name as customer_name,
                sa.bank_name,
                sa.account_number_last4,
                strftime('%Y-%m', st.transaction_date) as month,
                st.transaction_type,
                COUNT(*) as txn_count,
                SUM(st.amount) as total_amount,
                MIN(st.balance) as min_balance,
                MAX(st.balance) as max_balance
            FROM customers c
            JOIN savings_accounts sa ON sa.customer_id = c.id
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            WHERE st.balance IS NOT NULL
            GROUP BY c.name, sa.bank_name, sa.account_number_last4, month, st.transaction_type
            ORDER BY month, sa.bank_name
        ''')
        
        print("="*120)
        print("YEO CHEE WANG - 储蓄账户月度财务报告")
        print("="*120)
        
        monthly_data = defaultdict(lambda: {'credit': 0, 'debit': 0, 'credit_count': 0, 'debit_count': 0, 'min_bal': None, 'max_bal': None})
        
        for row in cursor.fetchall():
            customer, bank, acct, month, txn_type, count, amount, min_bal, max_bal = row
            
            key = f"{month}_{bank}_{acct}"
            
            if txn_type == 'credit':
                monthly_data[key]['credit'] = amount
                monthly_data[key]['credit_count'] = count
            else:
                monthly_data[key]['debit'] = amount
                monthly_data[key]['debit_count'] = count
            
            monthly_data[key]['month'] = month
            monthly_data[key]['bank'] = bank
            monthly_data[key]['acct'] = acct
            monthly_data[key]['customer'] = customer
            
            if monthly_data[key]['min_bal'] is None:
                monthly_data[key]['min_bal'] = min_bal
                monthly_data[key]['max_bal'] = max_bal
            else:
                monthly_data[key]['min_bal'] = min(monthly_data[key]['min_bal'], min_bal) if min_bal else monthly_data[key]['min_bal']
                monthly_data[key]['max_bal'] = max(monthly_data[key]['max_bal'], max_bal) if max_bal else monthly_data[key]['max_bal']
        
        print(f"\n{'月份':^12} | {'银行':^20} | {'账号':^6} | {'存款':^15} | {'支出':^15} | {'净流量':^15} | {'最低余额':^15} | {'最高余额':^15}")
        print("-"*120)
        
        total_credit = 0
        total_debit = 0
        
        for key in sorted(monthly_data.keys()):
            data = monthly_data[key]
            net_flow = data['credit'] - data['debit']
            net_symbol = "↑" if net_flow > 0 else "↓"
            
            min_bal = data.get('min_bal') or 0
            max_bal = data.get('max_bal') or 0
            
            print(f"{data.get('month', 'N/A'):^12} | {data.get('bank', 'N/A'):^20} | {data.get('acct', 'N/A'):^6} | "
                  f"RM {data.get('credit', 0):>11,.2f} | RM {data.get('debit', 0):>11,.2f} | "
                  f"{net_symbol} RM {abs(net_flow):>9,.2f} | "
                  f"RM {min_bal:>11,.2f} | RM {max_bal:>11,.2f}")
            
            total_credit += data['credit']
            total_debit += data['debit']
        
        print("-"*120)
        total_net = total_credit - total_debit
        net_symbol = "↑" if total_net > 0 else "↓"
        print(f"{'总计':^12} | {' ':^20} | {' ':^6} | "
              f"RM {total_credit:>11,.2f} | RM {total_debit:>11,.2f} | "
              f"{net_symbol} RM {abs(total_net):>9,.2f} | {' ':^15} | {' ':^15}")
        print("="*120)

def generate_transaction_breakdown():
    """交易明细分析"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 查找最常见的交易类型
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN description LIKE '%DuitNow%' THEN 'DuitNow转账'
                    WHEN description LIKE '%CR Card%' THEN '信用卡还款'
                    WHEN description LIKE '%Bonus Interest%' THEN '利息收入'
                    WHEN description LIKE '%Interest%' THEN '利息收入'
                    ELSE '其他'
                END as category,
                COUNT(*) as count,
                SUM(amount) as total
            FROM savings_accounts sa
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            GROUP BY category
            ORDER BY total DESC
        ''')
        
        print("\n交易类型分析")
        print("="*80)
        print(f"{'交易类型':^30} | {'笔数':^10} | {'总金额':^20} | {'占比':^15}")
        print("-"*80)
        
        rows = cursor.fetchall()
        total_amount = sum(row[2] for row in rows)
        
        for row in rows:
            category, count, amount = row
            pct = (amount / total_amount * 100) if total_amount > 0 else 0
            print(f"{category:^30} | {count:^10} | RM {amount:>15,.2f} | {pct:>6.1f}%")
        
        print("="*80)

def generate_balance_analysis():
    """余额分析"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取每月月末余额
        cursor.execute('''
            SELECT 
                sa.bank_name,
                sa.account_number_last4,
                ss.statement_date,
                st.balance
            FROM savings_accounts sa
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            WHERE st.transaction_date = (
                SELECT MAX(transaction_date)
                FROM savings_transactions st2
                WHERE st2.savings_statement_id = ss.id
            )
            ORDER BY ss.statement_date
        ''')
        
        print("\n月末余额趋势")
        print("="*80)
        print(f"{'月份':^20} | {'银行':^20} | {'账号':^10} | {'月末余额':^20}")
        print("-"*80)
        
        for row in cursor.fetchall():
            bank, acct, date, balance = row
            print(f"{date:^20} | {bank:^20} | {acct:^10} | RM {balance:>15,.2f}")
        
        print("="*80)

def generate_insights():
    """生成财务洞察"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 平均月度支出
        cursor.execute('''
            SELECT AVG(monthly_debit) as avg_monthly_debit
            FROM (
                SELECT SUM(amount) as monthly_debit
                FROM savings_transactions
                WHERE transaction_type = 'debit'
                GROUP BY strftime('%Y-%m', transaction_date)
            )
        ''')
        avg_debit = cursor.fetchone()[0] or 0
        
        # 平均月度存款
        cursor.execute('''
            SELECT AVG(monthly_credit) as avg_monthly_credit
            FROM (
                SELECT SUM(amount) as monthly_credit
                FROM savings_transactions
                WHERE transaction_type = 'credit'
                GROUP BY strftime('%Y-%m', transaction_date)
            )
        ''')
        avg_credit = cursor.fetchone()[0] or 0
        
        # 当前余额
        cursor.execute('''
            SELECT balance
            FROM savings_transactions
            ORDER BY transaction_date DESC
            LIMIT 1
        ''')
        current_balance = cursor.fetchone()[0] or 0
        
        print("\n💡 财务洞察")
        print("="*80)
        print(f"📊 平均月度支出: RM {avg_debit:>15,.2f}")
        print(f"📈 平均月度存款: RM {avg_credit:>15,.2f}")
        print(f"💰 当前账户余额: RM {current_balance:>15,.2f}")
        print(f"💡 月均净流量:   RM {avg_credit - avg_debit:>15,.2f}")
        print("="*80)

def main():
    print("\n" + "="*120)
    print("YEO CHEE WANG - 储蓄账户完整财务报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120 + "\n")
    
    generate_monthly_summary()
    generate_transaction_breakdown()
    generate_balance_analysis()
    generate_insights()
    
    print("\n✅ 财务报告生成完成！\n")

if __name__ == '__main__':
    main()
