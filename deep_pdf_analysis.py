#!/usr/bin/env python3
import pdfplumber
import re

# 分析每家银行的PDF样本，提取完整第一页内容
pdf_samples = {
    'UOB': 'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf',
    'HSBC': 'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf',
    'STANDARD_CHARTERED': 'attached_assets/SDC OCT _1761808054088.pdf'
}

for bank_name, pdf_path in pdf_samples.items():
    print(f"\n{'#'*120}")
    print(f"# {bank_name} - PDF完整第一页分析")
    print(f"# 文件: {pdf_path}")
    print(f"{'#'*120}\n")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            lines = text.split('\n')
            
            print(f"总行数: {len(lines)}\n")
            print("="*100)
            print("完整第一页内容 (带行号):")
            print("="*100)
            
            for i, line in enumerate(lines, 1):
                print(f"{i:4d}: {line}")
            
            print(f"\n{'='*100}")
            print(f"关键字段提取测试:")
            print('='*100)
            
            # 尝试提取statement date
            for i, line in enumerate(lines, 1):
                if 'statement date' in line.lower() or 'tarikh penyata' in line.lower():
                    print(f"Statement Date候选行 {i}: {line}")
            
            # 尝试提取due date
            for i, line in enumerate(lines, 1):
                if 'payment due' in line.lower() or 'due date' in line.lower() or 'tarikh akhir' in line.lower():
                    print(f"Due Date候选行 {i}: {line}")
            
            # 尝试提取minimum payment
            for i, line in enumerate(lines, 1):
                if 'minimum' in line.lower() and ('payment' in line.lower() or 'bayaran' in line.lower()):
                    print(f"Minimum Payment候选行 {i}: {line}")
                    # 检查下一行是否有数字
                    if i < len(lines):
                        print(f"  下一行 {i+1}: {lines[i]}")
    
    except Exception as e:
        print(f"❌ 无法读取PDF: {e}")
    
    print("\n")
