#!/usr/bin/env python3
"""
Maybank月结单1:1验证脚本
逐月、逐笔对比PDF原件与数据库记录，确保100%一致
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from ingest.savings_parser import parse_maybank_savings

# PDF文件映射
PDF_FILES = [
    ("attached_assets/28-02-24 Y_1761778437660.pdf", 221, "Feb 2024"),
    ("attached_assets/31-03-24_1761778437670.pdf", 222, "Mar 2024"),
    ("attached_assets/30-04-24_1761778437669.pdf", 223, "Apr 2024"),
    ("attached_assets/31-05-24_1761778437670.pdf", 224, "May 2024"),
    ("attached_assets/30-06-24_1761778437669.pdf", 225, "Jun 2024"),
    ("attached_assets/31-07-24_1761778437670.pdf", 226, "Jul 2024"),
    ("attached_assets/31-08-24_1761778437670.pdf", 227, "Aug 2024"),
    ("attached_assets/30-09-24_1761778437670.pdf", 228, "Sep 2024"),
    ("attached_assets/31-10-24_1761778437670.pdf", 229, "Oct 2024"),
    ("attached_assets/30-11-24_1761778437670.pdf", 230, "Nov 2024"),
    ("attached_assets/31-12-24_1761778437670.pdf", 231, "Dec 2024"),
]

def compare_transaction(pdf_txn, db_txn, index):
    """对比单笔交易，返回是否匹配及差异详情"""
    differences = []
    
    # 对比日期
    if pdf_txn['date'] != db_txn[0]:
        differences.append(f"日期不匹配: PDF={pdf_txn['date']}, DB={db_txn[0]}")
    
    # 对比描述
    if pdf_txn['description'] != db_txn[1]:
        differences.append(f"描述不匹配: PDF={pdf_txn['description']}, DB={db_txn[1]}")
    
    # 对比金额（精确到0.01）
    if abs(pdf_txn['amount'] - db_txn[2]) > 0.01:
        differences.append(f"金额不匹配: PDF={pdf_txn['amount']:.2f}, DB={db_txn[2]:.2f}")
    
    # 对比类型
    if pdf_txn['type'] != db_txn[3]:
        differences.append(f"类型不匹配: PDF={pdf_txn['type']}, DB={db_txn[3]}")
    
    # 对比余额（精确到0.01）
    if abs(pdf_txn['balance'] - db_txn[4]) > 0.01:
        differences.append(f"余额不匹配: PDF={pdf_txn['balance']:.2f}, DB={db_txn[4]:.2f}")
    
    return len(differences) == 0, differences

def verify_single_month(pdf_path, statement_id, month_name):
    """验证单个月份的所有交易记录"""
    print(f'\n{"="*100}')
    print(f'📅 验证月份: {month_name} (Statement ID: {statement_id})')
    print(f'{"="*100}')
    
    # 1. 解析PDF原件
    print(f'\n🔍 步骤1: 解析PDF原件...')
    try:
        statement_info, pdf_transactions = parse_maybank_savings(pdf_path)
        print(f'   ✅ PDF解析成功: {len(pdf_transactions)} 笔交易')
    except Exception as e:
        print(f'   ❌ PDF解析失败: {e}')
        return False, 0, 0, []
    
    # 2. 读取数据库记录
    print(f'\n🔍 步骤2: 读取数据库记录...')
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT transaction_date, description, amount, transaction_type, balance
        FROM savings_transactions
        WHERE savings_statement_id = ?
        ORDER BY id
    ''', (statement_id,))
    
    db_transactions = cursor.fetchall()
    print(f'   ✅ 数据库读取成功: {len(db_transactions)} 笔交易')
    conn.close()
    
    # 3. 对比交易数量
    print(f'\n🔍 步骤3: 对比交易数量...')
    if len(pdf_transactions) != len(db_transactions):
        print(f'   ❌ 交易数量不匹配!')
        print(f'      PDF原件: {len(pdf_transactions)} 笔')
        print(f'      数据库: {len(db_transactions)} 笔')
        return False, len(pdf_transactions), 0, []
    else:
        print(f'   ✅ 交易数量匹配: {len(pdf_transactions)} 笔')
    
    # 4. 逐笔对比
    print(f'\n🔍 步骤4: 逐笔对比所有交易...')
    mismatches = []
    matched_count = 0
    
    for i, (pdf_txn, db_txn) in enumerate(zip(pdf_transactions, db_transactions)):
        is_match, differences = compare_transaction(pdf_txn, db_txn, i)
        
        if is_match:
            matched_count += 1
        else:
            mismatches.append({
                'index': i + 1,
                'pdf': pdf_txn,
                'db': db_txn,
                'differences': differences
            })
    
    # 5. 输出验证结果
    print(f'\n📊 验证结果:')
    print(f'   总交易数: {len(pdf_transactions)}')
    print(f'   匹配成功: {matched_count} 笔 ({matched_count/len(pdf_transactions)*100:.1f}%)')
    print(f'   不匹配: {len(mismatches)} 笔')
    
    if len(mismatches) == 0:
        print(f'\n✅ {month_name} 验证通过 - 100%一致!')
    else:
        print(f'\n❌ {month_name} 验证失败 - 发现{len(mismatches)}笔不匹配的交易')
        print(f'\n不匹配交易详情:')
        for mismatch in mismatches[:5]:  # 只显示前5笔
            print(f'\n   交易 #{mismatch["index"]}:')
            print(f'   PDF原件: {mismatch["pdf"]["date"]} | {mismatch["pdf"]["description"][:50]} | {mismatch["pdf"]["type"]} | RM {mismatch["pdf"]["amount"]:.2f} → RM {mismatch["pdf"]["balance"]:.2f}')
            print(f'   数据库:  {mismatch["db"][0]} | {mismatch["db"][1][:50]} | {mismatch["db"][3]} | RM {mismatch["db"][2]:.2f} → RM {mismatch["db"][4]:.2f}')
            print(f'   差异: {", ".join(mismatch["differences"])}')
        
        if len(mismatches) > 5:
            print(f'\n   ... 还有 {len(mismatches) - 5} 笔不匹配的交易')
    
    return len(mismatches) == 0, len(pdf_transactions), matched_count, mismatches

def main():
    """主函数 - 验证所有11个月的Maybank月结单"""
    print('='*100)
    print('🔍 Maybank月结单1:1完整验证系统')
    print('='*100)
    print(f'验证范围: 2024年2月 - 12月 (11个月)')
    print(f'验证标准: PDF原件 vs 数据库记录 100%一致')
    print('='*100)
    
    total_months = len(PDF_FILES)
    passed_months = 0
    failed_months = 0
    total_transactions = 0
    total_matched = 0
    all_mismatches = {}
    
    # 逐月验证
    for pdf_path, statement_id, month_name in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f'\n❌ 文件不存在: {pdf_path}')
            failed_months += 1
            continue
        
        success, txn_count, matched, mismatches = verify_single_month(pdf_path, statement_id, month_name)
        
        total_transactions += txn_count
        total_matched += matched
        
        if success:
            passed_months += 1
        else:
            failed_months += 1
            all_mismatches[month_name] = mismatches
    
    # 最终总结
    print('\n\n')
    print('='*100)
    print('📊 全部月份验证完成总结')
    print('='*100)
    print(f'验证月份数: {total_months}')
    print(f'✅ 验证通过: {passed_months} 个月')
    print(f'❌ 验证失败: {failed_months} 个月')
    print(f'总交易数: {total_transactions} 笔')
    print(f'匹配成功: {total_matched} 笔 ({total_matched/total_transactions*100:.1f}%)' if total_transactions > 0 else '匹配成功: 0 笔')
    print(f'不匹配: {total_transactions - total_matched} 笔')
    print('='*100)
    
    if failed_months == 0:
        print('\n🎉 恭喜！所有11个月的Maybank月结单验证通过！')
        print('✅ 数据库记录与PDF原件100%一致！')
    else:
        print(f'\n⚠️  发现{failed_months}个月存在不匹配的交易，请检查以下月份:')
        for month_name, mismatches in all_mismatches.items():
            print(f'   - {month_name}: {len(mismatches)} 笔不匹配')
    
    print('='*100)
    
    return failed_months == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
