import sqlite3
import sys
sys.path.insert(0, '.')
from ingest.savings_parser import parse_gxbank_savings
from datetime import datetime
import os

conn = sqlite3.connect('db/smart_loan_manager.db')
cursor = conn.cursor()

pdfs_to_import = [
    ('attached_assets/JUL 2024_1761028205600.pdf', '2024-07'),
    ('attached_assets/AUG 2024_1761028205600.pdf', '2024-08'),
    ('attached_assets/SEPT 2024_1761028205601.pdf', '2024-09'),
    ('attached_assets/OCT 2024_1761028205601.pdf', '2024-10'),
    ('attached_assets/NOV 2024_1761028205601.pdf', '2024-11'),
    ('attached_assets/DEC 2024 _1761028205600.pdf', '2024-12'),
    ('attached_assets/JAN 2025_1761028221047.pdf', '2025-01'),
    ('attached_assets/FEB 2025_1761028221047.pdf', '2025-02'),
    ('attached_assets/MAR 2025_1761028221048.pdf', '2025-03'),
    ('attached_assets/APR 2025_1761028221045.pdf', '2025-04'),
    ('attached_assets/MAY 2025_1761028221048.pdf', '2025-05'),
    ('attached_assets/JUNE 2025_1761028221048.pdf', '2025-06'),
    ('attached_assets/JULY 2025_1761028221047.pdf', '2025-07'),
]

cursor.execute("""
    SELECT id FROM savings_accounts 
    WHERE bank_name = 'GX Bank' AND account_number_last4 = '8373'
""")
account = cursor.fetchone()

if not account:
    cursor.execute("""
        INSERT INTO savings_accounts (customer_id, bank_name, account_number_last4, account_type, account_holder_name)
        VALUES (1, 'GX Bank', '8373', 'Savings Account', 'YEO CHEE WANG')
    """)
    account_id = cursor.lastrowid
    print(f"创建新的GX Bank账户记录 (ID: {account_id})")
else:
    account_id = account[0]
    print(f"使用现有GX Bank账户 (ID: {account_id})")

total_credits = 0
total_debits = 0
total_transactions = 0

for pdf_path, statement_month in pdfs_to_import:
    if not os.path.exists(pdf_path):
        print(f"⚠️  文件不存在: {pdf_path}")
        continue
    
    print(f"\n导入 {statement_month}...")
    
    info, transactions = parse_gxbank_savings(pdf_path)
    
    if not transactions:
        print(f"  ❌ 无法解析PDF")
        continue
    
    statement_date = f"{statement_month}-01"
    
    cursor.execute("""
        INSERT INTO savings_statements 
        (savings_account_id, statement_date, file_path, file_type, total_transactions, is_processed)
        VALUES (?, ?, ?, 'pdf', ?, 1)
    """, (account_id, statement_date, pdf_path, len(transactions)))
    
    statement_id = cursor.lastrowid
    
    credits = 0
    debits = 0
    
    for txn in transactions:
        cursor.execute("""
            INSERT INTO savings_transactions 
            (savings_statement_id, transaction_date, description, 
             amount, transaction_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            statement_id,
            txn['date'],
            txn['description'],
            txn['amount'],
            txn['type'].upper()
        ))
        
        if txn['type'] == 'credit':
            credits += 1
        else:
            debits += 1
    
    total_credits += credits
    total_debits += debits
    total_transactions += len(transactions)
    
    print(f"  ✅ {statement_month}: {len(transactions)} 笔交易 (Credit: {credits}, Debit: {debits})")

conn.commit()
conn.close()

print(f"\n{'='*60}")
print(f"🎉 导入完成!")
print(f"{'='*60}")
print(f"总月份数: {len(pdfs_to_import)}")
print(f"总交易数: {total_transactions}")
print(f"  - Credit (入账): {total_credits} 笔")
print(f"  - Debit (支出): {total_debits} 笔")
print(f"{'='*60}")
