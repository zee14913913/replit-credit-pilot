#!/usr/bin/env python3
"""
清理孤立文件（文件存在但数据库无记录）
先备份，再删除
"""
import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime

def connect_db():
    return sqlite3.connect('db/smart_loan_manager.db')

def get_all_db_file_paths():
    """获取数据库中所有的文件路径"""
    print("\n" + "="*80)
    print("📊 扫描数据库中的文件记录")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    db_paths = set()
    
    # 信用卡账单
    cursor.execute("SELECT file_path FROM statements WHERE file_path IS NOT NULL AND file_path != ''")
    statement_paths = {row[0] for row in cursor.fetchall()}
    print(f"信用卡账单文件: {len(statement_paths)} 个")
    db_paths.update(statement_paths)
    
    # 储蓄账户月结单
    cursor.execute("SELECT file_path FROM savings_statements WHERE file_path IS NOT NULL AND file_path != ''")
    savings_paths = {row[0] for row in cursor.fetchall()}
    print(f"储蓄月结单文件: {len(savings_paths)} 个")
    db_paths.update(savings_paths)
    
    # 收据
    cursor.execute("SELECT file_path FROM receipts WHERE file_path IS NOT NULL AND file_path != ''")
    receipt_paths = {row[0] for row in cursor.fetchall()}
    print(f"收据文件: {len(receipt_paths)} 个")
    db_paths.update(receipt_paths)
    
    conn.close()
    
    print(f"\n✅ 数据库中共有 {len(db_paths)} 个文件记录")
    return db_paths

def scan_filesystem():
    """扫描文件系统中的所有文件"""
    print("\n" + "="*80)
    print("📁 扫描文件系统")
    print("="*80)
    
    scan_dirs = [
        'static/uploads',
        'static/customer_files',
        'static/reports',
        'static/monthly_reports',
        'attached_assets'
    ]
    
    all_files = []
    
    for scan_dir in scan_dirs:
        if os.path.exists(scan_dir):
            # 扫描PDF文件
            pdf_files = list(Path(scan_dir).rglob('*.pdf'))
            # 扫描图片文件
            img_files = list(Path(scan_dir).rglob('*.jpg')) + list(Path(scan_dir).rglob('*.png'))
            
            files_in_dir = pdf_files + img_files
            all_files.extend([str(f) for f in files_in_dir])
            
            print(f"{scan_dir}: {len(files_in_dir)} 个文件")
    
    print(f"\n✅ 文件系统中共有 {len(all_files)} 个文件")
    return all_files

def find_orphaned_files(db_paths, fs_files):
    """找出孤立文件"""
    print("\n" + "="*80)
    print("🔍 识别孤立文件")
    print("="*80)
    
    orphaned = []
    
    for file_path in fs_files:
        # 检查文件路径是否在数据库中
        if file_path not in db_paths:
            # 也检查相对路径（有些数据库记录可能没有前缀）
            relative_path = file_path.replace('static/', '')
            if relative_path not in db_paths:
                orphaned.append(file_path)
    
    print(f"\n⚠️  发现 {len(orphaned)} 个孤立文件")
    
    # 分类显示
    test_files = [f for f in orphaned if 'test' in f.lower() or 'Test' in f]
    report_files = [f for f in orphaned if 'report' in f]
    temp_files = [f for f in orphaned if f.startswith('static/uploads/202510')]
    other_files = [f for f in orphaned if f not in test_files + report_files + temp_files]
    
    print(f"\n分类统计:")
    print(f"  - 测试文件: {len(test_files)}")
    print(f"  - 报告文件: {len(report_files)}")
    print(f"  - 临时文件: {len(temp_files)}")
    print(f"  - 其他文件: {len(other_files)}")
    
    return orphaned

def backup_orphaned_files(orphaned_files):
    """备份孤立文件到backup文件夹"""
    print("\n" + "="*80)
    print("📦 备份孤立文件")
    print("="*80)
    
    backup_dir = 'static/backup_cleanup'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}/{timestamp}"
    
    # 创建备份目录
    os.makedirs(backup_path, exist_ok=True)
    
    # 创建备份清单
    manifest = []
    backed_up = 0
    total_size = 0
    
    for file_path in orphaned_files:
        if os.path.exists(file_path):
            try:
                # 保持原始目录结构
                relative_path = file_path.replace('static/', '')
                dest_path = os.path.join(backup_path, relative_path)
                
                # 创建目标目录
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # 复制文件
                shutil.copy2(file_path, dest_path)
                
                # 记录
                file_size = os.path.getsize(file_path)
                manifest.append({
                    'original': file_path,
                    'backup': dest_path,
                    'size': file_size
                })
                
                backed_up += 1
                total_size += file_size
                
            except Exception as e:
                print(f"⚠️  备份失败: {file_path} - {str(e)}")
    
    # 保存清单
    manifest_file = f"{backup_path}/MANIFEST.txt"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"备份文件数: {backed_up}\n")
        f.write(f"总大小: {total_size / 1024 / 1024:.2f} MB\n\n")
        f.write("="*80 + "\n")
        f.write("备份文件清单:\n")
        f.write("="*80 + "\n\n")
        for item in manifest:
            f.write(f"原始: {item['original']}\n")
            f.write(f"备份: {item['backup']}\n")
            f.write(f"大小: {item['size'] / 1024:.2f} KB\n\n")
    
    print(f"✅ 已备份 {backed_up} 个文件到: {backup_path}")
    print(f"📊 总大小: {total_size / 1024 / 1024:.2f} MB")
    print(f"📝 清单文件: {manifest_file}")
    
    return backup_path, backed_up, total_size

