#!/usr/bin/env python3
"""
全面审计所有信用卡和储蓄账户账单
- 检查日期错误
- 检查文件路径问题
- 识别重复记录
- 生成清理方案
"""

import sqlite3
from collections import defaultdict
from datetime import datetime

DB_PATH = 'db/smart_loan_manager.db'

def audit_credit_card_statements():
    """审计信用卡账单"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("="*80)
    print("信用卡账单审计报告".center(80))
    print("="*80)
    
    # 1. 检查日期格式错误
    print("\n【1】日期格式检查")
    statements = cursor.execute('''
        SELECT s.id, s.statement_date, s.file_path, 
               c.name, cc.bank_name, cc.card_number_last4
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        ORDER BY c.name, cc.bank_name, s.statement_date
    ''').fetchall()
    
    date_errors = []
    for sid, stmt_date, fpath, cname, bank, card in statements:
        try:
            # 检查日期格式
            date_obj = datetime.strptime(stmt_date, '%Y-%m-%d')
            # 检查年份合理性
            if date_obj.year < 2020 or date_obj.year > 2030:
                date_errors.append((sid, stmt_date, cname, bank, card))
            # 检查月份
            if date_obj.month > 12 or date_obj.month < 1:
                date_errors.append((sid, stmt_date, cname, bank, card))
        except ValueError:
            date_errors.append((sid, stmt_date, cname, bank, card))
    
    if date_errors:
        print(f"  ⚠ 发现 {len(date_errors)} 个日期错误:")
        for sid, sdate, cname, bank, card in date_errors:
            print(f"    ID {sid}: {sdate} - {cname} {bank} {card}")
    else:
        print("  ✓ 所有日期格式正确")
    
    # 2. 检查重复账单
    print("\n【2】重复账单检查")
    duplicates = defaultdict(list)
    for sid, stmt_date, fpath, cname, bank, card in statements:
        # 按客户+银行+卡号+年月分组
        year_month = stmt_date[:7] if len(stmt_date) >= 7 else stmt_date
        key = (cname, bank, card, year_month)
        duplicates[key].append((sid, stmt_date, fpath))
    
    duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}
    
    if duplicate_groups:
        print(f"  ⚠ 发现 {len(duplicate_groups)} 组重复账单:")
        for (cname, bank, card, ym), records in duplicate_groups.items():
            print(f"\n    {cname} - {bank} {card} - {ym} ({len(records)}份)")
            for sid, sdate, fpath in records:
                print(f"      ID {sid}: {sdate}")
    else:
        print("  ✓ 没有重复账单")
    
    # 3. 检查文件路径
    print("\n【3】文件路径检查")
    old_path_count = 0
    missing_files = []
    
    for sid, stmt_date, fpath, cname, bank, card in statements:
        if fpath and fpath.startswith('attached_assets/'):
            old_path_count += 1
        
        # 检查文件是否存在
        import os
        if fpath and not os.path.exists(fpath):
            missing_files.append((sid, fpath, cname))
    
    print(f"  - 使用旧路径 (attached_assets): {old_path_count} 个")
    print(f"  - 使用新路径 (static/uploads): {len(statements) - old_path_count} 个")
    
    if missing_files:
        print(f"  ⚠ 缺失文件: {len(missing_files)} 个")
        for sid, fpath, cname in missing_files[:5]:
            print(f"    ID {sid}: {cname} - {fpath}")
        if len(missing_files) > 5:
            print(f"    ... 及其他 {len(missing_files) - 5} 个")
    else:
        print("  ✓ 所有文件都存在")
    
    conn.close()
    
    return {
        'date_errors': date_errors,
        'duplicates': duplicate_groups,
        'old_paths': old_path_count,
        'missing_files': missing_files
    }

def audit_savings_statements():
    """审计储蓄账户账单"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("储蓄账户账单审计报告".center(80))
    print("="*80)
    
    # 检查是否有savings_statements表
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='savings_statements'"
    ).fetchone()
    
    if not tables:
        print("  ℹ 没有储蓄账户账单表")
        conn.close()
        return {}
    
    # 1. 检查重复
    print("\n【1】重复账单检查")
    statements = cursor.execute('''
        SELECT ss.id, ss.statement_date, ss.file_path,
               c.name, sa.bank_name, sa.account_number_last4
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        ORDER BY c.name, sa.bank_name, ss.statement_date
    ''').fetchall()
    
    duplicates = defaultdict(list)
    for sid, stmt_date, fpath, cname, bank, acc in statements:
        year_month = stmt_date[:7] if len(stmt_date) >= 7 else stmt_date
        key = (cname, bank, acc, year_month)
        duplicates[key].append((sid, stmt_date, fpath))
    
    duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}
    
    if duplicate_groups:
        print(f"  ⚠ 发现 {len(duplicate_groups)} 组重复账单:")
        for (cname, bank, acc, ym), records in duplicate_groups.items():
            print(f"\n    {cname} - {bank} {acc} - {ym} ({len(records)}份)")
            for sid, sdate, fpath in records:
                print(f"      ID {sid}: {sdate}")
    else:
        print("  ✓ 没有重复账单")
    
    conn.close()
    
    return {
        'duplicates': duplicate_groups
    }

