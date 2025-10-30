#!/usr/bin/env python3
"""
Public Bank Batch Import - DRY RUN
AI SMART TECH SDN. BHD. - Account #3824549009
2025年3月 - 2025年9月 (7个月结单)

执行方式: python3 scripts/dry_run_pbb_import.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ingest.savings_parser import parse_publicbank_savings

def main():
    print("=" * 120)
    print("PUBLIC BANK 批量导入 - 干运行模式（DRY RUN）")
    print("=" * 120)
    print(f"公司: AI SMART TECH SDN. BHD.")
    print(f"账户: 3824549009")
    print(f"银行: Public Bank Malaysia Berhad")
    print(f"账户类型: RM Cm Current Account-i (伊斯兰活期账户)")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    print()
    
    # PDF文件列表（按月份顺序）
    pdf_files = [
        ('attached_assets/31:03:25_1761805099156.pdf', '2025-03'),
        ('attached_assets/30:04:25_1761805099156.pdf', '2025-04'),
        ('attached_assets/31:05:25_1761805099156.pdf', '2025-05'),
        ('attached_assets/30:06:25_1761805099156.pdf', '2025-06'),
        ('attached_assets/31:07:25_1761805099157.pdf', '2025-07'),
        ('attached_assets/30:08:25_1761805099156.pdf', '2025-08'),
        ('attached_assets/31:09:25_1761805099157.pdf', '2025-09'),
    ]
    
    all_statements = []
    total_transactions = 0
    parsing_errors = []
    
    # 解析所有PDF
    for pdf_path, expected_month in pdf_files:
        print(f"\n{'=' * 120}")
        print(f"解析月结单: {expected_month}")
        print(f"文件: {pdf_path}")
        print(f"{'=' * 120}")
        
        try:
            # 解析月结单
            metadata, transactions = parse_publicbank_savings(pdf_path)
            
            # 计算余额信息
            if transactions:
                # 从第一笔交易推算期初余额
                first_txn = transactions[0]
                if first_txn['type'] == 'credit':
                    opening_balance = first_txn['balance'] - first_txn['amount']
                else:
                    opening_balance = first_txn['balance'] + first_txn['amount']
                
                closing_balance = transactions[-1]['balance']
                total_credits = sum(t['amount'] for t in transactions if t['type'] == 'credit')
                total_debits = sum(t['amount'] for t in transactions if t['type'] == 'debit')
            else:
                opening_balance = 0.0
                closing_balance = 0.0
                total_credits = 0.0
                total_debits = 0.0
            
            # Balance-Change验证
            calculated_closing = opening_balance + total_credits - total_debits
            balance_diff = abs(calculated_closing - closing_balance)
            balance_verified = balance_diff < 0.01
            
            statement_info = {
                'month': expected_month,
                'file': pdf_path,
                'statement_date': metadata.get('statement_date', 'N/A'),
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'total_credits': total_credits,
                'total_debits': total_debits,
                'transaction_count': len(transactions),
                'transactions': transactions,
                'balance_verified': balance_verified,
                'balance_diff': balance_diff,
            }
            
            all_statements.append(statement_info)
            total_transactions += len(transactions)
            
            # 打印月结单摘要
            print(f"\n【月结单摘要】")
            print(f"  月结单日期: {metadata.get('statement_date', 'N/A')}")
            print(f"  期初余额: RM {opening_balance:,.2f}")
            print(f"  期末余额: RM {closing_balance:,.2f}")
            print(f"  总存款 (Credits): RM {total_credits:,.2f}")
            print(f"  总取款 (Debits): RM {total_debits:,.2f}")
            print(f"  交易笔数: {len(transactions)}")
            print(f"\n【Balance-Change验证】")
            print(f"  公式: 期初 + 存款 - 取款 = 期末")
            print(f"  {opening_balance:,.2f} + {total_credits:,.2f} - {total_debits:,.2f} = {calculated_closing:,.2f}")
            print(f"  实际期末: RM {closing_balance:,.2f}")
            print(f"  差异: RM {balance_diff:,.2f}")
            
            if balance_verified:
                print(f"  ✅ 验证通过！")
            else:
                print(f"  ❌ 验证失败！差异超过0.01")
                parsing_errors.append(f"{expected_month}: Balance verification failed (diff={balance_diff:.2f})")
            
            # 打印交易明细（前5笔和后5笔）
            if transactions:
                print(f"\n【交易明细】前5笔:")
                print(f"  {'日期':<12} {'描述':<60} {'金额':>15} {'类型':<8} {'余额':>15}")
                print(f"  {'-' * 115}")
                for txn in transactions[:5]:
                    amount_str = f"RM {txn['amount']:,.2f}"
                    balance_str = f"RM {txn['balance']:,.2f}"
                    desc_short = txn['description'][:57] + "..." if len(txn['description']) > 60 else txn['description']
                    print(f"  {txn['date']:<12} {desc_short:<60} {amount_str:>15} {txn['type']:<8} {balance_str:>15}")
                
                if len(transactions) > 10:
                    print(f"  ... ({len(transactions) - 10} 笔交易省略) ...")
                
                if len(transactions) > 5:
                    print(f"\n【交易明细】后5笔:")
                    print(f"  {'日期':<12} {'描述':<60} {'金额':>15} {'类型':<8} {'余额':>15}")
                    print(f"  {'-' * 115}")
                    for txn in transactions[-5:]:
                        amount_str = f"RM {txn['amount']:,.2f}"
                        balance_str = f"RM {txn['balance']:,.2f}"
                        desc_short = txn['description'][:57] + "..." if len(txn['description']) > 60 else txn['description']
                        print(f"  {txn['date']:<12} {desc_short:<60} {amount_str:>15} {txn['type']:<8} {balance_str:>15}")
            
        except Exception as e:
            error_msg = f"{expected_month}: {str(e)}"
            parsing_errors.append(error_msg)
            print(f"\n❌ 解析失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 打印总体摘要
    print(f"\n\n{'=' * 120}")
    print("批量导入总结")
    print(f"{'=' * 120}")
    print(f"公司: AI SMART TECH SDN. BHD.")
    print(f"账户: 3824549009")
    print(f"时间范围: 2025年3月 - 2025年9月")
    print(f"月结单数量: {len(all_statements)}/{len(pdf_files)}")
    print(f"总交易笔数: {total_transactions}")
    
    if parsing_errors:
        print(f"\n❌ 发现 {len(parsing_errors)} 个错误:")
        for error in parsing_errors:
            print(f"  - {error}")
    else:
        print(f"\n✅ 所有月结单解析成功！")
    
    # 月度余额连续性检查
    print(f"\n【月度余额连续性检查】")
    print(f"{'月份':<12} {'期初余额':>15} {'期末余额':>15} {'上月期末':>15} {'匹配状态':<10}")
    print(f"{'-' * 75}")
    
    for i, stmt in enumerate(all_statements):
        opening = stmt['opening_balance']
        closing = stmt['closing_balance']
        
        if i > 0:
            prev_closing = all_statements[i-1]['closing_balance']
            match = abs(opening - prev_closing) < 0.01
            match_status = "✅ 匹配" if match else f"❌ 不匹配 (差异: {abs(opening - prev_closing):.2f})"
        else:
            prev_closing = 0.0
            match_status = "N/A (首月)"
        
        print(f"{stmt['month']:<12} RM {opening:>12,.2f} RM {closing:>12,.2f} RM {prev_closing:>12,.2f} {match_status:<10}")
    
    # 生成CSV报告
    csv_filename = f"reports/pbb_dry_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    os.makedirs('reports', exist_ok=True)
    
    with open(csv_filename, 'w', encoding='utf-8') as f:
        f.write("月份,月结单日期,期初余额,期末余额,总存款,总取款,交易笔数,余额验证\n")
        for stmt in all_statements:
            f.write(f"{stmt['month']},{stmt['statement_date']},{stmt['opening_balance']:.2f},"
                   f"{stmt['closing_balance']:.2f},{stmt['total_credits']:.2f},"
                   f"{stmt['total_debits']:.2f},{stmt['transaction_count']},"
                   f"{'PASS' if stmt['balance_verified'] else 'FAIL'}\n")
    
    print(f"\n✅ CSV报告已生成: {csv_filename}")
    
    # 生成Markdown详细报告
    md_filename = f"reports/pbb_dry_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(f"# Public Bank 批量导入验证报告\n\n")
        f.write(f"**公司**: AI SMART TECH SDN. BHD.\n")
        f.write(f"**账户**: 3824549009\n")
        f.write(f"**银行**: Public Bank Malaysia Berhad\n")
        f.write(f"**账户类型**: RM Cm Current Account-i (伊斯兰活期账户)\n")
        f.write(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"## 总体摘要\n\n")
        f.write(f"- 月结单数量: {len(all_statements)}/{len(pdf_files)}\n")
        f.write(f"- 总交易笔数: {total_transactions}\n")
        f.write(f"- 时间范围: 2025年3月 - 2025年9月\n\n")
        
        f.write(f"## 月度数据摘要\n\n")
        f.write(f"| 月份 | 月结单日期 | 期初余额 | 期末余额 | 总存款 | 总取款 | 交易数 | 余额验证 |\n")
        f.write(f"|------|-----------|---------|---------|--------|--------|--------|----------|\n")
        
        for stmt in all_statements:
            status = "✅ PASS" if stmt['balance_verified'] else "❌ FAIL"
            f.write(f"| {stmt['month']} | {stmt['statement_date']} | "
                   f"RM {stmt['opening_balance']:,.2f} | RM {stmt['closing_balance']:,.2f} | "
                   f"RM {stmt['total_credits']:,.2f} | RM {stmt['total_debits']:,.2f} | "
                   f"{stmt['transaction_count']} | {status} |\n")
        
        f.write(f"\n## 详细交易记录\n\n")
        
        for stmt in all_statements:
            f.write(f"### {stmt['month']} - {stmt['statement_date']}\n\n")
            f.write(f"**期初余额**: RM {stmt['opening_balance']:,.2f}\n\n")
            f.write(f"**期末余额**: RM {stmt['closing_balance']:,.2f}\n\n")
            f.write(f"**Balance-Change验证**: ")
            f.write(f"✅ 通过\n\n" if stmt['balance_verified'] else f"❌ 失败 (差异: RM {stmt['balance_diff']:.2f})\n\n")
            
            f.write(f"| 日期 | 描述 | 金额 | 类型 | 余额 |\n")
            f.write(f"|------|------|------|------|------|\n")
            
            for txn in stmt['transactions']:
                f.write(f"| {txn['date']} | {txn['description']} | "
                       f"RM {txn['amount']:,.2f} | {txn['type']} | RM {txn['balance']:,.2f} |\n")
            
            f.write(f"\n")
    
    print(f"✅ Markdown报告已生成: {md_filename}")
    
    print(f"\n{'=' * 120}")
    print("DRY RUN 完成！")
    print("此次运行未写入数据库，请检查报告后再执行正式导入。")
    print(f"{'=' * 120}")

if __name__ == '__main__':
    main()
