"""
批量处理 CHEOK JUN YOON 的41张信用卡账单
使用 Google Document AI 独占模式（无fallback）
按时间顺序：2025-05 → 2025-10
"""

import sys
import os
import json
import logging
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.statement_parser import parse_statement_auto
from services.transaction_classifier import TransactionClassifier
from services.credit_card_core import CreditCardCore

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 41张账单按时间顺序排列
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
    {"month": "2025-06", "bank": "HONG LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf"},
    {"month": "2025-06", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf"},
    {"month": "2025-06", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-06/OCBC_3506_2025-06-13.pdf"},
    {"month": "2025-06", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-06/STANDARD_CHARTERED_1237_2025-06-15.pdf"},
    {"month": "2025-06", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-06/UOB_3530_2025-06-13.pdf"},
    
    # 2025-07 (7张)
    {"month": "2025-07", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-07/AMBANK_9902_2025-07-28.pdf"},
    {"month": "2025-07", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-07/AmBank_6354_2025-07-28.pdf"},
    {"month": "2025-07", "bank": "HONG LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-07/HONG_LEONG_3964_2025-07-16.pdf"},
    {"month": "2025-07", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-07/HSBC_0034_2025-07-13.pdf"},
    {"month": "2025-07", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-07/OCBC_3506_2025-07-13.pdf"},
    {"month": "2025-07", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-07/STANDARD_CHARTERED_1237_2025-07-14.pdf"},
    {"month": "2025-07", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-07/UOB_3530_2025-07-13.pdf"},
    
    # 2025-08 (7张)
    {"month": "2025-08", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-08/AMBANK_9902_2025-08-28.pdf"},
    {"month": "2025-08", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-08/AmBank_6354_2025-08-28.pdf"},
    {"month": "2025-08", "bank": "HONG LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-08/HONG_LEONG_3964_2025-08-16.pdf"},
    {"month": "2025-08", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-08/HSBC_0034_2025-08-13.pdf"},
    {"month": "2025-08", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-08/OCBC_3506_2025-08-13.pdf"},
    {"month": "2025-08", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-08/STANDARD_CHARTERED_1237_2025-08-14.pdf"},
    {"month": "2025-08", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-08/UOB_3530_2025-08-13.pdf"},
    
    # 2025-09 (7张)
    {"month": "2025-09", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-09/AMBANK_9902_2025-09-28.pdf"},
    {"month": "2025-09", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-09/AmBank_6354_2025-09-28.pdf"},
    {"month": "2025-09", "bank": "HONG LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-09/HONG_LEONG_3964_2025-09-16.pdf"},
    {"month": "2025-09", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-09/HSBC_0034_2025-09-13.pdf"},
    {"month": "2025-09", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-09/OCBC_3506_2025-09-13.pdf"},
    {"month": "2025-09", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-09/STANDARD_CHARTERED_1237_2025-09-14.pdf"},
    {"month": "2025-09", "bank": "UOB", "card": "3530", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-09/UOB_3530_2025-09-13.pdf"},
    
    # 2025-10 (7张)
    {"month": "2025-10", "bank": "AMBANK", "card": "9902", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-10/AMBANK_9902_2025-10-28.pdf"},
    {"month": "2025-10", "bank": "AmBank", "card": "6354", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-10/AmBank_6354_2025-10-28.pdf"},
    {"month": "2025-10", "bank": "HONG LEONG", "card": "3964", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-10/HONG_LEONG_3964_2025-10-16.pdf"},
    {"month": "2025-10", "bank": "HSBC", "card": "0034", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf"},
    {"month": "2025-10", "bank": "OCBC", "card": "3506", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-10/OCBC_3506_2025-10-13.pdf"},
    {"month": "2025-10", "bank": "SCB", "card": "1237", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-10/STANDARD_CHARTERED_1237_2025-10-14.pdf"},
    {"month": "2025-10", "bank": "UOB", "card": "8387", "pdf": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-10/UOB_8387_2025-10-13.pdf"},
]


def process_statement(stmt_info: dict, index: int, total: int) -> dict:
    """处理单张账单"""
    logger.info("\n" + "="*80)
    logger.info(f"【{index}/{total}】{stmt_info['month']} - {stmt_info['bank']} *{stmt_info['card']}")
    logger.info("="*80)
    
    result = {
        'success': False,
        'month': stmt_info['month'],
        'bank': stmt_info['bank'],
        'card': stmt_info['card'],
        'pdf': stmt_info['pdf'],
        'transactions': 0,
        'dr_count': 0,
        'cr_count': 0,
        'error': ''
    }
    
    try:
        # 使用Google Document AI解析（无fallback）
        info, transactions = parse_statement_auto(stmt_info['pdf'])
        
        result['transactions'] = len(transactions)
        result['dr_count'] = sum(1 for t in transactions if t.get('type') == 'DR')
        result['cr_count'] = sum(1 for t in transactions if t.get('type') == 'CR')
        result['success'] = True
        
        logger.info(f"✅ 成功：{len(transactions)}笔交易（DR:{result['dr_count']}, CR:{result['cr_count']}）")
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"❌ 失败：{e}")
    
    return result


def main():
    """主函数"""
    logger.info("="*80)
    logger.info("CreditPilot - 批量处理 CHEOK JUN YOON 账单")
    logger.info("="*80)
    logger.info(f"客户：CHEOK JUN YOON (Be_rich_CJY)")
    logger.info(f"期间：2025年5月-10月")
    logger.info(f"账单数：{len(STATEMENTS)}张")
    logger.info(f"解析器：Google Document AI 独占模式（无fallback）")
    logger.info(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    results = []
    success_count = 0
    failed_count = 0
    total_transactions = 0
    total_dr = 0
    total_cr = 0
    
    # 逐张处理
    for i, stmt in enumerate(STATEMENTS, 1):
        result = process_statement(stmt, i, len(STATEMENTS))
        results.append(result)
        
        if result['success']:
            success_count += 1
            total_transactions += result['transactions']
            total_dr += result['dr_count']
            total_cr += result['cr_count']
        else:
            failed_count += 1
    
    # 生成汇总报告
    logger.info("\n" + "="*80)
    logger.info("📊 处理汇总报告")
    logger.info("="*80)
    logger.info(f"总账单数：{len(STATEMENTS)}张")
    logger.info(f"✅ 成功：{success_count}张")
    logger.info(f"❌ 失败：{failed_count}张")
    logger.info(f"成功率：{success_count/len(STATEMENTS)*100:.1f}%")
    logger.info(f"\n交易统计：")
    logger.info(f"  总交易数：{total_transactions}笔")
    logger.info(f"  DR交易：{total_dr}笔")
    logger.info(f"  CR交易：{total_cr}笔")
    
    # 按月汇总
    monthly_summary = {}
    for r in results:
        if r['success']:
            month = r['month']
            if month not in monthly_summary:
                monthly_summary[month] = {'count': 0, 'transactions': 0, 'dr': 0, 'cr': 0}
            monthly_summary[month]['count'] += 1
            monthly_summary[month]['transactions'] += r['transactions']
            monthly_summary[month]['dr'] += r['dr_count']
            monthly_summary[month]['cr'] += r['cr_count']
    
    logger.info(f"\n月度汇总：")
    for month in sorted(monthly_summary.keys()):
        s = monthly_summary[month]
        logger.info(f"  {month}: {s['count']}张账单 | {s['transactions']}笔交易 (DR:{s['dr']}, CR:{s['cr']})")
    
    # 保存报告
    os.makedirs('reports', exist_ok=True)
    report_path = 'reports/cheok_41_statements_report.json'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'customer': 'CHEOK JUN YOON',
            'customer_code': 'Be_rich_CJY',
            'period': '2025-05 to 2025-10',
            'parser': 'Google Document AI (Exclusive)',
            'total_statements': len(STATEMENTS),
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': f"{success_count/len(STATEMENTS)*100:.1f}%",
            'total_transactions': total_transactions,
            'total_dr': total_dr,
            'total_cr': total_cr,
            'monthly_summary': monthly_summary,
            'detailed_results': results,
            'processed_at': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ 详细报告已保存：{report_path}")
    logger.info(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    return results


if __name__ == "__main__":
    main()
