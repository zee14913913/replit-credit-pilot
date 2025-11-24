#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('db/smart_loan_manager.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 按银行统计所有记录
query = """
SELECT cc.bank_name, 
       COUNT(*) as total,
       SUM(CASE WHEN s.due_date IS NULL OR s.due_date = '' THEN 1 ELSE 0 END) as missing_due_date,
       SUM(CASE WHEN s.minimum_payment IS NULL THEN 1 ELSE 0 END) as missing_min_payment,
       COUNT(DISTINCT s.minimum_payment) as unique_min_payments,
       MIN(s.minimum_payment) as min_value,
       MAX(s.minimum_payment) as max_value
FROM statements s
JOIN credit_cards cc ON s.card_id = cc.id
GROUP BY cc.bank_name
ORDER BY cc.bank_name
"""

results = cursor.fetchall()

print("=" * 120)
print("所有银行数据质量统计")
print("=" * 120)
print(f"{'银行':<25} {'总记录':<10} {'缺due_date':<12} {'缺min_pay':<12} {'不同min值':<12} {'最小值':<15} {'最大值':<15}")
print("=" * 120)

for row in results:
    print(f"{row['bank_name']:<25} {row['total']:<10} {row['missing_due_date']:<12} {row['missing_min_payment']:<12} "
          f"{row['unique_min_payments']:<12} {row['min_value']:<15.2f} {row['max_value']:<15.2f}")

# 现在查看每个银行的具体问题记录
print("\n" + "=" * 120)
print("UOB银行记录样本")
print("=" * 120)

cursor.execute("""
SELECT s.id, s.statement_date, s.pdf_path, s.minimum_payment, s.due_date, s.statement_total
FROM statements s
JOIN credit_cards cc ON s.card_id = cc.id
WHERE cc.bank_name = 'UOB'
ORDER BY s.statement_date
LIMIT 5
""")

for row in cursor.fetchall():
    print(f"ID: {row['id']}, Date: {row['statement_date']}, Total: {row['statement_total']:.2f}, "
          f"MinPay: {row['minimum_payment']:.2f if row['minimum_payment'] else 'NULL'}, "
          f"DueDate: {row['due_date'] or 'NULL'}")
    print(f"  PDF: {row['pdf_path']}")

print("\n" + "=" * 120)
print("HSBC银行记录样本")
print("=" * 120)

cursor.execute("""
SELECT s.id, s.statement_date, s.pdf_path, s.minimum_payment, s.due_date, s.statement_total
FROM statements s
JOIN credit_cards cc ON s.card_id = cc.id
WHERE cc.bank_name = 'HSBC'
ORDER BY s.statement_date
LIMIT 5
""")

for row in cursor.fetchall():
    print(f"ID: {row['id']}, Date: {row['statement_date']}, Total: {row['statement_total']:.2f}, "
          f"MinPay: {row['minimum_payment']:.2f if row['minimum_payment'] else 'NULL'}, "
          f"DueDate: {row['due_date'] or 'NULL'}")
    print(f"  PDF: {row['pdf_path']}")

print("\n" + "=" * 120)
print("STANDARD CHARTERED银行记录样本")
print("=" * 120)

cursor.execute("""
SELECT s.id, s.statement_date, s.pdf_path, s.minimum_payment, s.due_date, s.statement_total
FROM statements s
JOIN credit_cards cc ON s.card_id = cc.id
WHERE cc.bank_name = 'STANDARD CHARTERED'
ORDER BY s.statement_date
LIMIT 5
""")

for row in cursor.fetchall():
    print(f"ID: {row['id']}, Date: {row['statement_date']}, Total: {row['statement_total']:.2f}, "
          f"MinPay: {row['minimum_payment']:.2f if row['minimum_payment'] else 'NULL'}, "
          f"DueDate: {row['due_date'] or 'NULL'}")
    print(f"  PDF: {row['pdf_path']}")

print("\n" + "=" * 120)
print("ALLIANCE BANK记录264和265")
print("=" * 120)

cursor.execute("""
SELECT s.id, s.statement_date, s.pdf_path, s.minimum_payment, s.due_date, s.statement_total
FROM statements s
JOIN credit_cards cc ON s.card_id = cc.id
WHERE cc.bank_name = 'ALLIANCE BANK' AND s.id IN (264, 265)
""")

for row in cursor.fetchall():
    print(f"ID: {row['id']}, Date: {row['statement_date']}, Total: {row['statement_total']:.2f}, "
          f"MinPay: {row['minimum_payment']:.2f if row['minimum_payment'] else 'NULL'}, "
          f"DueDate: {row['due_date'] or 'NULL'}")
    print(f"  PDF: {row['pdf_path']}")

conn.close()
