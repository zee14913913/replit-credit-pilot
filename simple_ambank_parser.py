#!/usr/bin/env python3
"""
简化版AmBank账单解析器
直接使用Document AI OCR + 规则解析
"""

import json
import re
import requests
from pathlib import Path

# 账单URL
STATEMENTS = [
    ("05", "2025", "AMB-28-05-2025.pdf", "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/0a54455d-f26d-49a8-9159-0bb7767e1e18/AMB-28-05-2025.pdf"),
    ("06", "2025", "AMB-28-06-2025.pdf", "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/8712d85b-c0cd-4fd4-b2db-bd38a3c90d5b/AMB-28-06-2025.pdf"),
    ("07", "2025", "AMB-28-07-2025.pdf", "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/9d34e532-0efc-4461-8213-1d8194ffa0f3/AMB-28-07-2025.pdf"),
    ("08", "2025", "AMB-28-08-2025.pdf", "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/21822321-3a98-4e09-a93c-10a4c11472ef/AMB-28-08-2025.pdf"),
    ("09", "2025", "AMB-28-09-2025.pdf", "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/4e2251f0-b555-4d04-b898-820d8dc7ecc8/AMB-28-09-2025.pdf")
]

def extract_ambank_data_from_text(text: str, filename: str) -> dict:
    """
    从OCR文本提取AmBank账单数据
    """
    result = {
        "bank": "AMBANK",
        "statement_type": "CREDIT_CARD",
        "filename": filename
    }
    
    # 提取客户姓名
    name_match = re.search(r'([A-Z][A-Z\s]+)\s+NO\s+\d+\s+JLN', text)
    if name_match:
        result['customer_name'] = name_match.group(1).strip()
    
    # 提取卡号
    card_match = re.search(r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})', text)
    if card_match:
        result['card_number'] = card_match.group(1).replace(' ', '')
    
    # 提取账单日期
    stmt_date_match = re.search(r'Statement Date[\s\S]*?(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2})', text, re.IGNORECASE)
    if stmt_date_match:
        result['statement_date'] = stmt_date_match.group(1)
    
    # 提取到期日期
    due_date_match = re.search(r'Payment Due Date[\s\S]*?(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2})', text, re.IGNORECASE)
    if due_date_match:
        result['payment_due_date'] = due_date_match.group(1)
    
    # 提取信用额度
    credit_limit_match = re.search(r'Total Credit Limit[\s\S]*?([\.\d,]+)', text, re.IGNORECASE)
    if credit_limit_match:
        result['credit_limit'] = credit_limit_match.group(1).replace(',', '')
    
    # 提取当前余额
    balance_match = re.search(r'Current Balance[\s\S]*?([\.\d,]+)', text, re.IGNORECASE)
    if balance_match:
        result['current_balance'] = balance_match.group(1).replace(',', '')
    
    # 提取最低还款
    min_payment_match = re.search(r'Minimum Payment[\s\S]*?([\.\d,]+)', text, re.IGNORECASE)
    if min_payment_match:
        result['minimum_payment'] = min_payment_match.group(1).replace(',', '')
    
    # 提取交易记录
    transactions = []
    
    # 查找TRANSACTION DETAILS部分
    trans_section_match = re.search(r'YOUR TRANSACTION DETAILS[\s\S]+?(?:End of Transaction Details|SUB TOTAL)', text, re.IGNORECASE)
    
    if trans_section_match:
        trans_text = trans_section_match.group(0)
        
        # 匹配交易行
        # 格式: 日期 + 日期 + 描述 + 金额
        trans_pattern = r'(\d{2}\s+[A-Z]{3}\s+\d{2})\s+(\d{2}\s+[A-Z]{3}\s+\d{2})\s+([A-Z].{20,80}?)\s+([\.\d,]+(?:\s+CR)?)'  
        
        for match in re.finditer(trans_pattern, trans_text):
            trans_date = match.group(1)
            post_date = match.group(2)
            description = match.group(3).strip()
            amount_str = match.group(4)
            
            # 处理金额
            is_credit = 'CR' in amount_str
            amount = amount_str.replace('CR', '').replace(',', '').strip()
            
            try:
                amount_float = float(amount)
                if is_credit:
                    amount_float = -amount_float
                
                transactions.append({
                    "transaction_date": trans_date,
                    "posting_date": post_date,
                    "description": description,
                    "amount": amount_float
                })
            except:
                pass
    
    result['transactions'] = transactions
    result['transaction_count'] = len(transactions)
    
    return result

def main():
    print("="*80)
    print("AmBank信用卡账单批量解析 (简化版)")
    print("="*80)
    
    all_results = []
    
    for month, year, filename, url in STATEMENTS:
        print(f"\n[{month}/{year}] {filename}")
        print("-" * 80)
        
        try:
            # 下载PDF
            print(f"  • 下载PDF...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 保存PDF
            pdf_dir = Path("test_statements/ambank")
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / filename
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✓ PDF已下载 ({len(response.content)} bytes)")
            
            # 使用pdfplumber提取文本
            try:
                import pdfplumber
                
                print(f"  • 提取文本...")
                full_text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        full_text += page.extract_text() or ""
                
                print(f"  ✓ 文本已提取 ({len(full_text)} 字符)")
                
                # 解析数据
                print(f"  • 解析数据...")
                parsed_data = extract_ambank_data_from_text(full_text, filename)
                
                # 显示结果
                print(f"  ✓ 解析完成")
                print(f"    - 客户: {parsed_data.get('customer_name', 'N/A')}")
                print(f"    - 卡号: {parsed_data.get('card_number', 'N/A')[-4:] if parsed_data.get('card_number') else 'N/A'}")
                print(f"    - 账单日期: {parsed_data.get('statement_date', 'N/A')}")
                print(f"    - 当前余额: RM{parsed_data.get('current_balance', 'N/A')}")
                print(f"    - 交易数: {parsed_data.get('transaction_count', 0)}")
                
                all_results.append({
                    "month": month,
                    "year": year,
                    "data": parsed_data
                })
                
            except ImportError:
                print(f"  ✗ 需要安装pdfplumber: pip install pdfplumber")
                
        except Exception as e:
            print(f"  ✗ 错误: {str(e)}")
    
    # 保存结果
    if all_results:
        output_file = "ambank_parsed_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print(f"\n✓ 解析完成! 成功: {len(all_results)}/{len(STATEMENTS)}")
        print(f"\n结果已保存: {output_file}")
        print("="*80)
    
if __name__ == "__main__":
    main()
