#!/usr/bin/env python3
"""
系统审计脚本 - 查找重复内容和优化建议
"""
import sqlite3
import os
from pathlib import Path
from collections import defaultdict
import json

def connect_db():
    return sqlite3.connect('db/smart_loan_manager.db')

def check_duplicate_statements():
    """检查重复的账单记录"""
    print("\n" + "="*80)
    print("📋 检查重复的信用卡账单")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 查找重复的信用卡账单（通过credit_cards表关联customer_id和bank_name）
    cursor.execute("""
        SELECT 
            c.customer_id,
            s.card_id,
            c.bank_name,
            strftime('%Y-%m', s.statement_date) as month,
            COUNT(*) as upload_count,
            GROUP_CONCAT(s.id) as statement_ids,
            GROUP_CONCAT(s.file_path, ' || ') as file_paths
        FROM statements s
        JOIN credit_cards c ON s.card_id = c.id
        GROUP BY c.customer_id, s.card_id, strftime('%Y-%m', s.statement_date)
        HAVING COUNT(*) > 1
        ORDER BY upload_count DESC
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n⚠️  发现 {len(duplicates)} 组重复账单：\n")
        total_redundant = 0
        for dup in duplicates:
            customer_id, card_id, bank, month, count, ids, paths = dup
            print(f"客户ID: {customer_id} | 卡片ID: {card_id} | 银行: {bank} | 月份: {month}")
            print(f"   重复次数: {count}")
            print(f"   账单IDs: {ids}")
            print(f"   文件路径:\n      {paths.replace(' || ', chr(10) + '      ')}")
            print()
            total_redundant += (count - 1)
        
        print(f"💾 总共有 {total_redundant} 条多余的重复记录需要清理")
    else:
        print("✅ 没有发现重复的信用卡账单")
    
    conn.close()
    return duplicates

def check_duplicate_savings_statements():
    """检查重复的储蓄账户月结单"""
    print("\n" + "="*80)
    print("💰 检查重复的储蓄账户月结单")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 通过savings_accounts表关联customer_id
    cursor.execute("""
        SELECT 
            sa.customer_id,
            sa.bank_name,
            strftime('%Y-%m', ss.statement_date) as month,
            COUNT(*) as upload_count,
            GROUP_CONCAT(ss.id) as statement_ids,
            GROUP_CONCAT(ss.file_path, ' || ') as file_paths
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        GROUP BY sa.customer_id, sa.bank_name, strftime('%Y-%m', ss.statement_date)
        HAVING COUNT(*) > 1
        ORDER BY upload_count DESC
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n⚠️  发现 {len(duplicates)} 组重复储蓄账户月结单：\n")
        total_redundant = 0
        for dup in duplicates:
            customer_id, bank, month, count, ids, paths = dup
            print(f"客户ID: {customer_id} | 银行: {bank} | 月份: {month}")
            print(f"   重复次数: {count}")
            print(f"   月结单IDs: {ids}")
            print(f"   文件路径:\n      {paths.replace(' || ', chr(10) + '      ')}")
            print()
            total_redundant += (count - 1)
        
        print(f"💾 总共有 {total_redundant} 条多余的储蓄账户记录需要清理")
    else:
        print("✅ 没有发现重复的储蓄账户月结单")
    
    conn.close()
    return duplicates

def analyze_file_storage():
    """分析文件存储结构"""
    print("\n" + "="*80)
    print("📁 分析文件存储结构")
    print("="*80)
    
    directories = {
        'uploads': 'static/uploads',
        'customer_files': 'static/customer_files',
        'reports': 'static/reports',
        'monthly_reports': 'static/monthly_reports',
        'exports': 'static/exports',
        'invoices': 'static/invoices'
    }
    
    file_analysis = {}
    
    for name, path in directories.items():
        if os.path.exists(path):
            pdf_files = list(Path(path).rglob('*.pdf'))
            jpg_files = list(Path(path).rglob('*.jpg')) + list(Path(path).rglob('*.png'))
            excel_files = list(Path(path).rglob('*.xlsx')) + list(Path(path).rglob('*.csv'))
            
            file_analysis[name] = {
                'path': path,
                'pdf_count': len(pdf_files),
                'image_count': len(jpg_files),
                'excel_count': len(excel_files),
                'total_size_mb': sum(f.stat().st_size for f in pdf_files + jpg_files + excel_files) / 1024 / 1024
            }
            
            print(f"\n📂 {name} ({path})")
            print(f"   PDF文件: {len(pdf_files)}")
            print(f"   图片文件: {len(jpg_files)}")
            print(f"   Excel文件: {len(excel_files)}")
            print(f"   总大小: {file_analysis[name]['total_size_mb']:.2f} MB")
    
    return file_analysis

def check_orphaned_files():
    """检查数据库中不存在的孤立文件"""
    print("\n" + "="*80)
    print("🔍 检查孤立文件（文件存在但数据库无记录）")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 获取数据库中所有的文件路径
    cursor.execute("SELECT file_path FROM statements WHERE file_path IS NOT NULL")
    db_statement_paths = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT file_path FROM savings_statements WHERE file_path IS NOT NULL")
    db_savings_paths = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT file_path FROM receipts WHERE file_path IS NOT NULL")
    db_receipt_paths = set(row[0] for row in cursor.fetchall())
    
    all_db_paths = db_statement_paths | db_savings_paths | db_receipt_paths
    
    conn.close()
    
    # 扫描所有上传的文件
    upload_dirs = ['static/uploads', 'static/customer_files']
    orphaned_files = []
    
    for upload_dir in upload_dirs:
        if os.path.exists(upload_dir):
            for file_path in Path(upload_dir).rglob('*.pdf'):
                relative_path = str(file_path)
                if relative_path not in all_db_paths:
                    orphaned_files.append(relative_path)
    
    if orphaned_files:
        print(f"\n⚠️  发现 {len(orphaned_files)} 个孤立文件：\n")
        for i, file in enumerate(orphaned_files[:20], 1):  # 只显示前20个
            print(f"{i}. {file}")
        if len(orphaned_files) > 20:
            print(f"... 还有 {len(orphaned_files) - 20} 个文件")
    else:
        print("✅ 没有发现孤立文件")
    
    return orphaned_files

def check_database_stats():
    """数据库统计信息"""
    print("\n" + "="*80)
    print("📊 数据库统计")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # 客户数
    cursor.execute("SELECT COUNT(*) FROM customers")
    stats['customers'] = cursor.fetchone()[0]
    
    # 信用卡数
    cursor.execute("SELECT COUNT(*) FROM credit_cards")
    stats['credit_cards'] = cursor.fetchone()[0]
    
    # 信用卡账单数
    cursor.execute("SELECT COUNT(*) FROM statements")
    stats['statements'] = cursor.fetchone()[0]
    
    # 储蓄账户数
    cursor.execute("SELECT COUNT(*) FROM savings_accounts")
    stats['savings_accounts'] = cursor.fetchone()[0]
    
    # 储蓄月结单数
    cursor.execute("SELECT COUNT(*) FROM savings_statements")
    stats['savings_statements'] = cursor.fetchone()[0]
    
    # 交易记录数
    cursor.execute("SELECT COUNT(*) FROM transactions")
    stats['transactions'] = cursor.fetchone()[0]
    
    # 收据数
    cursor.execute("SELECT COUNT(*) FROM receipts")
    stats['receipts'] = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n👥 客户数量: {stats['customers']}")
    print(f"💳 信用卡数量: {stats['credit_cards']}")
    print(f"📄 信用卡账单数量: {stats['statements']}")
    print(f"💰 储蓄账户数量: {stats['savings_accounts']}")
    print(f"📑 储蓄月结单数量: {stats['savings_statements']}")
    print(f"📝 交易记录数量: {stats['transactions']}")
    print(f"🧾 收据数量: {stats['receipts']}")
    
    return stats

def main():
    print("\n" + "="*80)
    print("🔍 开始系统审计 - Smart Credit & Loan Manager")
    print("="*80)
    
    # 1. 数据库统计
    stats = check_database_stats()
    
    # 2. 检查重复账单
    dup_statements = check_duplicate_statements()
    
    # 3. 检查重复储蓄月结单
    dup_savings = check_duplicate_savings_statements()
    
    # 4. 分析文件存储
    file_analysis = analyze_file_storage()
    
    # 5. 检查孤立文件
    orphaned = check_orphaned_files()
    
    # 生成总结报告
    print("\n" + "="*80)
    print("📋 审计总结")
    print("="*80)
    print(f"""
✅ 系统数据概况:
   - {stats['customers']} 个客户
   - {stats['credit_cards']} 张信用卡
   - {stats['statements']} 条信用卡账单
   - {stats['savings_accounts']} 个储蓄账户
   - {stats['savings_statements']} 条储蓄月结单
   - {stats['transactions']} 条交易记录
   - {stats['receipts']} 张收据

⚠️  发现的问题:
   - {len(dup_statements)} 组重复的信用卡账单
   - {len(dup_savings)} 组重复的储蓄月结单
   - {len(orphaned)} 个孤立文件（无数据库记录）

💡 优化建议:
   1. 清理重复的账单记录
   2. 统一文件存储结构
   3. 删除孤立文件
   4. 添加数据库唯一性约束
    """)

if __name__ == '__main__':
    main()
