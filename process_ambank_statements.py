#!/usr/bin/env python3
"""
AmBank信用卡账单批量解析脚本
处理6份AmBank账单（2025年5月-9月）
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.statement_processor import StatementProcessor

# 账单文件信息
STATEMENTS = [
    {
        "month": "05",
        "year": "2025",
        "file": "AMB-28-05-2025.pdf",
        "statement_date": "28 MAY 25",
        "due_date": "17 JUN 25"
    },
    {
        "month": "06",
        "year": "2025",
        "file": "AMB-28-06-2025.pdf",
        "statement_date": "28 JUN 25",
        "due_date": "18 JUL 25"
    },
    {
        "month": "07",
        "year": "2025",
        "file": "AMB-28-07-2025.pdf",
        "statement_date": "28 JUL 25",
        "due_date": "17 AUG 25"
    },
    {
        "month": "08",
        "year": "2025",
        "file": "AMB-28-08-2025.pdf",
        "statement_date": "28 AUG 25",
        "due_date": "17 SEP 25"
    },
    {
        "month": "09",
        "year": "2025",
        "file": "AMB-28-09-2025.pdf",
        "statement_date": "28 SEP 25",
        "due_date": "18 OCT 25"
    }
]

def process_ambank_statements():
    """
    批量处理AmBank信用卡账单
    """
    print("="*80)
    print("AmBank信用卡账单批量解析")
    print("="*80)
    
    # 初始化处理器
    processor = StatementProcessor()
    
    results = []
    
    for stmt_info in STATEMENTS:
        month = stmt_info['month']
        year = stmt_info['year']
        filename = stmt_info['file']
        
        print(f"\n处理账单: {filename}")
        print("-" * 80)
        
        # 注意：这里需要实际的PDF文件路径
        # 由于附件是通过API提供的，我们需要从特定路径读取
        file_path = f"test_statements/ambank/{filename}"
        
        if not Path(file_path).exists():
            print(f"警告: 文件不存在 {file_path}")
            print("请将PDF文件放置在 test_statements/ambank/ 目录下")
            continue
        
        try:
            # 处理账单
            result = processor.process_statement(file_path)
            
            if result:
                print(f"✓ 成功解析 {filename}")
                print(f"  - 账单日期: {result.get('statement_date', 'N/A')}")
                print(f"  - 到期日期: {result.get('payment_due_date', 'N/A')}")
                print(f"  - 当前余额: RM{result.get('current_balance', 'N/A')}")
                print(f"  - 最低还款: RM{result.get('minimum_payment', 'N/A')}")
                print(f"  - 交易笔数: {len(result.get('transactions', []))}")
                
                results.append({
                    "month": month,
                    "year": year,
                    "filename": filename,
                    "data": result
                })
            else:
                print(f"✗ 解析失败 {filename}")
                
        except Exception as e:
            print(f"✗ 处理出错 {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 保存结果
    if results:
        output_file = "ambank_statements_parsed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print(f"解析完成！结果已保存到: {output_file}")
        print(f"成功解析: {len(results)}/{len(STATEMENTS)} 份账单")
        print("="*80)
    else:
        print("\n没有成功解析任何账单")

if __name__ == "__main__":
    process_ambank_statements()
