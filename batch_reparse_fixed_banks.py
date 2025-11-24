#!/usr/bin/env python3
"""
批量重新解析UOB、HSBC、Standard Chartered的PDF文件
使用修复后的解析器，用真实PDF数据更新数据库
"""
import sqlite3
import os
from pdf_field_extractor import PDFFieldExtractor
from datetime import datetime

# 目标银行
TARGET_BANKS = ['UOB', 'HSBC', 'STANDARD CHARTERED']

def batch_reparse():
    """批量重新解析受影响的银行"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    extractor = PDFFieldExtractor()
    
    # 统计
    stats = {
        'total': 0,
        'success': 0,
        'pdf_missing': 0,
        'parse_error': 0,
        'by_bank': {}
    }
    
    print("=" * 100)
    print("批量重新解析UOB/HSBC/Standard Chartered PDF文件")
    print("=" * 100)
    
    # 查询所有需要重新解析的记录
    for bank in TARGET_BANKS:
        cursor.execute("""
            SELECT id, bank_name, pdf_filename, statement_date, due_date, 
                   statement_total, minimum_payment
            FROM credit_card_statements
            WHERE bank_name = ?
            ORDER BY statement_date DESC
        """, (bank,))
        
        records = cursor.fetchall()
        stats['by_bank'][bank] = {
            'total': len(records),
            'success': 0,
            'pdf_missing': 0,
            'parse_error': 0
        }
        
        print(f"\n{bank}: 找到 {len(records)} 条记录")
        print("-" * 100)
        
        for record in records:
            stmt_id, bank_name, pdf_filename, old_stmt_date, old_due_date, old_total, old_min_payment = record
            stats['total'] += 1
            
            # 检查PDF文件是否存在
            if not pdf_filename or not os.path.exists(pdf_filename):
                print(f"❌ ID {stmt_id}: PDF文件不存在 - {pdf_filename}")
                stats['pdf_missing'] += 1
                stats['by_bank'][bank]['pdf_missing'] += 1
                continue
            
            # 使用新解析器重新提取
            try:
                result = extractor.extract_fields(pdf_filename, bank_name)
                
                if result['extraction_errors']:
                    print(f"⚠️  ID {stmt_id}: 解析错误 - {result['extraction_errors']}")
                    stats['parse_error'] += 1
                    stats['by_bank'][bank]['parse_error'] += 1
                    continue
                
                # 更新数据库
                cursor.execute("""
                    UPDATE credit_card_statements
                    SET statement_date = ?,
                        due_date = ?,
                        statement_total = ?,
                        minimum_payment = ?
                    WHERE id = ?
                """, (
                    result['statement_date'],
                    result['due_date'],
                    result['statement_total'],
                    result['minimum_payment'],
                    stmt_id
                ))
                
                # 显示变更
                changed = []
                if old_stmt_date != result['statement_date']:
                    changed.append(f"StmtDate: {old_stmt_date} → {result['statement_date']}")
                if old_due_date != result['due_date']:
                    changed.append(f"DueDate: {old_due_date} → {result['due_date']}")
                if old_total != result['statement_total']:
                    changed.append(f"Total: {old_total} → {result['statement_total']}")
                if old_min_payment != result['minimum_payment']:
                    changed.append(f"MinPay: {old_min_payment} → {result['minimum_payment']}")
                
                if changed:
                    print(f"✅ ID {stmt_id}: 更新成功 - {', '.join(changed)}")
                else:
                    print(f"✅ ID {stmt_id}: 数据未变更（已是正确值）")
                
                stats['success'] += 1
                stats['by_bank'][bank]['success'] += 1
                
            except Exception as e:
                print(f"❌ ID {stmt_id}: 解析失败 - {str(e)}")
                stats['parse_error'] += 1
                stats['by_bank'][bank]['parse_error'] += 1
    
    # 提交更改
    conn.commit()
    conn.close()
    
    # 打印汇总统计
    print("\n" + "=" * 100)
    print("重新解析汇总统计")
    print("=" * 100)
    print(f"总记录数: {stats['total']}")
    print(f"✅ 成功更新: {stats['success']}")
    print(f"❌ PDF文件缺失: {stats['pdf_missing']}")
    print(f"⚠️  解析错误: {stats['parse_error']}")
    
    print("\n按银行统计:")
    for bank, bank_stats in stats['by_bank'].items():
        print(f"\n{bank}:")
        print(f"  总数: {bank_stats['total']}")
        print(f"  ✅ 成功: {bank_stats['success']}")
        print(f"  ❌ PDF缺失: {bank_stats['pdf_missing']}")
        print(f"  ⚠️  解析错误: {bank_stats['parse_error']}")
    
    print("\n" + "=" * 100)
    print("批量重新解析完成！")
    print("=" * 100)
    
    return stats

if __name__ == '__main__':
    batch_reparse()
