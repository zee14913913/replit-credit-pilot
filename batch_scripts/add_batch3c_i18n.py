#!/usr/bin/env python3
"""
Batch 3C i18n Script - Add translation keys for customer management forms
Adds new keys to static/i18n/en.json and static/i18n/zh.json
"""

import json
import os

# Define new translation keys
NEW_TRANSLATIONS = {
    # Edit Customer Page
    "edit_customer_info": {
        "en": "Edit Customer Information",
        "zh": "编辑客户信息"
    },
    "edit_customer_subtitle": {
        "en": "Update customer profile and payment accounts",
        "zh": "更新客户基本资料和收款账户"
    },
    "customer_name_label": {
        "en": "Customer Name",
        "zh": "客户姓名"
    },
    "email_label": {
        "en": "Email",
        "zh": "电子邮件"
    },
    "phone_number_label": {
        "en": "Phone Number",
        "zh": "电话号码"
    },
    "monthly_income_rm_label": {
        "en": "Monthly Income (RM)",
        "zh": "月收入 (RM)"
    },
    "payment_account_info": {
        "en": "Payment Account Information",
        "zh": "收款账户信息"
    },
    "for_gz_transfer": {
        "en": "For GZ transfer",
        "zh": "用于GZ转账"
    },
    "private_account_name": {
        "en": "Private Account Name",
        "zh": "私人账户名"
    },
    "private_account_number": {
        "en": "Private Account Number",
        "zh": "私人账户号码"
    },
    "company_account_name": {
        "en": "Company Account Name",
        "zh": "公司账户名"
    },
    "company_account_number": {
        "en": "Company Account Number",
        "zh": "公司账户号码"
    },
    "account_usage_note": {
        "en": "These accounts will be used for GZ transfer payments or Build transactions",
        "zh": "这些账户将用于GZ转账付款信用卡或Build流水"
    },
    "notice_label": {
        "en": "Notice:",
        "zh": "注意："
    },
    "edit_customer_warning": {
        "en": "After modifying customer information, please confirm whether credit card and statement data need to be updated.",
        "zh": "修改客户资料后，请确认信用卡和账单数据是否需要更新。"
    },
    "cancel_button": {
        "en": "Cancel",
        "zh": "取消"
    },
    "save_changes": {
        "en": "Save Changes",
        "zh": "保存修改"
    },
    
    # Add Credit Card Page
    "add_credit_card_title": {
        "en": "Add Credit Card",
        "zh": "添加信用卡"
    },
    "add_cc_for_customer": {
        "en": "Add credit card for {name}",
        "zh": "为 {name} 添加信用卡账户"
    },
    "credit_card_info": {
        "en": "Credit Card Information",
        "zh": "信用卡信息"
    },
    "day_suffix": {
        "en": "",
        "zh": "号"
    },
    "after_add_cc_hint": {
        "en": "After adding a credit card, you can upload statements for analysis",
        "zh": "添加信用卡后，您可以上传该卡的账单进行分析"
    },
    "all_info_encrypted": {
        "en": "All information will be securely encrypted",
        "zh": "所有信息将被安全加密保存"
    },
    "return_button": {
        "en": "Return",
        "zh": "返回"
    },
    "add_credit_card_button": {
        "en": "Add Credit Card",
        "zh": "添加信用卡"
    },
    "existing_credit_cards": {
        "en": "Existing Credit Cards",
        "zh": "已有信用卡"
    }
}

def add_translations():
    """Add new translations to both JSON files"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for lang in ['en', 'zh']:
        json_path = os.path.join(base_dir, 'static', 'i18n', f'{lang}.json')
        
        # Read existing translations
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count existing keys
        existing_count = len(data)
        
        # Add new translations
        added_count = 0
        for key, translations in NEW_TRANSLATIONS.items():
            if key not in data:
                data[key] = translations[lang]
                added_count += 1
                print(f"  Added '{key}': '{translations[lang]}'")
        
        # Write back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        new_count = len(data)
        print(f"\n[{lang.upper()}] Updated {json_path}")
        print(f"  Previous keys: {existing_count}")
        print(f"  Added keys: {added_count}")
        print(f"  Total keys: {new_count}\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Batch 3C i18n Translation Key Addition")
    print("=" * 60)
    add_translations()
    print("=" * 60)
    print("✅ Translation keys added successfully!")
    print("=" * 60)
