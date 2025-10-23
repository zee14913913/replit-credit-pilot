#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('db/smart_loan_manager.db')
cursor = conn.cursor()

# 查询Chang Choon Chow的所有账单
cursor.execute('''
    SELECT 
        s.id,
        c.bank_name,
        c.card_number_last4,
        s.statement_date,
        s.total_amount_due,
        s.transaction_count,
        s.validation_status
    FROM credit_card_statements s
    JOIN credit_cards c ON s.card_id = c.id
    WHERE c.customer_id = 10
    ORDER BY s.statement_date DESC
''')

statements = cursor.fetchall()
conn.close()

print("="*80)
print(f"📋 Chang Choon Chow 的信用卡账单 (共 {len(statements)} 份)")
print("="*80)

for stmt in statements:
    print(f"\n账单ID: {stmt[0]}")
    print(f"  银行: {stmt[1]} ****{stmt[2]}")
    print(f"  日期: {stmt[3]}")
    print(f"  应付金额: RM {stmt[4]:,.2f}")
    print(f"  交易数: {stmt[5]}")
    print(f"  验证状态: {stmt[6]}")

print("\n" + "="*80)
print(f"✅ 总计: {len(statements)} 份账单已成功上传并处理")
print("="*80)
