#!/usr/bin/env python3
"""
端到端测试脚本：上传3个CSV文件并捕获完整JSON响应
"""
import requests
import json
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"
COMPANY_ID = 1  # 测试公司ID

def print_separator(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def upload_csv(file_path, statement_month, scenario_name):
    """上传CSV文件并返回完整响应"""
    print_separator(f"{scenario_name} - 上传文件: {file_path}")
    
    url = f"{API_BASE}/api/import/bank-statement"
    params = {
        "company_id": COMPANY_ID,
        "bank_name": "Test Bank",
        "account_number": "ACC001",
        "statement_month": statement_month
    }
    
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'text/csv')}
        
        try:
            response = requests.post(url, params=params, files=files, timeout=30)
            
            # 打印HTTP状态
            print(f"\n📊 HTTP状态码: {response.status_code}")
            
            # 打印完整JSON响应（原样贴，不要概述）
            print(f"\n📋 完整JSON响应：")
            print("-" * 80)
            try:
                json_data = response.json()
                print(json.dumps(json_data, ensure_ascii=False, indent=2))
            except:
                print(response.text)
            print("-" * 80)
            
            return {
                'status_code': response.status_code,
                'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                'text': response.text
            }
            
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            return {
                'status_code': 0,
                'error': str(e)
            }

def main():
    print("\n🚀 开始端到端测试 - 3个CSV场景")
    print(f"API地址: {API_BASE}")
    print(f"测试公司ID: {COMPANY_ID}")
    
    results = {}
    
    # 场景A：标准CSV
    results['A'] = upload_csv(
        'A_standard.csv',
        '2025-01',
        '场景A：标准CSV（10笔交易，所有字段完整）'
    )
    
    # 场景B：缺失必填字段
    results['B'] = upload_csv(
        'B_missing_rows.csv',
        '2025-02',
        '场景B：缺失必填字段（Description为空，Date为空）'
    )
    
    # 场景C：重复月份
    results['C'] = upload_csv(
        'C_duplicate_month.csv',
        '2025-01',
        '场景C：重复月份（与场景A同为2025-01）'
    )
    
    # 打印汇总
    print_separator("📊 测试汇总")
    for scenario, result in results.items():
        status = result.get('status_code', 0)
        if status == 200:
            print(f"✅ 场景{scenario}: 成功 (HTTP {status})")
        elif status == 422:
            print(f"⚠️  场景{scenario}: 验证失败 (HTTP {status})")
        elif status == 400:
            print(f"⚠️  场景{scenario}: 参数错误 (HTTP {status})")
        else:
            print(f"❌ 场景{scenario}: 失败 (HTTP {status})")
    
    print("\n" + "="*80)
    print("✅ 端到端测试完成")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
