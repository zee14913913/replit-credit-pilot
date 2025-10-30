#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新计算CHEOK JUN YOON的信用卡账单六大分类并生成月结报告
按statement_date进行月度划分
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

def get_credit_cards(conn, customer_id):
    """获取客户的所有信用卡"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, card_number_last4, bank_name, card_type
        FROM credit_cards
        WHERE customer_id = ?
        ORDER BY bank_name, card_number_last4
    """, (customer_id,))
    
    cards = cursor.fetchall()
    print(f"\n找到 {len(cards)} 张信用卡:")
    for card in cards:
        print(f"  - {card['bank_name']} {card['card_type']} (*{card['card_number_last4']})")
    
    return cards

def get_statements_by_card(conn, card_id):
    """获取某张信用卡的所有账单"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            statement_date,
            previous_balance,
            closing_balance,
            payment_due_date
        FROM statements
        WHERE credit_card_id = ?
        ORDER BY statement_date
    """, (card_id,))
    
    return cursor.fetchall()

def get_transactions(conn, statement_id):
    """获取账单的所有交易"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            transaction_date,
            description,
            amount,
            transaction_type,
            category,
            infinite_classification
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date
    """, (statement_id,))
    
    return cursor.fetchall()

def recalculate_statement_classification(transactions):
    """
    重新计算账单的六大分类
    返回: {
        'owner_expenses': Decimal,
        'owner_payments': Decimal,
        'gz_expenses': Decimal,
        'gz_payments': Decimal,
        'owner_balance': Decimal,
        'gz_balance': Decimal
    }
    """
    result = {
        'owner_expenses': Decimal('0.00'),
        'owner_payments': Decimal('0.00'),
        'gz_expenses': Decimal('0.00'),
        'gz_payments': Decimal('0.00'),
        'owner_balance': Decimal('0.00'),
        'gz_balance': Decimal('0.00')
    }
    
    for trans in transactions:
        amount = Decimal(str(trans['amount']))
        trans_type = trans['transaction_type']  # 'DR' or 'CR'
        classification = trans['infinite_classification']  # 'OWNER' or 'INFINITE'
        
        if classification == 'OWNER':
            if trans_type == 'DR':
                # OWNER消费
                result['owner_expenses'] += amount
            else:  # CR
                # OWNER付款
                result['owner_payments'] += amount
        else:  # INFINITE (Supplier)
            if trans_type == 'DR':
                # Supplier消费
                result['gz_expenses'] += amount
            else:  # CR
                # Supplier付款（客户为供应商付款）
                result['gz_payments'] += amount
    
    # 计算余额
    result['owner_balance'] = result['owner_expenses'] - result['owner_payments']
    result['gz_balance'] = result['gz_expenses'] - result['gz_payments']
    
    return result

def get_savings_accounts(conn):
    """获取所有对账相关的储蓄/来往账户"""
    cursor = conn.cursor()
    
    # 这些是用于对账的账户名称
    account_names = [
        'INFINITE GZ',
        'AI SMART TECH',
        'TAN ZEE LIANG',
        'YEO CHEE WANG',
        'TEO YOK CHU & YEO CHEE WANG'
    ]
    
    accounts = []
    for name in account_names:
        cursor.execute("""
            SELECT 
                sa.id,
                sa.account_number,
                sa.account_name,
                sa.bank_name
            FROM savings_accounts sa
            WHERE sa.account_name LIKE ?
        """, (f'%{name}%',))
        
        results = cursor.fetchall()
        accounts.extend(results)
    
    print(f"\n找到 {len(accounts)} 个对账账户:")
    for acc in accounts:
        print(f"  - {acc['account_name']} ({acc['bank_name']} - {acc['account_number'][-4:]})")
    
    return accounts

def get_savings_transactions_by_month(conn, account_id, year, month):
    """获取某个储蓄账户在指定月份的所有交易"""
    cursor = conn.cursor()
    
    # 注意：savings_statements使用savings_account_id字段
    cursor.execute("""
        SELECT 
            st.id,
            st.transaction_date,
            st.description,
            st.withdrawal,
            st.deposit,
            st.balance,
            ss.statement_month,
            ss.statement_year
        FROM savings_transactions st
        JOIN savings_statements ss ON st.statement_id = ss.id
        WHERE ss.savings_account_id = ?
        AND ss.statement_year = ?
        AND ss.statement_month = ?
        ORDER BY st.transaction_date
    """, (account_id, year, month))
    
    return cursor.fetchall()

