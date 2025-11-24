#!/usr/bin/env python3
"""
快速修复：仅处理明显错误的minimum_payment值
重点修复OCBC、UOB、HSBC等银行的重复值
"""

import sqlite3
import os
from pdf_field_extractor import PDFFieldExtractor

def quick_fix():
    """快速修复重复的minimum_payment值"""
    db_path = 'db/smart_loan_manager.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找OCBC所有minimum_payment=20的记录
    cursor.execute('''
        SELECT 
            s.id, s.file_path, cc.bank_name, s.minimum_payment
        FROM statements s
        INNER JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.bank_name = 'OCBC' AND s.minimum_payment = 20.0
        ORDER BY s.id
    ''')
    
    ocbc_records = cursor.fetchall()
    print(f"\n修复OCBC记录：{len(ocbc_records)}条")
    
    extractor = PDFFieldExtractor()
    updated = 0
    
    for record in ocbc_records:
        stmt_id = record['id']
        pdf_path = record['file_path']
        
        if pdf_path and os.path.exists(pdf_path) and pdf_path.endswith('.pdf'):
            try:
                pdf_data = extractor.extract_fields(pdf_path, 'OCBC')
                pdf_min = pdf_data.get('minimum_payment')
                
                if pdf_min:
                    min_float = float(pdf_min)
                    cursor.execute('UPDATE statements SET minimum_payment = ? WHERE id = ?', (min_float, stmt_id))
                    print(f"  ✅ Statement {stmt_id}: RM20.0 → RM{min_float}")
                    updated += 1
            except Exception as e:
                print(f"  ❌ Statement {stmt_id}: {e}")
    
    # 修复UOB
    cursor.execute('''
        SELECT 
            s.id, s.file_path, cc.bank_name, s.minimum_payment
        FROM statements s
        INNER JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.bank_name = 'UOB' AND s.minimum_payment = 50.0
        ORDER BY s.id
    ''')
    
    uob_records = cursor.fetchall()
    print(f"\n修复UOB记录：{len(uob_records)}条")
    
    for record in uob_records:
        stmt_id = record['id']
        pdf_path = record['file_path']
        
        if pdf_path and os.path.exists(pdf_path) and pdf_path.endswith('.pdf'):
            try:
                pdf_data = extractor.extract_fields(pdf_path, 'UOB')
                pdf_min = pdf_data.get('minimum_payment')
                
                if pdf_min:
                    min_float = float(pdf_min)
                    cursor.execute('UPDATE statements SET minimum_payment = ? WHERE id = ?', (min_float, stmt_id))
                    print(f"  ✅ Statement {stmt_id}: RM50.0 → RM{min_float}")
                    updated += 1
            except Exception as e:
                print(f"  ❌ Statement {stmt_id}: {e}")
    
    # 修复HSBC异常值（25000.0显然不对）
    cursor.execute('''
        SELECT 
            s.id, s.file_path, cc.bank_name, s.minimum_payment
        FROM statements s
        INNER JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.bank_name = 'HSBC' AND s.minimum_payment > 20000
        ORDER BY s.id
    ''')
    
    hsbc_records = cursor.fetchall()
    print(f"\n修复HSBC异常记录：{len(hsbc_records)}条")
    
    for record in hsbc_records:
        stmt_id = record['id']
        pdf_path = record['file_path']
        
        if pdf_path and os.path.exists(pdf_path) and pdf_path.endswith('.pdf'):
            try:
                pdf_data = extractor.extract_fields(pdf_path, 'HSBC')
                pdf_min = pdf_data.get('minimum_payment')
                
                if pdf_min:
                    min_float = float(pdf_min)
                    cursor.execute('UPDATE statements SET minimum_payment = ? WHERE id = ?', (min_float, stmt_id))
                    print(f"  ✅ Statement {stmt_id}: RM{record['minimum_payment']} → RM{min_float}")
                    updated += 1
            except Exception as e:
                print(f"  ❌ Statement {stmt_id}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 总共更新了 {updated} 条记录")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    quick_fix()
