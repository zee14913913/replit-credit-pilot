#!/usr/bin/env python3
"""
删除测试文件、临时文件和旧数据库备份
保留所有系统核心文件
"""
import os
import glob

def clean_test_and_backup():
    print("=" * 120)
    print("删除测试文件和旧备份")
    print("=" * 120)
    
    # 测试Python脚本
    test_scripts = [
        'test_uob_parser.py',
        'test_hsbc_parser.py',
        'test_hsbc_522.py',
        'test_sc_parser.py',
        'deep_pdf_analysis.py',
        'check_uob_pages.py',
    ]
    
    # 旧数据库备份（保留最新的，删除旧的）
    db_backups = [
        'db/smart_loan_manager_backup_20251014_223541.db',
        'db/backup_before_migration_20251023_190630.db',
        'db/backup_monthly_migration_20251025_094532.db',
    ]
    
    # 其他备份文件
    other_backups = [
        'app.py.backup_before_route_fix',
    ]
    
    total = 0
    
    print("\n删除测试脚本:")
    print("-" * 120)
    for f in test_scripts:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✅ 删除: {f}")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    print("\n删除旧数据库备份:")
    print("-" * 120)
    for f in db_backups:
        if os.path.exists(f):
            try:
                # 检查文件大小
                size_mb = os.path.getsize(f) / (1024*1024)
                os.remove(f)
                print(f"✅ 删除: {f} ({size_mb:.1f}MB)")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    print("\n删除其他备份文件:")
    print("-" * 120)
    for f in other_backups:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✅ 删除: {f}")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    print(f"\n总计删除: {total} 个文件")

if __name__ == '__main__':
    clean_test_and_backup()
    print("\n" + "=" * 120)
    print("清理完成！")
    print("=" * 120)
    print("\n说明:")
    print("  ✅ 删除了测试脚本和旧数据库备份")
    print("  ✅ 保留了所有系统核心文件（app.py, services/, etc.）")
    print("  ✅ 保留了当前数据库（包含LEE E KAI数据）")
    print("\n剩余的103个包含客户名称的文件主要是:")
    print("  - 系统核心代码文件（包含代码注释/历史示例）")
    print("  - 文档文件（包含使用说明/示例）")
    print("  - 这些都是系统运行必需的，不应删除")
    print("=" * 120)
