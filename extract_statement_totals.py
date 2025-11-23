#!/usr/bin/env python3
"""
专门提取Statement Total和Minimum Payment的增强脚本
"""

import sqlite3
import pdfplumber
import re
from decimal import Decimal

def extract_ambank_amounts(text):
    """从AmBank PDF提取金额"""
    data = {}
    
    # 方法1：从表格中提取（第3页格式）
    # Current Balance  Payment
    # 9,008.71         1,268.55
    pattern1 = r'Current.*?Balance.*?Payment.*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})\s+(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(pattern1, text, re.DOTALL)
    if match:
        total_str = match.group(1).replace(',', '')
        min_str = match.group(2).replace(',', '')
        try:
            data['statement_total'] = float(total_str)
            data['minimum_payment'] = float(min_str)
            return data
        except:
            pass
    
    # 方法2：分别查找（更松散的匹配）
    # Current Balance XXX
    balance_pattern = r'(?:Current\s+Balance|Baki\s+Semasa).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(balance_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['statement_total'] = float(amount_str)
        except:
            pass
    
    # Minimum Payment XXX
    min_pattern = r'(?:Minimum\s+Payment|Bayaran\s+Minimum).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(min_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['minimum_payment'] = float(amount_str)
        except:
            pass
    
    # 方法3：从Total行提取
    total_pattern = r'(?:Total|Jumlah).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})\s+(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(total_pattern, text)
    if match and 'statement_total' not in data:
        total_str = match.group(1).replace(',', '')
        min_str = match.group(2).replace(',', '')
        try:
            data['statement_total'] = float(total_str)
            data['minimum_payment'] = float(min_str)
        except:
            pass
    
    return data

def extract_uob_amounts(text):
    """从UOB PDF提取金额"""
    data = {}
    
    # UOB格式：
    # Total Amount Due (RM) XXX
    # Minimum Payment Due (RM) YYY
    total_pattern = r'(?:Total\s+Amount\s+Due|Jumlah\s+Terhutang).*?\(RM\)\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(total_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['statement_total'] = float(amount_str)
        except:
            pass
    
    min_pattern = r'(?:Minimum\s+Payment.*?Due|Bayaran\s+Minimum).*?\(RM\)\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(min_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['minimum_payment'] = float(amount_str)
        except:
            pass
    
    return data

def extract_hsbc_amounts(text):
    """从HSBC PDF提取金额"""
    data = {}
    
    # HSBC格式：
    # New Balance RM XXX
    # Minimum Payment RM YYY
    total_pattern = r'(?:New\s+Balance|Total\s+Amount\s+Due).*?RM\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(total_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['statement_total'] = float(amount_str)
        except:
            pass
    
    min_pattern = r'(?:Minimum\s+Payment).*?RM\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(min_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['minimum_payment'] = float(amount_str)
        except:
            pass
    
    return data

def extract_ocbc_amounts(text):
    """从OCBC PDF提取金额"""
    data = {}
    
    # OCBC格式：
    # Your Amount Due  RM XXX
    # Minimum Payment  RM YYY
    total_pattern = r'(?:Your\s+Amount\s+Due|Amaun\s+Anda\s+Perlu\s+Bayar).*?RM\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(total_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['statement_total'] = float(amount_str)
        except:
            pass
    
    min_pattern = r'(?:Minimum\s+Payment|Bayaran\s+Minimum).*?RM\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
    match = re.search(min_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            data['minimum_payment'] = float(amount_str)
        except:
            pass
    
    return data

def extract_amounts_from_pdf(pdf_path, bank_name):
    """从PDF中提取Statement Total和Minimum Payment"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 读取所有页面文本
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            
            # 根据银行选择解析器
            bank_upper = bank_name.upper()
            if 'AMBANK' in bank_upper:
                return extract_ambank_amounts(full_text)
            elif 'UOB' in bank_upper:
                return extract_uob_amounts(full_text)
            elif 'HSBC' in bank_upper:
                return extract_hsbc_amounts(full_text)
            elif 'OCBC' in bank_upper:
                return extract_ocbc_amounts(full_text)
            else:
                # 通用解析器 - 尝试所有方法
                for extractor in [extract_ambank_amounts, extract_uob_amounts, extract_hsbc_amounts, extract_ocbc_amounts]:
                    data = extractor(full_text)
                    if data:
                        return data
                return {}
    except Exception as e:
        print(f"  ❌ PDF解析错误：{str(e)}")
        return {}

def main():
    """主函数"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 查询所有Statement Total = 0或Minimum Payment为空的记录
    cursor.execute("""
        SELECT 
            s.id,
            s.statement_date,
            s.statement_total,
            s.minimum_payment,
            s.file_path,
            c.bank_name,
            c.card_number_last4
        FROM statements s
        JOIN credit_cards c ON s.card_id = c.id
        WHERE 
            s.statement_total = 0 
            OR s.minimum_payment IS NULL
            OR s.minimum_payment = 0
        ORDER BY s.id
    """)
    
    rows = cursor.fetchall()
    total_records = len(rows)
    
    print(f"\n{'='*100}")
    print(f"💰 开始提取 {total_records} 条记录的Statement Total和Minimum Payment")
    print(f"{'='*100}\n")
    
    updated_count = 0
    failed_count = 0
    
    for i, row in enumerate(rows, 1):
        stmt_id, stmt_date, stmt_total, min_payment, pdf_path, bank_name, last4 = row
        
        print(f"\n[{i}/{total_records}] ID: {stmt_id} | {bank_name} - ***{last4}")
        print(f"  当前值: Total=RM{stmt_total if stmt_total else 0}, MinPay={f'RM{min_payment}' if min_payment else 'NULL'}")
        
        # 提取金额
        import os
        if not os.path.exists(pdf_path):
            print(f"  ❌ PDF文件不存在")
            failed_count += 1
            continue
        
        print(f"  🔍 解析PDF...")
        amounts = extract_amounts_from_pdf(pdf_path, bank_name)
        
        if not amounts:
            print(f"  ⚠️  未能提取金额")
            failed_count += 1
            continue
        
        # 显示提取的数据
        print(f"  ✅ 提取成功：", end="")
        if 'statement_total' in amounts:
            print(f"Total=RM{amounts['statement_total']}", end=" ")
        if 'minimum_payment' in amounts:
            print(f"MinPay=RM{amounts['minimum_payment']}", end="")
        print()
        
        # 更新数据库
        updates = []
        params = []
        
        if 'statement_total' in amounts and (stmt_total == 0 or stmt_total is None):
            updates.append("statement_total = ?")
            params.append(amounts['statement_total'])
        
        if 'minimum_payment' in amounts and (min_payment is None or min_payment == 0):
            updates.append("minimum_payment = ?")
            params.append(amounts['minimum_payment'])
        
        if updates:
            params.append(stmt_id)
            sql = f"UPDATE statements SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()
            print(f"  💾 数据库已更新")
            updated_count += 1
        else:
            print(f"  ℹ️  无需更新（值已存在）")
    
    conn.close()
    
    print(f"\n{'='*100}")
    print(f"✅ 金额提取完成！")
    print(f"  📊 总记录数：{total_records}")
    print(f"  ✅ 成功更新：{updated_count}")
    print(f"  ❌ 失败/跳过：{failed_count}")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    main()
