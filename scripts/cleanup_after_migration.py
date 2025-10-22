"""
迁移后清理脚本
1. 标准化银行名称文件夹（合并不同大小写）
2. 删除旧的 YYYY-MM 格式文件夹
3. 重新处理失败的储蓄账户迁移
"""

import sqlite3
import os
import shutil
from pathlib import Path
import re


def sanitize_bank_name(name):
    """标准化银行名称为Title Case"""
    clean_name = re.sub(r'[^\w\s-]', '', name).strip()
    clean_name = clean_name.title()
    return clean_name.replace(' ', '_')


def normalize_bank_folders():
    """标准化所有银行文件夹名称"""
    print("\n" + "="*60)
    print("📁 标准化银行文件夹名称...")
    print("="*60)
    
    uploads_folder = Path('static/uploads')
    
    for customer_folder in uploads_folder.iterdir():
        if not customer_folder.is_dir():
            continue
        
        for category in ['credit_cards', 'savings']:
            category_folder = customer_folder / category
            if not category_folder.exists():
                continue
            
            print(f"\n处理: {customer_folder.name}/{category}")
            
            # 收集所有银行文件夹
            bank_folders = {}
            for bank_folder in category_folder.iterdir():
                if not bank_folder.is_dir():
                    continue
                
                # 标准化名称
                standard_name = sanitize_bank_name(bank_folder.name)
                
                if standard_name not in bank_folders:
                    bank_folders[standard_name] = []
                
                bank_folders[standard_name].append(bank_folder)
            
            # 合并重复的银行文件夹
            for standard_name, folders in bank_folders.items():
                if len(folders) > 1:
                    print(f"  发现重复: {[f.name for f in folders]} → {standard_name}")
                    
                    # 创建标准文件夹
                    target_folder = category_folder / standard_name
                    target_folder.mkdir(exist_ok=True)
                    
                    # 合并所有文件
                    for source_folder in folders:
                        if source_folder == target_folder:
                            continue
                        
                        # 移动所有月份文件夹
                        for month_folder in source_folder.iterdir():
                            if not month_folder.is_dir():
                                continue
                            
                            target_month = target_folder / month_folder.name
                            if target_month.exists():
                                # 合并文件
                                for file in month_folder.iterdir():
                                    if file.is_file():
                                        shutil.move(str(file), str(target_month))
                            else:
                                # 移动整个月份文件夹
                                shutil.move(str(month_folder), str(target_folder))
                        
                        # 删除空文件夹
                        try:
                            source_folder.rmdir()
                            print(f"    ✅ 已合并并删除: {source_folder.name}")
                        except:
                            print(f"    ⚠️  无法删除: {source_folder.name}（可能不为空）")


def update_database_paths():
    """更新数据库中的路径，使用标准化的银行名称"""
    print("\n" + "="*60)
    print("🔄 更新数据库路径...")
    print("="*60)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 更新信用卡账单路径
    cursor.execute('SELECT id, file_path FROM statements WHERE file_path LIKE "static/uploads/%"')
    statements = cursor.fetchall()
    
    updated_count = 0
    for stmt in statements:
        old_path = stmt['file_path']
        
        # 解析路径
        parts = Path(old_path).parts
        if len(parts) < 6:
            continue
        
        # static/uploads/{customer}/credit_cards/{bank}/{month}/file.pdf
        customer, category, bank, month = parts[2], parts[3], parts[4], parts[5]
        
        # 标准化银行名称
        standard_bank = sanitize_bank_name(bank)
        
        if standard_bank != bank:
            new_path = str(Path('static/uploads') / customer / category / standard_bank / month / parts[-1])
            
            if os.path.exists(new_path):
                cursor.execute('UPDATE statements SET file_path = ? WHERE id = ?', (new_path, stmt['id']))
                updated_count += 1
                print(f"  ✅ 更新路径 (ID {stmt['id']})")
                print(f"     旧: {old_path}")
                print(f"     新: {new_path}")
    
    conn.commit()
    print(f"\n✅ 更新了 {updated_count} 条记录")
    
    conn.close()


