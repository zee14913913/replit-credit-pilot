#!/usr/bin/env python3
"""
快速测试Google Document AI
"""
import os
from services.google_document_ai_service import GoogleDocumentAIService
from services.ai_pdf_parser import AIBankStatementParser

def quick_test():
    print("="*80)
    print("Google Document AI 快速测试")
    print("="*80)
    
    # 检查认证
    json_secret = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not json_secret:
        print("\n❌ 错误：未设置 GOOGLE_SERVICE_ACCOUNT_JSON")
        print("\n请按照以下步骤操作：")
        print("1. 访问 https://console.cloud.google.com/iam-admin/serviceaccounts")
        print("2. 创建Service Account并下载JSON")
        print("3. 将JSON内容添加到Replit Secrets")
        print("   Key: GOOGLE_SERVICE_ACCOUNT_JSON")
        print("   Value: {完整JSON内容}")
        return False
    
    print(f"\n✅ Service Account JSON已设置（{len(json_secret)} 字符）")
    
    try:
        # 初始化服务
        print("\n⏳ 初始化Google Document AI...")
        service = GoogleDocumentAIService()
        print("✅ 初始化成功")
        
        # 测试文件
        test_file = 'docparser_templates/sample_pdfs/1_AMBANK.pdf'
        
        if not os.path.exists(test_file):
            print(f"\n⚠️  测试文件不存在: {test_file}")
            return True
        
        print(f"\n📄 测试文件: {test_file}")
        print("⏳ 正在解析...")
        
        # 解析PDF
        parsed = service.parse_pdf(test_file)
        fields = service.extract_bank_statement_fields(parsed)
        
        # AI识别银行
        ai_parser = AIBankStatementParser()
        text = ai_parser.extract_text_from_pdf(test_file)
        bank = ai_parser.detect_bank(text)
        
        print("\n" + "="*80)
        print("📊 解析结果")
        print("="*80)
        print(f"\n🏦 银行: {bank or 'N/A'}")
        print(f"💳 卡号: {fields.get('card_number', 'N/A')}")
        print(f"📅 日期: {fields.get('statement_date', 'N/A')}")
        print(f"💰 上期结余: RM {fields.get('previous_balance', 0):.2f}")
        print(f"💰 本期结余: RM {fields.get('current_balance', 0):.2f}")
        print(f"📝 交易数: {len(fields.get('transactions', []))}")
        
        print("\n" + "="*80)
        print("✅ 测试成功！")
        print("\n下一步：运行批量处理")
        print("python3 batch_parse_google_ai.py")
        print("="*80)
        
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    quick_test()
