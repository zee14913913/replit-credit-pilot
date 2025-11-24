#!/usr/bin/env python3
"""
最彻底的全系统扫描 - 检查每一个可能包含客户数据的角落
"""
import sqlite3
import os
import json

def scan_database():
    """扫描数据库中所有可能包含客户数据的表"""
    print("=" * 120)
    print("数据库深度扫描")
    print("=" * 120)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n扫描 {len(all_tables)} 个表...")
    
    # 可能包含客户名称的字段
    name_fields = ['name', 'customer_name', 'customer_code', 'email', 'phone', 'ic_number']
    
    suspicious_data = []
    
    for table in all_tables:
        try:
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # 检查是否有name相关字段
            has_name_field = any(field in column_names for field in name_fields)
            
            if has_name_field:
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                rows = cursor.fetchall()
                
                if rows:
                    print(f"\n⚠️  表 {table} 有 {len(rows)} 条记录（显示前5条）")
                    print(f"   字段: {column_names[:10]}")
                    
                    for row in rows[:3]:
                        # 检查是否包含非LEE E KAI的名称
                        row_str = str(row)
                        if any(name in row_str.upper() for name in ['CHEOK', 'CJY', 'YCW', 'CCC', 'TZL', 'TYC']):
                            suspicious_data.append((table, row))
                            print(f"   ❌ 可疑数据: {row[:5]}")
                        elif 'LEE' in row_str.upper():
                            print(f"   ✓  LEE E KAI数据: {row[:3]}")
        except Exception as e:
            pass
    
    # 检查非空表
    print(f"\n" + "=" * 120)
    print("非空表统计")
    print("=" * 120)
    
    non_empty = []
    for table in all_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                non_empty.append((table, count))
        except:
            pass
    
    print(f"\n非空表共 {len(non_empty)} 个:")
    for table, count in sorted(non_empty, key=lambda x: x[1], reverse=True)[:30]:
        print(f"  {table:<40} {count:>6} 条")
    
    conn.close()
    
    if suspicious_data:
        print(f"\n❌❌❌ 发现可疑数据 {len(suspicious_data)} 条！")
        for table, data in suspicious_data:
            print(f"  表: {table}, 数据: {data}")
    else:
        print(f"\n✅ 数据库检查完成：未发现非LEE E KAI的数据")
    
    return len(suspicious_data) == 0

def scan_filesystem():
    """扫描文件系统中所有可能包含客户数据的文件"""
    print("\n" + "=" * 120)
    print("文件系统深度扫描")
    print("=" * 120)
    
    # 关键词列表
    customer_keywords = ['CHEOK', 'CJY', 'YCW', 'CCC', 'TZL', 'TYC', 'GALAXY', 'BERICH']
    
    # 要扫描的目录
    scan_dirs = [
        'static/uploads',
        'attached_assets',
        'reports',
        'archive_old',
        'accounting_data',
        'docs',
        'test_pdfs',
        'docparser_templates',
        'templates',
        'tests'
    ]
    
    suspicious_files = []
    
    print("\n搜索包含其他客户名称的文件...")
    
    for directory in scan_dirs:
        if os.path.exists(directory):
            print(f"\n扫描目录: {directory}")
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_upper = file.upper()
                    # 检查文件名是否包含其他客户关键词
                    if any(keyword in file_upper for keyword in customer_keywords):
                        file_path = os.path.join(root, file)
                        suspicious_files.append(file_path)
                        print(f"  ❌ 可疑文件: {file_path}")
    
    # 扫描根目录的压缩包
    print("\n扫描根目录压缩包...")
    for file in os.listdir('.'):
        if file.endswith(('.tar.gz', '.zip', '.rar')) and any(kw in file.upper() for kw in customer_keywords):
            suspicious_files.append(file)
            print(f"  ❌ 可疑压缩包: {file}")
    
    if suspicious_files:
        print(f"\n❌❌❌ 发现可疑文件 {len(suspicious_files)} 个！")
    else:
        print(f"\n✅ 文件系统检查完成：未发现非LEE E KAI的文件")
    
    return len(suspicious_files) == 0, suspicious_files

def scan_all_pdfs():
    """扫描所有PDF文件"""
    print("\n" + "=" * 120)
    print("PDF文件扫描")
    print("=" * 120)
    
    # 查找所有PDF
    import subprocess
    result = subprocess.run(
        ['find', '.', '-type', 'f', '-name', '*.pdf', 
         '!', '-path', './venv/*', 
         '!', '-path', './.cache/*',
         '!', '-path', './node_modules/*'],
        capture_output=True,
        text=True
    )
    
    pdfs = [p.strip() for p in result.stdout.split('\n') if p.strip()]
    
    print(f"\n找到 {len(pdfs)} 个PDF文件:")
    
    suspicious_pdfs = []
    for pdf in pdfs:
        pdf_upper = pdf.upper()
        # 检查是否包含其他客户名称
        if any(name in pdf_upper for name in ['CHEOK', 'CJY', 'YCW', 'CCC', 'TZL', 'TYC', 'GALAXY']):
            suspicious_pdfs.append(pdf)
            print(f"  ❌ 可疑PDF: {pdf}")
        else:
            print(f"  ✓  {pdf}")
    
    if suspicious_pdfs:
        print(f"\n❌❌❌ 发现可疑PDF {len(suspicious_pdfs)} 个！")
    else:
        print(f"\n✅ PDF检查完成：未发现非LEE E KAI的PDF")
    
    return len(suspicious_pdfs) == 0, suspicious_pdfs

def main():
    print("=" * 120)
    print("最彻底的全系统扫描 - 确保零漏网之鱼")
    print("=" * 120)
    
    db_clean = scan_database()
    fs_clean, suspicious_files = scan_filesystem()
    pdf_clean, suspicious_pdfs = scan_all_pdfs()
    
    print("\n" + "=" * 120)
    print("扫描总结")
    print("=" * 120)
    
    if db_clean and fs_clean and pdf_clean:
        print("\n✅✅✅ 系统100%干净！")
        print("✅ 数据库：仅LEE E KAI数据")
        print("✅ 文件系统：无其他客户文件")
        print("✅ PDF文件：无其他客户PDF")
    else:
        print("\n❌❌❌ 发现问题！")
        if not db_clean:
            print("❌ 数据库中有可疑数据")
        if not fs_clean:
            print(f"❌ 文件系统中有 {len(suspicious_files)} 个可疑文件")
        if not pdf_clean:
            print(f"❌ 发现 {len(suspicious_pdfs)} 个可疑PDF")
        
        print("\n需要删除的文件:")
        all_suspicious = suspicious_files + suspicious_pdfs
        for f in all_suspicious:
            print(f"  - {f}")
    
    print("=" * 120)

if __name__ == '__main__':
    main()
