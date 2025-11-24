#!/usr/bin/env python3
"""数据质量诊断工具"""

import sqlite3
from decimal import Decimal

def diagnose_data_quality():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*80)
    print("📊 数据质量诊断报告")
    print("="*80)
    
    # 诊断1: 固定minimum_payment异常
    print("\n🔍 诊断1：固定minimum_payment异常（相同值重复>2次）")
    print("-" * 80)
    cursor.execute('''
        SELECT 
            c.name as customer_name,
            cc.bank_name,
            s.minimum_payment,
            COUNT(*) as count,
            MIN(s.statement_total) as min_total,
            MAX(s.statement_total) as max_total
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        WHERE s.minimum_payment IS NOT NULL
        GROUP BY c.id, cc.id, s.minimum_payment
        HAVING COUNT(*) > 2
        ORDER BY count DESC
        LIMIT 20
    ''')
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  ⚠️ {row['customer_name'][:20]:20} | {row['bank_name']:15} | "
                  f"固定值: RM {row['minimum_payment']:8.2f} | "
                  f"重复{row['count']:2}次 | "
                  f"Total范围: RM {row['min_total']:8.2f} - RM {row['max_total']:10.2f}")
    else:
        print("  ✅ 未发现固定值异常")
    
    # 诊断2: minimum_payment比例异常
    print("\n🔍 诊断2：minimum_payment比例异常（<2% 或 >12%）")
    print("-" * 80)
    cursor.execute('''
        SELECT 
            c.name as customer,
            cc.bank_name as bank,
            s.id,
            s.statement_date as stmt_date,
            s.statement_total as total,
            s.minimum_payment as min_pay,
            ROUND(CAST(s.minimum_payment AS FLOAT) / NULLIF(s.statement_total, 0) * 100, 2) as ratio_pct
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        WHERE s.statement_total > 0 
          AND s.minimum_payment > 0
          AND (
            CAST(s.minimum_payment AS FLOAT) / s.statement_total < 0.02 
            OR CAST(s.minimum_payment AS FLOAT) / s.statement_total > 0.12
          )
        ORDER BY ratio_pct ASC
        LIMIT 30
    ''')
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  ⚠️ ID {row['id']:4} | {row['customer'][:20]:20} | {row['bank']:15} | "
                  f"Total: RM {row['total']:10.2f} | Min: RM {row['min_pay']:8.2f} | "
                  f"比例: {row['ratio_pct']:5.2f}%")
    else:
        print("  ✅ 未发现比例异常")
    
    # 诊断3: 缺失due_date统计
    print("\n🔍 诊断3：缺失due_date统计（按银行分组）")
    print("-" * 80)
    cursor.execute('''
        SELECT 
            cc.bank_name,
            COUNT(*) as total,
            SUM(CASE WHEN s.due_date IS NULL OR s.due_date = '' THEN 1 ELSE 0 END) as missing,
            ROUND(CAST(SUM(CASE WHEN s.due_date IS NULL OR s.due_date = '' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as missing_pct
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        GROUP BY cc.bank_name
        HAVING SUM(CASE WHEN s.due_date IS NULL OR s.due_date = '' THEN 1 ELSE 0 END) > 0
        ORDER BY missing DESC
    ''')
    
    rows = cursor.fetchall()
    total_missing = 0
    if rows:
        for row in rows:
            print(f"  ⚠️ {row['bank_name']:20} | 总记录: {row['total']:4} | "
                  f"缺失: {row['missing']:4} ({row['missing_pct']:5.1f}%)")
            total_missing += row['missing']
    else:
        print("  ✅ 所有记录都有due_date")
    
    # 诊断4: Alliance Bank详细分析
    print("\n🔍 诊断4：Alliance Bank详细记录分析")
    print("-" * 80)
    cursor.execute('''
        SELECT 
            s.id,
            c.name as customer,
            s.statement_date as date,
            s.statement_total as total,
            s.minimum_payment as min_pay,
            s.due_date,
            CASE 
                WHEN s.statement_total > 0 AND s.minimum_payment > 0 
                THEN ROUND(CAST(s.minimum_payment AS FLOAT) / s.statement_total * 100, 2) 
                ELSE NULL 
            END as ratio
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        WHERE cc.bank_name = 'Alliance Bank'
        ORDER BY s.id DESC
        LIMIT 15
    ''')
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            due_status = row['due_date'] if row['due_date'] else "❌ NULL"
            ratio_str = f"{row['ratio']:.2f}%" if row['ratio'] else "N/A"
            print(f"  ID {row['id']:4} | {row['date']:10} | "
                  f"Total: RM {row['total']:10.2f} | Min: RM {row['min_pay']:8.2f} | "
                  f"比例: {ratio_str:6} | Due: {due_status}")
    else:
        print("  ℹ️ 未找到Alliance Bank记录")
    
    # 总结统计
    print("\n" + "="*80)
    print("📈 诊断总结")
    print("="*80)
    
    cursor.execute('SELECT COUNT(*) FROM statements')
    total_statements = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM statements WHERE due_date IS NULL OR due_date = ""')
    total_missing_due = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM statements 
        WHERE statement_total > 0 AND minimum_payment > 0
        AND (
            CAST(minimum_payment AS FLOAT) / statement_total < 0.02 
            OR CAST(minimum_payment AS FLOAT) / statement_total > 0.12
        )
    ''')
    total_ratio_anomalies = cursor.fetchone()[0]
    
    print(f"  • 总账单记录数: {total_statements}")
    print(f"  • 缺失due_date: {total_missing_due} ({total_missing_due/total_statements*100:.1f}%)")
    print(f"  • minimum_payment比例异常: {total_ratio_anomalies}")
    
    conn.close()
    
    return {
        'total_statements': total_statements,
        'missing_due_date': total_missing_due,
        'ratio_anomalies': total_ratio_anomalies
    }

if __name__ == '__main__':
    stats = diagnose_data_quality()