def audit_duplicate_customers():
    """检查重复客户（大小写不同）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("客户重复检查".center(80))
    print("="*80)
    
    customers = cursor.execute('SELECT id, name FROM customers ORDER BY UPPER(name)').fetchall()
    
    duplicates = defaultdict(list)
    for cid, cname in customers:
        key = cname.upper().strip()
        duplicates[key].append((cid, cname))
    
    duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}
    
    if duplicate_groups:
        print(f"  ⚠ 发现 {len(duplicate_groups)} 组重复客户:")
        for upper_name, records in duplicate_groups.items():
            print(f"\n    {upper_name}:")
            for cid, cname in records:
                # 统计该客户的卡数量
                card_count = cursor.execute(
                    'SELECT COUNT(*) FROM credit_cards WHERE customer_id = ?', (cid,)
                ).fetchone()[0]
                print(f"      ID {cid}: '{cname}' ({card_count}张卡)")
    else:
        print("  ✓ 没有重复客户")
    
    conn.close()
    
    return duplicate_groups

def audit_duplicate_cards():
    """检查重复信用卡（同客户+同银行+同卡号后4位）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("信用卡重复检查".center(80))
    print("="*80)
    
    cards = cursor.execute('''
        SELECT cc.id, c.name, cc.bank_name, cc.card_number_last4, cc.customer_id
        FROM credit_cards cc
        JOIN customers c ON cc.customer_id = c.id
        ORDER BY c.name, cc.bank_name, cc.card_number_last4
    ''').fetchall()
    
    duplicates = defaultdict(list)
    for card_id, cname, bank, last4, cust_id in cards:
        # 按客户ID+银行+卡号后4位分组（大小写无关）
        key = (cust_id, bank.upper().strip(), last4)
        duplicates[key].append((card_id, cname, bank, last4))
    
    duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}
    
    if duplicate_groups:
        print(f"  ⚠ 发现 {len(duplicate_groups)} 组重复信用卡:")
        for (cust_id, bank_upper, last4), records in duplicate_groups.items():
            print(f"\n    客户ID {cust_id} - {bank_upper} {last4} ({len(records)}张):")
            for card_id, cname, bank, l4 in records:
                # 统计该卡的账单数量
                stmt_count = cursor.execute(
                    'SELECT COUNT(*) FROM statements WHERE card_id = ?', (card_id,)
                ).fetchone()[0]
                print(f"      卡ID {card_id}: {cname} - {bank} ({stmt_count}个账单)")
    else:
        print("  ✓ 没有重复信用卡")
    
    conn.close()
    
    return duplicate_groups

def main():
    """执行完整审计"""
    print("\n" + "█"*80)
    print("数据完整性审计系统".center(80))
    print("█"*80)
    
    # 1. 审计信用卡账单
    cc_audit = audit_credit_card_statements()
    
    # 2. 审计储蓄账户账单
    savings_audit = audit_savings_statements()
    
    # 3. 审计重复客户
    dup_customers = audit_duplicate_customers()
    
    # 4. 审计重复信用卡
    dup_cards = audit_duplicate_cards()
    
    # 生成总结报告
    print("\n" + "="*80)
    print("审计总结".center(80))
    print("="*80)
    
    total_issues = 0
    
    if cc_audit.get('date_errors'):
        print(f"  ⚠ 信用卡账单日期错误: {len(cc_audit['date_errors'])} 个")
        total_issues += len(cc_audit['date_errors'])
    
    if cc_audit.get('duplicates'):
        print(f"  ⚠ 信用卡重复账单: {len(cc_audit['duplicates'])} 组")
        total_issues += len(cc_audit['duplicates'])
    
    if savings_audit.get('duplicates'):
        print(f"  ⚠ 储蓄账户重复账单: {len(savings_audit['duplicates'])} 组")
        total_issues += len(savings_audit['duplicates'])
    
    if dup_customers:
        print(f"  ⚠ 重复客户: {len(dup_customers)} 组")
        total_issues += len(dup_customers)
    
    if dup_cards:
        print(f"  ⚠ 重复信用卡: {len(dup_cards)} 组")
        total_issues += len(dup_cards)
    
    if cc_audit.get('old_paths', 0) > 0:
        print(f"  ℹ 使用旧路径的文件: {cc_audit['old_paths']} 个")
    
    if total_issues == 0:
        print("\n  ✓ 数据库完全干净，没有发现任何问题！")
    else:
        print(f"\n  共发现 {total_issues} 个需要修复的问题")
        print("  建议运行清理脚本进行修复")
    
    print("="*80)
    
    return {
        'credit_card': cc_audit,
        'savings': savings_audit,
        'duplicate_customers': dup_customers,
        'duplicate_cards': dup_cards
    }

if __name__ == '__main__':
    main()
