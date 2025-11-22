#!/usr/bin/env python3
"""
Alliance Bank活期账户批量导入 - 干运行验证

验证所有PDF文件可以正确解析，但不写入数据库
生成详细的验证报告供人工审核

公司：AI SMART TECH SDN. BHD.
银行：Alliance Bank Malaysia Berhad
账户：120790013035540 (CURRENT A/C - OTHERS)

作者：Smart Credit & Loan Manager
日期：2025-10-30
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.savings_parser import parse_savings_statement
from datetime import datetime
import glob

def dry_run_alliance_import():
    """执行干运行验证"""
    
    print("=" * 100)
    print("Alliance Bank活期账户批量导入 - 干运行验证")
    print("=" * 100)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Alliance Bank PDF文件列表（按日期排序）
    pdf_patterns = [
        'attached_assets/30:11:2024*.pdf',
        'attached_assets/31:12:2024*.pdf',
        'attached_assets/31:01:25*.pdf',
        'attached_assets/28:02:25*.pdf',
        'attached_assets/31:03:25*.pdf',
        'attached_assets/30:04:25*.pdf',
        'attached_assets/31:05:25*.pdf',
        'attached_assets/30:06:25*.pdf',
        'attached_assets/31:07:25*.pdf',
        'attached_assets/31:08:25*.pdf',
        'attached_assets/30:09:25*.pdf',
    ]
    
    pdf_files = []
    for pattern in pdf_patterns:
        matches = glob.glob(pattern)
        pdf_files.extend(matches)
    
    # 去重并排序
    pdf_files = sorted(set(pdf_files))
    
    print(f"找到 {len(pdf_files)} 个PDF文件:")
    for i, f in enumerate(pdf_files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    print()
    
    # 解析所有PDF
    all_statements = []
    total_transactions = 0
    parse_errors = []
    
    print("=" * 100)
    print("开始解析PDF文件...")
    print("=" * 100)
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 解析: {os.path.basename(pdf_path)}")
        print("-" * 100)
        
        try:
            statement_info, transactions = parse_savings_statement(pdf_path, bank_name='Alliance Bank')
            
            print(f"  ✓ 成功解析")
            print(f"    - 月结单日期: {statement_info.get('statement_date')}")
            print(f"    - 账户后4位: {statement_info.get('account_last4')}")
            print(f"    - 交易数量: {len(transactions)} 笔")
            
            # 计算期初期末余额
            if transactions:
                first_txn = transactions[0]
                last_txn = transactions[-1]
                
                # 推算期初余额（第一笔交易的余额 - 金额变化）
                if first_txn['type'] == 'credit':
                    opening_balance = first_txn['balance'] - first_txn['amount']
                else:
                    opening_balance = first_txn['balance'] + first_txn['amount']
                
                closing_balance = last_txn['balance']
                
                print(f"    - 期初余额: RM {opening_balance:,.2f}")
                print(f"    - 期末余额: RM {closing_balance:,.2f}")
                
                # 计算总存入/提取
                credits = [t for t in transactions if t.get('type') == 'credit']
                debits = [t for t in transactions if t.get('type') == 'debit']
                total_credit = sum(t.get('amount', 0) for t in credits)
                total_debit = sum(t.get('amount', 0) for t in debits)
                
                print(f"    - 总存入: RM {total_credit:,.2f}")
                print(f"    - 总提取: RM {total_debit:,.2f}")
                
                # 验证期初+存入-提取=期末
                expected_closing = opening_balance + total_credit - total_debit
                balance_match = abs(expected_closing - closing_balance) < 0.01
                
                if balance_match:
                    print(f"    - ✅ 余额验证: 期初 + 存入 - 提取 = 期末 (完美匹配)")
                else:
                    print(f"    - ❌ 余额验证失败: 预期 RM {expected_closing:,.2f}, 实际 RM {closing_balance:,.2f}")
                
                # 存储信息
                all_statements.append({
                    'file': os.path.basename(pdf_path),
                    'statement_date': statement_info.get('statement_date'),
                    'account_last4': statement_info.get('account_last4'),
                    'opening_balance': opening_balance,
                    'closing_balance': closing_balance,
                    'total_credit': total_credit,
                    'total_debit': total_debit,
                    'transaction_count': len(transactions),
                    'balance_verified': balance_match
                })
                
                total_transactions += len(transactions)
            else:
                print(f"    - ⚠️  无交易记录")
            
        except Exception as e:
            print(f"  ❌ 解析失败: {str(e)}")
            parse_errors.append({
                'file': os.path.basename(pdf_path),
                'error': str(e)
            })
    
    # 生成汇总报告
    print("\n" + "=" * 100)
    print("验证汇总报告")
    print("=" * 100)
    
    print(f"\n【文件处理统计】")
    print(f"  总文件数: {len(pdf_files)}")
    print(f"  成功解析: {len(all_statements)}")
    print(f"  解析失败: {len(parse_errors)}")
    print(f"  成功率: {len(all_statements)/len(pdf_files)*100:.1f}%")
    
    print(f"\n【交易统计】")
    print(f"  总交易数: {total_transactions} 笔")
    
    print(f"\n【余额验证】")
    verified_count = sum(1 for s in all_statements if s['balance_verified'])
    print(f"  验证通过: {verified_count}/{len(all_statements)} 个月结单")
    if verified_count == len(all_statements):
        print(f"  ✅ 100% 余额验证通过率!")
    else:
        print(f"  ⚠️  部分月结单余额验证失败")
    
    # 按日期排序显示月结单
    if all_statements:
        print(f"\n【月结单时间线】")
        sorted_statements = sorted(all_statements, key=lambda x: datetime.strptime(x['statement_date'], '%d/%m/%Y'))
        
        print(f"\n{'日期':<15} {'期初余额':<15} {'期末余额':<15} {'存入':<15} {'提取':<15} {'交易数':<10} {'验证':<10}")
        print("-" * 100)
        
        for s in sorted_statements:
            status = "✓" if s['balance_verified'] else "✗"
            print(f"{s['statement_date']:<15} RM {s['opening_balance']:>11,.2f}  RM {s['closing_balance']:>11,.2f}  "
                  f"RM {s['total_credit']:>11,.2f}  RM {s['total_debit']:>11,.2f}  {s['transaction_count']:>8}    {status:<10}")
    
    # 显示余额连续性
    if len(sorted_statements) > 1:
        print(f"\n【余额连续性检查】")
        print("(检查相邻月份的期末余额是否等于下月期初余额)")
        print()
        
        for i in range(len(sorted_statements) - 1):
            current = sorted_statements[i]
            next_stmt = sorted_statements[i + 1]
            
            current_date = datetime.strptime(current['statement_date'], '%d/%m/%Y')
            next_date = datetime.strptime(next_stmt['statement_date'], '%d/%m/%Y')
            
            month_diff = (next_date.year - current_date.year) * 12 + (next_date.month - current_date.month)
            
            if month_diff == 1:
                # 连续月份
                if abs(current['closing_balance'] - next_stmt['opening_balance']) < 0.01:
                    status = "✓ 连续匹配"
                else:
                    status = f"✗ 不匹配 (差异: RM {abs(current['closing_balance'] - next_stmt['opening_balance']):,.2f})"
            else:
                status = f"⚠ 断层 ({month_diff}个月)"
            
            print(f"  {current['statement_date']} → {next_stmt['statement_date']}: {status}")
            print(f"    期末 RM {current['closing_balance']:>12,.2f} vs 下月期初 RM {next_stmt['opening_balance']:>12,.2f}")
    
    # 显示解析错误
    if parse_errors:
        print(f"\n【解析错误】")
        for err in parse_errors:
            print(f"  ✗ {err['file']}: {err['error']}")
    
    print("\n" + "=" * 100)
    if len(all_statements) == len(pdf_files) and verified_count == len(all_statements):
        print("✅ 所有文件解析成功！余额验证100%通过！可以执行正式导入。")
    else:
        print("⚠️  部分文件解析失败或余额验证未通过，请检查错误信息后再执行正式导入。")
    print("=" * 100)
    
    return all_statements, parse_errors


if __name__ == '__main__':
    all_statements, parse_errors = dry_run_alliance_import()
