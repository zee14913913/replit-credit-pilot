#!/usr/bin/env python3
"""
7家银行8字段提取测试（无ic_number）
"""
import sys
sys.path.insert(0, '.')

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

# 测试配置
TESTS = [
    {
        "bank": "AMBANK",
        "card": "9902",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-06/AMBANK_9902_2025-06-28.pdf"
    },
    {
        "bank": "AMBANK",
        "card": "6354",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_6354_2025-05-28.pdf"
    },
    {
        "bank": "HONG_LEONG",
        "card": "3964",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf"
    },
    {
        "bank": "HSBC",
        "card": "0034",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf"
    },
    {
        "bank": "OCBC",
        "card": "3506",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf"
    },
    {
        "bank": "STANDARD_CHARTERED",
        "card": "1237",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf"
    },
    {
        "bank": "UOB",
        "card": "3530",
        "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf"
    }
]

FIELDS = [
    'customer_name',
    'card_number',
    'statement_date',
    'payment_due_date',
    'previous_balance',
    'credit_limit',
    'full_due_amount',
    'minimum_payment'
]

def main():
    doc_ai = GoogleDocumentAIService()
    parser = BankSpecificParser()
    
    print("\n" + "="*100)
    print("7家银行8字段提取测试 (无ic_number)")
    print("="*100 + "\n")
    
    total_fields = 0
    extracted_fields = 0
    results = []
    
    for test in TESTS:
        bank = test['bank']
        card = test['card']
        pdf_path = test['pdf']
        
        print(f"\n{'='*100}")
        print(f"[{bank}] 卡号: {card}")
        print(f"{'='*100}")
        
        try:
            # 解析PDF
            parsed_doc = doc_ai.parse_pdf(pdf_path)
            text = parsed_doc.get('text', '')
            result = parser.parse_bank_statement(text, bank)
            fields = result.get('fields', {})
            
            # 统计字段
            missing = []
            extracted_count = 0
            
            print(f"\n📊 字段提取结果:")
            for field in FIELDS:
                value = fields.get(field, 'N/A')
                has_value = value and str(value).strip() and value != 'N/A'
                
                if has_value:
                    extracted_count += 1
                    status = "✅"
                    display_value = str(value)[:50]
                else:
                    missing.append(field)
                    status = "❌"
                    display_value = "(未提取)"
                
                print(f"  {status} {field:<20} = {display_value}")
            
            total_fields += 8
            extracted_fields += extracted_count
            percentage = (extracted_count / 8) * 100
            
            print(f"\n✅ 提取: {extracted_count}/8 ({percentage:.0f}%)")
            if missing:
                print(f"❌ 缺失: {', '.join(missing)}")
            
            results.append({
                'bank': bank,
                'card': card,
                'extracted': extracted_count,
                'missing': missing
            })
            
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            results.append({
                'bank': bank,
                'card': card,
                'extracted': 0,
                'missing': FIELDS
            })
    
    # 总结表格
    print("\n" + "="*100)
    print("总结报告")
    print("="*100 + "\n")
    
    print("| 银行 | 卡号 | 提取结果 | 完成率 | 缺失字段 |")
    print("|------|------|---------|--------|---------|")
    
    for r in results:
        missing_str = ', '.join(r['missing']) if r['missing'] else '无'
        percentage = (r['extracted'] / 8) * 100
        emoji = "🏆" if r['extracted'] == 8 else "⭐" if r['extracted'] >= 6 else "🔧"
        print(f"| {emoji} {r['bank']:<20} | {r['card']} | **{r['extracted']}/8** | **{percentage:.0f}%** | {missing_str} |")
    
    overall_percentage = (extracted_fields / total_fields) * 100
    print(f"\n🎯 **总体完成率: {extracted_fields}/{total_fields} ({overall_percentage:.1f}%)**")
    
    if overall_percentage >= 80:
        print("\n✅ **达标！系统已就绪生产！** 🎉")
    else:
        print(f"\n⚠️ 距离80%目标还差{80-overall_percentage:.1f}%")

if __name__ == "__main__":
    main()
