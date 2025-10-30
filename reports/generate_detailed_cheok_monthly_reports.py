#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成CHEOK JUN YOON详细月结报告
包含所有Supplier消费和付款明细
"""

import sqlite3
from datetime import datetime
from decimal import Decimal
import json

DB_PATH = 'db/smart_loan_manager.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_detailed_monthly_report(conn, customer_id, year, month):
    """生成某月的详细月结报告"""
    cursor = conn.cursor()
    
    print(f"\n{'='*100}")
    print(f"详细月结报告: {year}年{month}月 - CHEOK JUN YOON")
    print(f"{'='*100}")
    
    # ============================================
    # 第一部分：Supplier消费明细
    # ============================================
    print(f"\n【第一部分】Supplier消费明细")
    print(f"{'='*100}")
    
    cursor.execute("""
        SELECT 
            t.transaction_date,
            t.description,
            t.amount,
            t.transaction_type,
            t.owner_flag,
            cc.bank_name,
            cc.card_number_last4,
            cc.card_type,
            s.statement_date
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.customer_id = ?
        AND t.owner_flag = 'INFINITE'
        AND t.transaction_type = 'purchase'
        AND strftime('%Y', s.statement_date) = ?
        AND strftime('%m', s.statement_date) = ?
        ORDER BY t.transaction_date, cc.bank_name
    """, (customer_id, str(year), f'{month:02d}'))
    
    supplier_transactions = cursor.fetchall()
    
    if supplier_transactions:
        print(f"\n找到 {len(supplier_transactions)} 笔Supplier消费:")
        print(f"\n{'序号':<4s} {'消费日期':<12s} {'银行':<15s} {'卡号后4位':<10s} {'Supplier名称':<40s} {'金额':>12s}")
        print('-'*100)
        
        total_supplier = Decimal('0.00')
        for idx, trans in enumerate(supplier_transactions, 1):
            amount = Decimal(str(abs(trans['amount'])))
            total_supplier += amount
            
            # 提取Supplier名称（从描述中）
            supplier_name = trans['description'][:38]
            
            print(f"{idx:<4d} {trans['transaction_date']:<12s} {trans['bank_name']:<15s} "
                  f"*{trans['card_number_last4']:<9s} {supplier_name:<40s} RM {amount:>10,.2f}")
        
        print('-'*100)
        print(f"{'':76s} {'Supplier消费总额:':<20s} RM {total_supplier:>10,.2f}")
        service_fee = total_supplier * Decimal('0.01')
        print(f"{'':76s} {'手续费(1%):':<20s} RM {service_fee:>10,.2f}")
        print(f"{'':76s} {'应收总额:':<20s} RM {(total_supplier + service_fee):>10,.2f}")
    else:
        print("\n✗ 该月没有Supplier消费")
        total_supplier = Decimal('0.00')
        service_fee = Decimal('0.00')
    
    # ============================================
    # 第二部分：付款/转账明细
    # ============================================
    print(f"\n\n【第二部分】付款/转账明细")
    print(f"{'='*100}")
    
    # 查找所有储蓄账户
    cursor.execute("""
        SELECT 
            id,
            account_number_last4,
            account_holder_name,
            bank_name
        FROM savings_accounts
        WHERE account_holder_name LIKE '%INFINITE%GZ%'
        OR account_holder_name LIKE '%AI%SMART%TECH%'
        OR account_holder_name LIKE '%TAN%ZEE%LIANG%'
        OR account_holder_name LIKE '%YEO%CHEE%WANG%'
        OR account_holder_name LIKE '%TEO%YOK%CHU%'
    """)
    
    savings_accounts = cursor.fetchall()
    
    print(f"\n查找付款记录（关键词: CHEOK, JUN YOON）:")
    
    total_payments = Decimal('0.00')
    payment_details = []
    
    for acc in savings_accounts:
        # 获取该账户该月的所有交易
        cursor.execute("""
            SELECT 
                st.transaction_date,
                st.description,
                st.amount,
                st.transaction_type,
                st.balance
            FROM savings_transactions st
            JOIN savings_statements ss ON st.savings_statement_id = ss.id
            WHERE ss.savings_account_id = ?
            AND strftime('%Y', st.transaction_date) = ?
            AND strftime('%m', st.transaction_date) = ?
            ORDER BY st.transaction_date
        """, (acc['id'], str(year), f'{month:02d}'))
        
        transactions = cursor.fetchall()
        
        # 查找付款给CHEOK的记录
        customer_keywords = ['CHEOK', 'JUN YOON', 'CHEOK JUN YOON']
        
        for trans in transactions:
            desc = (trans['description'] or '').upper()
            amount = Decimal(str(trans['amount'] or 0))
            trans_type = (trans['transaction_type'] or '').upper()
            
            # 如果是支出且描述包含客户关键词
            if trans_type in ['DR', 'DEBIT', 'WITHDRAWAL'] and amount > 0:
                matched = False
                for keyword in customer_keywords:
                    if keyword in desc:
                        matched = True
                        break
                
                if matched:
                    total_payments += amount
                    payment_details.append({
                        'date': trans['transaction_date'],
                        'from_account': acc['account_holder_name'],
                        'from_bank': acc['bank_name'],
                        'amount': amount,
                        'description': trans['description'],
                        'payment_type': '转账' if 'TRANSFER' in desc or '转账' in desc else '付款'
                    })
    
    if payment_details:
        print(f"\n找到 {len(payment_details)} 笔付款记录:")
        print(f"\n{'序号':<4s} {'付款日期':<12s} {'付款账户':<30s} {'付款银行':<15s} {'金额':>12s} {'付款类型':<8s}")
        print('-'*100)
        
        for idx, payment in enumerate(payment_details, 1):
            print(f"{idx:<4d} {payment['date']:<12s} {payment['from_account'][:28]:<30s} "
                  f"{payment['from_bank']:<15s} RM {payment['amount']:>10,.2f} {payment['payment_type']:<8s}")
            print(f"     描述: {payment['description'][:85]}")
            print()
        
        print('-'*100)
        print(f"{'':76s} {'实际付款总额:':<20s} RM {total_payments:>10,.2f}")
    else:
        print("\n✗ 该月没有找到付款记录")
    
    # ============================================
    # 第三部分：月结汇总
    # ============================================
    print(f"\n\n【第三部分】月结汇总")
    print(f"{'='*100}")
    
    total_due = total_supplier + service_fee
    net_balance = total_due - total_payments
    
    print(f"\nSupplier消费总额:     RM {total_supplier:>15,.2f}")
    print(f"手续费(1%):          RM {service_fee:>15,.2f}")
    print('-'*100)
    print(f"应收总额:            RM {total_due:>15,.2f}")
    print(f"\n实际付款总额:        RM {total_payments:>15,.2f}")
    print('-'*100)
    
    if net_balance > 0:
        print(f"净余额（客户欠款）:   RM {net_balance:>15,.2f} ❌ 需补款")
        status = "客户欠款"
    elif net_balance < 0:
        print(f"净余额（多付款）:     RM {abs(net_balance):>15,.2f} ✓ 客户处有多余款项")
        status = "多付款"
    else:
        print(f"净余额:             RM {net_balance:>15,.2f} ✓ 已结清")
        status = "已结清"
    
    print(f"{'='*100}\n")
    
    return {
        'year': year,
        'month': month,
        'supplier_transactions': supplier_transactions,
        'supplier_total': total_supplier,
        'service_fee': service_fee,
        'total_due': total_due,
        'payment_details': payment_details,
        'total_payments': total_payments,
        'net_balance': net_balance,
        'status': status
    }

def main():
    """主函数"""
    print("="*100)
    print("CHEOK JUN YOON 详细月结报告生成器")
    print("时间范围: 2025年5月-10月")
    print("="*100)
    
    conn = get_db_connection()
    
    try:
        customer_id = 6  # CHEOK JUN YOON
        year = 2025
        months = [5, 6, 7, 8, 9, 10]
        
        all_reports = []
        
        for month in months:
            report = generate_detailed_monthly_report(conn, customer_id, year, month)
            all_reports.append(report)
        
        # 生成总汇总
        print(f"\n{'='*100}")
        print(f"总汇总: {year}年5月-10月")
        print(f"{'='*100}")
        
        total_supplier = sum(r['supplier_total'] for r in all_reports)
        total_service_fee = sum(r['service_fee'] for r in all_reports)
        total_due = sum(r['total_due'] for r in all_reports)
        total_payments = sum(r['total_payments'] for r in all_reports)
        total_net = sum(r['net_balance'] for r in all_reports)
        
        print(f"\nSupplier消费总额:     RM {total_supplier:>15,.2f}")
        print(f"手续费(1%)总额:      RM {total_service_fee:>15,.2f}")
        print('-'*100)
        print(f"应收总额:            RM {total_due:>15,.2f}")
        print(f"\n实际付款总额:        RM {total_payments:>15,.2f}")
        print('-'*100)
        
        if total_net > 0:
            print(f"净余额（客户欠款）:   RM {total_net:>15,.2f} ❌ 需补款")
            print(f"\n结论: 我们使用的多，客户需要补款 RM {total_net:,.2f}")
        elif total_net < 0:
            print(f"净余额（多付款）:     RM {abs(total_net):>15,.2f} ✓ 客户处有多余款项")
            print(f"\n结论: 付款给客户的多，客户处有多余款项 RM {abs(total_net):,.2f}")
        else:
            print(f"净余额:             RM {total_net:>15,.2f} ✓ 已结清")
            print(f"\n结论: 收支平衡，已完全结清")
        
        print(f"\n{'='*100}")
        print(f"各月明细汇总:")
        print(f"{'='*100}")
        print(f"{'月份':<10s} {'Supplier笔数':<12s} {'应收':>15s} {'实付':>15s} {'净余额':>15s} {'状态':<10s}")
        print('-'*100)
        
        for r in all_reports:
            trans_count = len(r['supplier_transactions'])
            status_icon = "✓" if r['net_balance'] <= 0 else "❌"
            print(f"{r['year']}-{r['month']:02d}   {trans_count:<12d} RM {r['total_due']:>12,.2f} "
                  f"RM {r['total_payments']:>12,.2f} RM {r['net_balance']:>12,.2f} {status_icon}")
        
        print(f"{'='*100}\n")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
