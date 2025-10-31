#!/usr/bin/env python3
"""
逐一手动验证每份信用卡账单
直接重新解析PDF，与数据库比对
"""

import sys
sys.path.insert(0, '.')

import sqlite3
import os
from ingest import statement_parser

def get_parser_for_bank(bank_name):
    """根据银行名称获取解析器"""
    parsers = {
        'Alliance Bank': statement_parser.parse_alliance_statement,
        'AmBank': statement_parser.parse_ambank_statement,
        'AmBank Islamic': statement_parser.parse_ambank_statement,  # 使用同一个解析器
        'HSBC': statement_parser.parse_hsbc_statement,
        'Hong Leong Bank': statement_parser.parse_hong_leong_statement,
        'Maybank': statement_parser.parse_maybank_statement,
        'OCBC': statement_parser.parse_ocbc_statement,
        'STANDARD CHARTERED': statement_parser.parse_standard_chartered_statement,
        'UOB': statement_parser.parse_uob_statement,
    }
    return parsers.get(bank_name)

# 获取所有月结单
conn = sqlite3.connect('db/smart_loan_manager.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        s.id, s.statement_date, s.file_path,
        cc.bank_name, cc.card_number_last4,
        c.name as customer_name,
        COUNT(t.id) as txn_count
    FROM statements s
    JOIN credit_cards cc ON s.card_id = cc.id
    JOIN customers c ON cc.customer_id = c.id
    LEFT JOIN transactions t ON t.statement_id = s.id
    GROUP BY s.id
    ORDER BY cc.bank_name, cc.card_number_last4, s.statement_date
""")

statements = cursor.fetchall()
total = len(statements)

print("=" * 120)
print(f"开始逐一手动验证全部{total}份信用卡账单")
print("=" * 120)

passed = 0
failed = 0

for i, stmt in enumerate(statements, 1):
    print(f"\n【验证进度: {i}/{total}】")
    print(f"  客户: {stmt['customer_name']}")
    print(f"  银行: {stmt['bank_name']} #{stmt['card_number_last4']}")
    print(f"  日期: {stmt['statement_date']}")
    print(f"  PDF: {os.path.basename(stmt['file_path']) if stmt['file_path'] else 'N/A'}")
    
    # 检查PDF存在
    if not stmt['file_path'] or not os.path.exists(stmt['file_path']):
        print(f"  ❌ PDF文件不存在")
        failed += 1
        continue
    
    # 获取数据库交易
    cursor.execute("""
        SELECT transaction_date, description, amount
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date, id
    """, (stmt['id'],))
    db_txns = cursor.fetchall()
    
    # 获取解析器
    parser = get_parser_for_bank(stmt['bank_name'])
    if not parser:
        print(f"  ❌ 未找到解析器")
        failed += 1
        continue
    
    # 重新解析PDF
    try:
        info, pdf_txns = parser(stmt['file_path'])
    except Exception as e:
        print(f"  ❌ PDF解析失败: {str(e)[:60]}")
        failed += 1
        continue
    
    # 比对
    if len(pdf_txns) != len(db_txns):
        print(f"  ❌ 交易笔数不一致: PDF={len(pdf_txns)}笔, 数据库={len(db_txns)}笔")
        failed += 1
        continue
    
    # 逐笔比对金额
    all_match = True
    for j in range(len(pdf_txns)):
        pdf = pdf_txns[j]
        db = db_txns[j]
        
        pdf_amt = pdf.get('amount', 0)
        db_amt = abs(db['amount'])
        
        if abs(pdf_amt - db_amt) > 0.01:
            print(f"  ❌ 第{j+1}笔金额不匹配: PDF=RM{pdf_amt:.2f}, DB=RM{db_amt:.2f}")
            all_match = False
            break
    
    if all_match:
        print(f"  ✅ 100%一致！{len(db_txns)}笔交易全部匹配")
        passed += 1
    else:
        failed += 1

conn.close()

print("\n" + "=" * 120)
print("验证完成！")
print("=" * 120)
print(f"  总计: {total}份")
print(f"  ✅ 通过: {passed}份 ({passed/total*100:.1f}%)")
print(f"  ❌ 失败: {failed}份 ({failed/total*100:.1f}%)")
print("=" * 120)
