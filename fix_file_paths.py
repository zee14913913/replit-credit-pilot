#!/usr/bin/env python3
"""
修复数据库中的file_path，使其指向正确的文件位置
文件实际在: /UOB/2025-05/UOB_3530_2025-05-13.pdf
但数据库记录: /UOB_3530_2025-05-13.pdf
"""
import sqlite3
import os
import re

def fix_file_paths():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 查询所有记录
    cursor.execute("""
        SELECT s.id, c.bank_name, s.file_path, s.statement_date
        FROM statements s
        INNER JOIN credit_cards c ON s.card_id = c.id
        WHERE s.file_path IS NOT NULL AND s.file_path != ''
        ORDER BY c.bank_name, s.statement_date
    """)
    
    all_records = cursor.fetchall()
    
    fixed_count = 0
    not_found_count = 0
    already_correct_count = 0
    
    print("=" * 120)
    print("修复数据库文件路径")
    print("=" * 120)
    
    for stmt_id, bank_name, old_path, stmt_date in all_records:
        # 检查文件是否存在
        if os.path.exists(old_path):
            already_correct_count += 1
            continue
        
        # 尝试构建新路径
        # 从文件名提取信息
        filename = os.path.basename(old_path)
        base_dir = os.path.dirname(old_path)
        
        # 提取年月（从statement_date或filename）
        if stmt_date:
            # 解析日期格式
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', stmt_date)
            if date_match:
                year, month = date_match.group(1), date_match.group(2)
                year_month = f"{year}-{month}"
            else:
                # 尝试从filename提取
                date_match = re.search(r'(\d{4})-(\d{2})-\d{2}', filename)
                if date_match:
                    year, month = date_match.group(1), date_match.group(2)
                    year_month = f"{year}-{month}"
                else:
                    print(f"⚠️  ID {stmt_id}: 无法提取日期 - {stmt_date}, {filename}")
                    not_found_count += 1
                    continue
        else:
            print(f"⚠️  ID {stmt_id}: statement_date为空")
            not_found_count += 1
            continue
        
        # 构建新路径格式: base_dir/BANK_NAME/YYYY-MM/filename
        new_path = os.path.join(base_dir, bank_name.replace(' ', '_').upper(), year_month, filename)
        
        # 检查新路径是否存在
        if os.path.exists(new_path):
            # 更新数据库
            cursor.execute("UPDATE statements SET file_path = ? WHERE id = ?", (new_path, stmt_id))
            print(f"✅ ID {stmt_id}: {bank_name} - 路径已修复")
            print(f"   旧: {old_path}")
            print(f"   新: {new_path}")
            fixed_count += 1
        else:
            # 尝试其他可能的银行名称格式
            possible_bank_names = [
                bank_name,
                bank_name.replace(' ', '_'),
                bank_name.replace(' ', '_').upper(),
                bank_name.replace(' ', '').upper(),
                bank_name.upper()
            ]
            
            found = False
            for alt_bank in possible_bank_names:
                alt_path = os.path.join(base_dir, alt_bank, year_month, filename)
                if os.path.exists(alt_path):
                    cursor.execute("UPDATE statements SET file_path = ? WHERE id = ?", (alt_path, stmt_id))
                    print(f"✅ ID {stmt_id}: {bank_name} - 路径已修复（使用备选格式: {alt_bank}）")
                    print(f"   旧: {old_path}")
                    print(f"   新: {alt_path}")
                    fixed_count += 1
                    found = True
                    break
            
            if not found:
                print(f"❌ ID {stmt_id}: 文件未找到 - {bank_name}")
                print(f"   原路径: {old_path}")
                print(f"   尝试路径: {new_path}")
                not_found_count += 1
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 120)
    print("路径修复完成")
    print("=" * 120)
    print(f"✅ 已修复: {fixed_count}")
    print(f"✓  路径正确（无需修复）: {already_correct_count}")
    print(f"❌ 文件未找到: {not_found_count}")
    print(f"总计: {fixed_count + already_correct_count + not_found_count}")
    print("=" * 120)

if __name__ == '__main__':
    fix_file_paths()
