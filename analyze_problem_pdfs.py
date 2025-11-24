#!/usr/bin/env python3
import sqlite3
import pdfplumber
from pathlib import Path

def analyze_problem_records():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT s.id, c.name as customer_name, cc.bank_name, s.statement_date, 
           s.pdf_path, s.minimum_payment, s.due_date, s.statement_total
    FROM statements s 
    JOIN credit_cards cc ON s.card_id = cc.id 
    JOIN customers c ON cc.customer_id = c.id
    WHERE (cc.bank_name = 'UOB' AND s.minimum_payment = 50.00)
       OR (cc.bank_name = 'HSBC' AND s.minimum_payment = 25000.00)
       OR (cc.bank_name = 'STANDARD CHARTERED' AND (s.due_date IS NULL OR s.due_date = ''))
       OR (cc.bank_name = 'ALLIANCE BANK' AND s.id IN (264, 265))
    ORDER BY cc.bank_name, s.statement_date
    """
    
    results = cursor.fetchall()
    
    print("=" * 100)
    print("问题银行记录分析")
    print("=" * 100)
    
    problem_banks = {}
    
    for row in results:
        bank = row['bank_name']
        if bank not in problem_banks:
            problem_banks[bank] = []
        problem_banks[bank].append(dict(row))
    
    for bank, records in problem_banks.items():
        print(f"\n{'='*100}")
        print(f"银行: {bank} - 问题记录数: {len(records)}")
        print('='*100)
        
        for record in records[:3]:
            print(f"\nID: {record['id']}")
            print(f"客户: {record['customer_name']}")
            print(f"日期: {record['statement_date']}")
            print(f"PDF路径: {record['pdf_path']}")
            print(f"Statement Total: RM {record['statement_total']:.2f}")
            print(f"Minimum Payment: RM {record['minimum_payment']:.2f if record['minimum_payment'] else 'NULL'}")
            print(f"Due Date: {record['due_date'] or 'NULL'}")
            
            pdf_path = record['pdf_path']
            if pdf_path and Path(pdf_path).exists():
                print(f"\n📄 分析PDF内容 (前3页):")
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page_num, page in enumerate(pdf.pages[:3], 1):
                            text = page.extract_text()
                            print(f"\n--- Page {page_num} ---")
                            lines = text.split('\n')
                            for i, line in enumerate(lines[:50]):
                                if any(keyword in line.lower() for keyword in ['minimum', 'payment', 'due', 'date', 'amount', 'bayaran', 'tarikh']):
                                    print(f"  [{i:3d}] {line}")
                except Exception as e:
                    print(f"❌ PDF读取失败: {e}")
            else:
                print(f"❌ PDF文件不存在: {pdf_path}")
            
            print("-" * 100)
    
    conn.close()

if __name__ == "__main__":
    analyze_problem_records()
