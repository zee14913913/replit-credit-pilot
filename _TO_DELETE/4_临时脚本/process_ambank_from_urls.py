#!/usr/bin/env python3
"""
AmBank信用卡账单批量解析脚本 (从 URL)
直接从Ppl-ai附件URL下载PDF并解析
"""

import json
import sys
import requests
import tempfile
from pathlib import Path
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.statement_processor import StatementProcessor

# 账单URL信息 (从附件获取)
STATEMENTS_URLS = [
    {
        "month": "05",
        "year": "2025",
        "filename": "AMB-28-05-2025.pdf",
        "url": "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/0a54455d-f26d-49a8-9159-0bb7767e1e18/AMB-28-05-2025.pdf"
    },
    {
        "month": "06",
        "year": "2025",
        "filename": "AMB-28-06-2025.pdf",
        "url": "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/8712d85b-c0cd-4fd4-b2db-bd38a3c90d5b/AMB-28-06-2025.pdf"
    },
    {
        "month": "07",
        "year": "2025",
        "filename": "AMB-28-07-2025.pdf",
        "url": "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/9d34e532-0efc-4461-8213-1d8194ffa0f3/AMB-28-07-2025.pdf"
    },
    {
        "month": "08",
        "year": "2025",
        "filename": "AMB-28-08-2025.pdf",
        "url": "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/21822321-3a98-4e09-a93c-10a4c11472ef/AMB-28-08-2025.pdf"
    },
    {
        "month": "09",
        "year": "2025",
        "filename": "AMB-28-09-2025.pdf",
        "url": "https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124523618/4e2251f0-b555-4d04-b898-820d8dc7ecc8/AMB-28-09-2025.pdf"
    }
]

def download_pdf(url: str, filename: str) -> str:
    """
    从 URL 下载 PDF 文件
    """
    print(f"  - 下载: {filename}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 创建临时文件
        temp_dir = Path("test_statements/ambank")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = temp_dir / filename
        
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ 下载成功: {len(response.content)} bytes")
        return str(temp_path)
        
    except Exception as e:
        print(f"  ✗ 下载失败: {str(e)}")
        return None

def process_ambank_statements():
    """
    批量处理AmBank信用卡账单
    """
    print("="*80)
    print("AmBank信用卡账单批量解析 (从PDF URL)")
    print("="*80)
    
    # 初始化处理器
    processor = StatementProcessor()
    
    results = []
    
    for stmt_info in STATEMENTS_URLS:
        month = stmt_info['month']
        year = stmt_info['year']
        filename = stmt_info['filename']
        url = stmt_info['url']
        
        print(f"\n[{month}/{year}] 处理账单: {filename}")
        print("-" * 80)
        
        # 下载PDF
        file_path = download_pdf(url, filename)
        
        if not file_path:
            print(f"  ✗ 跳过 {filename} (下载失败)")
            continue
        
        try:
            # 处理账单
            print(f"  - 解析中...")
            result = processor.process_statement(file_path)
            
            if result:
                print(f"  ✓ 成功解析 {filename}")
                print(f"    • 客户姓名: {result.get('customer_name', 'N/A')}")
                print(f"    • 卡号: {result.get('card_number', 'N/A')}")
                print(f"    • 账单日期: {result.get('statement_date', 'N/A')}")
                print(f"    • 到期日期: {result.get('payment_due_date', 'N/A')}")
                print(f"    • 信用额度: RM{result.get('credit_limit', 'N/A')}")
                print(f"    • 当前余额: RM{result.get('current_balance', 'N/A')}")
                print(f"    • 最低还款: RM{result.get('minimum_payment', 'N/A')}")
                print(f"    • 交易笔数: {len(result.get('transactions', []))}")
                
                # 统计交易金额
                transactions = result.get('transactions', [])
                total_debit = sum(float(t.get('amount', 0)) for t in transactions if float(t.get('amount', 0)) > 0)
                total_credit = sum(abs(float(t.get('amount', 0))) for t in transactions if float(t.get('amount', 0)) < 0)
                
                print(f"    • 总消费: RM{total_debit:.2f}")
                print(f"    • 总还款: RM{total_credit:.2f}")
                
                results.append({
                    "month": month,
                    "year": year,
                    "filename": filename,
                    "data": result,
                    "summary": {
                        "total_debit": total_debit,
                        "total_credit": total_credit,
                        "transaction_count": len(transactions)
                    }
                })
            else:
                print(f"  ✗ 解析失败 {filename}")
                
        except Exception as e:
            print(f"  ✗ 处理出错 {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 保存结果
    if results:
        output_file = "ambank_statements_parsed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print("\n✓ 解析完成！")
        print(f"\n结果已保存到: {output_file}")
        print(f"成功解析: {len(results)}/{len(STATEMENTS_URLS)} 份账单")
        
        # 显示汇总
        print("\n汇总统计:")
        print("-" * 80)
        total_transactions = sum(r['summary']['transaction_count'] for r in results)
        total_spend = sum(r['summary']['total_debit'] for r in results)
        total_payment = sum(r['summary']['total_credit'] for r in results)
        
        print(f"  总交易笔数: {total_transactions}")
        print(f"  总消费金额: RM{total_spend:.2f}")
        print(f"  总还款金额: RM{total_payment:.2f}")
        
        print("\n" + "="*80)
    else:
        print("\n✗ 没有成功解析任何账单")

if __name__ == "__main__":
    process_ambank_statements()
