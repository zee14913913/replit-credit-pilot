#!/usr/bin/env python3
"""
批量修复所有信用卡账单字段
直接从PDF重新提取4个字段并更新数据库
重点修复：重复的minimum_payment、异常值、缺失值
"""

import sqlite3
import os
import sys
from pdf_field_extractor import PDFFieldExtractor
from datetime import datetime

def fix_all_statements(dry_run=True):
    """
    批量修复所有statements记录
    
    Args:
        dry_run: True=仅预览，False=实际更新
    """
    db_path = 'db/smart_loan_manager.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有statements记录
    cursor.execute('''
        SELECT 
            s.id,
            s.card_id,
            s.statement_date,
            s.due_date,
            s.statement_total,
            s.minimum_payment,
            s.file_path,
            cc.bank_name,
            c.name as customer_name
        FROM statements s
        INNER JOIN credit_cards cc ON s.card_id = cc.id
        INNER JOIN customers c ON cc.customer_id = c.id
        ORDER BY s.id
    ''')
    
    all_records = cursor.fetchall()
    total_records = len(all_records)
    
    print(f"\n{'='*100}")
    print(f"📊 批量修复信用卡账单字段 - {'🔍 DRY RUN (仅预览)' if dry_run else '⚠️ LIVE RUN (实际更新)'}")
    print(f"{'='*100}\n")
    print(f"总记录数: {total_records}条\n")
    
    extractor = PDFFieldExtractor()
    
    updated_count = 0
    error_count = 0
    skipped_count = 0
    
    for record in all_records:
        stmt_id = record['id']
        pdf_path = record['file_path']
        bank_name = record['bank_name']
        customer_name = record['customer_name']
        
        # 当前数据库值
        db_stmt_date = record['statement_date']
        db_due_date = record['due_date']
        db_stmt_total = record['statement_total']
        db_min_payment = record['minimum_payment']
        
        # 检查PDF文件是否存在
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"❌ Statement {stmt_id} ({customer_name} - {bank_name}): PDF文件不存在 ({pdf_path})")
            error_count += 1
            continue
        
        # 跳过非PDF文件
        if not pdf_path.lower().endswith('.pdf'):
            print(f"⏭️  Statement {stmt_id} ({customer_name} - {bank_name}): 跳过非PDF文件 ({os.path.basename(pdf_path)})")
            skipped_count += 1
            continue
        
        try:
            # 从PDF重新提取字段
            pdf_data = extractor.extract_fields(pdf_path, bank_name)
            
            pdf_stmt_date = pdf_data.get('statement_date')
            pdf_due_date = pdf_data.get('due_date')
            pdf_stmt_total = pdf_data.get('statement_total')
            pdf_min_payment = pdf_data.get('minimum_payment')
            
            # 检查是否需要更新
            needs_update = False
            updates = []
            
            # 比较Statement Date
            if pdf_stmt_date and pdf_stmt_date != db_stmt_date:
                needs_update = True
                updates.append(f"Statement Date: {db_stmt_date} → {pdf_stmt_date}")
            
            # 比较Due Date
            if pdf_due_date and pdf_due_date != db_due_date:
                needs_update = True
                updates.append(f"Due Date: {db_due_date} → {pdf_due_date}")
            
            # 比较Statement Total
            if pdf_stmt_total:
                try:
                    pdf_total_float = float(pdf_stmt_total)
                    if db_stmt_total is None or abs(pdf_total_float - db_stmt_total) > 0.01:
                        needs_update = True
                        updates.append(f"Statement Total: RM{db_stmt_total} → RM{pdf_total_float}")
                except:
                    pass
            
            # 比较Minimum Payment
            if pdf_min_payment:
                try:
                    pdf_min_float = float(pdf_min_payment)
                    if db_min_payment is None or abs(pdf_min_float - db_min_payment) > 0.01:
                        needs_update = True
                        updates.append(f"Minimum Payment: RM{db_min_payment} → RM{pdf_min_float}")
                except:
                    pass
            
            if needs_update:
                print(f"\n✅ Statement {stmt_id} ({customer_name} - {bank_name} - {db_stmt_date})")
                print(f"   PDF文件: {os.path.basename(pdf_path)}")
                for update in updates:
                    print(f"   • {update}")
                
                if not dry_run:
                    # 实际更新数据库
                    update_sql = '''
                        UPDATE statements
                        SET statement_date = ?,
                            due_date = ?,
                            statement_total = ?,
                            minimum_payment = ?
                        WHERE id = ?
                    '''
                    
                    cursor.execute(update_sql, (
                        pdf_stmt_date or db_stmt_date,
                        pdf_due_date or db_due_date,
                        float(pdf_stmt_total) if pdf_stmt_total else db_stmt_total,
                        float(pdf_min_payment) if pdf_min_payment else db_min_payment,
                        stmt_id
                    ))
                    conn.commit()
                
                updated_count += 1
            else:
                # 数据已匹配，无需更新
                pass
                
        except Exception as e:
            print(f"❌ Statement {stmt_id} ({customer_name} - {bank_name}): 提取失败 - {str(e)}")
            error_count += 1
            continue
    
    conn.close()
    
    print(f"\n{'='*100}")
    print(f"📊 修复完成统计")
    print(f"{'='*100}")
    print(f"总记录数: {total_records}条")
    print(f"✅ 需要更新: {updated_count}条")
    print(f"⏭️  跳过非PDF: {skipped_count}条")
    print(f"❌ 错误失败: {error_count}条")
    print(f"✓ 无需更新: {total_records - updated_count - skipped_count - error_count}条")
    
    if dry_run:
        print(f"\n⚠️  这是DRY RUN预览，未实际修改数据库")
        print(f"运行以下命令进行实际更新：")
        print(f"  python3 fix_all_statements.py --confirm")
    else:
        print(f"\n✅ 数据库已成功更新！")
    
    print(f"{'='*100}\n")

if __name__ == '__main__':
    # 检查是否有--confirm参数
    if '--confirm' in sys.argv:
        print("\n⚠️  WARNING: 这将修改数据库！\n")
        response = input("确认继续？(yes/no): ")
        if response.lower() == 'yes':
            fix_all_statements(dry_run=False)
        else:
            print("已取消。")
    else:
        # 默认DRY RUN
        fix_all_statements(dry_run=True)
