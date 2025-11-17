#!/usr/bin/env python3
"""
DocParser自动设置脚本
自动创建7家银行的Parser并上传示例PDF
"""
import os
import sys
import requests
import time
from pathlib import Path

API_KEY = os.getenv('DOCPARSER_API_KEY')
BASE_URL = 'https://api.docparser.com/v1'

# 7家银行配置
BANKS = [
    {
        'name': 'AmBank',
        'label': 'CreditPilot_AmBank_6354',
        'sample_pdf': 'docparser_templates/sample_pdfs/1_AMBANK.pdf',
        'card_last4': '6354'
    },
    {
        'name': 'AmBank Islamic',
        'label': 'CreditPilot_AmBank_Islamic_9902',
        'sample_pdf': 'docparser_templates/sample_pdfs/2_AMBANK_ISLAMIC.pdf',
        'card_last4': '9902'
    },
    {
        'name': 'Standard Chartered',
        'label': 'CreditPilot_Standard_Chartered_1237',
        'sample_pdf': 'docparser_templates/sample_pdfs/3_STANDARD_CHARTERED.pdf',
        'card_last4': '1237'
    },
    {
        'name': 'UOB',
        'label': 'CreditPilot_UOB_3530',
        'sample_pdf': 'docparser_templates/sample_pdfs/4_UOB.pdf',
        'card_last4': '3530'
    },
    {
        'name': 'Hong Leong',
        'label': 'CreditPilot_Hong_Leong_3964',
        'sample_pdf': 'docparser_templates/sample_pdfs/5_HONG_LEONG.pdf',
        'card_last4': '3964'
    },
    {
        'name': 'OCBC',
        'label': 'CreditPilot_OCBC_3506',
        'sample_pdf': 'docparser_templates/sample_pdfs/6_OCBC.pdf',
        'card_last4': '3506'
    },
    {
        'name': 'HSBC',
        'label': 'CreditPilot_HSBC_0034',
        'sample_pdf': 'docparser_templates/sample_pdfs/7_HSBC.pdf',
        'card_last4': '0034'
    }
]


def create_parser(label):
    """创建Parser"""
    headers = {'api_key': API_KEY}
    data = {'label': label}
    
    try:
        response = requests.post(
            f'{BASE_URL}/parsers',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return result.get('id'), None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        return None, str(e)


def upload_sample_document(parser_id, pdf_path):
    """上传示例PDF"""
    headers = {'api_key': API_KEY}
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f'{BASE_URL}/document/upload/{parser_id}',
                headers=headers,
                files=files,
                timeout=60
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return result.get('id'), None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        return None, str(e)


def get_existing_parsers():
    """获取已存在的Parsers"""
    headers = {'api_key': API_KEY}
    
    try:
        response = requests.get(f'{BASE_URL}/parsers', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def main():
    print('='*80)
    print('🚀 DocParser自动设置 - 7家银行Parser创建')
    print('='*80)
    
    if not API_KEY:
        print('❌ 错误：未找到DOCPARSER_API_KEY环境变量')
        sys.exit(1)
    
    # 检查现有Parsers
    print('\n📋 检查现有Parsers...')
    existing = get_existing_parsers()
    existing_labels = {p.get('label'): p.get('id') for p in existing}
    print(f'   找到 {len(existing)} 个现有Parser')
    
    results = []
    
    for i, bank in enumerate(BANKS, 1):
        print(f'\n【{i}/7】{bank["name"]} ({bank["card_last4"]})')
        print('-'*80)
        
        # 检查是否已存在
        if bank['label'] in existing_labels:
            parser_id = existing_labels[bank['label']]
            print(f'   ℹ️  Parser已存在: {parser_id}')
            results.append({
                'bank': bank['name'],
                'parser_id': parser_id,
                'status': 'already_exists'
            })
            continue
        
        # 创建Parser
        print(f'   ⏳ 创建Parser: {bank["label"]}...')
        parser_id, error = create_parser(bank['label'])
        
        if error:
            print(f'   ❌ 创建失败: {error}')
            results.append({
                'bank': bank['name'],
                'status': 'create_failed',
                'error': error
            })
            continue
        
        print(f'   ✅ Parser创建成功: {parser_id}')
        
        # 上传示例PDF
        if Path(bank['sample_pdf']).exists():
            print(f'   ⏳ 上传示例PDF...')
            time.sleep(1)  # 避免API限流
            
            doc_id, error = upload_sample_document(parser_id, bank['sample_pdf'])
            
            if error:
                print(f'   ⚠️  上传失败: {error}')
            else:
                print(f'   ✅ 示例PDF上传成功: {doc_id}')
        else:
            print(f'   ⚠️  示例PDF不存在: {bank["sample_pdf"]}')
        
        results.append({
            'bank': bank['name'],
            'parser_id': parser_id,
            'status': 'created'
        })
        
        time.sleep(1)  # API限流保护
    
    # 汇总结果
    print('\n' + '='*80)
    print('📊 设置结果汇总')
    print('='*80)
    
    created = [r for r in results if r['status'] == 'created']
    existing = [r for r in results if r['status'] == 'already_exists']
    failed = [r for r in results if r['status'] == 'create_failed']
    
    print(f'\n✅ 新创建: {len(created)} 个')
    for r in created:
        print(f'   - {r["bank"]}: {r["parser_id"]}')
    
    if existing:
        print(f'\nℹ️  已存在: {len(existing)} 个')
        for r in existing:
            print(f'   - {r["bank"]}: {r["parser_id"]}')
    
    if failed:
        print(f'\n❌ 失败: {len(failed)} 个')
        for r in failed:
            print(f'   - {r["bank"]}: {r.get("error", "Unknown error")}')
    
    print('\n' + '='*80)
    
    if len(created) + len(existing) == len(BANKS):
        print('🎉 所有7个Parser已就绪！')
        print('\n下一步：')
        print('1. 访问 https://app.docparser.com')
        print('2. 为每个Parser配置字段提取规则（使用上传的示例PDF）')
        print('3. 配置完成后，系统将自动解析所有上传的PDF')
    else:
        print('⚠️  部分Parser创建失败，请检查错误信息')
    
    print('='*80)


if __name__ == '__main__':
    main()
