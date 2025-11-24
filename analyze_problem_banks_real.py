#!/usr/bin/env python3
import sqlite3
import pdfplumber
from pathlib import Path

conn = sqlite3.connect('db/smart_loan_manager.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 按银行统计所有记录
query = """
SELECT cc.bank_name, 
       COUNT(*) as total,
       SUM(CASE WHEN s.due_date IS NULL OR s.due_date = '' THEN 1 ELSE 0 END) as missing_due_date,
       SUM(CASE WHEN s.minimum_payment IS NULL THEN 1 ELSE 0 END) as missing_min_payment,
       COUNT(DISTINCT s.minimum_payment) as unique_min_payments
FROM statements s
JOIN credit_cards cc ON s.card_id = cc.id
GROUP BY cc.bank_name
ORDER BY cc.bank_name
"""

results = cursor.fetchall()

print("=" * 120)
print("所有银行数据质量统计")
print("=" * 120)
print(f"{'银行':<30} {'总记录':<10} {'缺due_date':<15} {'缺min_pay':<15} {'不同min值':<15}")
print("=" * 120)

problem_banks_summary = {}
for row in results:
    print(f"{row['bank_name']:<30} {row['total']:<10} {row['missing_due_date']:<15} {row['missing_min_payment']:<15} {row['unique_min_payments']:<15}")
    if row['missing_due_date'] > 0 or row['missing_min_payment'] > 0 or row['unique_min_payments'] == 1:
        problem_banks_summary[row['bank_name']] = {
            'total': row['total'],
            'missing_due_date': row['missing_due_date'],
            'missing_min_payment': row['missing_min_payment'],
            'unique_min_payments': row['unique_min_payments']
        }

print("\n" + "=" * 120)
print("问题银行详细分析（需要修复解析器的银行）")
print("=" * 120)

for bank_name in ['UOB', 'HSBC', 'STANDARD CHARTERED', 'ALLIANCE BANK']:
    print(f"\n{'#'*120}")
    print(f"# 银行: {bank_name}")
    print(f"{'#'*120}\n")
    
    cursor.execute("""
    SELECT s.id, s.statement_date, s.file_path, s.minimum_payment, s.due_date, s.statement_total
    FROM statements s
    JOIN credit_cards cc ON s.card_id = cc.id
    WHERE cc.bank_name = ?
    ORDER BY s.statement_date
    LIMIT 3
    """, (bank_name,))
    
    records = cursor.fetchall()
    
    if not records:
        print(f"❌ 没有找到{bank_name}的记录")
        continue
    
    for record in records:
        print(f"\n{'='*100}")
        print(f"记录ID: {record['id']}")
        print(f"日期: {record['statement_date']}")
        print(f"Statement Total: RM {record['statement_total']:.2f}")
        min_pay_str = f"RM {record['minimum_payment']:.2f}" if record['minimum_payment'] else 'NULL'
        print(f"Minimum Payment: {min_pay_str}")
        print(f"Due Date: {record['due_date'] or 'NULL'}")
        print(f"文件路径: {record['file_path']}")
        print('='*100)
        
        if record['file_path'] and Path(record['file_path']).exists():
            print(f"\n📄 提取PDF中包含关键字的行:")
            try:
                with pdfplumber.open(record['file_path']) as pdf:
                    page = pdf.pages[0]
                    text = page.extract_text()
                    lines = text.split('\n')
                    
                    keywords = ['minimum', 'payment', 'due', 'date', 'amount', 'bayaran', 'tarikh', 
                               'pay by', 'payment due', 'total due', 'outstanding']
                    
                    print(f"\n关键行 (Page 1, 前80行):")
                    for i, line in enumerate(lines[:80], 1):
                        if any(kw in line.lower() for kw in keywords):
                            print(f"  Line {i:3d}: {line}")
            except Exception as e:
                print(f"❌ PDF读取失败: {e}")
        else:
            print(f"❌ PDF文件不存在")
        
        print("\n")

conn.close()

print("\n" + "=" * 120)
print("总结：需要修复的问题")
print("=" * 120)
for bank, stats in problem_banks_summary.items():
    print(f"\n{bank}:")
    if stats['missing_due_date'] > 0:
        print(f"  ❌ {stats['missing_due_date']}/{stats['total']} 条记录缺少 due_date")
    if stats['missing_min_payment'] > 0:
        print(f"  ❌ {stats['missing_min_payment']}/{stats['total']} 条记录缺少 minimum_payment")
    if stats['unique_min_payments'] == 1 and stats['total'] > 1:
        print(f"  ⚠️  所有记录使用相同的 minimum_payment 值（可能是固定默认值）")
