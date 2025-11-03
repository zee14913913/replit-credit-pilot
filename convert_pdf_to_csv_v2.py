#!/usr/bin/env python3
"""
将PDF银行月结单转换为CSV（模拟前端PDF.js行为）
修复版本：处理多行挤在一起的情况
"""
import pdfplumber
import csv
import re

def split_column(text):
    """将文本按换行符分割成列表"""
    if not text or text.strip() == '':
        return []
    return [line.strip() for line in str(text).split('\n') if line.strip()]

def clean_amount(text):
    """清理金额文本"""
    if not text or text.strip() == '':
        return ''
    cleaned = text.replace(',', '').replace(' ', '').strip()
    return cleaned

def extract_transactions_from_pdf(pdf_path):
    """从PDF提取交易记录"""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"  📄 处理第 {page_num}/{len(pdf.pages)} 页...")
            
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                
                # 跳过表头行
                for row_idx, row in enumerate(table[1:], 1):  # 跳过第一行（表头）
                    if not row or len(row) < 3:
                        continue
                    
                    # 将每列按换行符分割
                    dates = split_column(row[0])
                    descriptions = split_column(row[1])
                    deposits = split_column(row[2]) if len(row) > 2 else []
                    withdrawals = split_column(row[3]) if len(row) > 3 else []
                    balances = split_column(row[4]) if len(row) > 4 else []
                    
                    # 处理每个日期对应的交易
                    for i, date in enumerate(dates):
                        # 验证日期格式
                        if not re.match(r'^\d{2}-\d{2}-\d{4}$', date):
                            continue
                        
                        # 获取对应的描述（可能一个日期对应多行描述）
                        desc_start = i
                        desc_end = i + 1
                        
                        # 尝试找到完整描述（直到下一个日期）
                        desc_lines = []
                        for j, desc in enumerate(descriptions[desc_start:], desc_start):
                            # 检查是否是另一个交易的开始标志
                            if j > desc_start and any(kw in desc.upper() for kw in ['FUND TRANSFER', 'CIB', 'CDM', 'INSTANT TRANSFER']):
                                break
                            desc_lines.append(desc)
                            if len(desc_lines) >= 3:  # 最多3行描述
                                break
                        
                        description = ' '.join(desc_lines).strip()
                        if not description or description.upper() in ['BALANCE FROM PREVIOUS STATEMENT']:
                            continue
                        
                        # 获取对应的金额
                        deposit = clean_amount(deposits[min(i, len(deposits)-1)]) if i < len(deposits) else ''
                        withdrawal = clean_amount(withdrawals[min(i, len(withdrawals)-1)]) if i < len(withdrawals) else ''
                        balance = clean_amount(balances[min(i, len(balances)-1)]) if i < len(balances) else ''
                        
                        # 只保留有金额的记录
                        if not (deposit or withdrawal):
                            continue
                        
                        transactions.append({
                            'Date': date,
                            'Description': description[:200],  # 限制长度
                            'Debit': withdrawal,
                            'Credit': deposit,
                            'Balance': balance
                        })
                    
                    print(f"    ✓ 第{row_idx}行提取到 {len(dates)} 个日期记录")
    
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
        print("用法: python convert_pdf_to_csv_v2.py <input.pdf> [output.csv]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else input_pdf.replace('.pdf', '.csv')
    
    pdf_to_csv(input_pdf, output_csv)
