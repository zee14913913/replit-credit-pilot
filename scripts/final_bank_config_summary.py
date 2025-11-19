#!/usr/bin/env python3
"""
最终银行配置摘要报告
"""
import json

with open('config/bank_parser_templates.json', 'r') as f:
    config = json.load(f)

print("\n" + "="*100)
print(" "*30 + "🏦 CreditPilot 银行配置系统")
print("="*100 + "\n")

# 统计数据
total_banks = len(config)
banks_with_trans = [b for b in config if 'transaction_patterns' in config[b]]
banks_without_trans = [b for b in config if 'transaction_patterns' not in config[b]]

print(f"📊 **系统总览**\n")
print(f"  ✅ 总银行数: {total_banks}家")
print(f"  🔥 支持交易提取: {len(banks_with_trans)}家")
print(f"  📋 仅账单字段: {len(banks_without_trans)}家")

# 新增的5家银行
new_banks = ['AFFIN_BANK', 'CIMB', 'ALLIANCE_BANK', 'PUBLIC_BANK', 'MAYBANK']
print(f"\n🆕 **新增银行 (5家)**: {', '.join(new_banks)}")

# 分类展示
print(f"\n{'='*100}")
print("银行分类详情")
print(f"{'='*100}\n")

print("🔥 **完整功能银行 (账单 + 交易)**\n")
for i, bank in enumerate(banks_with_trans, 1):
    bank_config = config[bank]
    field_count = len(bank_config.get('patterns', {}))
    trans_count = len(bank_config.get('transaction_patterns', {}))
    
    # 检查DR/CR配置
    has_dr_cr = 'dr_cr_detection' in bank_config.get('transaction_patterns', {})
    dr_cr_mark = "✅" if has_dr_cr else "❌"
    
    print(f"  {i}. {bank:<20} | {field_count}账单字段 | {trans_count}交易配置 | DR/CR:{dr_cr_mark}")

print(f"\n📋 **基础功能银行 (仅账单)**\n")
for i, bank in enumerate(banks_without_trans, 1):
    bank_config = config[bank]
    field_count = len(bank_config.get('patterns', {}))
    print(f"  {i}. {bank:<20} | {field_count}账单字段")

# 字段标准化检查
print(f"\n{'='*100}")
print("字段标准化检查")
print(f"{'='*100}\n")

standard_fields = [
    'customer_name', 'card_number', 'statement_date', 'payment_due_date',
    'previous_balance', 'credit_limit', 'current_balance', 'minimum_payment'
]

print("✅ **标准8字段**: " + ", ".join(standard_fields) + "\n")

for bank in config:
    patterns = config[bank].get('patterns', {})
    missing = [f for f in standard_fields if f not in patterns]
    
    if missing:
        print(f"  ⚠️  {bank}: 缺失 {', '.join(missing)}")

# 交易提取格式总结
print(f"\n{'='*100}")
print("交易提取格式总结")
print(f"{'='*100}\n")

trans_formats = {
    'AFFIN_BANK': 'DDMMYYYY DDMMYYYY Description Amount [CR]',
    'CIMB': 'DD MMM DD MMM Description Amount [CR]',
    'ALLIANCE_BANK': 'DDMMYY DDMMYY Description Amount [CR]',
    'PUBLIC_BANK': 'DD MMM DD MMM Description Amount [CR]',
    'MAYBANK': 'DDMM DDMM Description Amount [CR]'
}

for bank, format_str in trans_formats.items():
    print(f"  📝 {bank:<20}: {format_str}")

print(f"\n{'='*100}")
print("✅ 配置系统已就绪！")
print(f"{'='*100}\n")

print("📌 **下一步操作**：\n")
print("  1. 使用 BankSpecificParser().parse_bank_statement(text, bank_name)")
print("  2. 支持的bank_name: " + ", ".join(list(config.keys())[:3]) + ", ...")
print("  3. 返回结果包含: fields字典 + transactions列表\n")
