"""
批量处理 CHEOK JUN YOON 的41张信用卡账单
使用 Google Document AI + 自动分类 + 计算引擎
遵循 ARCHITECT_CONSTRAINTS.md 规范
"""

import os
import sys
import json
import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.statement_parser import parse_statement_auto
from services.transaction_classifier import TransactionClassifier
from services.credit_card_core import CreditCardCore
from services.credit_card_validation import CreditCardValidation
from db.database import get_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cheok Jun Yoon的PDF账单列表（41张）
STATEMENT_PDFS = [
    # 2025-05 (7张)
    "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf",
    
    # 2025-06 (7张)
    "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-06/AMBANK_9902_2025-06-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-06/AmBank_6354_2025-06-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-06/HSBC_0034_2025-06-14.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-06/OCBC_3506_2025-06-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-06/STANDARD_CHARTERED_1237_2025-06-15.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-06/UOB_3530_2025-06-13.pdf",
    
    # 2025-07 (7张)
    "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-07/AMBANK_9902_2025-07-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-07/AmBank_6354_2025-07-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-07/HONG_LEONG_3964_2025-07-16.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-07/HSBC_0034_2025-07-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-07/OCBC_3506_2025-07-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-07/STANDARD_CHARTERED_1237_2025-07-14.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-07/UOB_3530_2025-07-13.pdf",
    
    # 2025-08 (7张)
    "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-08/AMBANK_9902_2025-08-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-08/AmBank_6354_2025-08-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-08/HONG_LEONG_3964_2025-08-16.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-08/HSBC_0034_2025-08-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-08/OCBC_3506_2025-08-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-08/STANDARD_CHARTERED_1237_2025-08-14.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-08/UOB_3530_2025-08-13.pdf",
    
    # 2025-09 (7张)
    "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-09/AMBANK_9902_2025-09-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-09/AmBank_6354_2025-09-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-09/HONG_LEONG_3964_2025-09-16.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-09/HSBC_0034_2025-09-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-09/OCBC_3506_2025-09-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-09/STANDARD_CHARTERED_1237_2025-09-14.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-09/UOB_3530_2025-09-13.pdf",
    
    # 2025-10 (6张)
    "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-10/AMBANK_9902_2025-10-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-10/AmBank_6354_2025-10-28.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-10/HONG_LEONG_3964_2025-10-16.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-10/OCBC_3506_2025-10-13.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-10/STANDARD_CHARTERED_1237_2025-10-14.pdf",
    "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-10/UOB_8387_2025-10-13.pdf",
]


