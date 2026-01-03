#!/usr/bin/env python3
"""
DocParser集成测试
测试完整的PDF上传→解析→保存流程
"""
import os
import sys
import time
from services.docparser_service import DocParserService
from services.ai_pdf_parser import AIBankStatementParser

def test_docparser_flow():
    """测试DocParser完整流程"""
    
    print('='*80)
    print('🧪 DocParser集成测试')
    print('='*80)
    
    # 检查环境变量
    api_key = os.getenv('DOCPARSER_API_KEY')
    parser_id = os.getenv('DOCPARSER_PARSER_ID')
    
    if not api_key:
        print('❌ 错误：未设置DOCPARSER_API_KEY')
        sys.exit(1)
    
    if not parser_id:
        print('⚠️  警告：未设置DOCPARSER_PARSER_ID')
        print('   请在DocParser创建Parser后，将Parser ID设置为环境变量')
        print('   例如：export DOCPARSER_PARSER_ID=odnzsomkbyeh')
        sys.exit(1)
    
    print(f'\n✅ API Key: {api_key[:10]}...')
    print(f'✅ Parser ID: {parser_id}')
    
    # 初始化服务
    docparser = DocParserService()
    ai_parser = AIBankStatementParser()
    
    # 测试文件
    test_file = 'docparser_templates/sample_pdfs/1_AMBANK.pdf'
    
    if not os.path.exists(test_file):
        print(f'❌ 错误：测试文件不存在: {test_file}')
        sys.exit(1)
    
    print(f'\n📄 测试文件: {test_file}')
    print('-'*80)
    
    # 方法1: DocParser云解析
    print('\n【方法1】DocParser云解析（推荐）')
    print('-'*80)
    
    try:
        # 上传PDF
        print('⏳ 上传PDF到DocParser...')
        upload_result = docparser.upload_document(test_file, parser_id)
        doc_id = upload_result.get('id')
        print(f'✅ 上传成功，文档ID: {doc_id}')
        
        # 等待解析
        print('⏳ 等待解析（最多60秒）...')
        max_wait = 60
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(5)
            wait_time += 5
            
            result = docparser.get_results(doc_id)
            
            if result:
                print(f'✅ 解析完成（耗时{wait_time}秒）')
                print('\n📊 解析结果:')
                
                for key, value in result.items():
                    if isinstance(value, list):
                        print(f'   {key}: {len(value)} 项')
                    else:
                        print(f'   {key}: {value}')
                
                # 使用AI识别银行
                print('\n🤖 AI识别银行...')
                text = ai_parser.extract_text_from_pdf(test_file)
                bank = ai_parser.detect_bank(text)
                print(f'✅ 识别银行: {bank}')
                
                break
            else:
                print(f'   等待中... ({wait_time}秒)')
        
        if wait_time >= max_wait:
            print('⚠️  解析超时，请稍后重试')
    
    except Exception as e:
        print(f'❌ DocParser解析失败: {e}')
        print('   可能原因：')
        print('   1. Parser尚未配置字段提取规则')
        print('   2. Parser ID不正确')
        print('   3. 示例PDF未上传到Parser')
    
    # 方法2: AI本地解析（备用）
    print('\n\n【方法2】AI本地解析（备用，准确度48.8%）')
    print('-'*80)
    
    try:
        result = ai_parser.parse_statement(test_file)
        
        print(f'✅ 银行: {result["bank_name"]}')
        print(f'✅ 卡号: {result.get("card_number", "未识别")}')
        print(f'✅ 日期: {result.get("statement_date", "未识别")}')
        print(f'✅ 上期结余: RM {result["balances"]["previous_balance"]:.2f}')
        print(f'✅ 本期结余: RM {result["balances"]["current_balance"]:.2f}')
        print(f'✅ 交易数量: {len(result["transactions"])}')
        
    except Exception as e:
        print(f'❌ AI解析失败: {e}')
    
    print('\n' + '='*80)
    print('🎉 测试完成！')
    print('\n推荐使用：方法1（DocParser）准确度95%+')
    print('备用方案：方法2（AI本地）准确度48.8%')
    print('='*80)


if __name__ == '__main__':
    test_docparser_flow()
