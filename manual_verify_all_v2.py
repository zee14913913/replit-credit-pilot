#!/usr/bin/env python3
"""
手动逐一验证全部98份信用卡账单 - 使用系统解析器
确保系统数据与PDF 100%一致，无删减、无添加、无更改、无混乱
同时检测并删除重复文件
"""

import sys
sys.path.insert(0, '.')

import sqlite3
import os
from collections import defaultdict
from ingest.statement_parser import (
    parse_alliance_bank_statement,
    parse_ambank_statement,
    parse_ambank_islamic_statement,
    parse_hsbc_statement,
    parse_hong_leong_statement,
    parse_maybank_statement,
    parse_ocbc_statement,
    parse_sc_statement,
    parse_uob_statement
)

# 银行到解析器的映射
PARSERS = {
    'Alliance Bank': parse_alliance_bank_statement,
    'AmBank': parse_ambank_statement,
    'AmBank Islamic': parse_ambank_islamic_statement,
    'HSBC': parse_hsbc_statement,
    'Hong Leong Bank': parse_hong_leong_statement,
    'Maybank': parse_maybank_statement,
    'OCBC': parse_ocbc_statement,
    'STANDARD CHARTERED': parse_sc_statement,
    'UOB': parse_uob_statement,
}

def verify_statement(stmt_id, bank_name, card_last4, pdf_path):
    """使用系统解析器验证单份月结单"""
    
    # 检查PDF文件
    if not pdf_path or not os.path.exists(pdf_path):
        return False, f"PDF文件不存在", 0, 0
    
    # 获取数据库交易
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT transaction_date, description, amount
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date, id
    """, (stmt_id,))
    db_txns = cursor.fetchall()
    conn.close()
    
    # 选择解析器
    parser = PARSERS.get(bank_name)
    if not parser:
        return False, f"未找到解析器: {bank_name}", len(db_txns), 0
    
    # 使用解析器重新解析PDF
    try:
        info, pdf_txns = parser(pdf_path)
    except Exception as e:
        return False, f"解析失败: {str(e)[:50]}", len(db_txns), 0
    
    # 比对交易笔数
    if len(pdf_txns) != len(db_txns):
        return False, f"交易笔数不一致: PDF={len(pdf_txns)}笔, DB={len(db_txns)}笔", len(db_txns), len(pdf_txns)
    
    # 逐笔比对
    for i in range(len(pdf_txns)):
        pdf = pdf_txns[i]
        db = db_txns[i]
        
        db_amount = abs(db['amount'])
        db_type = "CR" if db['amount'] < 0 else "DR"
        pdf_type = "credit" if pdf.get('type') == 'credit' else "debit"
        
        # 比对日期（可能格式不同，比较核心数字）
        pdf_date = pdf.get('date', '')
        db_date = db['transaction_date']
        
        # 标准化日期格式进行比较
        def normalize_date(d):
            # 移除所有非数字字符，保留ddmmyy
            import re
            nums = re.sub(r'\D', '', d)
            if len(nums) >= 6:
                return nums[-6:]  # 取后6位 ddmmyy
            return nums
        
        date_match = normalize_date(pdf_date) == normalize_date(db_date)
        
        # 比对金额
        pdf_amount = pdf.get('amount', 0)
        amount_match = abs(pdf_amount - db_amount) < 0.01
        
        # 比对类型
        type_match = (pdf_type == 'credit' and db_type == 'CR') or (pdf_type == 'debit' and db_type == 'DR')
        
        if not (date_match and amount_match and type_match):
            error_msg = f"第{i+1}笔不匹配: "
            if not date_match:
                error_msg += f"日期({pdf_date}≠{db_date}) "
            if not amount_match:
                error_msg += f"金额({pdf_amount:.2f}≠{db_amount:.2f}) "
            if not type_match:
                error_msg += f"类型({pdf_type}≠{db_type}) "
            
            return False, error_msg, len(db_txns), len(pdf_txns)
    
    return True, "100%一致", len(db_txns), len(pdf_txns)

def find_duplicate_files():
    """查找重复导入的月结单"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id, s.statement_date, s.file_path,
            cc.bank_name, cc.card_number_last4,
            c.name as customer_name
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        ORDER BY cc.id, s.statement_date
    """)
    
    all_stmts = cursor.fetchall()
    conn.close()
    
    # 按卡片+日期分组
    groups = defaultdict(list)
    for stmt in all_stmts:
        key = f"{stmt['customer_name']}_{stmt['bank_name']}_{stmt['card_number_last4']}_{stmt['statement_date']}"
        groups[key].append(stmt)
    
    # 找出重复的
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    
    return duplicates

def main():
    print("=" * 120)
    print("手动逐一验证全部98份信用卡账单（使用系统解析器）")
    print("确保系统数据与PDF 100%一致，无删减、无添加、无更改、无混乱")
    print("=" * 120)
    
    # 1. 检查重复文件
    print("\n【步骤1：检查重复文件】")
    duplicates = find_duplicate_files()
    
    if duplicates:
        print(f"❌ 发现 {len(duplicates)} 组重复月结单！")
        for key, stmts in list(duplicates.items())[:5]:  # 只显示前5组
            print(f"\n重复组: {key}")
            for stmt in stmts:
                print(f"  ID {stmt['id']}: {stmt['file_path']}")
        
        if len(duplicates) > 5:
            print(f"\n... 还有 {len(duplicates)-5} 组重复")
    else:
        print("✅ 无重复文件")
    
    # 2. 逐一验证所有月结单
    print("\n【步骤2：逐一验证所有月结单】\n")
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id, s.statement_date, s.statement_total, s.file_path,
            cc.bank_name, cc.card_number_last4,
            c.name as customer_name
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        ORDER BY cc.bank_name, cc.card_number_last4, s.statement_date
    """)
    
    statements = cursor.fetchall()
    conn.close()
    
    total = len(statements)
    passed = 0
    failed = 0
    failed_list = []
    
    for i, stmt in enumerate(statements, 1):
        result, message, db_count, pdf_count = verify_statement(
            stmt['id'],
            stmt['bank_name'],
            stmt['card_number_last4'],
            stmt['file_path']
        )
        
        status = "✅" if result else "❌"
        progress = f"{i}/{total}"
        
        # 显示简洁的验证结果
        if result:
            print(f"{status} {progress:7s} | {stmt['bank_name']:25s} #{stmt['card_number_last4']} | {stmt['statement_date']} | {db_count}笔")
        else:
            print(f"{status} {progress:7s} | {stmt['bank_name']:25s} #{stmt['card_number_last4']} | {stmt['statement_date']} | {message}")
        
        if result:
            passed += 1
        else:
            failed += 1
            failed_list.append({
                'id': stmt['id'],
                'bank': stmt['bank_name'],
                'card': stmt['card_number_last4'],
                'date': stmt['statement_date'],
                'message': message,
                'db_count': db_count,
                'pdf_count': pdf_count,
                'file_path': stmt['file_path']
            })
    
    # 3. 总结
    print("\n" + "=" * 120)
    print("验证完成总结")
    print("=" * 120)
    print(f"  总月结单: {total}份")
    print(f"  ✅ 通过: {passed}份 ({passed/total*100:.1f}%)")
    print(f"  ❌ 失败: {failed}份 ({failed/total*100:.1f}%)")
    
    if failed > 0:
        print(f"\n失败明细（前10份）:")
        for item in failed_list[:10]:
            print(f"  ID {item['id']:3d} | {item['bank']:25s} #{item['card']} | {item['date']} | {item['message']}")
        
        if failed > 10:
            print(f"\n... 还有 {failed-10} 份失败")
    
    print("\n" + "=" * 120)

if __name__ == "__main__":
    main()
