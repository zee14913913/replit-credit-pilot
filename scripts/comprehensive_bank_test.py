"""
7间银行完整测试报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser, SUPPLIERS

# 测试样本
test_samples = [
    ("AMBANK (9902)", "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf"),
    ("AmBank (6354)", "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf"),
    ("HONG_LEONG", "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf"),
    ("HSBC", "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf"),
    ("OCBC", "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf"),
    ("STANDARD_CHARTERED", "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf"),
    ("UOB", "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf"),
]

doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

results = {}

print("="*120)
print("7间银行完整测试报告".center(120))
print("="*120)

required_fields = ['customer_name', 'card_number', 'statement_date', 'payment_due_date', 
                   'previous_balance', 'minimum_payment', 'credit_limit']

for bank_name, pdf_path in test_samples:
    print(f"\n{'='*120}")
    print(f"银行：{bank_name}".center(120))
    print(f"PDF：{pdf_path}".center(120))
    print('='*120)
    
    try:
        # 解析PDF
        parsed_doc = doc_ai.parse_pdf(pdf_path)
        text = parsed_doc.get('text', '')
        
        # 检测银行
        detected_bank = bank_name.split()[0] if '(' not in bank_name else bank_name.split()[0]
        
        # 使用银行parser
        result = parser.parse_bank_statement(text, detected_bank)
        
        # 字段完整性检查
        fields = result['fields']
        field_coverage = {}
        for field in required_fields:
            field_coverage[field] = '✅' if field in fields and fields[field] else '❌'
        
        # 交易分析
        transactions = result['transactions']
        owner_count = sum(1 for t in transactions if t['classification'] == 'Owner')
        gz_count = sum(1 for t in transactions if t['classification'] == 'GZ')
        dr_count = sum(1 for t in transactions if t['dr_amount'] > 0)
        cr_count = sum(1 for t in transactions if t['cr_amount'] > 0)
        
        # 显示结果
        print(f"\n📋 字段提取（{len(fields)}/7 required）:")
        for field, status in field_coverage.items():
            value = fields.get(field, 'N/A')
            print(f"  {status} {field:20}: {str(value)[:50]}")
        
        print(f"\n💰 交易记录：{len(transactions)}笔")
        print(f"  DR交易：{dr_count}笔 | CR交易：{cr_count}笔")
        print(f"  Owner分类：{owner_count}笔 | GZ分类：{gz_count}笔")
        
        if transactions:
            print(f"\n  前3笔交易示例:")
            for i, trans in enumerate(transactions[:3], 1):
                dr = f"RM {trans['dr_amount']:>8}" if trans['dr_amount'] else "        -"
                cr = f"RM {trans['cr_amount']:>8}" if trans['cr_amount'] else "        -"
                print(f"  {i}. {trans['date'][:10]:10} | {trans['description'][:35]:35} | {trans['classification']:5} | DR: {dr} | CR: {cr}")
        
        # Supplier检查
        if gz_count > 0:
            print(f"\n  ✅ GZ分类正常（{gz_count}笔GZ交易）")
            # 显示匹配的Suppliers
            gz_trans = [t for t in transactions if t['classification'] == 'GZ']
            for trans in gz_trans[:3]:
                desc_upper = trans['description'].upper()
                matched = [s for s in SUPPLIERS if s.upper() in desc_upper]
                if matched:
                    print(f"     - {trans['description'][:40]} → 匹配Supplier: {matched[0]}")
        else:
            print(f"\n  ⚠️ 无GZ分类（可能无Supplier交易）")
        
        results[bank_name] = {
            'status': '✅',
            'fields': len(fields),
            'field_coverage': sum(1 for v in field_coverage.values() if v == '✅'),
            'transactions': len(transactions),
            'owner': owner_count,
            'gz': gz_count,
            'dr': dr_count,
            'cr': cr_count
        }
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)[:200]}")
        results[bank_name] = {
            'status': '❌',
            'error': str(e)[:100]
        }

# 汇总报告
print("\n" + "="*120)
print("📊 汇总报告".center(120))
print("="*120)

success_count = sum(1 for r in results.values() if r['status'] == '✅')
total_transactions = sum(r.get('transactions', 0) for r in results.values())
total_gz = sum(r.get('gz', 0) for r in results.values())

print(f"\n整体成功率: {success_count}/{len(test_samples)} ({success_count*100//len(test_samples)}%)")
print(f"总交易提取: {total_transactions}笔")
print(f"总GZ分类: {total_gz}笔")

print(f"\n{'银行':<25} | {'状态':^6} | {'字段覆盖':^10} | {'交易数':^8} | {'Owner':^6} | {'GZ':^6} | {'DR':^6} | {'CR':^6}")
print("-" * 120)

for bank_name, result in results.items():
    if result['status'] == '✅':
        field_cov = f"{result['field_coverage']}/7"
        print(f"{bank_name:<25} | {result['status']:^6} | {field_cov:^10} | {result['transactions']:^8} | {result['owner']:^6} | {result['gz']:^6} | {result['dr']:^6} | {result['cr']:^6}")
    else:
        print(f"{bank_name:<25} | {result['status']:^6} | {'N/A':^10} | {'N/A':^8} | {'N/A':^6} | {'N/A':^6} | {'N/A':^6} | {'N/A':^6}")

print("="*120)
