"""
调试分类逻辑
"""

SUPPLIERS = [
    "7SL",
    "Dinas",
    "Raub Syc Hainan",
    "Ai Smart Tech",
    "HUAWEI",
    "PasarRaya",
    "Puchong Herbs"
]

test_descriptions = [
    ("Lazada Topup KUALA LUMPUR MY", False),  # DR
    ("AI SMART TECH", False),  # DR
    ("PAYMENT VIA RPP RECEIVED - THANK YOU, CH", True),  # CR
    ("Balance Transfer - 0 11th/12 (RM650)", False),  # DR
]

print("="*100)
print("分类逻辑调试")
print("="*100)

for desc, is_credit in test_descriptions:
    desc_upper = desc.upper()
    
    print(f"\n描述: {desc}")
    print(f"  类型: {'CR' if is_credit else 'DR'}")
    
    if not is_credit:  # DR交易
        matched = False
        for supplier in SUPPLIERS:
            if supplier.upper() in desc_upper:
                print(f"  ✅ 匹配Supplier: {supplier}")
                print(f"  分类: GZ")
                matched = True
                break
        if not matched:
            print(f"  ❌ 未匹配任何Supplier")
            print(f"  分类: Owner")
    else:  # CR交易
        owner_cr_keywords = ['PAYMENT', 'BAYARAN', 'THANK YOU', 'TERIMA KASIH']
        matched = False
        for keyword in owner_cr_keywords:
            if keyword in desc_upper:
                print(f"  ✅ 匹配关键词: {keyword}")
                print(f"  分类: Owner")
                matched = True
                break
        if not matched:
            print(f"  ❌ 未匹配任何关键词")
            print(f"  分类: GZ")

print("\n" + "="*100)