def process_single_statement(pdf_path: str, index: int, total: int) -> dict:
    """
    处理单张账单
    
    返回：{
        'success': bool,
        'pdf_path': str,
        'bank': str,
        'month': str,
        'transactions_count': int,
        'dr_count': int,
        'cr_count': int,
        'calculation': dict,
        'error': str (if failed)
    }
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"【{index}/{total}】处理账单: {pdf_path}")
    logger.info(f"{'='*80}")
    
    result = {
        'success': False,
        'pdf_path': pdf_path,
        'bank': '',
        'month': '',
        'transactions_count': 0,
        'dr_count': 0,
        'cr_count': 0,
        'calculation': {},
        'error': ''
    }
    
    try:
        # 步骤1：解析PDF（使用Google Document AI + fallback）
        logger.info("🚀 步骤1：解析PDF...")
        info, transactions = parse_statement_auto(pdf_path)
        
        if not info or not transactions:
            raise Exception("PDF解析失败：未提取到有效数据")
        
        result['bank'] = info.get('bank', 'UNKNOWN')
        result['month'] = info.get('statement_date', 'UNKNOWN')
        result['transactions_count'] = len(transactions)
        
        # 统计DR/CR
        dr_count = sum(1 for t in transactions if t.get('type') == 'DR')
        cr_count = sum(1 for t in transactions if t.get('type') == 'CR')
        result['dr_count'] = dr_count
        result['cr_count'] = cr_count
        
        logger.info(f"✅ 解析成功：{len(transactions)}笔交易（DR:{dr_count}, CR:{cr_count}）")
        
        # 验证DR/CR完整性
        if dr_count == 0 or cr_count == 0:
            logger.warning(f"⚠️ 警告：DR或CR交易为0！DR:{dr_count}, CR:{cr_count}")
        
        # 步骤2：分类交易
        logger.info("🔍 步骤2：分类交易...")
        classifier = TransactionClassifier()
        classified_count = 0
        for txn in transactions:
            if txn.get('type') == 'DR':
                # 检查是否为Supplier
                is_supplier = False
                for supplier in classifier.suppliers:
                    if supplier.upper() in txn.get('description', '').upper():
                        txn['category'] = "GZ's Expenses"
                        is_supplier = True
                        break
                if not is_supplier:
                    txn['category'] = "Owner's Expenses"
                classified_count += 1
            elif txn.get('type') == 'CR':
                # CR自动分类在计算引擎中处理
                txn['category'] = "Payment"
                classified_count += 1
        
        logger.info(f"✅ 分类完成：{classified_count}笔交易已分类")
        
        # 步骤3：模拟计算（不存入数据库）
        logger.info("🧮 步骤3：计算财务指标...")
        
        # 模拟statement_info
        statement_info = {
            'id': 0,
            'statement_month': result['month'],
            'previous_balance': Decimal(str(info.get('previous_balance', 0))),
            'bank_name': result['bank'],
            'card_holder_name': 'CHEOK JUN YOON',
            'customer_name': 'CHEOK JUN YOON'
        }
        
        # 执行计算
        core = CreditCardCore()
        round1 = core._calculate_round_1(statement_info, [
            {
                'id': i,
                'date': t.get('date', ''),
                'description': t.get('description', ''),
                'amount': Decimal(str(t.get('amount', 0))),
                'type': t.get('type', 'DR'),
                'category': t.get('category', '')
            }
            for i, t in enumerate(transactions)
        ])
        
        gz_payment2 = Decimal('0')  # 暂时为0，需要从bank_transfers表查询
        
        final = core._calculate_final(round1, gz_payment2)
        
        calculation = {
            'previous_balance': float(statement_info['previous_balance']),
            'owner_expenses': float(round1['owner_expenses']),
            'gz_expenses': float(round1['gz_expenses']),
            'owner_payment': float(round1['owner_payment']),
            'gz_payment1': float(round1['gz_payment1']),
            'owner_os_bal_round1': float(round1['owner_os_bal_round1']),
            'gz_os_bal_round1': float(round1['gz_os_bal_round1']),
            'gz_payment2': float(gz_payment2),
            'final_owner_os_bal': float(final['final_owner_os_bal']),
            'final_gz_os_bal': float(final['final_gz_os_bal']),
            'total_dr': float(round1['total_dr']),
            'total_cr': float(round1['total_cr']),
            'balance_diff': float(round1['total_dr'] - round1['total_cr'])
        }
        
        result['calculation'] = calculation
        
        logger.info(f"✅ 计算完成：")
        logger.info(f"   - Owner's Expenses: RM {calculation['owner_expenses']:,.2f}")
        logger.info(f"   - GZ's Expenses: RM {calculation['gz_expenses']:,.2f}")
        logger.info(f"   - Owner's Payment: RM {calculation['owner_payment']:,.2f}")
        logger.info(f"   - GZ's Payment1: RM {calculation['gz_payment1']:,.2f}")
        logger.info(f"   - FINAL Owner OS Bal: RM {calculation['final_owner_os_bal']:,.2f}")
        logger.info(f"   - FINAL GZ OS Bal: RM {calculation['final_gz_os_bal']:,.2f}")
        logger.info(f"   - DR/CR Balance: DR={calculation['total_dr']:,.2f} CR={calculation['total_cr']:,.2f} Diff={calculation['balance_diff']:,.2f}")
        
        # 步骤4：验证
        logger.info("✔️ 步骤4：验证数据...")
        validator = CreditCardValidation()
        is_balanced = abs(calculation['balance_diff']) <= 0.01
        
        if is_balanced:
            logger.info("✅ DR/CR平衡验证通过！")
        else:
            logger.warning(f"⚠️ DR/CR不平衡！差异: RM {calculation['balance_diff']:.2f}")
        
        result['success'] = True
        logger.info(f"✅ 账单处理成功！\n")
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"❌ 账单处理失败：{e}\n")
    
    return result


def main():
    """主函数：批量处理41张账单"""
    logger.info("="*80)
    logger.info("CreditPilot - 批量处理 CHEOK JUN YOON 的41张信用卡账单")
    logger.info("="*80)
    logger.info(f"客户：CHEOK JUN YOON (Be_rich_CJY)")
    logger.info(f"期间：2025年5月 - 2025年10月")
    logger.info(f"账单数量：{len(STATEMENT_PDFS)}张")
    logger.info(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    results = []
    success_count = 0
    failed_count = 0
    
    # 逐张处理
    for i, pdf_path in enumerate(STATEMENT_PDFS, 1):
        result = process_single_statement(pdf_path, i, len(STATEMENT_PDFS))
        results.append(result)
        
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
    
    # 生成汇总报告
    logger.info("\n" + "="*80)
    logger.info("📊 处理汇总报告")
    logger.info("="*80)
    logger.info(f"总账单数：{len(STATEMENT_PDFS)}张")
    logger.info(f"成功处理：{success_count}张 ✅")
    logger.info(f"处理失败：{failed_count}张 ❌")
    logger.info(f"成功率：{success_count/len(STATEMENT_PDFS)*100:.1f}%")
    
    # 统计交易总数
    total_transactions = sum(r['transactions_count'] for r in results if r['success'])
    total_dr = sum(r['dr_count'] for r in results if r['success'])
    total_cr = sum(r['cr_count'] for r in results if r['success'])
    
    logger.info(f"\n交易统计：")
    logger.info(f"  - 总交易数：{total_transactions}笔")
    logger.info(f"  - DR交易：{total_dr}笔")
    logger.info(f"  - CR交易：{total_cr}笔")
    
    # 保存详细报告
    report_path = "reports/cheok_batch_processing_report.json"
    os.makedirs("reports", exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'customer': 'CHEOK JUN YOON',
            'customer_code': 'Be_rich_CJY',
            'period': '2025-05 to 2025-10',
            'total_statements': len(STATEMENT_PDFS),
            'success_count': success_count,
            'failed_count': failed_count,
            'total_transactions': total_transactions,
            'total_dr': total_dr,
            'total_cr': total_cr,
            'results': results,
            'processed_at': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ 详细报告已保存：{report_path}")
    logger.info(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    return results


if __name__ == "__main__":
    main()