def delete_orphaned_files(orphaned_files):
    """删除孤立文件"""
    print("\n" + "="*80)
    print("🗑️  删除孤立文件")
    print("="*80)
    
    deleted_count = 0
    freed_space = 0
    
    for file_path in orphaned_files:
        if os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                freed_space += file_size
                
            except Exception as e:
                print(f"⚠️  删除失败: {file_path} - {str(e)}")
    
    print(f"✅ 成功删除 {deleted_count} 个文件")
    print(f"💾 释放空间: {freed_space / 1024 / 1024:.2f} MB")
    
    return deleted_count, freed_space

def cleanup_empty_directories():
    """清理空目录"""
    print("\n" + "="*80)
    print("📂 清理空目录")
    print("="*80)
    
    scan_dirs = [
        'static/uploads',
        'static/customer_files',
        'static/reports',
        'static/monthly_reports'
    ]
    
    removed_dirs = 0
    
    for scan_dir in scan_dirs:
        if os.path.exists(scan_dir):
            for root, dirs, files in os.walk(scan_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # 尝试删除空目录
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            removed_dirs += 1
                            print(f"删除空目录: {dir_path}")
                    except:
                        pass
    
    print(f"✅ 清理了 {removed_dirs} 个空目录")
    return removed_dirs

def generate_cleanup_report(backup_path, backed_up, total_size, deleted_count, freed_space):
    """生成清理报告"""
    print("\n" + "="*80)
    print("📄 生成清理报告")
    print("="*80)
    
    report = f"""
孤立文件清理报告
{'='*80}

清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

清理统计:
  - 发现孤立文件: {backed_up} 个
  - 备份文件数: {backed_up} 个
  - 删除文件数: {deleted_count} 个
  - 释放磁盘空间: {freed_space / 1024 / 1024:.2f} MB

备份位置:
  - 路径: {backup_path}
  - 大小: {total_size / 1024 / 1024:.2f} MB
  - 清单: {backup_path}/MANIFEST.txt

清理内容类型:
  1. 测试文件（CIMB_Test_Statement.pdf等）
  2. 临时报告文件（report_*.pdf）
  3. 旧的临时上传文件
  4. 其他无数据库记录的文件

恢复方法:
  如需恢复任何文件，请从备份目录复制回原位置：
  cp {backup_path}/[relative_path] static/[relative_path]

保留期限:
  建议保留备份7天，确认系统正常后可删除

状态: ✅ 成功完成
"""
    
    print(report)
    
    # 保存报告
    report_file = 'cleanup_report_orphaned_files.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📝 报告已保存到: {report_file}")

def main():
    print("\n" + "="*80)
    print("🧹 开始清理孤立文件")
    print("="*80)
    print("\n清理策略:")
    print("  1. 扫描数据库，获取所有文件记录")
    print("  2. 扫描文件系统，获取所有实际文件")
    print("  3. 识别孤立文件（无数据库记录）")
    print("  4. 先备份到backup文件夹")
    print("  5. 再删除原文件")
    print("  6. 清理空目录")
    print("  7. 生成清理报告\n")
    
    try:
        # 步骤1：获取数据库文件路径
        db_paths = get_all_db_file_paths()
        
        # 步骤2：扫描文件系统
        fs_files = scan_filesystem()
        
        # 步骤3：识别孤立文件
        orphaned_files = find_orphaned_files(db_paths, fs_files)
        
        if not orphaned_files:
            print("\n✅ 没有发现孤立文件！系统很干净！")
            return
        
        # 步骤4：备份孤立文件
        backup_path, backed_up, total_size = backup_orphaned_files(orphaned_files)
        
        # 步骤5：删除孤立文件
        deleted_count, freed_space = delete_orphaned_files(orphaned_files)
        
        # 步骤6：清理空目录
        cleanup_empty_directories()
        
        # 步骤7：生成报告
        generate_cleanup_report(backup_path, backed_up, total_size, deleted_count, freed_space)
        
        print("\n" + "="*80)
        print("✅ 清理完成！系统已优化！")
        print("="*80)
        print(f"\n💡 提示: 备份文件保存在 {backup_path}")
        print("   如需恢复任何文件，请查看 MANIFEST.txt 清单")
        
    except Exception as e:
        print(f"\n❌ 清理过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
