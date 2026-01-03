#!/usr/bin/env python3
"""测试处理单个账单"""

import os
import json
from pathlib import Path
from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account
from main import StatementProcessor

# 配置
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_LOCATION", "us")
PROCESSOR_ID = os.getenv("GOOGLE_PROCESSOR_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# 测试文件
TEST_PDF = "./static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf"

print("=" * 80)
print("测试处理单个账单")
print("=" * 80)
print(f"PDF: {TEST_PDF}\n")

# 初始化 Document AI
print("步骤1: 初始化 Document AI...", end=" ")
try:
    credentials_dict = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    client = documentai.DocumentProcessorServiceClient(credentials=credentials)
    print("成功 ✅")
except Exception as e:
    print(f"失败 ❌ - {e}")
    exit(1)

# 解析 PDF
print("步骤2: 调用 Document AI 解析 PDF...", end=" ")
try:
    with open(TEST_PDF, 'rb') as f:
        pdf_content = f.read()
    
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    
    raw_document = documentai.RawDocument(
        content=pdf_content,
        mime_type="application/pdf"
    )
    
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document
    )
    
    result = client.process_document(request=request)
    document = result.document
    
    print(f"成功 ✅ (提取了 {len(document.entities)} 个实体)")
    
except Exception as e:
    print(f"失败 ❌ - {e}")
    exit(1)

# 转换为 JSON
print("步骤3: 转换为 JSON 格式...", end=" ")
doc_ai_json = {
    "text": document.text,
    "entities": []
}

for entity in document.entities:
    entity_dict = {
        "type": entity.type_,
        "mentionText": entity.mention_text,
        "confidence": entity.confidence
    }
    
    if entity.properties:
        entity_dict["properties"] = [
            {
                "type": prop.type_,
                "mentionText": prop.mention_text
            }
            for prop in entity.properties
        ]
    
    doc_ai_json["entities"].append(entity_dict)

print("成功 ✅")

# 后处理
print("步骤4: 后处理系统...", end=" ")
try:
    processor = StatementProcessor()
    result = processor.process(doc_ai_json)
    print("成功 ✅\n")
    
    # 显示结果
    print("=" * 80)
    print("提取结果")
    print("=" * 80)
    print(f"银行名称: {result.get('bank_name', 'N/A')}")
    print(f"客户姓名: {result.get('customer_name', 'N/A')}")
    print(f"身份证号: {result.get('ic_no', 'N/A')}")
    print(f"卡类型: {result.get('card_type', 'N/A')}")
    print(f"卡号: {result.get('card_no', 'N/A')}")
    print(f"信用额度: RM{result.get('credit_limit', 0):.2f}")
    print(f"账单日期: {result.get('statement_date', 'N/A')}")
    print(f"到期日期: {result.get('payment_due_date', 'N/A')}")
    print(f"上期余额: RM{result.get('previous_balance', 0):.2f}")
    print(f"本期余额: RM{result.get('current_balance', 0):.2f}")
    print(f"最低还款: RM{result.get('minimum_payment', 0):.2f}")
    print(f"交易数量: {len(result.get('transactions', []))}")
    
    # 余额验证
    balance_check = result.get('balance_verification', {})
    print(f"\n余额验证: {balance_check.get('status', 'N/A')}")
    if balance_check.get('status') == 'PASS':
        print("  ✅ 余额一致性验证通过")
    else:
        print(f"  ❌ 差异: RM{balance_check.get('difference', 0):.2f}")
    
    print("\n✅ 测试成功！脚本可以正常工作。")
    
except Exception as e:
    print(f"失败 ❌ - {e}")
    import traceback
    traceback.print_exc()
    exit(1)
