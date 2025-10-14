#!/usr/bin/env python3
"""
完整交易验证脚本 - 验证所有信用卡账单的DR/CR分类和计算准确性
"""
import sqlite3
from typing import Dict, List, Tuple

# 供应商列表
SUPPLIERS = [
    '7SL', 
    'DINAS', 
    'RAUB SYC HAINAN', 
    'AI SMART TECH', 
    'HUAWEI', 
    'PASAR RAYA', 
    'PUCHONG HERBS'
]

# 客户名字（用于识别客户付款）
CUSTOMER_NAMES = ['CHEOK JUN YOON', 'CHANG CHOON CHOW', 'KENG CHOW', 'MAKAN DULU', 'LEE CHEE HWA', 'WING CHOW']

def verify_statement(cursor, stmt_id: int, bank_name: str, card_last4: str, stmt_date: str):
    """验证单个账单的所有交易"""
    
    # 获取账单信息
    cursor.execute('''
        SELECT previous_balance, statement_total
        FROM statements
        WHERE id = ?
    ''', (stmt_id,))
    
    stmt_info = cursor.fetchone()
    if not stmt_info:
        return None
    
    prev_balance, stmt_total = stmt_info
    
    # 获取所有交易
    cursor.execute('''
        SELECT 
            transaction_date,
            description,
            amount,
            transaction_type
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date
    ''', (stmt_id,))
    
    transactions = cursor.fetchall()
    
    # 分类统计
    customer_purchases = []
    customer_payments = []
    infinite_purchases = []
    infinite_payments = []
    
    for date, desc, amt, txn_type in transactions:
        desc_upper = desc.upper()
        
        if txn_type == 'purchase':
            # 检查是否为供应商
            is_supplier = False
            for supplier in SUPPLIERS:
                if supplier in desc_upper:
                    infinite_purchases.append({
                        'date': date,
                        'desc': desc,
                        'amount': amt,
                        'supplier': supplier
                    })
                    is_supplier = True
                    break
            
            if not is_supplier:
                customer_purchases.append({
                    'date': date,
                    'desc': desc,
                    'amount': amt
                })
        
        elif txn_type == 'payment':
            # 检查是否为客户/公司付款
            is_customer_payment = False
            for name in CUSTOMER_NAMES:
                if name in desc_upper:
                    customer_payments.append({
                        'date': date,
                        'desc': desc,
                        'amount': amt
                    })
                    is_customer_payment = True
                    break
            
            if not is_customer_payment:
                infinite_payments.append({
                    'date': date,
                    'desc': desc,
                    'amount': amt
                })
    
    # 计算总额
    customer_spend = sum([t['amount'] for t in customer_purchases])
    customer_payment = sum([t['amount'] for t in customer_payments])
    infinite_spend = sum([t['amount'] for t in infinite_purchases])
    infinite_payment = sum([t['amount'] for t in infinite_payments])
    
    # 计算余额
    customer_balance = prev_balance + customer_spend - customer_payment
    infinite_balance = infinite_spend - infinite_payment
    
    # 计算手续费
    supplier_fee = infinite_spend * 0.01
    
    # 验证总额
    total_spend = customer_spend + infinite_spend
    total_payment = customer_payment + infinite_payment
    calculated_total = prev_balance + total_spend - total_payment
    
    # 检查是否匹配
    matches_stmt_total = abs(calculated_total - stmt_total) < 0.01
    
    return {
        'statement_id': stmt_id,
        'bank': bank_name,
        'card': card_last4,
        'date': stmt_date,
        'prev_balance': prev_balance,
        'stmt_total': stmt_total,
        'customer_purchases': customer_purchases,
        'customer_payments': customer_payments,
        'infinite_purchases': infinite_purchases,
        'infinite_payments': infinite_payments,
        'customer_spend': customer_spend,
        'customer_payment': customer_payment,
        'infinite_spend': infinite_spend,
        'infinite_payment': infinite_payment,
        'supplier_fee': supplier_fee,
        'customer_balance': customer_balance,
        'infinite_balance': infinite_balance,
        'calculated_total': calculated_total,
        'matches': matches_stmt_total
    }

