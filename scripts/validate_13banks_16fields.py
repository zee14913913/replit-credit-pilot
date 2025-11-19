#!/usr/bin/env python3
"""
验证所有13家银行的16字段配置完整性
Validates 16-field configuration completeness for all 13 banks
✅ 16字段 = bank_name（顶层）+ 15个patterns字段
"""
import json
import sys

# 定义15个必需patterns字段（bank_name在顶层，不在patterns中）
REQUIRED_PATTERNS_FIELDS = [
    'customer_name', 'ic_no', 'card_type', 'card_no', 
    'credit_limit', 'statement_date', 'payment_due_date', 
    'full_due_amount', 'minimum_payment', 'previous_balance',
    'transaction_date', 'description', 'amount_CR', 'amount_DR', 
    'earned_point'
]

# 定义13家银行
REQUIRED_BANKS = [
    'AMBANK', 'AMBANK_ISLAMIC', 'UOB', 'HONG_LEONG', 'OCBC', 
    'HSBC', 'STANDARD_CHARTERED', 'MAYBANK', 'AFFIN_BANK', 
    'CIMB', 'ALLIANCE_BANK', 'PUBLIC_BANK', 'RHB_BANK'
]

def validate_config():
    """验证配置文件"""
    print("="*80)
    print("13家银行16字段配置验证")
    print("16字段 = bank_name(顶层) + 15个patterns字段")
    print("="*80)
    
    # 加载配置
    try:
        with open('config/bank_parser_templates.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 无法加载配置文件: {e}")
        return False
    
    # 检查classification_rules
    if 'classification_rules' not in config:
        print("\n⚠️  警告: 缺少classification_rules全局配置！")
    else:
        suppliers = config['classification_rules'].get('suppliers', [])
        print(f"\n✅ classification_rules已配置（{len(suppliers)}个suppliers用于GZ分类）")
    
    print(f"\n📋 配置文件包含 {len([k for k in config.keys() if k != 'classification_rules'])} 家银行\n")
    
    all_valid = True
    total_fields = 0
    total_missing = 0
    
    # 验证每家银行
    for bank in REQUIRED_BANKS:
        if bank not in config:
            print(f"❌ {bank:20s} - 配置不存在！")
            all_valid = False
            total_missing += 16  # 16个字段都缺失
            continue
        
        bank_config = config[bank]
        
        # 检查顶层bank_name
        if 'bank_name' not in bank_config:
            print(f"⚠️  {bank:20s} - 缺少顶层bank_name字段")
            bank_name_exists = False
            total_missing += 1
        else:
            bank_name_exists = True
        
        # 检查patterns字段
        patterns = bank_config.get('patterns', {})
        missing = []
        
        for field in REQUIRED_PATTERNS_FIELDS:
            if field not in patterns:
                missing.append(field)
            elif not patterns[field].get('regex'):
                missing.append(f"{field}(无regex)")
        
        total_fields += 16  # 1个bank_name + 15个patterns字段
        total_missing += len(missing) + (0 if bank_name_exists else 0)  # 已在上面计数
        
        # 显示结果
        extracted_count = 16 - len(missing) - (0 if bank_name_exists else 1)
        if not missing and bank_name_exists:
            print(f"✅ {bank:20s} - 16/16 字段完整 (100%)")
        else:
            print(f"⚠️  {bank:20s} - {extracted_count}/16 字段 ({extracted_count/16*100:.1f}%)")
            if missing:
                print(f"     缺失patterns: {', '.join(missing[:5])}{' ...' if len(missing) > 5 else ''}")
            all_valid = False
    
    # 总结
    print("\n" + "="*80)
    print(f"总体完成率: {total_fields - total_missing}/{total_fields} ({(total_fields - total_missing)/total_fields*100:.1f}%)")
    print("="*80)
    
    if all_valid:
        print("\n🎉 所有13家银行配置完整！每家银行都有完整的16个字段！")
        print("   ✅ bank_name (顶层) + 15个patterns字段 = 16字段")
        return True
    else:
        print(f"\n⚠️  部分银行配置不完整，缺失 {total_missing} 个字段配置")
        return False

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