def delete_old_folders():
    """删除旧的 YYYY-MM 格式文件夹"""
    print("\n" + "="*60)
    print("🗑️  删除旧文件夹...")
    print("="*60)
    
    uploads_folder = Path('static/uploads')
    deleted_count = 0
    
    for customer_folder in uploads_folder.iterdir():
        if not customer_folder.is_dir():
            continue
        
        for item in customer_folder.iterdir():
            # 匹配 YYYY-MM 格式
            if item.is_dir() and re.match(r'^\d{4}-\d{2}$', item.name):
                try:
                    shutil.rmtree(item)
                    print(f"  ✅ 删除: {customer_folder.name}/{item.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ 无法删除: {customer_folder.name}/{item.name} - {str(e)}")
    
    print(f"\n✅ 删除了 {deleted_count} 个旧文件夹")


def retry_failed_savings():
    """重新处理失败的储蓄账户迁移"""
    print("\n" + "="*60)
    print("💾 重新处理失败的储蓄账户...")
    print("="*60)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找还在 attached_assets 的储蓄账户
    cursor.execute('''
        SELECT 
            ss.id, ss.file_path, ss.statement_date,
            c.name as customer_name,
            sa.bank_name, sa.account_number_last4
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE ss.file_path LIKE "attached_assets%"
        ORDER BY c.name, sa.bank_name, ss.statement_date
    ''')
    
    statements = cursor.fetchall()
    print(f"找到 {len(statements)} 条未迁移的储蓄账户账单")
    
    success_count = 0
    error_count = 0
    
    for stmt in statements:
        try:
            old_path = stmt['file_path']
            
            if not os.path.exists(old_path):
                print(f"⚠️  文件不存在: {old_path}")
                error_count += 1
                continue
            
            # 解析日期
            stmt_date = stmt['statement_date']
            
            # 处理不同的日期格式
            from datetime import datetime
            try:
                # 尝试标准格式 YYYY-MM-DD
                if '-' in stmt_date and len(stmt_date.split('-')[0]) == 4:
                    year, month = stmt_date.split('-')[0:2]
                else:
                    # 尝试其他格式 "30 Apr 2025"
                    date_obj = datetime.strptime(stmt_date, '%d %b %Y')
                    year = str(date_obj.year)
                    month = f"{date_obj.month:02d}"
                    stmt_date = date_obj.strftime('%Y-%m-%d')  # 标准化日期
            except:
                print(f"⚠️  无法解析日期: {stmt_date}")
                error_count += 1
                continue
            
            # 构建新路径
            safe_customer = re.sub(r'[^\w\s-]', '', stmt['customer_name']).strip().replace(' ', '_')
            safe_bank = sanitize_bank_name(stmt['bank_name'])
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
            
            print(f"✅ [{success_count + 1}] {stmt['customer_name']} / {stmt['bank_name']} / {month_folder}")
            print(f"   旧: {old_path}")
            print(f"   新: {new_path}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ 错误 (ID {stmt['id']}): {str(e)}")
            error_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 储蓄账户迁移: {success_count} 成功, {error_count} 失败")


def main():
    print("\n" + "="*60)
    print("🧹 迁移后清理工具")
    print("="*60)
    
    input("\n按 Enter 开始清理...")
    
    # 1. 标准化银行文件夹名称
    normalize_bank_folders()
    
    # 2. 更新数据库路径
    update_database_paths()
    
    # 3. 重新处理失败的储蓄账户
    retry_failed_savings()
    
    # 4. 删除旧文件夹
    delete_old_folders()
    
    print("\n" + "="*60)
    print("✅ 清理完成！")
    print("="*60)


if __name__ == "__main__":
    main()
