#!/usr/bin/env python3
"""
完整解析Cheok Jun Yoon的41份信用卡账单
提取16字段 + CR/DR分类 + Owner/GZ分类
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

# 定义7家银行的所有PDF文件
PDF_FILES = {
    'AMBANK': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-06/AMBANK_9902_2025-06-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-07/AMBANK_9902_2025-07-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-08/AMBANK_9902_2025-08-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-09/AMBANK_9902_2025-09-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-10/AMBANK_9902_2025-10-28.pdf',
    ],
    'AMBANK_ISLAMIC': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-06/AmBank_6354_2025-06-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-07/AmBank_6354_2025-07-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-08/AmBank_6354_2025-08-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-09/AmBank_6354_2025-09-28.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-10/AmBank_6354_2025-10-28.pdf',
    ],
    'HONG_LEONG': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-07/HONG_LEONG_3964_2025-07-16.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-08/HONG_LEONG_3964_2025-08-16.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-09/HONG_LEONG_3964_2025-09-16.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-10/HONG_LEONG_3964_2025-10-16.pdf',
    ],
    'HSBC': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-07/HSBC_0034_2025-07-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-08/HSBC_0034_2025-08-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-09/HSBC_0034_2025-09-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf',
    ],
    'OCBC': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-06/OCBC_3506_2025-06-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-07/OCBC_3506_2025-07-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-08/OCBC_3506_2025-08-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-09/OCBC_3506_2025-09-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-10/OCBC_3506_2025-10-13.pdf',
    ],
    'STANDARD_CHARTERED': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-06/STANDARD_CHARTERED_1237_2025-06-15.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-07/STANDARD_CHARTERED_1237_2025-07-14.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-08/STANDARD_CHARTERED_1237_2025-08-14.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-09/STANDARD_CHARTERED_1237_2025-09-14.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-10/STANDARD_CHARTERED_1237_2025-10-14.pdf',
    ],
    'UOB': [
        'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-06/UOB_3530_2025-06-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-07/UOB_3530_2025-07-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-08/UOB_3530_2025-08-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-09/UOB_3530_2025-09-13.pdf',
        'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-10/UOB_8387_2025-10-13.pdf',
    ],
}

# 16个必需字段
REQUIRED_FIELDS = [
    'bank_name', 'customer_name', 'ic_no', 'card_type', 'card_no',
    'credit_limit', 'statement_date', 'payment_due_date', 'full_due_amount',
    'minimum_payment', 'previous_balance', 'transaction_date', 'description',
    'amount_CR', 'amount_DR', 'earned_point'
]

def parse_bank(bank_name, pdf_files, doc_ai, parser):
    """解析单个银行的所有账单"""
    print(f"\n{'='*100}")
    print(f"🏦 开始解析: {bank_name} ({len(pdf_files)}份账单)")
    print(f"{'='*100}")
    
    results = []
    total_transactions = 0
    total_cr_transactions = 0
    total_dr_transactions = 0
    total_gz_transactions = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        month = pdf_path.split('/')[-2]
        
        print(f"\n[{idx}/{len(pdf_files)}] 📄 {month}/{filename}")
        
        if not os.path.exists(pdf_path):
            print(f"  ❌ 文件不存在，跳过")
            continue
        
        try:
            # 使用Google Document AI解析PDF
            parsed_doc = doc_ai.parse_pdf(pdf_path)
            text = parsed_doc.get('text', '')
            
            # 使用bank-specific parser提取字段
            result = parser.parse_bank_statement(text, bank_name)
            
            # 提取字段
            fields = result.get('fields', {})
            transactions = result.get('transactions', [])
            
            # 统计字段提取率
            extracted_count = sum(1 for f in REQUIRED_FIELDS if fields.get(f))
            field_rate = (extracted_count / len(REQUIRED_FIELDS)) * 100
            
            # 统计交易分类
            cr_count = sum(1 for t in transactions if t.get('type') == 'CR')
            dr_count = sum(1 for t in transactions if t.get('type') == 'DR')
            gz_count = sum(1 for t in transactions if t.get('classification') == 'GZ')
            owner_count = sum(1 for t in transactions if t.get('classification') == 'Owner')
            
            total_transactions += len(transactions)
            total_cr_transactions += cr_count
            total_dr_transactions += dr_count
            total_gz_transactions += gz_count
            
            # 显示结果
            print(f"  ✅ 字段提取: {extracted_count}/{len(REQUIRED_FIELDS)} ({field_rate:.1f}%)")
            print(f"  💰 交易数量: {len(transactions)} 笔 (CR: {cr_count}, DR: {dr_count})")
            print(f"  🏷️  分类: Owner {owner_count}笔 | GZ {gz_count}笔")
            
            # 保存结果
            results.append({
                'file': filename,
                'month': month,
                'bank': bank_name,
                'fields': fields,
                'field_extraction_rate': field_rate,
                'transactions': transactions,
                'transaction_count': len(transactions),
                'cr_count': cr_count,
                'dr_count': dr_count,
                'gz_count': gz_count,
                'owner_count': owner_count
            })
            
        except Exception as e:
            print(f"  ❌ 解析失败: {str(e)}")
            results.append({
                'file': filename,
                'month': month,
                'bank': bank_name,
                'error': str(e)
            })
    
    # 保存银行结果到文件
    output_file = f'parsing_results/{bank_name}_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'bank': bank_name,
            'total_statements': len(pdf_files),
            'parsed_count': len([r for r in results if 'error' not in r]),
            'total_transactions': total_transactions,
            'total_cr': total_cr_transactions,
            'total_dr': total_dr_transactions,
            'total_gz': total_gz_transactions,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*100}")
    print(f"✅ {bank_name} 解析完成！")
    print(f"   📊 账单数: {len(pdf_files)}份")
    print(f"   💰 交易总数: {total_transactions}笔")
    print(f"   📈 CR交易: {total_cr_transactions}笔 | DR交易: {total_dr_transactions}笔")
    print(f"   🏷️  GZ公司: {total_gz_transactions}笔")
    print(f"   💾 结果已保存: {output_file}")
    print(f"{'='*100}")
    
    return results

def main():
    print("="*100)
    print("CreditPilot - 41份信用卡账单完整解析系统".center(100))
    print("客户: Cheok Jun Yoon | 2025年5-10月".center(100))
    print("="*100)
    
    # 初始化服务
    doc_ai = GoogleDocumentAIService()
    parser = BankSpecificParser()
    
    # 解析所有银行
    all_results = {}
    
    for bank_name, pdf_files in PDF_FILES.items():
        results = parse_bank(bank_name, pdf_files, doc_ai, parser)
        all_results[bank_name] = results
    
    # 生成综合报告
    print("\n" + "="*100)
    print("📊 综合解析报告".center(100))
    print("="*100)
    
    total_statements = sum(len(files) for files in PDF_FILES.values())
    total_parsed = sum(len([r for r in results if 'error' not in r]) 
                      for results in all_results.values())
    
    print(f"\n✅ 总账单数: {total_statements}份")
    print(f"✅ 成功解析: {total_parsed}份")
    print(f"✅ 完成率: {(total_parsed/total_statements)*100:.1f}%")
    
    # 保存综合报告
    summary_file = 'parsing_results/comprehensive_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'customer': 'Cheok Jun Yoon',
            'period': '2025-05 to 2025-10',
            'total_statements': total_statements,
            'total_parsed': total_parsed,
            'completion_rate': (total_parsed/total_statements)*100,
            'banks': list(PDF_FILES.keys()),
            'generated_at': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 综合报告已保存: {summary_file}")
    print("="*100)

if __name__ == "__main__":
    main()
