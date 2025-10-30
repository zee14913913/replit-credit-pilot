#!/usr/bin/env python3
"""
HLB活期账户批量导入 - 干运行脚本 (Dry-Run)

功能：
1. 解析所有16个HLB活期账户PDF
2. 应用Balance-Change算法确保100%准确
3. 生成详细验证报告（每个文件+汇总）
4. 显示交易样本（前5笔+后5笔）
5. **不写入数据库** - 仅供人工审核

作者：Smart Credit & Loan Manager
日期：2025-10-30
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pdfplumber
import re
import glob
from datetime import datetime
from ingest.savings_parser import apply_balance_change_algorithm


def parse_hlb_current_account(file_path):
    """
    HLB活期账户解析器
    
    Returns:
        tuple: (info dict, transactions list)
    """
    with pdfplumber.open(file_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            full_text += page.extract_text() + '\n'
        
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        
        info = {
            'bank_name': 'Hong Leong Bank',
            'bank_code': 'HLB',
            'account_number': None,
            'account_holder': None,
            'statement_date': None,
            'statement_period': None,
            'opening_balance': None,
            'closing_balance': None,
            'total_deposits_pdf': None,
            'total_withdrawals_pdf': None,
            'branch': None
        }
        
        for line in lines:
            if 'A/C No' in line:
                match = re.search(r'(\d{11})', line)
                if match:
                    info['account_number'] = match.group(1)
            
            if 'Date / Tarikh :' in line:
                match = re.search(r'(\d{2}-\d{2}-\d{4})', line)
                if match:
                    info['statement_date'] = match.group(1)
            
            if 'Statement Period' in line:
                match = re.search(r'(\d{2}/\d{2}/\d{2}\s*-\s*\d{2}/\d{2}/\d{2})', line)
                if match:
                    info['statement_period'] = match.group(1)
            
            if 'Branch / Cawangan :' in line:
                match = re.search(r':\s*(.+)', line)
                if match:
                    info['branch'] = match.group(1).strip()
            
            if lines[0] and not info['account_holder']:
                for i, l in enumerate(lines):
                    if 'INFINITE GZ SDN' in l:
                        info['account_holder'] = l.strip()
                        break
            
            if 'Balance from previous statement' in line:
                match = re.search(r'([\d,]*\.?\d+)$', line)
                if match:
                    bal_str = match.group(1).replace(',', '')
                    info['opening_balance'] = float(bal_str) if bal_str else 0.0
            
            if 'Total Deposits' in line and 'Closing Balance' in line:
                match = re.search(r'Closing Balance.*?([\d,]+\.\d{2})', line)
                if match:
                    info['closing_balance'] = float(match.group(1).replace(',', ''))
            
            if 'Total Deposits' in line:
                match = re.search(r'Total Deposits.*?:\s*\d+\s+([\d,]+\.\d{2})', line)
                if match:
                    info['total_deposits_pdf'] = float(match.group(1).replace(',', ''))
            
            if 'Total Withdrawals' in line:
                match = re.search(r'Total Withdrawals.*?:\s*\d+\s+([\d,]+\.\d{2})', line)
                if match:
                    info['total_withdrawals_pdf'] = float(match.group(1).replace(',', ''))
        
        temp_transactions = []
        
        for i, line in enumerate(lines):
            if re.match(r'^\d{2}-\d{2}-\d{4}', line):
                if 'balance from previous' in line.lower() or 'balance c/f' in line.lower():
                    continue
                
                date_match = re.match(r'^(\d{2}-\d{2}-\d{4})', line)
                date_str = date_match.group(1)
                
                amounts = re.findall(r'([\d,]+\.\d{2})', line)
                
                if len(amounts) >= 1:
                    balance = float(amounts[-1].replace(',', ''))
                    
                    desc = line
                    desc = re.sub(r'^\d{2}-\d{2}-\d{4}\s+', '', desc)
                    desc = re.sub(r'[\d,]+\.\d{2}', '', desc)
                    desc = desc.strip()
                    
                    j = i + 1
                    while j < len(lines) and j < i + 6:
                        next_line = lines[j]
                        if re.match(r'^\d{2}-\d{2}-\d{4}', next_line):
                            break
                        if 'Total' in next_line:
                            break
                        if re.match(r'^[\d,\.]+$', next_line):
                            j += 1
                            continue
                        desc += ' ' + next_line
                        j += 1
                    
                    temp_transactions.append({
                        'date': date_str,
                        'description': desc.strip(),
                        'balance': balance,
                        'amount': 0,
                        'type': 'unknown'
                    })
        
        if info['opening_balance'] is None:
            raise ValueError(f"无法提取期初余额 - PDF格式可能已变更")
        
        if info['closing_balance'] is None:
            raise ValueError(f"无法提取期末余额 - PDF格式可能已变更（检查'Total Deposits ... Closing Balance'行格式）")
        
        final_transactions = apply_balance_change_algorithm(temp_transactions, info['opening_balance'])
        
        return info, final_transactions


def generate_dry_run_report(pdf_files):
    """
    生成干运行验证报告
    
    Args:
        pdf_files: PDF文件路径列表
    
    Returns:
        dict: 汇总报告数据
    """
    print("=" * 130)
    print(f"HLB活期账户批量导入 - 干运行验证报告")
    print(f"INFINITE GZ SDN. BHD. | 账户 #23600594645 | 2024年7月 - 2025年10月")
    print("=" * 130)
    print()
    
    all_results = []
    total_transactions = 0
    total_deposits = 0.0
    total_withdrawals = 0.0
    
    for idx, file_path in enumerate(sorted(pdf_files), 1):
        try:
            print(f"\n{'=' * 130}")
            print(f"[{idx}/{len(pdf_files)}] 解析文件: {os.path.basename(file_path)}")
            print(f"{'=' * 130}")
            
            info, transactions = parse_hlb_current_account(file_path)
            
            total_credit = sum(t['amount'] for t in transactions if t['type'] == 'credit')
            total_debit = sum(t['amount'] for t in transactions if t['type'] == 'debit')
            expected_closing = info['opening_balance'] + total_credit - total_debit
            
            balance_verified = abs(expected_closing - info['closing_balance']) < 0.01
            
            print(f"\n账单信息:")
            print(f"  银行：{info['bank_name']} ({info['bank_code']})")
            print(f"  账号：{info['account_number']}")
            print(f"  账户持有人：{info['account_holder']}")
            print(f"  账单日期：{info['statement_date']}")
            print(f"  账单周期：{info['statement_period']}")
            print(f"  分行：{info['branch']}")
            
            print(f"\n余额信息:")
            print(f"  期初余额：RM {info['opening_balance']:>15,.2f}")
            print(f"  + 存款总额：RM {total_credit:>15,.2f}")
            print(f"  - 提款总额：RM {total_debit:>15,.2f}")
            print(f"  = 预期期末：RM {expected_closing:>15,.2f}")
            print(f"  实际期末：RM {info['closing_balance']:>15,.2f}")
            
            if balance_verified:
                print(f"  ✅ 余额验证通过 (差异 < RM 0.01)")
            else:
                diff = abs(expected_closing - info['closing_balance'])
                print(f"  ❌ 余额验证失败 (差异: RM {diff:,.2f})")
            
            print(f"\n交易统计:")
            print(f"  总交易数：{len(transactions)} 笔")
            print(f"  存款交易：{sum(1 for t in transactions if t['type'] == 'credit')} 笔")
            print(f"  提款交易：{sum(1 for t in transactions if t['type'] == 'debit')} 笔")
            
            print(f"\n交易样本 (前5笔):")
            for i, txn in enumerate(transactions[:5], 1):
                type_icon = "💰" if txn['type'] == 'credit' else "💸"
                print(f"  {i}. {txn['date']} {type_icon} {txn['type']:<6} RM {txn['amount']:>10,.2f} | 余额: RM {txn.get('balance', 0):>10,.2f}")
                print(f"     {txn['description'][:100]}")
            
            if len(transactions) > 10:
                print(f"\n交易样本 (后5笔):")
                for i, txn in enumerate(transactions[-5:], len(transactions) - 4):
                    type_icon = "💰" if txn['type'] == 'credit' else "💸"
                    print(f"  {i}. {txn['date']} {type_icon} {txn['type']:<6} RM {txn['amount']:>10,.2f} | 余额: RM {txn.get('balance', 0):>10,.2f}")
                    print(f"     {txn['description'][:100]}")
            
            all_results.append({
                'file': os.path.basename(file_path),
                'date': info['statement_date'],
                'opening': info['opening_balance'],
                'closing': info['closing_balance'],
                'transactions': len(transactions),
                'credit': total_credit,
                'debit': total_debit,
                'verified': balance_verified
            })
            
            total_transactions += len(transactions)
            total_deposits += total_credit
            total_withdrawals += total_debit
            
        except Exception as e:
            import traceback
            print(f"❌ 解析失败: {e}")
            print(traceback.format_exc())
            all_results.append({
                'file': os.path.basename(file_path),
                'error': str(e)
            })
    
    all_results.sort(key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y') if 'date' in x else datetime.min)
    
    print(f"\n\n{'=' * 130}")
    print("汇总验证报告")
    print(f"{'=' * 130}\n")
    
    print(f"{'#':<3} {'日期':<13} {'文件名':<35} {'期初':<13} {'期末':<13} {'存款':<13} {'提款':<13} {'交易':<5} {'验证'}")
    print("-" * 130)
    
    passed = 0
    failed = 0
    
    for i, r in enumerate(all_results, 1):
        if 'error' in r:
            print(f"{i:<3} ERROR: {r['file']}")
            failed += 1
        else:
            status = f"✅ PASS" if r['verified'] else f"❌ FAIL"
            print(f"{i:<3} {r['date']:<13} {r['file']:<35} "
                  f"RM {r['opening']:>9,.2f} RM {r['closing']:>9,.2f} "
                  f"RM {r['credit']:>9,.2f} RM {r['debit']:>9,.2f} "
                  f"{r['transactions']:>3} {status}")
            if r['verified']:
                passed += 1
            else:
                failed += 1
    
    print("=" * 130)
    print(f"\n汇总统计:")
    print(f"  文件总数：{len(all_results)} 个")
    print(f"  ✅ 通过：{passed} 个")
    print(f"  ❌ 失败：{failed} 个")
    print(f"  交易总数：{total_transactions} 笔")
    print(f"  总存款：RM {total_deposits:,.2f}")
    print(f"  总提款：RM {total_withdrawals:,.2f}")
    print(f"  净变化：RM {(total_deposits - total_withdrawals):,.2f}")
    
    if passed == len(all_results):
        print(f"\n{'=' * 130}")
        print(f"🎉 所有{len(all_results)}个PDF文件余额验证100%通过！")
        print(f"✅ 系统准备就绪 - 可以执行正式批量导入")
        print(f"{'=' * 130}")
        return True
    else:
        print(f"\n{'=' * 130}")
        print(f"⚠️  有{failed}个文件验证失败，需要进一步检查")
        print(f"{'=' * 130}")
        return False


def main():
    """主函数"""
    pdf_dir = 'attached_assets'
    pdf_pattern = '05-*.pdf'
    
    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, pdf_pattern)))
    
    if not pdf_files:
        print(f"❌ 未找到任何PDF文件: {os.path.join(pdf_dir, pdf_pattern)}")
        return False
    
    print(f"\n发现 {len(pdf_files)} 个HLB活期账户PDF文件")
    print(f"目录：{pdf_dir}")
    print(f"模式：{pdf_pattern}\n")
    
    success = generate_dry_run_report(pdf_files)
    
    if success:
        print(f"\n{'=' * 130}")
        print("下一步：")
        print("  1. 仔细审核上述验证报告")
        print("  2. 确认所有交易数据准确无误")
        print("  3. 执行正式批量导入脚本: python scripts/batch_import_hlb_current.py")
        print(f"{'=' * 130}\n")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
