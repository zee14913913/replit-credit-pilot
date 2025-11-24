#!/usr/bin/env python3
"""
清理所有包含其他客户名称的文件
"""
import os
import shutil

def cleanup_all_files():
    print("=" * 120)
    print("清理所有包含其他客户名称的文件")
    print("=" * 120)
    
    # 需要完全删除的目录
    dirs_to_delete = [
        'parsing_results',
        'results',
        'docs/archived',
    ]
    
    # 需要删除的具体文件
    files_to_delete = [
        # docs目录中的报告
        'docs/HSBC_100%_ACCURACY_CONFIRMATION_REPORT.md',
        'docs/UOB_100%_ACCURACY_CONFIRMATION_REPORT.md',
        'docs/SCB_100%_ACCURACY_CONFIRMATION_REPORT.md',
        'docs/SAVINGS_CURRENT_STATE.md',
        'docs/FILE_STORAGE_ARCHITECTURE.md',
        'docs/MANUAL_VERIFICATION_WORKFLOW.md',
        'docs/batch_processing_guide.md',
        'docs/business/用户使用指南.md',
        
        # 根目录文档
        'ATTACHED_ASSETS_MIGRATION_PLAN.md',
        'FILE_DATABASE_MATCH_SUMMARY.md',
        'VERIFICATION_PROGRESS.md',
        'VBA_LOCAL_PROCESSING_GUIDE.md',
        'VBA_COMPLETE_PROCESSING_GUIDE.md',
        'VBA_上传指引.md',
        'BATCH_PROCESSING_SUMMARY.md',
        'README_BATCH_PROCESSING.md',
        'README_POSTPROCESSING.md',
        'README_MAC_PROCESSING.md',
        'MAC_COMPLETE_GUIDE.md',
        'QUICK_START_MAC.md',
        'QUICK_START_CHINESE.md',
        'PROCESSING_OPTIONS_COMPARISON.md',
        'COMPLETE_SYSTEM_REPAIR_REPORT.md',
        'CRITICAL_FINDINGS.md',
        'final_data_quality_report_zh.md',
        
        # 日志和结果文件
        'batch_processing_log.txt',
        'batch_results.txt',
        'batch_results_fixed.txt',
        'ambank_analysis_report.txt',
        'orphan_files_list.txt',
        'DOWNLOAD_INSTRUCTIONS.txt',
        'UAT_STAGE4_OUTPUT.txt',
        'UAT_STAGE4_REPORT.md',
        
        # JSON文件
        'file_database_match_report.json',
        'color_compliance_report.json',
        
        # static/uploads中的审计文档
        'static/uploads/system/audit/VBA_上传指引.md',
        
        # 数据质量报告
        'data_quality_report_20251124_014217.txt',
    ]
    
    total_deleted = 0
    
    # 删除目录
    print("\n删除目录:")
    print("-" * 120)
    for directory in dirs_to_delete:
        if os.path.exists(directory):
            try:
                # 统计文件数
                file_count = sum([len(files) for _, _, files in os.walk(directory)])
                shutil.rmtree(directory)
                print(f"✅ 删除目录: {directory} ({file_count}个文件)")
                total_deleted += file_count
            except Exception as e:
                print(f"❌ 删除失败: {directory} - {str(e)}")
        else:
            print(f"⚠️  不存在: {directory}")
    
    # 删除文件
    print("\n删除文件:")
    print("-" * 120)
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ 删除: {file_path}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {file_path} - {str(e)}")
        else:
            print(f"⚠️  不存在: {file_path}")
    
    print("\n" + "=" * 120)
    print(f"清理完成！总计删除: {total_deleted}+ 个文件/目录")
    print("=" * 120)

if __name__ == '__main__':
    cleanup_all_files()
