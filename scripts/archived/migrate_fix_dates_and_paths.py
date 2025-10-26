#!/usr/bin/env python3
"""
数据迁移脚本：修复statement_date错误和文件路径
用途：
1. 修复错误的日期（1025年 → 2025年）
2. 从文件名解析正确的月份信息  
3. 将attached_assets路径迁移到StatementOrganizer结构
4. 移动实际PDF文件到新位置
"""

import sqlite3
import os
import shutil
import re
from datetime import datetime
from pathlib import Path

DB_PATH = 'db/smart_loan_manager.db'
OLD_BASE = 'attached_assets'
NEW_BASE = 'static/uploads'

def parse_date_from_filename(filename):
    """从文件名解析正确的日期 DD:MM:YYYY 或 DD-MM-YYYY"""
    # 匹配 12:01:2025 格式 (这是 DD:MM:YYYY 不是 MM:DD:YYYY!)
    match1 = re.search(r'(\d{2}):(\d{2}):(\d{4})', filename)
    if match1:
        day, month, year = match1.groups()
        # 验证日期有效性
        try:
            datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d')
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except ValueError:
            # 如果无效，尝试反转月日
            try:
                datetime.strptime(f"{year}-{day}-{month}", '%Y-%m-%d')
                return f"{year}-{day.zfill(2)}-{month.zfill(2)}"
            except:
                return None
    
    # 匹配 13-01-2025 格式  
    match2 = re.search(r'(\d{2})-(\d{2})-(\d{4})', filename)
    if match2:
        day, month, year = match2.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # 匹配 AMB 28052025 格式 (DDMMYYYY)
    match3 = re.search(r'[A-Z]+\s*(\d{8})', filename)
    if match3:
        date_str = match3.group(1)
        day = date_str[:2]
        month = date_str[2:4]
        year = date_str[4:]
        return f"{year}-{month}-{day}"
        
    return None

def get_customer_name(cursor, customer_id):
    """获取客户名称"""
    result = cursor.execute(
        'SELECT name FROM customers WHERE id = ?', 
        (customer_id,)
    ).fetchone()
    return result[0] if result else None

def fix_statement_dates(conn):
    """第一步：修复statement_date错误"""
    cursor = conn.cursor()
    
    print("\n=== 步骤1: 修复statement_date ===")
    
    # 获取所有需要修复的记录
    statements = cursor.execute('''
        SELECT s.id, s.statement_date, s.file_path, cc.customer_id
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        ORDER BY s.id
    ''').fetchall()
    
    fixed_count = 0
    for stmt_id, old_date, file_path, customer_id in statements:
        # 从文件名解析正确日期
        correct_date = parse_date_from_filename(file_path)
        
        if correct_date and correct_date != old_date:
            cursor.execute(
                'UPDATE statements SET statement_date = ? WHERE id = ?',
                (correct_date, stmt_id)
            )
            print(f"  ✓ Statement {stmt_id}: {old_date} → {correct_date}")
            fixed_count += 1
    
    conn.commit()
    print(f"\n修复了 {fixed_count} 条日期记录")
    return fixed_count