def main():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 获取CHEOK JUN YOON的所有账单
    cursor.execute('''
        SELECT 
            s.id,
            cc.bank_name,
            cc.card_number_last4,
            s.statement_date,
            s.statement_total
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.customer_id = 6
        ORDER BY cc.bank_name, cc.card_number_last4, s.statement_date
    ''')
    
    statements = cursor.fetchall()
    
    print('=' * 120)
    print('CHEOK JUN YOON - 完整交易验证报告')
    print('=' * 120)
    print()
    
    total_errors = 0
    verified_statements = []
    
    for stmt_id, bank, card, date, total in statements:
        result = verify_statement(cursor, stmt_id, bank, card, date)
        if result:
            verified_statements.append(result)
            
            status = '✅' if result['matches'] else '❌'
            print(f"{status} {bank:<20} *{card:<6} {date:<12} | "
                  f"客户: RM {result['customer_spend']:>10,.2f} - RM {result['customer_payment']:>10,.2f} = RM {result['customer_balance']:>10,.2f} | "
                  f"INFINITE: RM {result['infinite_spend']:>10,.2f} - RM {result['infinite_payment']:>10,.2f} = RM {result['infinite_balance']:>10,.2f}")
            
            if not result['matches']:
                print(f"   ⚠️  计算总额: RM {result['calculated_total']:,.2f} != 账单总额: RM {result['stmt_total']:,.2f} (差异: RM {abs(result['calculated_total'] - result['stmt_total']):,.2f})")
                total_errors += 1
    
    print()
    print('=' * 120)
    print(f"验证完成：共 {len(verified_statements)} 个账单，{total_errors} 个错误")
    print('=' * 120)
    print()
    
    # 汇总所有客户余额和INFINITE余额
    if verified_statements:
        # 按卡片分组获取最新余额
        card_balances = {}
        for result in verified_statements:
            card_key = f"{result['bank']} *{result['card']}"
            if card_key not in card_balances or result['date'] > card_balances[card_key]['date']:
                card_balances[card_key] = result
        
        print('📊 最新余额汇总（按信用卡）：')
        print(f"{'信用卡':<30} {'客户余额':<20} {'INFINITE余额':<20}")
        print('-' * 70)
        
        total_customer = 0
        total_infinite = 0
        
        for card_name, result in sorted(card_balances.items()):
            print(f"{card_name:<30} RM {result['customer_balance']:>15,.2f} RM {result['infinite_balance']:>15,.2f}")
            total_customer += result['customer_balance']
            total_infinite += result['infinite_balance']
        
        print('-' * 70)
        print(f"{'总计':<30} RM {total_customer:>15,.2f} RM {total_infinite:>15,.2f}")
        print()
        
        # 详细列出有错误的账单
        if total_errors > 0:
            print()
            print('❌ 发现以下账单有计算错误，需要手动检查：')
            print()
            
            for result in verified_statements:
                if not result['matches']:
                    print(f"\n{'='*100}")
                    print(f"📄 {result['bank']} *{result['card']} - {result['date']}")
                    print(f"{'='*100}")
                    print(f"Previous Balance: RM {result['prev_balance']:,.2f}")
                    print(f"Statement Total (账单): RM {result['stmt_total']:,.2f}")
                    print(f"Calculated Total (计算): RM {result['calculated_total']:,.2f}")
                    print(f"差异: RM {abs(result['calculated_total'] - result['stmt_total']):,.2f}")
                    print()
                    
                    print("客户交易：")
                    print(f"  消费 ({len(result['customer_purchases'])}笔): RM {result['customer_spend']:,.2f}")
                    for txn in result['customer_purchases'][:5]:  # 只显示前5笔
                        print(f"    {txn['date']} - {txn['desc'][:50]}: RM {txn['amount']:,.2f}")
                    if len(result['customer_purchases']) > 5:
                        print(f"    ... 及其他 {len(result['customer_purchases']) - 5} 笔")
                    
                    print(f"  付款 ({len(result['customer_payments'])}笔): RM {result['customer_payment']:,.2f}")
                    for txn in result['customer_payments']:
                        print(f"    {txn['date']} - {txn['desc'][:50]}: RM {txn['amount']:,.2f}")
                    
                    print(f"  余额: RM {result['customer_balance']:,.2f}")
                    print()
                    
                    print("INFINITE交易：")
                    print(f"  供应商消费 ({len(result['infinite_purchases'])}笔): RM {result['infinite_spend']:,.2f}")
                    for txn in result['infinite_purchases']:
                        print(f"    {txn['date']} - {txn['supplier']}: {txn['desc'][:50]}: RM {txn['amount']:,.2f}")
                    
                    print(f"  付款 ({len(result['infinite_payments'])}笔): RM {result['infinite_payment']:,.2f}")
                    for txn in result['infinite_payments'][:5]:  # 只显示前5笔
                        print(f"    {txn['date']} - {txn['desc'][:50]}: RM {txn['amount']:,.2f}")
                    if len(result['infinite_payments']) > 5:
                        print(f"    ... 及其他 {len(result['infinite_payments']) - 5} 笔")
                    
                    print(f"  手续费 (1%): RM {result['supplier_fee']:,.2f}")
                    print(f"  余额: RM {result['infinite_balance']:,.2f}")
    
    conn.close()

if __name__ == '__main__':
    main()
