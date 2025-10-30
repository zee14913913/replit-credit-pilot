#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新计算CHEOK JUN YOON的月度汇总报告
按statement_month进行月度划分，交叉对账储蓄账户付款记录
"""

import sqlite3
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

DB_PATH = 'db/smart_loan_manager.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_customer_id(conn, customer_name):
    """获取客户ID"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, customer_code 
        FROM customers 
        WHERE name LIKE ? OR customer_code LIKE ?
    """, (f'%{customer_name}%', f'%{customer_name}%'))
    
    result = cursor.fetchone()
    if result:
        print(f"✓ 找到客户: {result['name']} ({result['customer_code']}), ID: {result['id']}")
        return result['id']
    else:
        print(f"✗ 未找到客户: {customer_name}")
        return None

def get_monthly_statements(conn, customer_id, year, month):
    """获取客户某月的所有月度账单"""
    cursor = conn.cursor()
    statement_month = f"{year}-{month:02d}"
    
    cursor.execute("""
        SELECT 
            id,
            customer_id,
            bank_name,
            statement_month,
            period_start_date,
            period_end_date,
            previous_balance_total,
            closing_balance_total,
            owner_balance,
            gz_balance,
            owner_expenses,
            owner_payments,
            gz_expenses,
            gz_payments,
            card_count,
            transaction_count
        FROM monthly_statements
        WHERE customer_id = ?
        AND statement_month = ?
        ORDER BY bank_name
    """, (customer_id, statement_month))
    
    return cursor.fetchall()

def get_savings_accounts(conn):
    """获取所有对账相关的储蓄/来往账户"""
    cursor = conn.cursor()
    
    # 这些是用于对账的账户名称
    account_patterns = [
        '%INFINITE%GZ%',
        '%AI%SMART%TECH%',
        '%TAN%ZEE%LIANG%',
        '%YEO%CHEE%WANG%',
        '%TEO%YOK%CHU%'
    ]
    
    accounts = []
    for pattern in account_patterns:
        cursor.execute("""
            SELECT 
                id,
                account_number_last4,
                account_holder_name,
                bank_name
            FROM savings_accounts
            WHERE account_holder_name LIKE ?
        """, (pattern,))
        
        results = cursor.fetchall()
        accounts.extend(results)
    
    # 去重
    seen = set()
    unique_accounts = []
    for acc in accounts:
        if acc['id'] not in seen:
            seen.add(acc['id'])
            unique_accounts.append(acc)
    
    return unique_accounts

def get_savings_transactions_by_month(conn, account_id, year, month):
    """获取某个储蓄账户在指定月份的所有交易"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            st.id,
            st.transaction_date,
            st.description,
            st.withdrawal,
            st.deposit,
            st.balance
        FROM savings_transactions st
        JOIN savings_statements ss ON st.statement_id = ss.id
        WHERE ss.savings_account_id = ?
        AND ss.statement_year = ?
        AND ss.statement_month = ?
        ORDER BY st.transaction_date
    """, (account_id, year, month))
    
    return cursor.fetchall()

def find_payment_to_customer(transactions, customer_keywords):
    """
    在储蓄账户交易中查找付款给客户的记录
    返回: 付款总额（Decimal）和详细记录
    """
    total_payment = Decimal('0.00')
    payment_records = []
    
    # 关键词匹配
    keywords = customer_keywords
    
    for trans in transactions:
        desc = (trans['description'] or '').upper()
        withdrawal = Decimal(str(trans['withdrawal'] or 0))
        
        # 如果是支出（withdrawal > 0）且描述包含关键词
        if withdrawal > 0:
            matched = False
            for keyword in keywords:
                if keyword.upper() in desc:
                    matched = True
                    break
            
            if matched:
                total_payment += withdrawal
                payment_records.append({
                    'date': trans['transaction_date'],
                    'description': trans['description'],
                    'amount': withdrawal
                })
    
    return total_payment, payment_records

def generate_monthly_report(conn, customer_id, customer_name, year, month):
    """生成某月的月结报告"""
    print(f"\n{'='*80}")
    print(f"月结报告: {year}年{month}月")
    print(f"{'='*80}")
    
    # 1. 获取该月的所有monthly_statements
    monthly_stmts = get_monthly_statements(conn, customer_id, year, month)
    
    if not monthly_stmts:
        print(f"✗ {year}年{month}月没有找到任何月度账单")
        return None
    
    print(f"\n找到 {len(monthly_stmts)} 个银行的月度账单:")
    
    # 2. 汇总所有银行的数据
    total_gz_expenses = Decimal('0.00')
    total_gz_payments = Decimal('0.00')
    total_owner_expenses = Decimal('0.00')
    total_owner_payments = Decimal('0.00')
    
    for stmt in monthly_stmts:
        print(f"\n  {stmt['bank_name']}:")
        print(f"    期间: {stmt['period_start_date']} ~ {stmt['period_end_date']}")
        print(f"    卡片数: {stmt['card_count']}, 交易数: {stmt['transaction_count']}")
        print(f"    OWNER消费: RM {Decimal(str(stmt['owner_expenses'])):,.2f}")
        print(f"    OWNER付款: RM {Decimal(str(stmt['owner_payments'])):,.2f}")
        print(f"    Supplier消费: RM {Decimal(str(stmt['gz_expenses'])):,.2f}")
        print(f"    Supplier付款: RM {Decimal(str(stmt['gz_payments'])):,.2f}")
        
        total_gz_expenses += Decimal(str(stmt['gz_expenses']))
        total_gz_payments += Decimal(str(stmt['gz_payments']))
        total_owner_expenses += Decimal(str(stmt['owner_expenses']))
        total_owner_payments += Decimal(str(stmt['owner_payments']))
    
    # 3. 计算1%手续费
    service_fee = total_gz_expenses * Decimal('0.01')
    
    print(f"\n{'='*80}")
    print(f"信用卡账单汇总:")
    print(f"{'='*80}")
    print(f"Supplier消费总额:     RM {total_gz_expenses:>15,.2f}")
    print(f"手续费(1%):          RM {service_fee:>15,.2f}")
    print(f"{'-'*80}")
    print(f"应收总额:            RM {(total_gz_expenses + service_fee):>15,.2f}")
    
    # 4. 查找储蓄账户的付款记录
    print(f"\n{'='*80}")
    print(f"储蓄账户付款记录查找:")
    print(f"{'='*80}")
    
    savings_accounts = get_savings_accounts(conn)
    print(f"找到 {len(savings_accounts)} 个对账账户")
    
    total_bank_payments = Decimal('0.00')
    payment_details = []
    
    # 客户姓名关键词
    customer_keywords = ['CHEOK', 'JUN YOON', 'CHEOK JUN YOON']
    
    for acc in savings_accounts:
        print(f"\n  检查账户: {acc['account_holder_name']} ({acc['bank_name']})")
        trans = get_savings_transactions_by_month(conn, acc['id'], year, month)
        
        if trans:
            print(f"    找到 {len(trans)} 笔交易")
            payment_amount, records = find_payment_to_customer(trans, customer_keywords)
            
            if payment_amount > 0:
                print(f"    ✓ 付款给客户: RM {payment_amount:,.2f} ({len(records)}笔)")
                total_bank_payments += payment_amount
                
                payment_details.append({
                    'account_name': acc['account_holder_name'],
                    'bank': acc['bank_name'],
                    'amount': payment_amount,
                    'records': records
                })
                
                # 显示详细记录
                for rec in records:
                    print(f"      - {rec['date']}: RM {rec['amount']:,.2f} - {rec['description'][:50]}")
            else:
                print(f"    ✗ 未找到付款记录")
        else:
            print(f"    ✗ 该月无交易记录")
    
    # 5. 计算月结
    print(f"\n{'='*80}")
    print(f"月结汇总: {year}年{month}月")
    print(f"{'='*80}")
    print(f"Supplier消费总额:     RM {total_gz_expenses:>15,.2f}")
    print(f"手续费(1%):          RM {service_fee:>15,.2f}")
    print(f"{'-'*80}")
    print(f"应收总额:            RM {(total_gz_expenses + service_fee):>15,.2f}")
    print(f"\n实际付款总额:        RM {total_bank_payments:>15,.2f}")
    print(f"{'-'*80}")
    
    net_balance = (total_gz_expenses + service_fee) - total_bank_payments
    
    if net_balance > 0:
        print(f"净余额（客户欠款）:   RM {net_balance:>15,.2f} ❌ 需补款")
        status = "客户欠款"
    elif net_balance < 0:
        print(f"净余额（多付款）:     RM {abs(net_balance):>15,.2f} ✓ 客户处有多余款项")
        status = "多付款"
    else:
        print(f"净余额:             RM {net_balance:>15,.2f} ✓ 已结清")
        status = "已结清"
    
    print(f"{'='*80}")
    
    return {
        'year': year,
        'month': month,
        'supplier_expenses': total_gz_expenses,
        'service_fee': service_fee,
        'total_due': total_gz_expenses + service_fee,
        'total_payments': total_bank_payments,
        'net_balance': net_balance,
        'status': status,
        'monthly_statements': monthly_stmts,
        'payment_details': payment_details
    }

def main():
    """主函数"""
    print("="*80)
    print("CHEOK JUN YOON 月度汇总报告")
    print("时间范围: 2025年5月-10月")
    print("数据来源: monthly_statements 表")
    print("="*80)
    
    conn = get_db_connection()
    
    try:
        # 1. 获取客户ID
        customer_id = get_customer_id(conn, 'CHEOK JUN YOON')
        if not customer_id:
            print("错误: 找不到客户")
            return
        
        customer_name = 'CHEOK JUN YOON'
        
        # 2. 生成5月-10月的月结报告
        months = [5, 6, 7, 8, 9, 10]
        year = 2025
        
        all_reports = []
        
        for month in months:
            report = generate_monthly_report(conn, customer_id, customer_name, year, month)
            if report:
                all_reports.append(report)
        
        # 3. 生成总汇总报告
        if not all_reports:
            print("\n没有找到任何月结报告")
            return
        
        print(f"\n\n{'='*80}")
        print(f"总汇总: {year}年5月-10月 ({len(all_reports)}个月)")
        print(f"{'='*80}")
        
        total_supplier_expenses = sum(r['supplier_expenses'] for r in all_reports)
        total_service_fee = sum(r['service_fee'] for r in all_reports)
        total_due = sum(r['total_due'] for r in all_reports)
        total_payments = sum(r['total_payments'] for r in all_reports)
        total_net = sum(r['net_balance'] for r in all_reports)
        
        print(f"\nSupplier消费总额:     RM {total_supplier_expenses:>15,.2f}")
        print(f"手续费(1%)总额:      RM {total_service_fee:>15,.2f}")
        print(f"{'-'*80}")
        print(f"应收总额:            RM {total_due:>15,.2f}")
        print(f"\n实际付款总额:        RM {total_payments:>15,.2f}")
        print(f"{'-'*80}")
        
        if total_net > 0:
            print(f"净余额（客户欠款）:   RM {total_net:>15,.2f} ❌ 需补款")
            print(f"\n结论: 我们使用的多，客户需要补款 RM {total_net:,.2f}")
        elif total_net < 0:
            print(f"净余额（多付款）:     RM {abs(total_net):>15,.2f} ✓ 客户处有多余款项")
            print(f"\n结论: 付款给客户的多，客户处有多余款项 RM {abs(total_net):,.2f}")
        else:
            print(f"净余额:             RM {total_net:>15,.2f} ✓ 已结清")
            print(f"\n结论: 收支平衡，已完全结清")
        
        print(f"\n{'='*80}")
        print(f"各月明细:")
        print(f"{'='*80}")
        for r in all_reports:
            status_icon = "✓" if r['net_balance'] <= 0 else "❌"
            print(f"{r['year']}-{r['month']:02d}: 应收 RM {r['total_due']:>12,.2f}, 实付 RM {r['total_payments']:>12,.2f}, 净余额 RM {r['net_balance']:>12,.2f} {status_icon}")
        
        print(f"{'='*80}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
