#!/usr/bin/env python3
"""
测试5家新银行的配置
"""
import sys
import json

# 读取配置文件
with open('config/bank_parser_templates.json', 'r') as f:
    config = json.load(f)

print("\n" + "="*100)
print("银行Parser配置验证报告")
print("="*100 + "\n")

new_banks = ['AFFIN_BANK', 'CIMB', 'ALLIANCE_BANK', 'PUBLIC_BANK', 'MAYBANK']
required_fields = [
    'customer_name', 'card_number', 'card_type', 'statement_date', 
    'payment_due_date', 'previous_balance', 'credit_limit', 
    'current_balance', 'minimum_payment'
]
required_trans_fields = ['transaction_date', 'description', 'amount']

print(f"📋 **5家新银行配置验证**\n")

for bank in new_banks:
    print(f"{'='*100}")
    print(f"🏦 {bank}")
    print(f"{'='*100}")
    
    if bank not in config:
        print(f"❌ 未找到配置！\n")
        continue
    
    bank_config = config[bank]
    patterns = bank_config.get('patterns', {})
    trans_patterns = bank_config.get('transaction_patterns', {})
    
    # 检查账单字段
    print(f"\n📊 账单字段配置：")
    missing_fields = []
    for field in required_fields:
        if field in patterns:
            regex_count = len(patterns[field].get('regex', []))
            print(f"  ✅ {field:<25} ({regex_count} patterns)")
        else:
            missing_fields.append(field)
            print(f"  ❌ {field:<25} (缺失)")
    
    # 检查交易字段
    print(f"\n💰 交易字段配置：")
    if trans_patterns:
        missing_trans = []
        for field in required_trans_fields:
            if field in trans_patterns:
                regex_count = len(trans_patterns[field].get('regex', []))
                print(f"  ✅ {field:<25} ({regex_count} patterns)")
            else:
                missing_trans.append(field)
                print(f"  ❌ {field:<25} (缺失)")
        
        # DR/CR检测
        if 'dr_cr_detection' in trans_patterns:
            dr_cr = trans_patterns['dr_cr_detection']
            print(f"\n🔍 DR/CR检测配置：")
            print(f"  ✅ CR关键词: {dr_cr.get('cr_keywords', [])}")
            print(f"  ✅ 负数=Credit: {dr_cr.get('negative_is_credit', False)}")
    else:
        print(f"  ❌ 未配置交易提取规则")
    
    # 总结
    field_complete = (9 - len(missing_fields)) / 9 * 100
    trans_complete = (3 - len(missing_trans)) / 3 * 100 if trans_patterns else 0
    
    print(f"\n📈 完成度：")
    print(f"  - 账单字段: {9 - len(missing_fields)}/9 ({field_complete:.0f}%)")
    print(f"  - 交易字段: {3 - len(missing_trans) if trans_patterns else 0}/3 ({trans_complete:.0f}%)")
    
    if field_complete == 100 and trans_complete == 100:
        print(f"\n✅ 状态: **完美配置** 🏆")
    elif field_complete >= 80 and trans_complete >= 80:
        print(f"\n⭐ 状态: **良好配置**")
    else:
        print(f"\n⚠️  状态: **需要优化**")
    
    print()

# 总体统计
print(f"\n{'='*100}")
print(f"总体统计")
print(f"{'='*100}\n")

total_banks = len(config)
banks_with_trans = sum(1 for b in config.values() if 'transaction_patterns' in b)

print(f"🏦 总银行数: {total_banks}")
print(f"✅ 支持交易提取: {banks_with_trans}/{total_banks}")
print(f"🆕 新增银行: {len(new_banks)}")

print(f"\n{'='*100}")
print("所有银行列表")
print(f"{'='*100}\n")

for bank_name in sorted(config.keys()):
    has_trans = "✅" if 'transaction_patterns' in config[bank_name] else "❌"
    print(f"  {has_trans} {bank_name}")

print(f"\n✅ **配置验证完成！**\n")
