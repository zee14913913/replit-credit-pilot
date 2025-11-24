#!/usr/bin/env python3
"""
Google Document AI 测试脚本
快速测试单个PDF解析
"""
import os
import sys
from services.google_document_ai_service import GoogleDocumentAIService
from services.ai_pdf_parser import AIBankStatementParser


def test_single_pdf():
    """测试单个PDF解析"""
    
    print("="*80)
    print("🧪 Google Document AI 单文件测试")
    print("="*80)
    
    # 检查环境变量
    required_vars = [
        'GOOGLE_DOCUMENT_AI_API_KEY',
        'GOOGLE_PROJECT_ID',
        'GOOGLE_LOCATION',
        'GOOGLE_PROCESSOR_ID'
    ]
    
    print("\n📋 检查环境变量...")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:10] + '...' if len(value) > 10 else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: 未设置")
            sys.exit(1)
    
    # 初始化服务
    try:
        print("\n⏳ 初始化服务...")
        google_ai = GoogleDocumentAIService()
        ai_parser = AIBankStatementParser()
        print("✅ 服务初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
    
    # 测试文件
    test_file = 'docparser_templates/sample_pdfs/1_AMBANK.pdf'
    
    if not os.path.exists(test_file):
        print(f"\n❌ 测试文件不存在: {test_file}")
        sys.exit(1)
    
    print(f"\n📄 测试文件: {test_file}")
    print("-"*80)
    
    try:
        # 解析PDF
        print("\n⏳ 正在调用Google Document AI...")
        parsed_json = google_ai.parse_pdf(test_file)
        print("✅ API调用成功")
        
        # 提取字段
        print("\n⏳ 提取账单字段...")
        fields = google_ai.extract_bank_statement_fields(parsed_json)
        
        # AI识别银行
        print("\n⏳ AI识别银行...")
        text = ai_parser.extract_text_from_pdf(test_file)
        bank_code = ai_parser.detect_bank(text)
        
        # 显示结果
        print("\n" + "="*80)
        print("📊 解析结果")
        print("="*80)
        
        print(f"\n🏦 银行: {bank_code or 'N/A'}")
        print(f"💳 卡号: {fields.get('card_number', 'N/A')}")
        print(f"📅 账单日期: {fields.get('statement_date', 'N/A')}")
        print(f"👤 持卡人: {fields.get('cardholder_name', 'N/A')}")
        
        print(f"\n💰 余额信息:")
        print(f"   上期结余: RM {fields.get('previous_balance', 0):.2f}")
        print(f"   本期消费: RM {fields.get('total_debit', 0):.2f}")
        print(f"   本期还款: RM {fields.get('total_credit', 0):.2f}")
        print(f"   本期结余: RM {fields.get('current_balance', 0):.2f}")
        print(f"   最低还款: RM {fields.get('minimum_payment', 0):.2f}")
        
        transactions = fields.get('transactions', [])
        print(f"\n📝 交易明细: {len(transactions)} 笔")
        
        if transactions:
            print("\n前5笔交易:")
            for i, trans in enumerate(transactions[:5], 1):
                print(f"   {i}. {trans.get('date', 'N/A')} - {trans.get('description', 'N/A')[:40]} - RM {trans.get('amount', 0):.2f} ({trans.get('type', 'N/A')})")
        
        print("\n" + "="*80)
        print("✅ 测试成功！Google Document AI工作正常")
        print("="*80)
        
        print("\n💡 下一步:")
        print("   运行批量处理: python3 batch_parse_google_ai.py")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_single_pdf()
