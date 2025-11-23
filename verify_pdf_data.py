#!/usr/bin/env python3
"""
从PDF原件中提取真实的Statement Date, Statement Total, Minimum Payment, Due Date
并更新数据库
"""

import sqlite3
import pdfplumber
import re
from datetime import datetime
from decimal import Decimal
import os

def extract_date(text, patterns):
    """提取日期"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            # 尝试解析多种日期格式
            for fmt in [
                "%d %b %y",
                "%d %B %y",
                "%d %b %Y",
                "%d %B %Y",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%Y-%m-%d"
            ]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%d/%m/%Y")
                except:
                    continue
    return None

def extract_amount(text, patterns):
    """提取金额"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '').strip()
            try:
                return float(amount_str)
            except:
                continue
    return None

def parse_ambank_pdf(text):
    """解析AmBank PDF"""
    data = {}
    
    # Statement Date
    stmt_date = extract_date(text, [
        r'Statement Date.*?(\d{1,2}\s+[A-Z]{3}\s+\d{2})',
        r'Tarikh Penyata\s+(\d{1,2}\s+[A-Z]{3}\s+\d{2})'
    ])
    if stmt_date:
        data['statement_date'] = stmt_date
    
    # Due Date
    due_date = extract_date(text, [
        r'Payment Due Date.*?(\d{1,2}\s+[A-Z]{3}\s+\d{2})',
        r'Tarikh Matang Bayaran\s+(\d{1,2}\s+[A-Z]{3}\s+\d{2})'
    ])
    if due_date:
        data['due_date'] = due_date
    
    # Statement Total (寻找多个可能的字段)
    total = extract_amount(text, [
        r'Total Amount Due.*?RM\s*([\d,]+\.?\d*)',
        r'Jumlah Terhutang.*?RM\s*([\d,]+\.?\d*)',
        r'New Balance.*?RM\s*([\d,]+\.?\d*)',
        r'Baki Baru.*?RM\s*([\d,]+\.?\d*)',
        r'TOTAL AMOUNT DUE\s+RM\s*([\d,]+\.?\d*)'
    ])
    if total:
        data['statement_total'] = total
    
    # Minimum Payment
    min_pay = extract_amount(text, [
        r'Minimum Payment Due.*?RM\s*([\d,]+\.?\d*)',
        r'Bayaran Minimum.*?RM\s*([\d,]+\.?\d*)',
        r'MINIMUM PAYMENT DUE\s+RM\s*([\d,]+\.?\d*)'
    ])
    if min_pay:
        data['minimum_payment'] = min_pay
    
    return data

def parse_uob_pdf(text):
    """解析UOB PDF"""
    data = {}
    
    # Statement Date
    stmt_date = extract_date(text, [
        r'Statement Date\s+(\d{1,2}\s+[A-Z]{3}\s+\d{2})',
        r'Tarikh Penyata\s+(\d{1,2}\s+[A-Z]{3}\s+\d{2})'
    ])
    if stmt_date:
        data['statement_date'] = stmt_date
    
    # Due Date
    due_date = extract_date(text, [
        r'Payment Due Date\s+(\d{1,2}\s+[A-Z]{3}\s+\d{2})',
        r'Tarikh Akhir Bayaran\s+(\d{1,2}\s+[A-Z]{3}\s+\d{2})'
    ])
    if due_date:
        data['due_date'] = due_date
    
    # Statement Total
    total = extract_amount(text, [
        r'Total Amount Due.*?RM\s*([\d,]+\.?\d*)',
        r'Jumlah Terhutang.*?RM\s*([\d,]+\.?\d*)',
        r'New Balance.*?\(RM\)\s*([\d,]+\.?\d*)',
        r'Baki Baharu.*?\(RM\)\s*([\d,]+\.?\d*)'
    ])
    if total:
        data['statement_total'] = total
    
    # Minimum Payment
    min_pay = extract_amount(text, [
        r'Minimum Payment.*?RM\s*([\d,]+\.?\d*)',
        r'Bayaran Minimum.*?RM\s*([\d,]+\.?\d*)',
        r'Minimum Payment Due.*?\(RM\)\s*([\d,]+\.?\d*)'
    ])
    if min_pay:
        data['minimum_payment'] = min_pay
    
    return data

