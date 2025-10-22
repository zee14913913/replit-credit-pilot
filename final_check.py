#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('db/smart_loan_manager.db')
cursor = conn.cursor()

# 先找到正确的表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%statement%'")
tables = cursor.fetchall()
print("账单相关表:", tables)

# 查询账单数据
cursor.execute('''
    SELECT 
        s.id,
        c.bank_name,
        c.card_number_last4,
        s.statement_date,
        s.total_amount_due,
        s.transaction_count
    FROM statements s
    JOIN credit_cards c ON s.card_id = c.id
    WHERE c.customer_id = 10
    ORDER BY s.statement_date DESC
''')

statements = cursor.fetchall()
conn.close()

print("\n" + "="*80)
print(f"📋 Chang Choon Chow - Hong Leong Bank 账单汇总")
print("="*80)

hlb_count = 0
for stmt in statements:
    if 'Hong Leong' in stmt[1]:
        hlb_count += 1
        print(f"\n{hlb_count}. 账单日期: {stmt[3]}")
        print(f"   卡号: {stmt[1]} ****{stmt[2]}")
        print(f"   应付金额: RM {stmt[4]:,.2f}")
        print(f"   交易数: {stmt[5]}")

print("\n" + "="*80)
print(f"✅ Hong Leong Bank 账单总数: {hlb_count} 份")
print("="*80)
