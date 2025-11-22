#!/usr/bin/env python3
"""
处理上传的VBA JSON文件
用于接收本地处理的JSON并生成最终结算报告
"""
import os
import sys
import json
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, '.')
from services.vba_json_processor import VBAJSONProcessor

def process_uploaded_json_files():
    """处理上传的JSON文件"""
    json_dir = Path('static/uploads/customers/Be_rich_CCC/vba_json_files')
    
    if not json_dir.exists():
        print(f"❌ JSON目录不存在: {json_dir}")
        print(f"请先上传JSON文件到此目录")
        return
    
    # 查找所有JSON文件
    json_files = list(json_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ 未找到JSON文件！")
        print(f"请上传JSON文件到: {json_dir}")
        return
    
    print("=" * 100)
    print(f"🔍 找到 {len(json_files)} 个JSON文件")
    print("=" * 100)
    
    # 创建处理器
    processor = VBAJSONProcessor()
    
    # 统计
    success_count = 0
    failed_count = 0
    
    # 处理每个JSON
    for idx, json_path in enumerate(json_files, 1):
        print(f"\n[{idx}/{len(json_files)}] 处理: {json_path.name}")
        
        try:
            # 读取JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                vba_json = json.load(f)
            
            # 处理
            result = processor.process_json(vba_json, user_id=1, filename=json_path.name)
            
            if result['success']:
                bank = vba_json.get('account_info', {}).get('bank', 'Unknown')
                month = vba_json.get('statement_month', 'Unknown')
                txn_count = vba_json.get('summary', {}).get('total_transactions', 0)
                
                print(f"  ✅ 成功入库: {bank} {month} - {txn_count}笔交易")
                success_count += 1
            else:
                print(f"  ❌ 入库失败: {result['message']}")
                failed_count += 1
        
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
            failed_count += 1
    
    print("\n" + "=" * 100)
    print("📊 处理完成统计")
    print("=" * 100)
    print(f"✅ 成功: {success_count} 个文件")
    print(f"❌ 失败: {failed_count} 个文件")
    print(f"📁 总计: {len(json_files)} 个文件")
    print("=" * 100)
    
    if success_count > 0:
        print("\n正在生成最终结算报告...")
        os.system('python3 scripts/generate_ccc_final_report.py')

if __name__ == '__main__':
    process_uploaded_json_files()
