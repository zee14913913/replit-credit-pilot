#!/usr/bin/env python3
"""
测试旧的7家银行字段提取（8字段标准）
"""
import sys
sys.path.insert(0, '.')

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

# 测试配置 - 7家旧银行
TESTS = [
    {
        "bank": "AMBANK",
        "card": "9902",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-06/AMBANK_9902_2025-06-28.pdf"
    },
    {
        "bank": "UOB",
        "card": "3530",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf"
    },
    {
        "bank": "HONG_LEONG",
        "card": "3964",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf"
    },
    {
        "bank": "OCBC",
        "card": "3506",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf"
    },
    {
        "bank": "HSBC",
        "card": "0034",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf"
    },
    {
        "bank": "STANDARD_CHARTERED",
        "card": "1237",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf"
    },
    {
        "bank": "MAYBANK",
        "card": "N/A",
        "pdf": None  # 暂无测试文件
    }
]

# 8个标准字段（正确的字段名）
FIELDS = [
    'customer_name',
    'card_number',
    'statement_date',
    'payment_due_date',
    'previous_balance',
    'credit_limit',
    'full_due_amount',  # 不是current_balance!
    'minimum_payment'
]

def main():
    doc_ai = GoogleDocumentAIService()
    parser = BankSpecificParser()
    
    print("\n" + "="*100)
    print("7家旧银行 - 8字段提取测试")
    print("="*100 + "\n")
    
    print("📋 测试字段（8个）：")
    for i, field in enumerate(FIELDS, 1):
        print(f"  {i}. {field}")
    
    print(f"\n{'='*100}\n")
    
    results = []
    
    for test in TESTS:
        bank = test['bank']
        card = test['card']
        pdf_path = test['pdf']
        
        if pdf_path is None:
            # MAYBANK暂无测试文件
            results.append({
                'bank': bank,
                'extracted': 0,
                'missing': FIELDS.copy()
            })
            continue
        
        try:
            # 解析PDF
            parsed_doc = doc_ai.parse_pdf(pdf_path)
            text = parsed_doc.get('text', '')
            result = parser.parse_bank_statement(text, bank)
            fields = result.get('fields', {})
            
            # 统计字段
            missing = []
            extracted_count = 0
            
            for field in FIELDS:
                value = fields.get(field, 'N/A')
                has_value = value and str(value).strip() and value != 'N/A'
                
                if has_value:
                    extracted_count += 1
                else:
                    missing.append(field)
            
            results.append({
                'bank': bank,
                'extracted': extracted_count,
                'missing': missing
            })
            
        except Exception as e:
            print(f"❌ {bank} 解析错误: {str(e)}")
            results.append({
                'bank': bank,
                'extracted': 0,
                'missing': FIELDS.copy()
            })
    
    # 输出表格
    print("="*100)
    print("测试结果")
    print("="*100 + "\n")
    
    print("| 银行 | 字段提取 | 缺失字段 |")
    print("|------|---------|---------|")
    
    for r in results:
        missing_str = ', '.join(r['missing']) if r['missing'] else '无'
        print(f"| {r['bank']:<20} | {r['extracted']}/8 | {missing_str} |")
    
    # 总体统计
    total_extracted = sum(r['extracted'] for r in results)
    total_possible = len(results) * 8
    percentage = (total_extracted / total_possible * 100) if total_possible > 0 else 0
    
    print(f"\n{'='*100}")
    print(f"总体完成率: {total_extracted}/{total_possible} ({percentage:.1f}%)")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    main()
