#!/usr/bin/env python3
"""
信用卡月结单手动逐一验证工具
从头开始验证所有98份月结单
"""

import sys
sys.path.insert(0, '/home/runner/SmartCreditLoanManager')

import sqlite3
import subprocess
import os

def get_all_statements():
    """获取所有信用卡月结单，按银行、卡号、日期排序"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id,
            c.name as customer_name,
            c.customer_code,
            cc.bank_name,
            cc.card_number_last4,
            s.statement_date,
            s.statement_total,
            s.file_path,
            s.is_confirmed,
            COUNT(t.id) as txn_count,
            SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as debit_total,
            SUM(CASE WHEN t.amount < 0 THEN -t.amount ELSE 0 END) as credit_total
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        LEFT JOIN transactions t ON t.statement_id = s.id
        GROUP BY s.id
        ORDER BY cc.bank_name, cc.card_number_last4, s.statement_date
    """)
    
    statements = cursor.fetchall()
    conn.close()
    
    return statements

def get_statement_transactions(stmt_id):
    """获取月结单的所有交易"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT transaction_date, description, amount, category
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date, id
    """, (stmt_id,))
    
    txns = cursor.fetchall()
    conn.close()
    
    return txns

def display_statement(stmt, index, total):
    """显示月结单详细信息"""
    print("\n" + "=" * 120)
    print(f"验证进度: {index}/{total} ({index/total*100:.1f}%)")
    print("=" * 120)
    
    print(f"\n【月结单信息】")
    print(f"  Statement ID: {stmt['id']}")
    print(f"  客户: {stmt['customer_name']} ({stmt['customer_code']})")
    print(f"  银行: {stmt['bank_name']}")
    print(f"  卡号: #{stmt['card_number_last4']}")
    print(f"  账单日期: {stmt['statement_date']}")
    print(f"  账单总额: RM {stmt['statement_total']:,.2f}")
    print(f"  确认状态: {'✅ 已确认' if stmt['is_confirmed'] else '⏳ 未确认'}")
    print(f"  PDF路径: {stmt['file_path']}")
    
    print(f"\n【交易统计】")
    print(f"  交易笔数: {stmt['txn_count']}")
    print(f"  消费总额: RM {stmt['debit_total']:,.2f}")
    print(f"  付款总额: RM {stmt['credit_total']:,.2f}")
    
    # 获取交易明细
    txns = get_statement_transactions(stmt['id'])
    
    print(f"\n【交易明细】")
    for i, txn in enumerate(txns, 1):
        txn_type = "CR" if txn['amount'] < 0 else "DR"
        print(f"  {i:2d}. {txn['transaction_date']:9s} | {txn_type} | {txn['description'][:60]:60s} | RM {abs(txn['amount']):>10,.2f}")
    
    print("\n" + "=" * 120)

def open_pdf(pdf_path):
    """在系统中打开PDF（如果可能）"""
    if os.path.exists(pdf_path):
        try:
            # 使用pdfplumber显示PDF文本内容（前100行）
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages[:2])  # 前2页
                lines = text.split('\n')[:100]  # 前100行
                
                print("\n" + "=" * 120)
                print("PDF内容预览（前100行）")
                print("=" * 120)
                for i, line in enumerate(lines, 1):
                    print(f"{i:3d} | {line[:110]}")
                print("=" * 120)
        except Exception as e:
            print(f"❌ 无法读取PDF: {e}")
    else:
        print(f"❌ PDF文件不存在: {pdf_path}")

def mark_confirmed(stmt_id):
    """标记月结单为已确认"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE statements SET is_confirmed = 1 WHERE id = ?", (stmt_id,))
    conn.commit()
    conn.close()
    print("✅ 已标记为确认")

def main():
    statements = get_all_statements()
    total = len(statements)
    
    print("=" * 120)
    print(f"信用卡月结单手动验证工具 - 共{total}份月结单")
    print("=" * 120)
    
    current_index = 0
    
    while current_index < total:
        stmt = statements[current_index]
        display_statement(stmt, current_index + 1, total)
        
        print("\n操作选项:")
        print("  [Enter] 下一份")
        print("  [p] 查看PDF内容")
        print("  [c] 标记为已确认并继续")
        print("  [j] 跳转到指定序号")
        print("  [q] 退出")
        
        choice = input("\n请选择操作: ").strip().lower()
        
        if choice == 'q':
            print("\n退出验证。")
            break
        elif choice == 'p':
            open_pdf(stmt['file_path'])
        elif choice == 'c':
            mark_confirmed(stmt['id'])
            current_index += 1
        elif choice == 'j':
            try:
                jump_to = int(input("跳转到序号（1-{}）: ".format(total)))
                if 1 <= jump_to <= total:
                    current_index = jump_to - 1
                else:
                    print("❌ 无效序号")
            except:
                print("❌ 无效输入")
        else:  # Enter或其他
            current_index += 1
    
    # 显示最终统计
    statements = get_all_statements()
    confirmed = sum(1 for s in statements if s['is_confirmed'])
    
    print("\n" + "=" * 120)
    print("验证统计")
    print("=" * 120)
    print(f"  总月结单: {total}份")
    print(f"  已确认: {confirmed}份")
    print(f"  未确认: {total - confirmed}份")
    print("=" * 120)

if __name__ == "__main__":
    main()