def parse_hsbc_pdf(text):
    """解析HSBC PDF"""
    data = {}
    
    # Statement Date
    stmt_date = extract_date(text, [
        r'Statement Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        r'Date of Statement.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})'
    ])
    if stmt_date:
        data['statement_date'] = stmt_date
    
    # Due Date
    due_date = extract_date(text, [
        r'Payment Due Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        r'Due Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})'
    ])
    if due_date:
        data['due_date'] = due_date
    
    # Statement Total
    total = extract_amount(text, [
        r'New Balance.*?RM\s*([\d,]+\.?\d*)',
        r'Total Amount Due.*?RM\s*([\d,]+\.?\d*)',
        r'TOTAL AMOUNT DUE.*?RM\s*([\d,]+\.?\d*)'
    ])
    if total:
        data['statement_total'] = total
    
    # Minimum Payment
    min_pay = extract_amount(text, [
        r'Minimum Payment.*?RM\s*([\d,]+\.?\d*)',
        r'MINIMUM PAYMENT DUE.*?RM\s*([\d,]+\.?\d*)'
    ])
    if min_pay:
        data['minimum_payment'] = min_pay
    
    return data

def parse_ocbc_pdf(text):
    """解析OCBC PDF"""
    data = {}
    
    # Statement Date
    stmt_date = extract_date(text, [
        r'Statement Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        r'Tarikh Penyata.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})'
    ])
    if stmt_date:
        data['statement_date'] = stmt_date
    
    # Due Date
    due_date = extract_date(text, [
        r'Payment Due Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        r'Tarikh Akhir Bayaran.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})'
    ])
    if due_date:
        data['due_date'] = due_date
    
    # Statement Total - 从 Summary 中查找
    total = extract_amount(text, [
        r'Your Amount Due.*?RM\s*([\d,]+\.?\d*)',
        r'Amaun Anda Perlu Bayar.*?RM\s*([\d,]+\.?\d*)',
        r'Total Amount Due.*?RM\s*([\d,]+\.?\d*)',
        r'New Balance.*?RM\s*([\d,]+\.?\d*)'
    ])
    if total:
        data['statement_total'] = total
    
    # Minimum Payment
    min_pay = extract_amount(text, [
        r'Minimum Payment.*?RM\s*([\d,]+\.?\d*)',
        r'Bayaran Minimum.*?RM\s*([\d,]+\.?\d*)'
    ])
    if min_pay:
        data['minimum_payment'] = min_pay
    
    return data

def parse_hong_leong_pdf(text):
    """解析Hong Leong PDF"""
    data = {}
    
    # Statement Date
    stmt_date = extract_date(text, [
        r'Statement Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        r'Tarikh Penyata.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})'
    ])
    if stmt_date:
        data['statement_date'] = stmt_date
    
    # Due Date
    due_date = extract_date(text, [
        r'Payment Due Date.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        r'Tarikh Akhir Bayaran.*?(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})'
    ])
    if due_date:
        data['due_date'] = due_date
    
    # Statement Total
    total = extract_amount(text, [
        r'Total Amount Due.*?RM\s*([\d,]+\.?\d*)',
        r'New Balance.*?RM\s*([\d,]+\.?\d*)'
    ])
    if total:
        data['statement_total'] = total
    
    # Minimum Payment
    min_pay = extract_amount(text, [
        r'Minimum Payment.*?RM\s*([\d,]+\.?\d*)'
    ])
    if min_pay:
        data['minimum_payment'] = min_pay
    
    return data

