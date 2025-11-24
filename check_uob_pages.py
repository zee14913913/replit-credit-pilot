#!/usr/bin/env python3
import pdfplumber

pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf'

print(f"分析UOB PDF所有页面")
print(f"文件: {pdf_path}\n")

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}\n")
    
    for page_num, page in enumerate(pdf.pages, 1):
        text = page.extract_text()
        lines = text.split('\n')
        
        print(f"{'#'*100}")
        print(f"# Page {page_num} - 总行数: {len(lines)}")
        print(f"{'#'*100}\n")
        
        # 查找包含minimum/payment/balance的行
        found_keywords = False
        for i, line in enumerate(lines, 1):
            if any(kw in line.lower() for kw in ['minimum', 'payment', 'balance', 'amount', 'total', 'due']):
                if not found_keywords:
                    print(f"关键行:")
                    found_keywords = True
                print(f"  {i:3d}: {line}")
        
        if not found_keywords:
            print("  (无关键字)")
        print("\n")
