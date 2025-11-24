#!/usr/bin/env python3
"""
综合银行Parser系统最终测试报告
验证所有修复是否达到目标
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser
from decimal import Decimal

print("="*100)
print("CreditPilot 银行Parser系统 - 综合最终测试报告".center(100))
print("="*100)

# 测试PDF文件列表
test_cases = [
    {
        'bank': 'AMBANK',
        'card': '9902',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-06/AMBANK_9902_2025-06-28.pdf',
        'target': {'gz_count': '>0', 'field_rate': '>50%'}
    },
    {
        'bank': 'AMBANK',
        'card': '6354',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-06/AmBank_6354_2025-06-28.pdf',
        'target': {'field_rate': '>50%'}
    },
    {
        'bank': 'HONG_LEONG',
        'card': '3964',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf',
        'target': {'field_rate': '>=60%'}
    },
    {
        'bank': 'HSBC',
        'card': '0034',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf',
        'target': {'field_rate': '>50%'}
    },
    {
        'bank': 'OCBC',
        'card': '3506',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf',
        'target': {'field_rate': '>=60%'}
    },
    {
        'bank': 'STANDARD_CHARTERED',
        'card': '1237',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-06/STANDARD_CHARTERED_1237_2025-06-15.pdf',
        'target': {'transaction_count': '>0'}
    },
    {
        'bank': 'UOB',
        'card': '3530',
        'path': 'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf',
        'target': {'field_rate': '>=60%'}
    }
]

required_fields = [
    'customer_name', 'ic_number', 'card_number', 
    'statement_date', 'payment_due_date', 'previous_balance', 
    'credit_limit'
]

doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

# 统计数据
total_field_extractions = 0
total_possible_fields = 0
total_transactions = 0
total_gz_transactions = 0
pass_count = 0
fail_count = 0

results = []

print("\n" + "="*100)
print("开始测试7家银行...")
print("="*100)

for idx, test in enumerate(test_cases, 1):
    bank = test['bank']
    card = test['card']
    pdf_path = test['path']
    target = test['target']
    
    print(f"\n{'='*100}")
    print(f"[{idx}/{len(test_cases)}] 测试银行: {bank} (卡号: {card})")
    print(f"{'='*100}")
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        fail_count += 1
        continue
    
    # 解析
    try:
        parsed_doc = doc_ai.parse_pdf(pdf_path)
        text = parsed_doc.get('text', '')
        
        result = parser.parse_bank_statement(text, bank)
        
        # 分析字段
        fields = result.get('fields', {})
        extracted_fields = []
        missing_fields = []
        
        for field in required_fields:
            value = fields.get(field)
            if value and str(value).strip() and value != 'N/A':
                extracted_fields.append(field)
            else:
                missing_fields.append(field)
        
        field_count = len(extracted_fields)
        field_pct = (field_count / 7) * 100
        
        total_field_extractions += field_count
        total_possible_fields += 7
        
        # 分析交易
        transactions = result.get('transactions', [])
        owner_count = sum(1 for t in transactions if t.get('classification') == 'Owner')
        gz_count = sum(1 for t in transactions if t.get('classification') == 'GZ')
        
        total_transactions += len(transactions)
        total_gz_transactions += gz_count
        
        # 验证目标
        pass_status = True
        reasons = []
        
        # 字段提取率目标
        if 'field_rate' in target:
            target_rate = target['field_rate']
            if '>=60%' in target_rate:
                if field_pct < 60:
                    pass_status = False
                    reasons.append(f"字段提取率{field_pct:.0f}% < 60%")
            elif '>50%' in target_rate:
                if field_pct <= 50:
                    pass_status = False
                    reasons.append(f"字段提取率{field_pct:.0f}% <= 50%")
        
        # GZ分类目标
        if 'gz_count' in target:
            if gz_count == 0:
                pass_status = False
                reasons.append(f"GZ交易数量为0")
        
        # 交易数量目标
        if 'transaction_count' in target:
            if len(transactions) == 0:
                pass_status = False
                reasons.append(f"交易数量为0")
        
        # 输出结果
        print(f"\n📊 字段提取: {field_count}/7 ({field_pct:.0f}%)")
        for field in extracted_fields:
            value = fields.get(field)
            print(f"  ✅ {field:<20} = {value}")
        for field in missing_fields:
            print(f"  ❌ {field:<20} = (未提取)")
        
        print(f"\n💰 交易记录: {len(transactions)}笔")
        print(f"   - Owner: {owner_count}笔")
        print(f"   - GZ: {gz_count}笔")
        
        # 显示部分交易
        if len(transactions) > 0:
            print(f"\n前3笔交易:")
            for i, trans in enumerate(transactions[:3], 1):
                date = trans.get('date', 'N/A')
                desc = trans.get('description', 'N/A')[:40]
                classification = trans.get('classification', 'N/A')
                trans_type = trans.get('type', 'N/A')
                print(f"  {i}. {date:<10} | {trans_type:<3} | {classification:<6} | {desc}")
        
        # 目标验证
        print(f"\n🎯 目标验证:")
        for key, val in target.items():
            if key == 'field_rate':
                print(f"   - 字段提取率: {val} → 实际{field_pct:.0f}%")
            elif key == 'gz_count':
                print(f"   - GZ分类: {val} → 实际{gz_count}笔")
            elif key == 'transaction_count':
                print(f"   - 交易数量: {val} → 实际{len(transactions)}笔")
        
        if pass_status:
            print(f"\n✅ 状态: PASS - 所有目标达成！")
            pass_count += 1
        else:
            print(f"\n❌ 状态: FAIL - 未达标")
            for reason in reasons:
                print(f"   - {reason}")
            fail_count += 1
        
        # 保存结果
        results.append({
            'bank': bank,
            'card': card,
            'field_count': field_count,
            'field_pct': field_pct,
            'transaction_count': len(transactions),
            'gz_count': gz_count,
            'pass': pass_status
        })
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        fail_count += 1

# 生成总结报告
print(f"\n{'='*100}")
print("最终总结报告".center(100))
print("="*100)

print(f"\n📊 总体统计:")
print(f"   - 测试银行数: {len(test_cases)}家")
print(f"   - 通过数: {pass_count}家 ✅")
print(f"   - 失败数: {fail_count}家 ❌")
print(f"   - 通过率: {(pass_count/len(test_cases)*100):.1f}%")

avg_field_pct = (total_field_extractions / total_possible_fields * 100) if total_possible_fields > 0 else 0
print(f"\n📋 字段提取:")
print(f"   - 总提取字段: {total_field_extractions}/{total_possible_fields}")
print(f"   - 平均完整度: {avg_field_pct:.1f}%")

print(f"\n💰 交易统计:")
print(f"   - 总交易数: {total_transactions}笔")
print(f"   - Owner分类: {total_transactions - total_gz_transactions}笔")
print(f"   - GZ分类: {total_gz_transactions}笔")

print(f"\n{'='*100}")
print("各银行详细结果")
print("="*100)
print(f"{'银行':<20} {'卡号':<10} {'字段':<15} {'交易':<10} {'GZ':<10} {'状态'}")
print("-"*100)
for r in results:
    status = "✅ PASS" if r['pass'] else "❌ FAIL"
    print(f"{r['bank']:<20} {r['card']:<10} {r['field_count']}/7 ({r['field_pct']:.0f}%){'':<5} {r['transaction_count']:<10} {r['gz_count']:<10} {status}")

# 验证总体目标
print(f"\n{'='*100}")
print("总体目标验证")
print("="*100)

objectives = [
    {
        'name': 'AMBANK GZ分类',
        'target': '>0笔',
        'actual': sum(r['gz_count'] for r in results if r['bank'] == 'AMBANK'),
        'pass': sum(r['gz_count'] for r in results if r['bank'] == 'AMBANK') > 0
    },
    {
        'name': 'OCBC字段提取率',
        'target': '>=60%',
        'actual': f"{[r['field_pct'] for r in results if r['bank'] == 'OCBC'][0]:.0f}%",
        'pass': [r['field_pct'] for r in results if r['bank'] == 'OCBC'][0] >= 60
    },
    {
        'name': 'HONG_LEONG字段提取率',
        'target': '>=60%',
        'actual': f"{[r['field_pct'] for r in results if r['bank'] == 'HONG_LEONG'][0]:.0f}%",
        'pass': [r['field_pct'] for r in results if r['bank'] == 'HONG_LEONG'][0] >= 60
    },
    {
        'name': 'UOB字段提取率',
        'target': '>=60%',
        'actual': f"{[r['field_pct'] for r in results if r['bank'] == 'UOB'][0]:.0f}%",
        'pass': [r['field_pct'] for r in results if r['bank'] == 'UOB'][0] >= 60
    },
    {
        'name': 'STANDARD_CHARTERED交易提取',
        'target': '>0笔',
        'actual': f"{sum(r['transaction_count'] for r in results if r['bank'] == 'STANDARD_CHARTERED')}笔",
        'pass': sum(r['transaction_count'] for r in results if r['bank'] == 'STANDARD_CHARTERED') > 0
    },
    {
        'name': '总体完成率',
        'target': '>=80%',
        'actual': f"{avg_field_pct:.1f}%",
        'pass': avg_field_pct >= 80
    }
]

all_pass = True
for obj in objectives:
    status = "✅ PASS" if obj['pass'] else "❌ FAIL"
    print(f"{obj['name']:<30} | 目标: {obj['target']:<10} | 实际: {str(obj['actual']):<10} | {status}")
    if not obj['pass']:
        all_pass = False

print(f"\n{'='*100}")
if all_pass:
    print("🎉 恭喜！所有目标全部达成！".center(100))
else:
    print("⚠️  部分目标未达成，需要继续修复。".center(100))
print("="*100)

# 退出码
sys.exit(0 if all_pass else 1)
