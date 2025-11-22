#!/usr/bin/env python3
"""YEO CHEE WANG - 储蓄账户简明财务报告"""

import sys
sys.path.insert(0, '.')

from db.database import get_db
from datetime import datetime

print("\n" + "="*100)
print("YEO CHEE WANG - 储蓄账户财务报告")
print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100 + "\n")

with get_db() as conn:
    cursor = conn.cursor()
    
    # 1. 账户概览
    print("📊 账户概览")
    print("-"*100)
    cursor.execute('''
        SELECT 
            c.name,
            sa.bank_name,
            sa.account_number_last4,
            COUNT(DISTINCT ss.id) as statements,
            COUNT(st.id) as transactions,
            SUM(CASE WHEN st.transaction_type='credit' THEN st.amount ELSE 0 END) as total_credit,
            SUM(CASE WHEN st.transaction_type='debit' THEN st.amount ELSE 0 END) as total_debit
        FROM customers c
        JOIN savings_accounts sa ON sa.customer_id = c.id
        JOIN savings_statements ss ON ss.savings_account_id = sa.id
        JOIN savings_transactions st ON st.savings_statement_id = ss.id
        GROUP BY c.name, sa.bank_name, sa.account_number_last4
    ''')
    
    for row in cursor.fetchall():
        name, bank, acct, stmts, txns, credit, debit = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        print(f"客户: {name}")
        print(f"银行: {bank} | 账号: ****{acct}")
        print(f"对账单数: {stmts} | 交易笔数: {txns}")
        print(f"总存款: RM {credit:,.2f} | 总支出: RM {debit:,.2f}")
        print(f"净流量: RM {credit - debit:,.2f}")
    
    # 2. 月度汇总
    print("\n" + "="*100)
    print("📅 月度交易汇总")
    print("-"*100)
    
    cursor.execute('''
        SELECT 
            substr(st.transaction_date, 4, 7) as month,
            SUM(CASE WHEN st.transaction_type='credit' THEN st.amount ELSE 0 END) as credit,
            SUM(CASE WHEN st.transaction_type='debit' THEN st.amount ELSE 0 END) as debit,
            COUNT(*) as count
        FROM savings_transactions st
        GROUP BY month
        ORDER BY month
    ''')
    
    print(f"{'月份':12s} | {'存款':>15s} | {'支出':>15s} | {'净流量':>15s} | {'笔数':>6s}")
    print("-"*100)
    
    for row in cursor.fetchall():
        month, credit, debit, count = row[0], row[1], row[2], row[3]
        net = credit - debit
        symbol = "↑" if net >= 0 else "↓"
        print(f"{month:12s} | RM {credit:>12,.2f} | RM {debit:>12,.2f} | {symbol} RM {abs(net):>9,.2f} | {count:>6d}")
    
    # 3. 交易类型分析
    print("\n" + "="*100)
    print("🔍 交易类型分析")
    print("-"*100)
    
    cursor.execute('''
        SELECT 
            CASE 
                WHEN description LIKE '%DuitNow%' THEN 'DuitNow转账'
                WHEN description LIKE '%CR Card%' THEN '信用卡还款'
                WHEN description LIKE '%Bonus%' OR description LIKE '%Interest%' THEN '利息收入'
                WHEN description LIKE '%Trf%' OR description LIKE '%Transfer%' THEN '银行转账'
                ELSE '其他'
            END as category,
            transaction_type,
            COUNT(*) as count,
            SUM(amount) as total
        FROM savings_transactions
        GROUP BY category, transaction_type
        ORDER BY total DESC
    ''')
    
    print(f"{'交易类型':25s} | {'类别':10s} | {'笔数':>6s} | {'总金额':>20s}")
    print("-"*100)
    
    for row in cursor.fetchall():
        cat, txn_type, count, total = row[0], row[1], row[2], row[3]
        type_cn = "存款" if txn_type == 'credit' else "支出"
        print(f"{cat:25s} | {type_cn:10s} | {count:>6d} | RM {total:>16,.2f}")
    
    # 4. 余额趋势
    print("\n" + "="*100)
    print("📈 余额趋势（月末）")
    print("-"*100)
    
    cursor.execute('''
        SELECT 
            ss.statement_date,
            st.balance
        FROM savings_statements ss
        JOIN savings_transactions st ON st.savings_statement_id = ss.id
        WHERE st.id IN (
            SELECT MAX(id)
            FROM savings_transactions
            GROUP BY savings_statement_id
        )
        ORDER BY ss.statement_date
    ''')
    
    print(f"{'月份':20s} | {'月末余额':>20s}")
    print("-"*100)
    
    for row in cursor.fetchall():
        date, balance = row[0], row[1]
        print(f"{date:20s} | RM {balance:>16,.2f}")
    
    # 5. 财务洞察
    print("\n" + "="*100)
    print("💡 财务洞察")
    print("-"*100)
    
    cursor.execute('''
        SELECT 
            AVG(monthly_credit) as avg_credit,
            AVG(monthly_debit) as avg_debit
        FROM (
            SELECT 
                substr(transaction_date, 4, 7) as month,
                SUM(CASE WHEN transaction_type='credit' THEN amount ELSE 0 END) as monthly_credit,
                SUM(CASE WHEN transaction_type='debit' THEN amount ELSE 0 END) as monthly_debit
            FROM savings_transactions
            GROUP BY month
        )
    ''')
    
    row = cursor.fetchone()
    avg_credit, avg_debit = row[0], row[1]
    
    cursor.execute('SELECT balance FROM savings_transactions ORDER BY id DESC LIMIT 1')
    current_balance = cursor.fetchone()[0]
    
    print(f"✅ 平均月度存款: RM {avg_credit:>15,.2f}")
    print(f"✅ 平均月度支出: RM {avg_debit:>15,.2f}")
    print(f"✅ 月均净流量:   RM {avg_credit - avg_debit:>15,.2f}")
    print(f"✅ 当前账户余额: RM {current_balance:>15,.2f}")
    
    print("\n" + "="*100)
    print("✅ 报告生成完成！")
    print("="*100 + "\n")
