#!/usr/bin/env python3
"""批量重新解析Alliance Bank PDF文件并更新数据库"""

import sqlite3
import os
from pdf_field_extractor import PDFFieldExtractor
from decimal import Decimal

def batch_reparse_alliance():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找所有Alliance Bank记录
    cursor.execute('''
        SELECT 
            s.id,
            s.file_path,
            s.statement_date,
            s.statement_total,
            s.minimum_payment,
            s.due_date,
            c.name as customer_name
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        WHERE cc.bank_name = 'Alliance Bank'
        ORDER BY s.id
    ''')
    
    records = cursor.fetchall()
    total_records = len(records)
    updated_count = 0
    failed_count = 0
    
    print("=" * 80)
    print(f"📊 Alliance Bank批量重新解析")
    print("=" * 80)
    print(f"找到 {total_records} 条Alliance Bank记录\n")
    
    extractor = PDFFieldExtractor()
    
    for record in records:
        stmt_id = record['id']
        pdf_path = record['file_path']
        old_total = record['statement_total']
        old_min_pay = record['minimum_payment']
        old_due_date = record['due_date']
        
        print(f"\n处理ID {stmt_id}: {record['customer_name']} - {record['statement_date']}")
        print(f"  旧值: Total=RM{old_total}, MinPay=RM{old_min_pay}, DueDate={old_due_date}")
        
        # 检查PDF文件是否存在
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"  ❌ PDF文件不存在: {pdf_path}")
            failed_count += 1
            continue
        
        # 重新解析PDF
        try:
            result = extractor.extract_fields(pdf_path, 'Alliance Bank')
            
            if result['extraction_errors']:
                print(f"  ⚠️ 解析警告: {result['extraction_errors']}")
            
            # 检查是否成功提取所有必需字段
            if result['statement_total'] and result['minimum_payment']:
                # 更新数据库
                cursor.execute('''
                    UPDATE statements
                    SET statement_total = ?,
                        minimum_payment = ?,
                        due_date = ?
                    WHERE id = ?
                ''', (
                    float(result['statement_total']) if result['statement_total'] else old_total,
                    float(result['minimum_payment']) if result['minimum_payment'] else old_min_pay,
                    result['due_date'] if result['due_date'] else old_due_date,
                    stmt_id
                ))
                
                print(f"  ✅ 更新成功:")
                print(f"     Total: RM{old_total} → RM{result['statement_total']}")
                print(f"     MinPay: RM{old_min_pay} → RM{result['minimum_payment']}")
                print(f"     DueDate: {old_due_date} → {result['due_date']}")
                
                updated_count += 1
            else:
                print(f"  ❌ 提取失败: 缺少必需字段")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            failed_count += 1
    
    # 提交事务
    conn.commit()
    
    # 最终统计
    print("\n" + "=" * 80)
    print(f"📈 批量处理完成")
    print("=" * 80)
    print(f"  • 总记录数: {total_records}")
    print(f"  • 成功更新: {updated_count}")
    print(f"  • 处理失败: {failed_count}")
    
    # 验证更新结果
    print("\n" + "=" * 80)
    print(f"🔍 验证更新后的数据")
    print("=" * 80)
    
    cursor.execute('''
        SELECT 
            s.id,
            s.statement_date,
            s.statement_total,
            s.minimum_payment,
            s.due_date,
            CASE 
                WHEN s.statement_total > 0 AND s.minimum_payment > 0 
                THEN ROUND(CAST(s.minimum_payment AS FLOAT) / s.statement_total * 100, 2) 
                ELSE NULL 
            END as payment_ratio
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.bank_name = 'Alliance Bank'
        ORDER BY s.id DESC
        LIMIT 10
    ''')
    
    verified_records = cursor.fetchall()
    for rec in verified_records:
        ratio_str = f"{rec['payment_ratio']:.2f}%" if rec['payment_ratio'] else "N/A"
        print(f"  ID {rec['id']:3}: {rec['statement_date']} | "
              f"Total: RM {rec['statement_total']:10.2f} | "
              f"MinPay: RM {rec['minimum_payment']:8.2f} | "
              f"比例: {ratio_str:6} | "
              f"Due: {rec['due_date'] or 'NULL'}")
    
    conn.close()
    
    return {
        'total': total_records,
        'updated': updated_count,
        'failed': failed_count
    }

if __name__ == '__main__':
    stats = batch_reparse_alliance()
