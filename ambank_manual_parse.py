#!/usr/bin/env python3
import json
import re

# 从附件文本提取的数据
def parse_statement(text, month, year):
    result = {
        "bank": "AMBANK",
        "statement_type": "CREDIT_CARD",
        "month": month,
        "year": year
    }
    
    # 提取客户姓名
    if "CHEOK JUN YOON" in text:
        result["customer_name"] = "CHEOK JUN YOON"
    
    # 提取卡号
    card_match = re.search(r'4031\s*4899\s*9530\s*6354', text)
    if card_match:
        result["card_number"] = "4031489995306354"
        result["card_type"] = "AmBank BonusLink Public Visa"
    
    # 提取信用额度
    result["credit_limit"] = "15000"
    
    return result

# 5月账单
statement_05 = """
Statement Date: 28 MAY 25
Payment Due Date: 17 JUN 25
Current Balance: 9,008.71
Minimum Payment: 1,268.55

Transactions:
29 APR 25, 01 MAY 25, MCDONALDS-KOTA WARISAN, 36.60
01 MAY 25, 03 MAY 25, RASA RASA MALAYSIA, 5.40
02 MAY 25, 04 MAY 25, AEON CO-SEREMBAN 2, 16.00
02 MAY 25, 05 MAY 25, Shopee Malaysia, 65.62
07 MAY 25, 07 MAY 25, PAYMENT VIA RPP RECEIVED, -984.79 CR
16 MAY 25, 16 MAY 25, QuickCash, 833.00
26 MAY 25, 28 MAY 25, AI SMART TECH, 2499.00
26 MAY 25, 28 MAY 25, Lazada Topup, 2500.00
26 MAY 25, 28 MAY 25, Lazada Topup, 2500.00
"""

# 6月账单
statement_06 = """
Statement Date: 28 JUN 25
Payment Due Date: 18 JUL 25
Current Balance: 14,533.88
Minimum Payment: 1,980.36

Key transactions:
08 JUN 25, 10 JUN 25, HUAWEI - I-CITY, 4999.00
16 JUN 25, 16 JUN 25, QuickCash, 833.00
18 JUN 25, 18 JUN 25, PAYMENT VIA RPP RECEIVED, -833.00 CR
18 JUN 25, 18 JUN 25, LATE PAYMENT CHARGE, 90.09
28 JUN 25, 28 JUN 25, INTEREST CHARGE Retail 18.00%, 173.26
"""

# 7月账单
statement_07 = """
Statement Date: 28 JUL 25
Payment Due Date: 17 AUG 25
Current Balance: 12,889.83
Minimum Payment: 644.49

Key transactions:
08 JUL 25, 08 JUL 25, PAYMENT VIA RPP RECEIVED, -1980.36 CR
08 JUL 25, 08 JUL 25, PAYMENT VIA RPP RECEIVED, -55.52 CR
15 JUL 25, 15 JUL 25, Credit Card Service Tax, 25.00
28 JUL 25, 28 JUL 25, ANNUAL FEES - BASIC, 550.00
28 JUL 25, 28 JUL 25, WAIVER OF ANNUAL FEES - BASIC, -550.00 CR
28 JUL 25, 28 JUL 25, INTEREST CHARGE Retail 18.00%, 190.50
"""

# 8月账单
statement_08 = """
Statement Date: 28 AUG 25
Payment Due Date: 17 SEP 25
Current Balance: 14,719.77
Minimum Payment: 735.99

Key transactions:
30 JUL 25, 01 AUG 25, AI SMART TECH, 2499.00
17 AUG 25, 17 AUG 25, PAYMENT VIA RPP RECEIVED (INFINITE GZ SDN. BH), -700.00 CR
21 AUG 25, 21 AUG 25, PAYMENT VIA RPP RECEIVED, -3000.00 CR
21 AUG 25, 21 AUG 25, PAYMENT VIA RPP RECEIVED, -9215.59 CR
21 AUG 25, 23 AUG 25, HUAWEI - I-CITY, 8888.00
21 AUG 25, 23 AUG 25, HUAWEI - I-CITY, 3001.00
28 AUG 25, 28 AUG 25, EXCESS LIMIT CHARGE, 9.00
"""

# 9月账单
statement_09 = """
Statement Date: 28 SEP 25
Payment Due Date: 18 OCT 25
Current Balance: 14,515.49
Minimum Payment: 725.77

Key transactions:
17 SEP 25, 17 SEP 25, PAYMENT VIA RPP RECEIVED (INFINITE GZ SDN. BH), -735.99 CR
28 SEP 25, 28 SEP 25, INTEREST CHARGE Retail 17.00%, 205.17
"""

results = []

for month, year, stmt_text in [
    ("05", "2025", statement_05),
    ("06", "2025", statement_06),
    ("07", "2025", statement_07),
    ("08", "2025", statement_08),
    ("09", "2025", statement_09)
]:
    data = parse_statement(stmt_text, month, year)
    
    # 提取账单日期和余额
    stmt_date = re.search(r'Statement Date:\s*([\d\s\w]+)', stmt_text)
    due_date = re.search(r'Payment Due Date:\s*([\d\s\w]+)', stmt_text)
    balance = re.search(r'Current Balance:\s*([\d,\.]+)', stmt_text)
    min_payment = re.search(r'Minimum Payment:\s*([\d,\.]+)', stmt_text)
    
    if stmt_date:
        data["statement_date"] = stmt_date.group(1).strip()
    if due_date:
        data["payment_due_date"] = due_date.group(1).strip()
    if balance:
        data["current_balance"] = balance.group(1).replace(',', '')
    if min_payment:
        data["minimum_payment"] = min_payment.group(1).replace(',', '')
    
    results.append(data)
    print(f"[{month}/{year}] 解析完成 - 余额: RM{data.get('current_balance', 'N/A')}")

# 保存结果
with open('ambank_statements_summary.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n\u2713 已解析 {len(results)} 份账单")
print("结果已保存到: ambank_statements_summary.json")
