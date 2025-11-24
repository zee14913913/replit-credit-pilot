"""
文件结构迁移脚本
从旧结构迁移到新的四级结构

旧结构：
static/uploads/{customer_name}/{year}-{month}/statements/

新结构：
static/uploads/{customer_name}/credit_cards/{bank_name}/{year}-{month}/
static/uploads/{customer_name}/savings/{bank_name}/{year}-{month}/
"""

import sqlite3
import os
import shutil
from pathlib import Path
import re


def sanitize_name(name):
    """清理名称，移除特殊字符"""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')


def migrate_credit_card_statements():
    """迁移信用卡账单到新结构"""
    print("\n" + "="*60)
    print("📦 开始迁移信用卡账单...")
    print("="*60)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有信用卡账单
    cursor.execute('''
        SELECT 
            s.id, s.file_path, s.statement_date,
            c.name as customer_name,
            cc.bank_name, cc.card_number_last4
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
        WHERE s.file_path IS NOT NULL
        ORDER BY c.name, cc.bank_name, s.statement_date
    ''')
    
    statements = cursor.fetchall()
    print(f"找到 {len(statements)} 条信用卡账单记录")
    
    migrated_count = 0
    error_count = 0
    
    for stmt in statements:
        try:
            old_path = stmt['file_path']
            
            # 检查旧文件是否存在
            if not os.path.exists(old_path):
                print(f"⚠️  文件不存在，跳过: {old_path}")
                continue
            
            # 解析日期
            stmt_date = stmt['statement_date']
            year, month = stmt_date.split('-')[0:2]
            
            # 构建新路径
            safe_customer = sanitize_name(stmt['customer_name'])
            safe_bank = sanitize_name(stmt['bank_name'])
            month_folder = f"{year}-{month}"
            
            new_folder = Path('static/uploads') / safe_customer / 'credit_cards' / safe_bank / month_folder
            os.makedirs(new_folder, exist_ok=True)
            
            # 生成新文件名
            file_extension = os.path.splitext(old_path)[1]
            new_filename = f"{safe_bank}_{stmt['card_number_last4']}_{stmt_date}{file_extension}"
            new_path = str(new_folder / new_filename)
            
            # 复制文件
            shutil.copy2(old_path, new_path)
            
            # 更新数据库
            cursor.execute('UPDATE statements SET file_path = ? WHERE id = ?', (new_path, stmt['id']))
            
            print(f"✅ [{migrated_count + 1}] {stmt['customer_name']} / {stmt['bank_name']} / {month_folder}")
            print(f"   旧: {old_path}")
            print(f"   新: {new_path}")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ 错误 (ID {stmt['id']}): {str(e)}")
            error_count += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "-"*60)
    print(f"✅ 信用卡账单迁移完成: {migrated_count} 成功, {error_count} 失败")
    print("-"*60)
    
    return migrated_count, error_count


def migrate_savings_statements():
    """迁移储蓄账户账单到新结构"""
    print("\n" + "="*60)
    print("💰 开始迁移储蓄账户账单...")
    print("="*60)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有储蓄账户账单
    cursor.execute('''
        SELECT 
            ss.id, ss.file_path, ss.statement_date,
            c.name as customer_name,
            sa.bank_name, sa.account_number_last4
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE ss.file_path IS NOT NULL
        ORDER BY c.name, sa.bank_name, ss.statement_date
    ''')
    
    statements = cursor.fetchall()
    print(f"找到 {len(statements)} 条储蓄账户账单记录")
    
    migrated_count = 0
    error_count = 0
    
    for stmt in statements:
        try:
            old_path = stmt['file_path']
            
            # 检查旧文件是否存在
            if not os.path.exists(old_path):
                print(f"⚠️  文件不存在，跳过: {old_path}")
                continue
            
            # 解析日期
            stmt_date = stmt['statement_date']
            year, month = stmt_date.split('-')[0:2]
            
            # 构建新路径
            safe_customer = sanitize_name(stmt['customer_name'])
            safe_bank = sanitize_name(stmt['bank_name'])
            month_folder = f"{year}-{month}"
            
            new_folder = Path('static/uploads') / safe_customer / 'savings' / safe_bank / month_folder
            os.makedirs(new_folder, exist_ok=True)
            
            # 生成新文件名
            file_extension = os.path.splitext(old_path)[1]
            new_filename = f"{safe_bank}_{stmt['account_number_last4']}_{stmt_date}{file_extension}"
            new_path = str(new_folder / new_filename)
            
            # 复制文件
            shutil.copy2(old_path, new_path)
            
            # 更新数据库
            cursor.execute('UPDATE savings_statements SET file_path = ? WHERE id = ?', (new_path, stmt['id']))
            
            print(f"✅ [{migrated_count + 1}] {stmt['customer_name']} / {stmt['bank_name']} / {month_folder}")
            print(f"   旧: {old_path}")
            print(f"   新: {new_path}")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ 错误 (ID {stmt['id']}): {str(e)}")
            error_count += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "-"*60)
    print(f"✅ 储蓄账户账单迁移完成: {migrated_count} 成功, {error_count} 失败")
    print("-"*60)
    
    return migrated_count, error_count


def cleanup_old_folders():
    """清理旧的文件夹结构（可选）"""
    print("\n" + "="*60)
    print("🧹 检查可清理的旧文件夹...")
    print("="*60)
    
    uploads_folder = Path('static/uploads')
    
    if not uploads_folder.exists():
        print("上传文件夹不存在")
        return
    
    # 查找旧结构的文件夹（YYYY-MM格式）
    old_folders = []
    for customer_folder in uploads_folder.iterdir():
        if not customer_folder.is_dir():
            continue
        
        for item in customer_folder.iterdir():
            # 匹配 YYYY-MM 格式的文件夹
            if item.is_dir() and re.match(r'^\d{4}-\d{2}$', item.name):
                old_folders.append(item)
    
    if old_folders:
        print(f"发现 {len(old_folders)} 个旧格式文件夹:")
        for folder in old_folders[:5]:  # 只显示前5个
            print(f"  - {folder}")
        if len(old_folders) > 5:
            print(f"  ... 还有 {len(old_folders) - 5} 个")
        
        print("\n⚠️  迁移完成后，请手动验证数据正确性，然后可以删除这些旧文件夹")
        print("删除命令示例: rm -rf static/uploads/*/20*")
    else:
        print("✅ 没有发现需要清理的旧文件夹")


def main():
    print("\n" + "="*60)
    print("🚀 文件结构迁移工具")
    print("="*60)
    print("\n新结构说明:")
    print("  客户名/")
    print("    ├── credit_cards/信用卡/")
    print("    │   └── 银行名/")
    print("    │       └── YYYY-MM/")
    print("    └── savings/储蓄账户/")
    print("        └── 银行名/")
    print("            └── YYYY-MM/")
    
    input("\n按 Enter 开始迁移...")
    
    # 迁移信用卡账单
    cc_success, cc_error = migrate_credit_card_statements()
    
    # 迁移储蓄账户账单
    sv_success, sv_error = migrate_savings_statements()
    
    # 清理提示
    cleanup_old_folders()
    
    # 总结
    print("\n" + "="*60)
    print("📊 迁移总结")
    print("="*60)
    print(f"信用卡账单: {cc_success} 成功, {cc_error} 失败")
    print(f"储蓄账户账单: {sv_success} 成功, {sv_error} 失败")
    print(f"总计: {cc_success + sv_success} 成功, {cc_error + sv_error} 失败")
    print("="*60)


if __name__ == "__main__":
    main()
