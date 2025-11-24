#!/usr/bin/env python3
"""
识别PDF文件缺失的记录
生成需要重新上传的清单
同时重新解析以追踪解析失败（即使有旧数据）
"""
import sqlite3
import os
from datetime import datetime
from pdf_field_extractor import PDFFieldExtractor

def identify_missing_pdfs():
    """识别所有PDF文件缺失的记录"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 查询所有记录（所有银行）
    cursor.execute("""
        SELECT s.id, c.bank_name, s.statement_date, s.file_path, 
               c.card_number_last4, s.statement_total, s.minimum_payment
        FROM statements s
        INNER JOIN credit_cards c ON s.card_id = c.id
        ORDER BY c.bank_name, s.statement_date DESC
    """)
    
    all_records = cursor.fetchall()
    
    # 初始化解析器
    extractor = PDFFieldExtractor()
    
    # 分类统计
    missing_pdfs = []
    parse_errors = []
    success = []
    
    for record in all_records:
        stmt_id, bank_name, stmt_date, file_path, last4, total, min_payment = record
        
        # 检查PDF文件是否存在
        if not file_path or not os.path.exists(file_path):
            missing_pdfs.append({
                'id': stmt_id,
                'bank': bank_name,
                'date': stmt_date,
                'path': file_path or 'NULL',
                'last4': last4,
                'reason': 'PDF文件不存在'
            })
        # 检查是否有字段为NULL（解析失败）- 使用is None避免将0.00误判为缺失
        elif stmt_date is None or total is None or min_payment is None:
            parse_errors.append({
                'id': stmt_id,
                'bank': bank_name,
                'date': stmt_date or 'NULL',
                'path': file_path,
                'last4': last4,
                'missing_fields': [],
                'reason': '字段为NULL'
            })
            if stmt_date is None:
                parse_errors[-1]['missing_fields'].append('statement_date')
            if total is None:
                parse_errors[-1]['missing_fields'].append('statement_total')
            if min_payment is None:
                parse_errors[-1]['missing_fields'].append('minimum_payment')
        # 对于PDF文件（非Excel），重新解析以验证数据质量
        elif file_path.endswith('.pdf'):
            try:
                result = extractor.extract_fields(file_path, bank_name)
                if result['extraction_errors']:
                    # 解析失败，但数据库有旧数据
                    parse_errors.append({
                        'id': stmt_id,
                        'bank': bank_name,
                        'date': stmt_date,
                        'path': file_path,
                        'last4': last4,
                        'missing_fields': result['extraction_errors'],
                        'reason': 'PDF无法解析（数据库有旧数据）'
                    })
                else:
                    # 解析成功
                    success.append({
                        'id': stmt_id,
                        'bank': bank_name,
                        'date': stmt_date
                    })
            except Exception as e:
                # 解析异常
                parse_errors.append({
                    'id': stmt_id,
                    'bank': bank_name,
                    'date': stmt_date,
                    'path': file_path,
                    'last4': last4,
                    'missing_fields': [str(e)],
                    'reason': 'PDF解析异常'
                })
        else:
            # Excel文件或其他格式
            success.append({
                'id': stmt_id,
                'bank': bank_name,
                'date': stmt_date
            })
    
    # 生成报告
    print("=" * 120)
    print("PDF文件质量审计报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    
    print(f"\n总记录数: {len(all_records)}")
    print(f"✅ 成功提取: {len(success)} ({len(success)/len(all_records)*100:.1f}%)")
    print(f"❌ PDF文件缺失: {len(missing_pdfs)} ({len(missing_pdfs)/len(all_records)*100:.1f}%)")
    print(f"⚠️  解析错误/字段缺失: {len(parse_errors)} ({len(parse_errors)/len(all_records)*100:.1f}%)")
    
    # 按银行分组统计
    bank_stats = {}
    for record in all_records:
        bank = record[1]
        if bank not in bank_stats:
            bank_stats[bank] = {'total': 0, 'success': 0, 'missing': 0, 'error': 0}
        bank_stats[bank]['total'] += 1
    
    for item in success:
        bank_stats[item['bank']]['success'] += 1
    for item in missing_pdfs:
        bank_stats[item['bank']]['missing'] += 1
    for item in parse_errors:
        bank_stats[item['bank']]['error'] += 1
    
    print("\n" + "=" * 120)
    print("按银行统计")
    print("=" * 120)
    print(f"{'银行':<30} {'总数':>8} {'成功':>8} {'PDF缺失':>10} {'解析错误':>10} {'成功率':>10}")
    print("-" * 120)
    for bank, stats in sorted(bank_stats.items()):
        success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"{bank:<30} {stats['total']:>8} {stats['success']:>8} {stats['missing']:>10} {stats['error']:>10} {success_rate:>9.1f}%")
    
    # 打印缺失PDF清单
    if missing_pdfs:
        print("\n" + "=" * 120)
        print("❌ PDF文件缺失清单 - 需要客户重新上传")
        print("=" * 120)
        print(f"{'ID':<6} {'银行':<25} {'对账单日期':<15} {'卡号后4位':<12} {'原因':<30} {'原路径'}")
        print("-" * 120)
        for item in sorted(missing_pdfs, key=lambda x: (x['bank'], x['date'])):
            print(f"{item['id']:<6} {item['bank']:<25} {item['date']:<15} {item['last4']:<12} {item['reason']:<30} {item['path']}")
    
    # 打印解析错误清单
    if parse_errors:
        print("\n" + "=" * 120)
        print("⚠️  解析错误清单 - PDF存在但字段提取失败")
        print("=" * 120)
        print(f"{'ID':<6} {'银行':<25} {'对账单日期':<15} {'卡号后4位':<12} {'原因':<35} {'错误详情':<50}")
        print("-" * 120)
        for item in sorted(parse_errors, key=lambda x: (x['bank'], x['date'] or '')):
            missing_str = '; '.join([str(f) for f in item['missing_fields']][:100])
            print(f"{item['id']:<6} {item['bank']:<25} {item['date']:<15} {item['last4']:<12} {item['reason']:<35} {missing_str[:50]}")
    
    # 生成CSV文件供客户参考
    with open('missing_pdfs_report.csv', 'w', encoding='utf-8') as f:
        f.write("分类,ID,银行,对账单日期,卡号后4位,原PDF路径,原因,缺失字段/错误详情\n")
        for item in missing_pdfs:
            f.write(f"PDF缺失,{item['id']},{item['bank']},{item['date']},{item['last4']},{item['path']},{item['reason']},\n")
        for item in parse_errors:
            missing_str = ';'.join([str(f) for f in item['missing_fields']])
            f.write(f"解析错误,{item['id']},{item['bank']},{item['date']},{item['last4']},{item['path']},{item['reason']},{missing_str}\n")
    
    print("\n" + "=" * 120)
    print("✅ CSV报告已生成: missing_pdfs_report.csv")
    print("=" * 120)
    
    conn.close()
    
    return {
        'total': len(all_records),
        'success': len(success),
        'missing': len(missing_pdfs),
        'error': len(parse_errors),
        'missing_list': missing_pdfs,
        'error_list': parse_errors
    }

if __name__ == '__main__':
    identify_missing_pdfs()