def migrate_files_to_new_structure(conn):
    """第二步：迁移文件到新组织结构"""
    cursor = conn.cursor()
    
    print("\n=== 步骤2: 迁移文件到新结构 ===")
    
    # 获取所有attached_assets路径的记录
    statements = cursor.execute('''
        SELECT s.id, s.statement_date, s.file_path, 
               c.id as customer_id, c.name as customer_name,
               cc.bank_name, cc.card_number_last4
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id  
        JOIN customers c ON cc.customer_id = c.id
        WHERE s.file_path LIKE 'attached_assets/%'
        ORDER BY c.name, s.statement_date
    ''').fetchall()
    
    migrated_count = 0
    missing_files = []
    
    for stmt_id, stmt_date, old_path, cust_id, cust_name, bank, card_last4 in statements:
        # 检查旧文件是否存在
        if not os.path.exists(old_path):
            print(f"  ⚠ 文件不存在: {old_path}")
            missing_files.append(old_path)
            continue
        
        # 解析日期
        try:
            date_obj = datetime.strptime(stmt_date, '%Y-%m-%d')
            year_month = date_obj.strftime('%Y-%m')
        except:
            print(f"  ⚠ 日期格式错误: {stmt_date}")
            continue
        
        # 构建新路径
        # static/uploads/{customer_name}/{year}-{month}/statements/{bank}_{card_last4}_{date}.pdf
        safe_name = cust_name.replace(' ', '_').replace('/', '_')
        safe_bank = bank.replace(' ', '_')
        
        new_dir = f"{NEW_BASE}/{safe_name}/{year_month}/statements"
        new_filename = f"{safe_bank}_{card_last4}_{stmt_date}.pdf"
        new_path = f"{new_dir}/{new_filename}"
        
        # 创建目录
        os.makedirs(new_dir, exist_ok=True)
        
        # 复制文件（不删除旧文件，安全起见）
        try:
            shutil.copy2(old_path, new_path)
            
            # 更新数据库
            cursor.execute(
                'UPDATE statements SET file_path = ? WHERE id = ?',
                (new_path, stmt_id)
            )
            
            print(f"  ✓ {old_path} → {new_path}")
            migrated_count += 1
        except Exception as e:
            print(f"  ✗ 迁移失败 {old_path}: {e}")
    
    conn.commit()
    
    print(f"\n成功迁移 {migrated_count} 个文件")
    if missing_files:
        print(f"\n缺失文件列表 ({len(missing_files)}):")
        for f in missing_files:
            print(f"  - {f}")
    
    return migrated_count, missing_files

def merge_duplicate_customers(conn):
    """第三步：合并重复客户"""
    cursor = conn.cursor()
    
    print("\n=== 步骤3: 合并重复客户 ===")
    
    # 查找Chang Choon Chow (id=5)和CHANG CHOON CHOW (id=10)
    customers = cursor.execute('''
        SELECT id, name FROM customers 
        WHERE UPPER(name) = 'CHANG CHOON CHOW'
        ORDER BY id
    ''').fetchall()
    
    if len(customers) < 2:
        print("  没有发现重复客户")
        return 0
    
    # 保留id较大的（id=10），删除id=5
    keep_id = customers[-1][0]  # 10
    remove_id = customers[0][0]  # 5
    
    print(f"  保留: ID {keep_id} ({customers[-1][1]})")
    print(f"  删除: ID {remove_id} ({customers[0][1]})")
    
    # 更新所有引用到旧ID的外键
    # 检查是否有credit_cards引用remove_id
    cards = cursor.execute(
        'SELECT COUNT(*) FROM credit_cards WHERE customer_id = ?',
        (remove_id,)
    ).fetchone()[0]
    
    if cards > 0:
        cursor.execute(
            'UPDATE credit_cards SET customer_id = ? WHERE customer_id = ?',
            (keep_id, remove_id)
        )
        print(f"  更新了 {cards} 张信用卡的客户关联")
    
    # 删除重复客户
    cursor.execute('DELETE FROM customers WHERE id = ?', (remove_id,))
    
    conn.commit()
    print(f"  ✓ 成功合并客户")
    return 1

def add_backward_compatibility_note():
    """第四步：提示添加向后兼容代码"""
    print("\n=== 步骤4: 向后兼容提示 ===")
    print("  需要在app.py的view_statement_file路由添加fallback逻辑")
    print("  如果新路径不存在，尝试从attached_assets读取")

def main():
    """执行完整迁移"""
    print("="*60)
    print("开始数据迁移".center(60))
    print("="*60)
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # 1. 修复日期
        fixed = fix_statement_dates(conn)
        
        # 2. 迁移文件
        migrated, missing = migrate_files_to_new_structure(conn)
        
        # 3. 合并客户
        merged = merge_duplicate_customers(conn)
        
        # 4. 提示向后兼容
        add_backward_compatibility_note()
        
        print("\n" + "="*60)
        print("迁移完成！".center(60))
        print("="*60)
        print(f"  修复日期: {fixed} 条")
        print(f"  迁移文件: {migrated} 个")
        print(f"  合并客户: {merged} 个")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
