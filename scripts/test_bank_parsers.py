"""
测试7间银行的专用parser模版
验证字段提取和交易分类功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService

# 7间银行的样本PDF
BANKS = {
    "AMBANK": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf",
    "HONG_LEONG": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf",
    "HSBC": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf",
    "OCBC": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf",
    "SCB": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf",
    "UOB": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf",
}

print("="*100)
print("测试银行专用Parser模版系统")
print("="*100)

doc_ai = GoogleDocumentAIService()
results = {}

for bank_name, pdf_path in BANKS.items():
    print(f"\n{'='*100}")
    print(f"银行: {bank_name}")
    print(f"PDF: {pdf_path}")
    print(f"{'='*100}")
    
    try:
        # 解析PDF
        parsed_doc = doc_ai.parse_pdf(pdf_path)
        
        # 使用银行专用模版提取字段
        fields = doc_ai.extract_bank_statement_fields(parsed_doc, bank_name=bank_name)
        
        # 显示提取结果
        print(f"\n📋 基本字段提取:")
        print(f"  ✅ 客户名: {fields.get('cardholder_name', 'N/A')}")
        print(f"  ✅ 卡号后4位: {fields.get('card_number', 'N/A')}")
        print(f"  ✅ 账单日期: {fields.get('statement_date', 'N/A')}")
        print(f"  ✅ 到期日期: {fields.get('payment_due_date', 'N/A')}")
        print(f"  ✅ Previous Balance: RM {fields.get('previous_balance', 0):,.2f}")
        print(f"  ✅ 最低还款: RM {fields.get('minimum_payment', 0):,.2f}")
        print(f"  ✅ 本期结余: RM {fields.get('current_balance', 0):,.2f}")
        print(f"  ✅ 信用额度: RM {fields.get('credit_limit', 0):,.2f}")
        print(f"  ✅ 积分: {fields.get('reward_points', 'N/A')}")
        
        # 交易记录统计
        transactions = fields.get('transactions', [])
        print(f"\n💰 交易记录统计:")
        print(f"  总交易数: {len(transactions)}笔")
        
        if len(transactions) > 0:
            # 统计DR/CR
            dr_txns = [t for t in transactions if t.get('type') == 'DR']
            cr_txns = [t for t in transactions if t.get('type') == 'CR']
            
            print(f"  DR交易: {len(dr_txns)}笔")
            print(f"  CR交易: {len(cr_txns)}笔")
            
            # 统计分类
            owner_txns = [t for t in transactions if t.get('classification') == 'Owner']
            gz_txns = [t for t in transactions if t.get('classification') == 'GZ']
            
            print(f"\n🔖 分类统计:")
            print(f"  Owner交易: {len(owner_txns)}笔")
            print(f"  GZ交易: {len(gz_txns)}笔")
            
            # 显示前3笔交易示例
            print(f"\n📝 交易示例（前3笔）:")
            for i, txn in enumerate(transactions[:3], 1):
                dr = f"RM {txn.get('dr_amount', 0):,.2f}" if txn.get('dr_amount') else "-"
                cr = f"RM {txn.get('cr_amount', 0):,.2f}" if txn.get('cr_amount') else "-"
                print(f"  {i}. {txn.get('date')} | {txn.get('description')[:40]:40} | DR:{dr:>15} | CR:{cr:>15} | {txn.get('classification')}")
            
            results[bank_name] = {
                'success': True,
                'transactions': len(transactions),
                'dr': len(dr_txns),
                'cr': len(cr_txns),
                'owner': len(owner_txns),
                'gz': len(gz_txns)
            }
        else:
            print(f"  ❌ 未能提取交易记录")
            results[bank_name] = {'success': False, 'transactions': 0}
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        results[bank_name] = {'success': False, 'error': str(e)}

# 汇总报告
print(f"\n{'='*100}")
print("📊 测试汇总报告")
print(f"{'='*100}")

success_count = sum(1 for r in results.values() if r.get('success', False))
total_txns = sum(r.get('transactions', 0) for r in results.values() if r.get('success', False))

print(f"成功: {success_count}/{len(BANKS)}间银行")
print(f"总提取交易: {total_txns}笔")

print(f"\n详细结果:")
for bank_name, result in results.items():
    if result.get('success'):
        print(f"  ✅ {bank_name:20} | {result.get('transactions', 0):3}笔交易 (DR:{result.get('dr', 0):2}, CR:{result.get('cr', 0):2}) | Owner:{result.get('owner', 0):2}, GZ:{result.get('gz', 0):2}")
    else:
        print(f"  ❌ {bank_name:20} | 失败")

print(f"{'='*100}")
