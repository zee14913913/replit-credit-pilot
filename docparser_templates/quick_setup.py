#!/usr/bin/env python3
"""
DocParser快速配置脚本
用途：验证7个Parser是否已创建，并配置系统
"""
import os
import requests
import json

def main():
    print("="*80)
    print("DocParser 7家银行Parser配置向导")
    print("="*80)
    
    # 检查API Key
    api_key = os.getenv('DOCPARSER_API_KEY')
    if not api_key:
        print("❌ 错误：DOCPARSER_API_KEY未设置")
        return
    
    session = requests.Session()
    session.auth = (api_key, '')
    
    # 获取现有Parser列表
    print("\n📋 正在获取您的Parser列表...")
    try:
        response = session.get("https://api.docparser.com/v1/parsers")
        response.raise_for_status()
        parsers = response.json()
    except Exception as e:
        print(f"❌ 错误：{e}")
        return
    
    # 需要的7个Parser
    required_parsers = {
        'AMBANK': None,
        'AMBANK_ISLAMIC': None,
        'STANDARD_CHARTERED': None,
        'UOB': None,
        'HONG_LEONG': None,
        'OCBC': None,
        'HSBC': None
    }
    
    # 匹配现有Parser
    print(f"\n✅ 找到 {len(parsers)} 个Parser:")
    print("-"*80)
    
    for parser in parsers:
        parser_id = parser.get('id')
        parser_name = parser.get('label', '').upper().replace(' ', '_')
        
        print(f"  • {parser.get('label')} (ID: {parser_id})")
        
        # 检查是否匹配需要的Parser
        for bank in required_parsers.keys():
            if bank in parser_name:
                required_parsers[bank] = parser_id
                break
    
    print("-"*80)
    
    # 检查完成度
    print("\n🎯 Parser创建状态:")
    print("-"*80)
    
    completed = 0
    config = {}
    
    for bank, parser_id in required_parsers.items():
        if parser_id:
            print(f"  ✅ {bank:25s} → {parser_id}")
            config[bank] = parser_id
            completed += 1
        else:
            print(f"  ⬜ {bank:25s} → 尚未创建")
    
    print("-"*80)
    print(f"\n进度: {completed}/7 ({completed/7*100:.0f}%)")
    
    # 如果全部完成，生成配置文件
    if completed == 7:
        print("\n🎉 恭喜！所有Parser已创建完成！")
        print("\n正在生成配置文件...")
        
        config_content = f"""# DocParser 7家银行Parser ID配置
# 自动生成于: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

BANK_PARSERS = {{
"""
        for bank, parser_id in config.items():
            config_content += f"    '{bank}': '{parser_id}',\n"
        
        config_content += "}\n"
        
        # 保存配置
        with open('docparser_templates/parser_config.py', 'w') as f:
            f.write(config_content)
        
        print("✅ 配置文件已生成: docparser_templates/parser_config.py")
        
        # 显示下一步
        print("\n" + "="*80)
        print("🚀 下一步操作:")
        print("="*80)
        print("1. 系统已自动识别您的7个Parser")
        print("2. 配置文件已生成，可以直接使用")
        print("3. 现在客户上传PDF时会自动调用对应的Parser解析")
        print("\n测试命令:")
        print("  python3 test_docparser_parsing.py")
        
    else:
        print(f"\n⚠️  还需要创建 {7-completed} 个Parser")
        print("\n请按照以下步骤操作:")
        print("1. 打开 docparser_templates/CREATE_PARSERS_GUIDE.md")
        print("2. 按照指南创建缺少的Parser")
        print("3. 完成后重新运行本脚本验证")
        
        print("\n缺少的Parser:")
        for bank, parser_id in required_parsers.items():
            if not parser_id:
                print(f"  • {bank}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