def find_payment_to_customer(transactions, customer_name):
    """
    在储蓄账户交易中查找付款给客户的记录
    返回: 付款总额（Decimal）
    """
    total_payment = Decimal('0.00')
    payment_records = []
    
    # 关键词匹配：可能的付款描述
    keywords = [
        'CHEOK',
        'JUN YOON',
        'TRANSFER',
        'PAYMENT',
        '转账',
        '付款'
    ]
    
    for trans in transactions:
        desc = (trans['description'] or '').upper()
        withdrawal = Decimal(str(trans['withdrawal'] or 0))
        
        # 如果是支出（withdrawal > 0）且描述包含客户相关关键词
        if withdrawal > 0:
            for keyword in keywords:
                if keyword in desc:
                    total_payment += withdrawal
                    payment_records.append({
                        'date': trans['transaction_date'],
                        'description': trans['description'],
                        'amount': withdrawal
                    })
                    break
    
    return total_payment, payment_records

def generate_monthly_reconciliation(conn, customer_id, year, month):
    """
    生成某月的月结报告
    月份定义：以statement_date为准
    """
    print(f"\n{'='*80}")
    print(f"月结报告: {year}年{month}月")
    print(f"{'='*80}")
    
    # 1. 获取客户的所有信用卡
    cards = get_credit_cards(conn, customer_id)
    
    # 2. 查找该月的所有信用卡账单（以statement_date为准）
    monthly_statements = []
    
    for card in cards:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.id,
                s.statement_date,
                s.previous_balance,
                s.closing_balance,
                cc.bank_name,
                cc.card_number_last4,
                cc.card_type
            FROM statements s
            JOIN credit_cards cc ON s.credit_card_id = cc.id
            WHERE s.credit_card_id = ?
            AND strftime('%Y', s.statement_date) = ?
            AND strftime('%m', s.statement_date) = ?
        """, (card['id'], str(year), f'{month:02d}'))
        
        results = cursor.fetchall()
        monthly_statements.extend(results)
    
    if not monthly_statements:
        print(f"✗ {year}年{month}月没有找到任何信用卡账单")
        return None
    
    print(f"\n找到 {len(monthly_statements)} 份信用卡账单:")
    
    # 3. 计算每份账单的六大分类
    month_summary = {
        'total_owner_expenses': Decimal('0.00'),
        'total_owner_payments': Decimal('0.00'),
        'total_gz_expenses': Decimal('0.00'),
        'total_gz_payments': Decimal('0.00'),
        'total_service_fee': Decimal('0.00'),
        'statements': []
    }
    
    for stmt in monthly_statements:
        print(f"\n  处理账单: {stmt['bank_name']} {stmt['card_type']} (*{stmt['card_number_last4']})")
        print(f"    账单日期: {stmt['statement_date']}")
        
        # 获取交易
        transactions = get_transactions(conn, stmt['id'])
        print(f"    交易笔数: {len(transactions)}")
        
        # 重新计算分类
        classification = recalculate_statement_classification(transactions)
        
        # 计算1%手续费（只对Supplier消费计算）
        service_fee = classification['gz_expenses'] * Decimal('0.01')
        
        print(f"    OWNER消费: RM {classification['owner_expenses']:,.2f}")
        print(f"    OWNER付款: RM {classification['owner_payments']:,.2f}")
        print(f"    Supplier消费: RM {classification['gz_expenses']:,.2f}")
        print(f"    Supplier付款: RM {classification['gz_payments']:,.2f}")
        print(f"    手续费(1%): RM {service_fee:,.2f}")
        
        # 累加到月度汇总
        month_summary['total_owner_expenses'] += classification['owner_expenses']
        month_summary['total_owner_payments'] += classification['owner_payments']
        month_summary['total_gz_expenses'] += classification['gz_expenses']
        month_summary['total_gz_payments'] += classification['gz_payments']
        month_summary['total_service_fee'] += service_fee
        
        month_summary['statements'].append({
            'statement_id': stmt['id'],
            'bank': stmt['bank_name'],
            'card_type': stmt['card_type'],
            'card_last4': stmt['card_number_last4'],
            'statement_date': stmt['statement_date'],
            'classification': classification,
            'service_fee': service_fee
        })
    
    # 4. 查找储蓄账户的付款记录
    print(f"\n查找储蓄账户付款记录...")
    
    savings_accounts = get_savings_accounts(conn)
    total_bank_payments = Decimal('0.00')
    payment_details = []
    
    for acc in savings_accounts:
        trans = get_savings_transactions_by_month(conn, acc['id'], year, month)
        if trans:
            payment_amount, records = find_payment_to_customer(trans, 'CHEOK')
            if payment_amount > 0:
                print(f"  {acc['account_name']}: RM {payment_amount:,.2f} ({len(records)}笔)")
                total_bank_payments += payment_amount
                payment_details.append({
                    'account_name': acc['account_name'],
                    'bank': acc['bank_name'],
                    'amount': payment_amount,
                    'records': records
                })
    
    # 5. 计算月结
    print(f"\n{'='*80}")
    print(f"月结汇总: {year}年{month}月")
    print(f"{'='*80}")
    print(f"Supplier消费总额:     RM {month_summary['total_gz_expenses']:>15,.2f}")
    print(f"手续费(1%):          RM {month_summary['total_service_fee']:>15,.2f}")
    print(f"{'-'*80}")
    print(f"应收总额:            RM {(month_summary['total_gz_expenses'] + month_summary['total_service_fee']):>15,.2f}")
    print(f"\n实际付款总额:        RM {total_bank_payments:>15,.2f}")
    print(f"{'-'*80}")
    
    net_balance = (month_summary['total_gz_expenses'] + month_summary['total_service_fee']) - total_bank_payments
    
    if net_balance > 0:
        print(f"净余额（客户欠款）:   RM {net_balance:>15,.2f} ❌ 需补款")
    elif net_balance < 0:
        print(f"净余额（多付款）:     RM {abs(net_balance):>15,.2f} ✓ 客户处有多余款项")
    else:
        print(f"净余额:             RM {net_balance:>15,.2f} ✓ 已结清")
    
    print(f"{'='*80}")
    
    return {
        'year': year,
        'month': month,
        'supplier_expenses': month_summary['total_gz_expenses'],
        'service_fee': month_summary['total_service_fee'],
        'total_due': month_summary['total_gz_expenses'] + month_summary['total_service_fee'],
        'total_payments': total_bank_payments,
        'net_balance': net_balance,
        'statements': month_summary['statements'],
        'payment_details': payment_details
    }

def main():
    """主函数"""
    print("="*80)
    print("CHEOK JUN YOON 信用卡账单重新计算及月结报告")
    print("时间范围: 2025年5月-10月")
    print("="*80)
    
    conn = get_db_connection()
    
    try:
        # 1. 获取客户ID
        customer_id = get_customer_id(conn, 'CHEOK JUN YOON')
        if not customer_id:
            print("错误: 找不到客户")
            return
        
        # 2. 生成5月-10月的月结报告
        months = [5, 6, 7, 8, 9, 10]
        year = 2025
        
        all_reports = []
        
        for month in months:
            report = generate_monthly_reconciliation(conn, customer_id, year, month)
            if report:
                all_reports.append(report)
        
        # 3. 生成汇总报告
        print(f"\n\n{'='*80}")
        print(f"总汇总: {year}年5月-10月")
        print(f"{'='*80}")
        
        total_supplier_expenses = sum(r['supplier_expenses'] for r in all_reports)
        total_service_fee = sum(r['service_fee'] for r in all_reports)
        total_due = sum(r['total_due'] for r in all_reports)
        total_payments = sum(r['total_payments'] for r in all_reports)
        total_net = sum(r['net_balance'] for r in all_reports)
        
        print(f"Supplier消费总额:     RM {total_supplier_expenses:>15,.2f}")
        print(f"手续费(1%)总额:      RM {total_service_fee:>15,.2f}")
        print(f"{'-'*80}")
        print(f"应收总额:            RM {total_due:>15,.2f}")
        print(f"\n实际付款总额:        RM {total_payments:>15,.2f}")
        print(f"{'-'*80}")
        
        if total_net > 0:
            print(f"净余额（客户欠款）:   RM {total_net:>15,.2f} ❌ 需补款")
        elif total_net < 0:
            print(f"净余额（多付款）:     RM {abs(total_net):>15,.2f} ✓ 客户处有多余款项")
        else:
            print(f"净余额:             RM {total_net:>15,.2f} ✓ 已结清")
        
        print(f"{'='*80}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
