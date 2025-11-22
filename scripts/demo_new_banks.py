#!/usr/bin/env python3
"""
演示5家新银行的配置使用
"""
import sys
sys.path.insert(0, '.')
import json

with open('config/bank_parser_templates.json', 'r') as f:
    config = json.load(f)

print("\n" + "="*100)
print("5家新银行配置演示")
print("="*100 + "\n")

new_banks = ['AFFIN_BANK', 'CIMB', 'ALLIANCE_BANK', 'PUBLIC_BANK', 'MAYBANK']

for bank in new_banks:
    print(f"\n{'='*100}")
    print(f"🏦 {bank}")
    print(f"{'='*100}\n")
    
    bank_config = config[bank]
    
    # 账单字段示例
    print("📊 **账单字段Regex示例**：\n")
    patterns = bank_config['patterns']
    examples = {
        'statement_date': 'Statement Date\\s+(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})',
        'payment_due_date': 'Payment Due Date\\s+(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})',
        'credit_limit': 'Credit Limit\\s+([\\d,]+)'
    }
    
    for field, example in examples.items():
        if field in patterns:
            actual = patterns[field]['regex'][0]
            print(f"  {field}:")
            print(f"    {actual}\n")
    
    # 交易字段示例
    trans = bank_config['transaction_patterns']
    print("💰 **交易字段Regex示例**：\n")
    
    for field in ['transaction_date', 'description', 'amount']:
        if field in trans:
            regex = trans[field]['regex'][0]
            print(f"  {field}:")
            print(f"    {regex}\n")
    
    # 交易格式说明
    print("📝 **交易格式示例**：\n")
    
    examples_data = {
        'AFFIN_BANK': '16042025 06052025 HUAWEI-I-CITY SHAH ALAM MYS 28,888.00',
        'CIMB': '30 APR 28 APR MYTNB SSP-EC BANGSAR MY 298.10',
        'ALLIANCE_BANK': '181224 181224 Credit Balance Refund 4,427.95',
        'PUBLIC_BANK': '24 JAN 24 JAN Shopee Kuala Lumpur MYS 200.00',
        'MAYBANK': '2209 2109 HUAWEI - I-CITY SHAH ALAM MY 18,888.00'
    }
    
    if bank in examples_data:
        print(f"  {examples_data[bank]}\n")
        
        # 提取日期格式
        date_regex = trans['transaction_date']['regex'][0]
        if '\\d{8}' in date_regex:
            print("  日期格式: DDMMYYYY (8位数字)")
        elif '\\d{6}' in date_regex:
            print("  日期格式: DDMMYY (6位数字)")
        elif '\\d{4}' in date_regex:
            print("  日期格式: DDMM (4位数字)")
        elif '\\d{2}\\s+[A-Z]{3}' in date_regex:
            print("  日期格式: DD MMM (如: 30 APR)")

print("\n" + "="*100)
print("✅ 配置演示完成！")
print("="*100 + "\n")
