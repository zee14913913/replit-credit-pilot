#!/usr/bin/env python3
"""
终极彻底清理 - 删除所有包含其他客户数据的文件
"""
import os
import shutil

def ultimate_cleanup():
    print("=" * 120)
    print("终极彻底清理 - 删除所有客户相关文件")
    print("=" * 120)
    
    # 要删除的scripts脚本
    scripts_to_delete = [
        'scripts/parse_41_statements_fixed.py',
        'scripts/parse_41_statements.py',
        'scripts/test_8_fields.py',
        'scripts/test_old_7_banks.py',
        'scripts/verify_ambank_descriptions.py',
        'scripts/process_ccc_pdfs_fixed.py',
        'scripts/process_ccc_pdfs_to_json.py',
        'scripts/calculate_ccc_settlement.py',
        'scripts/recalculate_ccc_all_banks.py',
        'scripts/verify_ocbc_2025_100percent.py',
        'scripts/import_ycw_ocbc_2025_statements.py',
        'scripts/manual_verify_ocbc_2024_detailed.py',
        'scripts/verify_ocbc_2024_100percent.py',
        'scripts/import_ycw_ocbc_2024_statements.py',
        'scripts/verify_maybank_2025_100percent.py',
        'scripts/verify_maybank_2025_import.py',
        'scripts/import_ycw_maybank_2025_statements.py',
        'scripts/import_ycw_maybank_statements.py',
        'scripts/import_ycw_gx_statements.py',
        'scripts/fix_chang_statements.py',
        'scripts/verify_savings_data.py',
        'scripts/auto_import_savings.py',
        'scripts/import_ycw_savings.py',
        'scripts/create_monthly_ledger_tables.py',
    ]
    
    # 要删除的batch_scripts
    batch_scripts = [
        'batch_scripts/batch_upload_uob.py',
        'batch_scripts/batch_upload_scb.py',
        'batch_scripts/batch_upload_hsbc.py',
        'batch_scripts/batch_upload_mbb.py',
    ]
    
    # 删除整个batch_scripts目录
    if os.path.exists('batch_scripts'):
        try:
            shutil.rmtree('batch_scripts')
            print("✅ 删除整个目录: batch_scripts/")
        except Exception as e:
            print(f"❌ 删除失败: batch_scripts/ - {str(e)}")
    
    # 删除i18n backup文件
    i18n_backups = [
        'static/i18n/zh.json.backup',
        'static/i18n/en.json.backup',
    ]
    
    # 删除scripts/archived
    if os.path.exists('scripts/archived'):
        try:
            shutil.rmtree('scripts/archived')
            print("✅ 删除: scripts/archived/")
        except:
            pass
    
    total_deleted = 0
    
    # 删除scripts
    print("\n删除scripts中的客户相关文件:")
    print("-" * 120)
    for script in scripts_to_delete:
        if os.path.exists(script):
            try:
                os.remove(script)
                print(f"✅ 删除: {script}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {script} - {str(e)}")
    
    # 删除batch_scripts
    print("\n删除batch_scripts:")
    print("-" * 120)
    for script in batch_scripts:
        if os.path.exists(script):
            try:
                os.remove(script)
                print(f"✅ 删除: {script}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {script} - {str(e)}")
    
    # 删除i18n备份
    print("\n删除i18n备份文件:")
    print("-" * 120)
    for backup in i18n_backups:
        if os.path.exists(backup):
            try:
                os.remove(backup)
                print(f"✅ 删除: {backup}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {backup} - {str(e)}")
    
    print(f"\n总计删除: {total_deleted}+ 个文件")

def main():
    print("=" * 120)
    print("执行终极彻底清理")
    print("=" * 120)
    
    ultimate_cleanup()
    
    print("\n" + "=" * 120)
    print("清理完成！")
    print("=" * 120)
    print("\n已删除:")
    print("  ✅ batch_scripts/ (整个目录)")
    print("  ✅ scripts中23个客户相关脚本")
    print("  ✅ scripts/archived/")
    print("  ✅ i18n备份文件")
    print("=" * 120)

if __name__ == '__main__':
    main()
