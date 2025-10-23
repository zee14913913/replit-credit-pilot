#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('db/smart_loan_manager.db')
cursor = conn.cursor()

# 查看statements表结构
cursor.execute("PRAGMA table_info(statements)")
columns = cursor.fetchall()
print("statements表的列:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# 查询Hong Leong Bank的账单
cursor.execute('''
    SELECT 
        s.id,
        c.bank_name,
        c.card_number_last4,
        s.statement_date,
        s.current_balance
    FROM statements s
    JOIN credit_cards c ON s.card_id = c.id
    WHERE c.customer_id = 10 AND c.bank_name = 'Hong Leong Bank'
    ORDER BY s.statement_date DESC
''')

statements = cursor.fetchall()
conn.close()

print("\n" + "="*80)
print(f"✅ Chang Choon Chow - Hong Leong Bank 账单上传成功")
print("="*80)

for idx, stmt in enumerate(statements, 1):
    print(f"\n{idx}. 账单日期: {stmt[3]}")
    print(f"   {stmt[1]} ****{stmt[2]}")
    print(f"   当前余额: RM {stmt[4]:,.2f}")

print("\n" + "="*80)
print(f"📊 总计: {len(statements)} 份Hong Leong Bank账单已成功上传")
print("="*80)
