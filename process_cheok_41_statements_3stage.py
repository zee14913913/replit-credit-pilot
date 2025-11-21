
#!/usr/bin/env python3
"""
三段式解析处理 CHEOK JUN YOON 的 41 份信用卡账单
确保 100% 准确度的分类和验证
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.fallback_parser import FallbackParser
from services.transaction_classifier import TransactionClassifier

# 41张账单路径配置
STATEMENTS = [
    # 2025-05 (6张)
    {"month": "2025-05", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf"},
    {"month": "2025-05", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf"},
    {"month": "2025-05", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf"},
    {"month": "2025-05", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf"},
    {"month": "2025-05", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf"},
    {"month": "2025-05", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf"},
    
    # 2025-06 (7张)
    {"month": "2025-06", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-06/AMBANK_9902_2025-06-28.pdf"},
    {"month": "2025-06", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-06/AmBank_6354_2025-06-28.pdf"},
    {"month": "2025-06", "bank": "HONG_LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf"},
    {"month": "2025-06", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf"},
    {"month": "2025-06", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-06/OCBC_3506_2025-06-13.pdf"},
    {"month": "2025-06", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-06/STANDARD_CHARTERED_1237_2025-06-15.pdf"},
    {"month": "2025-06", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-06/UOB_3530_2025-06-13.pdf"},
    
    # 2025-07 (7张)
    {"month": "2025-07", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-07/AMBANK_9902_2025-07-28.pdf"},
    {"month": "2025-07", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-07/AmBank_6354_2025-07-28.pdf"},
    {"month": "2025-07", "bank": "HONG_LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-07/HONG_LEONG_3964_2025-07-16.pdf"},
    {"month": "2025-07", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-07/HSBC_0034_2025-07-13.pdf"},
    {"month": "2025-07", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-07/OCBC_3506_2025-07-13.pdf"},
    {"month": "2025-07", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-07/STANDARD_CHARTERED_1237_2025-07-14.pdf"},
    {"month": "2025-07", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-07/UOB_3530_2025-07-13.pdf"},
    
    # 2025-08 (7张)
    {"month": "2025-08", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-08/AMBANK_9902_2025-08-28.pdf"},
    {"month": "2025-08", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-08/AmBank_6354_2025-08-28.pdf"},
    {"month": "2025-08", "bank": "HONG_LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-08/HONG_LEONG_3964_2025-08-16.pdf"},
    {"month": "2025-08", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-08/HSBC_0034_2025-08-13.pdf"},
    {"month": "2025-08", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-08/OCBC_3506_2025-08-13.pdf"},
    {"month": "2025-08", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-08/STANDARD_CHARTERED_1237_2025-08-14.pdf"},
    {"month": "2025-08", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-08/UOB_3530_2025-08-13.pdf"},
    
    # 2025-09 (7张)
    {"month": "2025-09", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-09/AMBANK_9902_2025-09-28.pdf"},
    {"month": "2025-09", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-09/AmBank_6354_2025-09-28.pdf"},
    {"month": "2025-09", "bank": "HONG_LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-09/HONG_LEONG_3964_2025-09-16.pdf"},
    {"month": "2025-09", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-09/HSBC_0034_2025-09-13.pdf"},
    {"month": "2025-09", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-09/OCBC_3506_2025-09-13.pdf"},
    {"month": "2025-09", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-09/STANDARD_CHARTERED_1237_2025-09-14.pdf"},
    {"month": "2025-09", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-09/UOB_3530_2025-09-13.pdf"},
    
    # 2025-10 (7张)
    {"month": "2025-10", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-10/AMBANK_9902_2025-10-28.pdf"},
    {"month": "2025-10", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-10/AmBank_6354_2025-10-28.pdf"},
    {"month": "2025-10", "bank": "HONG_LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-10/HONG_LEONG_3964_2025-10-16.pdf"},
    {"month": "2025-10", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf"},
    {"month": "2025-10", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-10/OCBC_3506_2025-10-13.pdf"},
    {"month": "2025-10", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-10/STANDARD_CHARTERED_1237_2025-10-14.pdf"},
    {"month": "2025-10", "bank": "UOB", "card": "8387", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-10/UOB_8387_2025-10-13.pdf"},
]


def process_stage1_parsing():
    """第1段：FallbackParser解析所有PDF"""
    print("\n" + "="*100)
    print("第1段：FallbackParser 解析 PDF")
    print("="*100)
    
    parser = FallbackParser()
    all_results = []
    
    for idx, stmt in enumerate(STATEMENTS, 1):
        print(f"\n[{idx}/41] 解析: {stmt['month']} - {stmt['bank']} *{stmt['card']}")
        
        try:
            if not os.path.exists(stmt['pdf']):
                print(f"  ❌ 文件不存在: {stmt['pdf']}")
                all_results.append({
                    'statement': stmt,
                    'success': False,
                    'error': 'File not found'
                })
                continue
            
            info, transactions = parser.parse_pdf(stmt['pdf'])
            
            print(f"  ✅ 成功提取 {len(transactions)} 笔交易")
            print(f"     银行: {info.get('bank_name')}")
            print(f"     账单日期: {info.get('statement_date')}")
            print(f"     余额: RM {info.get('current_balance', 0):,.2f}")
            
            all_results.append({
                'statement': stmt,
                'success': True,
                'info': info,
                'transactions': transactions,
                'transaction_count': len(transactions)
            })
            
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            all_results.append({
                'statement': stmt,
                'success': False,
                'error': str(e)
            })
    
    # 统计
    success_count = sum(1 for r in all_results if r['success'])
    print(f"\n第1段完成：{success_count}/41 成功")
    
    return all_results


def process_stage2_classification(stage1_results):
    """第2段：TransactionClassifier分类（98%精度）"""
    print("\n" + "="*100)
    print("第2段：TransactionClassifier 分类（98% 精度）")
    print("="*100)
    
    classifier = TransactionClassifier(
        customer_name='CHEOK JUN YOON',
        suppliers_list=['7SL', 'Dinas Raub', 'SYC Hainan', 'Ai Smart Tech', 'HUAWEI', 'Pasar Raya', 'Puchong Herbs']
    )
    
    all_classified = []
    total_stats = {
        "Owner's Expenses": 0,
        "GZ's Expenses": 0,
        "Owner's Payment": 0,
        "GZ's Payment": 0
    }
    total_merchant_fees = 0.0
    total_transactions = 0
    
    for result in stage1_results:
        if not result['success']:
            all_classified.append(result)
            continue
        
        stmt = result['statement']
        print(f"\n分类: {stmt['month']} - {stmt['bank']} *{stmt['card']}")
        
        transactions = result['transactions']
        classified_txns = []
        
        for txn in transactions:
            txn_type = txn.get('type', 'DR')
            description = txn.get('description', '')
            amount = abs(txn.get('amount', 0))
            
            if txn_type in ['DR', 'DEBIT']:
                # 费用分类
                classification = classifier.classify_expense(description)
                category = classification['category']
                
                # 计算1%商家手续费（仅GZ's Expenses）
                merchant_fee = amount * 0.01 if category == "GZ's Expenses" else 0.0
                
                classified_txns.append({
                    'date': txn.get('transaction_date'),
                    'description': description,
                    'amount': amount,
                    'type': 'DR',
                    'category': category,
                    'is_supplier': classification.get('is_supplier', False),
                    'matched_supplier': classification.get('matched_supplier'),
                    'merchant_fee': merchant_fee,
                    'confidence': classification.get('confidence', 'medium')
                })
                
                total_stats[category] += 1
                total_merchant_fees += merchant_fee
                
            else:  # CR/CREDIT
                # 付款分类
                classification = classifier.classify_payment(description)
                category = classification['category']
                
                classified_txns.append({
                    'date': txn.get('transaction_date'),
                    'description': description,
                    'amount': amount,
                    'type': 'CR',
                    'category': category,
                    'rule_applied': classification.get('rule_applied'),
                    'confidence': classification.get('confidence', 'medium')
                })
                
                total_stats[category] += 1
        
        total_transactions += len(classified_txns)
        
        # 处理负数余额（预付款）
        current_balance = result['info'].get('current_balance', 0)
        has_prepayment = current_balance < 0
        
        print(f"  ✅ 分类完成: {len(classified_txns)} 笔交易")
        print(f"     Owner's Expenses: {sum(1 for t in classified_txns if t['category'] == 'Owner\\'s Expenses')}")
        print(f"     GZ's Expenses: {sum(1 for t in classified_txns if t['category'] == 'GZ\\'s Expenses')}")
        print(f"     Owner's Payment: {sum(1 for t in classified_txns if t['category'] == 'Owner\\'s Payment')}")
        print(f"     GZ's Payment: {sum(1 for t in classified_txns if t['category'] == 'GZ\\'s Payment')}")
        if has_prepayment:
            print(f"     ⚠️  检测到预付款: RM {abs(current_balance):,.2f}")
        
        result['classified_transactions'] = classified_txns
        result['has_prepayment'] = has_prepayment
        result['prepayment_amount'] = abs(current_balance) if has_prepayment else 0
        all_classified.append(result)
    
    print(f"\n第2段完成：")
    print(f"  总交易数: {total_transactions}")
    print(f"  分类统计:")
    for category, count in total_stats.items():
        print(f"    {category}: {count}")
    print(f"  商家手续费总额: RM {total_merchant_fees:,.2f}")
    
    return all_classified, total_stats, total_merchant_fees


def process_stage3_report(classified_results, stats, total_fees):
    """第3段：生成验证报告"""
    print("\n" + "="*100)
    print("第3段：生成验证报告")
    print("="*100)
    
    # 生成JSON报告
    json_report = {
        'generated_at': datetime.now().isoformat(),
        'customer': 'CHEOK JUN YOON',
        'total_statements': len(classified_results),
        'successful_statements': sum(1 for r in classified_results if r['success']),
        'classification_stats': stats,
        'total_merchant_fees': total_fees,
        'statements': []
    }
    
    # 需要人工复核的交易
    manual_review_needed = []
    
    for result in classified_results:
        if not result['success']:
            continue
        
        stmt = result['statement']
        stmt_data = {
            'month': stmt['month'],
            'bank': stmt['bank'],
            'card': stmt['card'],
            'transaction_count': len(result.get('classified_transactions', [])),
            'has_prepayment': result.get('has_prepayment', False),
            'prepayment_amount': result.get('prepayment_amount', 0),
            'transactions': []
        }
        
        for txn in result.get('classified_transactions', []):
            txn_data = {
                'date': txn['date'],
                'description': txn['description'],
                'amount': txn['amount'],
                'type': txn['type'],
                'category': txn['category'],
                'confidence': txn['confidence']
            }
            
            if txn['type'] == 'DR':
                txn_data['is_supplier'] = txn.get('is_supplier', False)
                txn_data['matched_supplier'] = txn.get('matched_supplier')
                txn_data['merchant_fee'] = txn.get('merchant_fee', 0)
            else:
                txn_data['rule_applied'] = txn.get('rule_applied')
            
            stmt_data['transactions'].append(txn_data)
            
            # 标记低置信度交易
            if txn['confidence'] in ['low', 'medium']:
                manual_review_needed.append({
                    'statement': f"{stmt['month']} - {stmt['bank']} *{stmt['card']}",
                    'transaction': txn_data
                })
        
        json_report['statements'].append(stmt_data)
    
    json_report['manual_review_count'] = len(manual_review_needed)
    json_report['manual_review_transactions'] = manual_review_needed
    
    # 保存JSON报告
    os.makedirs('reports', exist_ok=True)
    json_path = f"reports/cheok_41_statements_classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ JSON报告已生成: {json_path}")
    print(f"\n验证摘要:")
    print(f"  成功处理: {json_report['successful_statements']}/41")
    print(f"  需要人工复核: {len(manual_review_needed)} 笔交易")
    print(f"  分类统计:")
    for category, count in stats.items():
        print(f"    {category}: {count}")
    print(f"  商家手续费总额: RM {total_fees:,.2f}")
    
    if manual_review_needed:
        print(f"\n⚠️  以下交易需要人工复核（置信度较低）:")
        for idx, item in enumerate(manual_review_needed[:10], 1):  # 只显示前10个
            print(f"  {idx}. {item['statement']}")
            print(f"     {item['transaction']['description']} - RM {item['transaction']['amount']:,.2f}")
            print(f"     分类: {item['transaction']['category']} (置信度: {item['transaction']['confidence']})")
    
    return json_path


def main():
    """主函数"""
    print("="*100)
    print("三段式解析处理 CHEOK JUN YOON 的 41 份信用卡账单")
    print("="*100)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 第1段：解析
    stage1_results = process_stage1_parsing()
    
    # 第2段：分类
    classified_results, stats, total_fees = process_stage2_classification(stage1_results)
    
    # 第3段：报告
    report_path = process_stage3_report(classified_results, stats, total_fees)
    
    print(f"\n{'='*100}")
    print(f"处理完成！")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"详细报告: {report_path}")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()
