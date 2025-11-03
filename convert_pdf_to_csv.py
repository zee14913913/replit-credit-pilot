#!/usr/bin/env python3
"""
将PDF银行月结单转换为CSV（模拟前端PDF.js行为）
"""
import pdfplumber
import csv
import io
import re
from decimal import Decimal

def clean_amount(text):
    """清理金额文本"""
    if not text or text.strip() == '':
        return ''
    # 移除逗号和空格
    cleaned = text.replace(',', '').replace(' ', '').strip()
    return cleaned

def extract_transactions_from_pdf(pdf_path):
    """从PDF提取交易记录"""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"  📄 处理第 {page_num}/{len(pdf.pages)} 页...")
            
            # 提取表格
            tables = page.extract_tables()
            
            for table in tables:
                if not table:
                    continue
                
                # 查找表头行
                header_row = None
                data_start_idx = 0
                
                for idx, row in enumerate(table):
                    if row and any('Date' in str(cell) or 'Tarikh' in str(cell) for cell in row if cell):
                        header_row = row
                        data_start_idx = idx + 1
                        break
                
                if not header_row:
                    print(f"    ⚠️  第{page_num}页未找到表头，跳过")
                    continue
                
                print(f"    ✓ 找到表头: {header_row}")
                
                # 处理数据行
                for row in table[data_start_idx:]:
                    if not row or all(not cell or str(cell).strip() == '' for cell in row):
                        continue
                    
                    # 跳过小计/总计行
                    row_text = ' '.join(str(cell) for cell in row if cell).upper()
                    if any(kw in row_text for kw in ['TOTAL', 'BALANCE FROM', 'BROUGHT FORWARD', 'PAGE NO']):
                        continue
                    
                    # 解析日期 (DD-MM-YYYY)
                    date = str(row[0]).strip() if row[0] else ''
                    if not re.match(r'^\d{2}-\d{2}-\d{4}$', date):
                        continue
                    
                    # 解析描述
                    description = ' '.join(str(cell).strip() for cell in row[1:3] if cell).strip()
                    if not description:
                        continue
                    
                    # 解析金额列（Deposit/Withdrawal/Balance）
                    deposit = ''
                    withdrawal = ''
                    balance = ''
                    
                    # 根据列数判断格式
                    if len(row) >= 5:
                        deposit = clean_amount(str(row[-3])) if row[-3] else ''
                        withdrawal = clean_amount(str(row[-2])) if row[-2] else ''
                        balance = clean_amount(str(row[-1])) if row[-1] else ''
                    elif len(row) >= 4:
                        withdrawal = clean_amount(str(row[-2])) if row[-2] else ''
                        balance = clean_amount(str(row[-1])) if row[-1] else ''
                    
                    transactions.append({
                        'Date': date,
                        'Description': description,
                        'Debit': withdrawal,
                        'Credit': deposit,
                        'Balance': balance
                    })
    
    return transactions

def pdf_to_csv(pdf_path, csv_path):
    """将PDF转换为CSV文件"""
    print(f"🔄 正在将PDF转换为CSV...")
    print(f"📂 输入: {pdf_path}")
    
    transactions = extract_transactions_from_pdf(pdf_path)
    
    if not transactions:
        print("❌ 未从PDF中提取到任何交易记录")
        return None
    
    print(f"✅ 成功提取 {len(transactions)} 条交易记录")
    
    # 写入CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for txn in transactions:
            writer.writerow(txn)
    
    print(f"📂 输出: {csv_path}")
    print(f"✅ CSV转换完成！")
    
    return csv_path

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python convert_pdf_to_csv.py <input.pdf> [output.csv]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else input_pdf.replace('.pdf', '.csv')
    
    pdf_to_csv(input_pdf, output_csv)
