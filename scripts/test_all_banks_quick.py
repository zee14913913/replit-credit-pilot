"""
快速测试所有7间银行的parser
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

# 测试样本
test_samples = [
    ("HONG_LEONG", "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf"),
    ("HSBC", "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf"),
    ("OCBC", "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf"),
    ("STANDARD_CHARTERED", "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf"),
    ("UOB", "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf"),
]

doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

results = {}

print("="*100)
print("快速测试所有银行parser")
print("="*100)

for bank_name, pdf_path in test_samples:
    print(f"\n{'='*100}")
    print(f"测试银行：{bank_name}")
    print(f"PDF：{pdf_path}")
    print('='*100)
    
    try:
        # 解析PDF
        parsed_doc = doc_ai.parse_pdf(pdf_path)
        text = parsed_doc.get('text', '')
        
        # 使用银行parser
        result = parser.parse_bank_statement(text, bank_name)
        
        # 显示结果
        print(f"\n📋 字段提取（{len(result['fields'])}个）:")
        for key, value in list(result['fields'].items())[:8]:
            print(f"  {key}: {value}")
        
        print(f"\n💰 交易记录：{len(result['transactions'])}笔")
        if result['transactions']:
            print("  前3笔:")
            for i, trans in enumerate(result['transactions'][:3], 1):
                dr = f"RM {trans['dr_amount']:>8}" if trans['dr_amount'] else "        -"
                cr = f"RM {trans['cr_amount']:>8}" if trans['cr_amount'] else "        -"
                print(f"  {i}. {trans['date'][:10]:10} | {trans['description'][:30]:30} | DR: {dr} | CR: {cr}")
        
        results[bank_name] = {
            'status': '✅ 成功',
            'fields': len(result['fields']),
            'transactions': len(result['transactions'])
        }
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)[:100]}")
        results[bank_name] = {
            'status': '❌ 失败',
            'error': str(e)[:50]
        }

# 汇总报告
print("\n" + "="*100)
print("📊 测试汇总")
print("="*100)

success_count = sum(1 for r in results.values() if r['status'] == '✅ 成功')
print(f"\n成功率: {success_count}/{len(test_samples)} ({success_count*100//len(test_samples)}%)")

print("\n详细结果:")
for bank_name, result in results.items():
    status = result['status']
    if status == '✅ 成功':
        print(f"  {status} {bank_name:20} | 字段: {result['fields']:2}个 | 交易: {result['transactions']:2}笔")
    else:
        print(f"  {status} {bank_name:20} | {result.get('error', 'Unknown error')}")

print("\n" + "="*100)