def parse_pdf_by_bank(pdf_path, bank_name):
    """根据银行类型解析PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 读取前3页文本（通常账单信息在前几页）
            text = ""
            for i, page in enumerate(pdf.pages[:3]):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # 根据银行选择解析器
            bank_upper = bank_name.upper()
            if 'AMBANK' in bank_upper:
                return parse_ambank_pdf(text)
            elif 'UOB' in bank_upper:
                return parse_uob_pdf(text)
            elif 'HSBC' in bank_upper:
                return parse_hsbc_pdf(text)
            elif 'OCBC' in bank_upper:
                return parse_ocbc_pdf(text)
            elif 'HONG' in bank_upper or 'LEONG' in bank_upper:
                return parse_hong_leong_pdf(text)
            else:
                # 通用解析器（尝试所有模式）
                data = {}
                for parser in [parse_ambank_pdf, parse_uob_pdf, parse_hsbc_pdf, parse_ocbc_pdf, parse_hong_leong_pdf]:
                    parsed = parser(text)
                    data.update(parsed)
                return data
    except Exception as e:
        print(f"  ❌ 解析PDF失败：{str(e)}")
        return {}

def main():
    """主函数"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 查询所有需要验证的记录
    cursor.execute("""
        SELECT 
            s.id,
            s.statement_date,
            s.statement_total,
            s.minimum_payment,
            s.due_date,
            s.file_path,
            c.bank_name,
            c.card_number_last4
        FROM statements s
        JOIN credit_cards c ON s.card_id = c.id
        WHERE 
            s.statement_total = 0 
            OR s.minimum_payment IS NULL 
            OR s.minimum_payment = 0
            OR s.due_date IS NULL
        ORDER BY s.id
    """)
    
    rows = cursor.fetchall()
    total_records = len(rows)
    
    print(f"\n{'='*100}")
    print(f"🔍 开始验证 {total_records} 条记录的PDF原件")
    print(f"{'='*100}\n")
    
    updated_count = 0
    failed_count = 0
    
    for i, row in enumerate(rows, 1):
        stmt_id, stmt_date, stmt_total, min_payment, due_date, pdf_path, bank_name, last4 = row
        
        print(f"\n[{i}/{total_records}] ID: {stmt_id} | {bank_name} - ***{last4}")
        print(f"  📄 PDF: {pdf_path}")
        
        # 检查PDF文件是否存在
        if not os.path.exists(pdf_path):
            print(f"  ❌ PDF文件不存在，跳过")
            failed_count += 1
            continue
        
        # 解析PDF
        print(f"  🔍 正在解析PDF...")
        extracted_data = parse_pdf_by_bank(pdf_path, bank_name)
        
        if not extracted_data:
            print(f"  ⚠️ 未能从PDF中提取任何数据")
            failed_count += 1
            continue
        
        # 显示提取的数据
        print(f"  ✅ 提取的数据：")
        for key, value in extracted_data.items():
            print(f"     {key}: {value}")
        
        # 准备更新SQL
        updates = []
        params = []
        
        if 'statement_date' in extracted_data:
            updates.append("statement_date = ?")
            params.append(extracted_data['statement_date'])
        
        if 'statement_total' in extracted_data:
            updates.append("statement_total = ?")
            params.append(extracted_data['statement_total'])
        
        if 'minimum_payment' in extracted_data:
            updates.append("minimum_payment = ?")
            params.append(extracted_data['minimum_payment'])
        
        if 'due_date' in extracted_data:
            updates.append("due_date = ?")
            params.append(extracted_data['due_date'])
        
        if updates:
            params.append(stmt_id)
            sql = f"UPDATE statements SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()
            print(f"  💾 数据库已更新")
            updated_count += 1
        else:
            print(f"  ⚠️ 没有数据需要更新")
    
    conn.close()
    
    print(f"\n{'='*100}")
    print(f"✅ 验证完成！")
    print(f"  📊 总记录数：{total_records}")
    print(f"  ✅ 成功更新：{updated_count}")
    print(f"  ❌ 失败/跳过：{failed_count}")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    main()
