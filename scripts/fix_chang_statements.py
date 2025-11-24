#!/usr/bin/env python3
"""
专门修复Chang Choon Chow的12个月账单日期
文件名格式: 12:01:2025 = DD:MM:YYYY = 2025年1月12日
"""

import sqlite3
import os
import shutil
import re

DB_PATH = 'db/smart_loan_manager.db'

# 账单ID到正确日期的映射（基于文件名分析）
CORRECTIONS = {
    154: ('2025-01-12', '12:01:2025'),  # 1月
    155: ('2025-02-12', '12:02:2025'),  # 2月
    156: ('2025-03-12', '12:03:2025'),  # 3月
    157: ('2025-04-12', '12:04:1025'),  # 4月 (原本1025年错误)
    158: ('2025-05-12', '12:05:2025'),  # 5月
    159: ('2025-06-12', '12:06:2025'),  # 6月
    160: ('2025-07-12', '12:07:2025'),  # 7月
    161: ('2025-08-12', '12:08:2025'),  # 8月
    162: ('2025-09-12', '12:09:2024'),  # 9月 (原本2024年)
    163: ('2025-10-12', '12:10:2024'),  # 10月
    164: ('2025-11-12', '12:11:2024'),  # 11月
    165: ('2025-12-12', '12:12:2024'),  # 12月
}

def fix_chang_statements():
    """修复Chang的账单日期和文件路径"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("="*60)
    print("修复Chang Choon Chow的12个月账单".center(60))
    print("="*60)
    
    fixed_count = 0
    
    for stmt_id, (correct_date, original_filename) in CORRECTIONS.items():
        # 获取当前记录
        row = cursor.execute(
            'SELECT statement_date, file_path FROM statements WHERE id = ?',
            (stmt_id,)
        ).fetchone()
        
        if not row:
            print(f"⚠ Statement {stmt_id} 不存在")
            continue
        
        old_date, old_path = row
        
        # 计算新路径
        year_month = correct_date[:7]  # 2025-01
        new_path = f"static/uploads/CHANG_CHOON_CHOW/{year_month}/statements/Alliance_Bank_4514_{correct_date}.pdf"
        
        print(f"\nStatement {stmt_id}:")
        print(f"  日期: {old_date} → {correct_date}")
        print(f"  路径: {old_path}")
        print(f"      → {new_path}")
        
        # 创建新目录
        new_dir = os.path.dirname(new_path)
        os.makedirs(new_dir, exist_ok=True)
        
        # 移动或复制文件
        if os.path.exists(old_path):
            try:
                shutil.copy2(old_path, new_path)
                print(f"  ✓ 文件已复制到新位置")
            except Exception as e:
                print(f"  ✗ 文件复制失败: {e}")
                continue
        else:
            # 尝试从attached_assets找
            attached_path = f"attached_assets/{original_filename}_1760442029793.pdf"
            if not os.path.exists(attached_path):
                attached_path = f"attached_assets/{original_filename}_1760442029794.pdf"
            
            if os.path.exists(attached_path):
                try:
                    shutil.copy2(attached_path, new_path)
                    print(f"  ✓ 从attached_assets复制: {attached_path}")
                except Exception as e:
                    print(f"  ✗ 文件复制失败: {e}")
                    continue
            else:
                print(f"  ⚠ 原始文件未找到")
                continue
        
        # 更新数据库
        cursor.execute('''
            UPDATE statements 
            SET statement_date = ?, file_path = ?
            WHERE id = ?
        ''', (correct_date, new_path, stmt_id))
        
        fixed_count += 1
        print(f"  ✓ 数据库已更新")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print(f"修复完成！共修复 {fixed_count}/12 个账单".center(60))
    print("="*60)

if __name__ == '__main__':
    fix_chang_statements()
