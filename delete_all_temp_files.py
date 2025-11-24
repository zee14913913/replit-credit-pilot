#!/usr/bin/env python3
"""
删除所有临时文件、解析结果、报告等
保留：备份目录、银行样本、测试样本
"""
import os
import shutil

def delete_temp_files():
    """删除所有临时文件"""
    print("=" * 120)
    print("删除所有临时文件、解析结果、报告")
    print("=" * 120)
    
    # 要完全删除的目录
    dirs_to_delete = [
        'accounting_data',
        'report',
        'output',
        'logs',
    ]
    
    # 要删除的文件模式（不在备份目录中的）
    files_to_delete = []
    
    # 扫描static目录
    if os.path.exists('static'):
        for item in os.listdir('static'):
            item_path = os.path.join('static', item)
            # 删除CHEOK相关文件
            if 'cheok' in item.lower() or 'galaxy' in item.lower():
                files_to_delete.append(item_path)
            # 删除Excel报告
            elif item.endswith('.xlsx') and 'LOAN_PRODUCTS' in item:
                files_to_delete.append(item_path)
    
    # 根目录的临时文件
    root_temp_files = [
        '月结单验证报告_20251030_211842.xlsx',
        'api_validation_report.md',
        'missing_pdfs_report.csv',
        'page_health_report.json',
    ]
    
    # scripts目录中的报告生成脚本（保留但不删除scripts目录本身）
    report_scripts = [
        'scripts/generate_savings_report.py',
        'scripts/simple_savings_report.py',
        'scripts/ycw_maybank_complete_report.py',
        'scripts/ycw_complete_portfolio_report.py',
        'scripts/ycw_savings_portfolio_report.py',
        'scripts/generate_verification_report.py',
        'scripts/generate_ccc_detailed_report.py',
        'scripts/generate_ccc_excel_report.py',
        'scripts/generate_ccc_final_report.py',
        'scripts/generate_ccc_settlement_report.py',
        'scripts/comprehensive_final_bank_report.py',
        'scripts/generate_daily_report.py',
    ]
    
    # templates目录中的报告模板
    template_reports = [
        'static/cheok_jun_yoon_report.html',
        'templates/savings_report.html',
        'templates/loan_reports.html',
        'templates/credit_card_optimizer_report.html',
        'templates/monthly_reports.html',
    ]
    
    total_deleted = 0
    
    # 删除目录
    print("\n删除目录:")
    print("-" * 120)
    for directory in dirs_to_delete:
        if os.path.exists(directory):
            file_count = sum([len(files) for _, _, files in os.walk(directory)])
            try:
                shutil.rmtree(directory)
                print(f"✅ 删除: {directory}/ ({file_count}个文件)")
                total_deleted += file_count
            except Exception as e:
                print(f"❌ 删除失败: {directory} - {str(e)}")
    
    # 删除static中的临时文件
    print("\n删除static目录中的临时文件:")
    print("-" * 120)
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"✅ 删除: {file}")
                    total_deleted += 1
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                    print(f"✅ 删除目录: {file}")
                    total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {file} - {str(e)}")
    
    # 删除根目录临时文件
    print("\n删除根目录临时文件:")
    print("-" * 120)
    for file in root_temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ 删除: {file}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {file} - {str(e)}")
    
    # 删除报告生成脚本
    print("\n删除报告生成脚本:")
    print("-" * 120)
    for script in report_scripts:
        if os.path.exists(script):
            try:
                os.remove(script)
                print(f"✅ 删除: {script}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {script} - {str(e)}")
    
    # 删除报告模板
    print("\n删除报告模板:")
    print("-" * 120)
    for template in template_reports:
        if os.path.exists(template):
            try:
                os.remove(template)
                print(f"✅ 删除: {template}")
                total_deleted += 1
            except Exception as e:
                print(f"❌ 删除失败: {template} - {str(e)}")
    
    # 删除templates/reports目录
    if os.path.exists('templates/reports'):
        try:
            shutil.rmtree('templates/reports')
            print(f"✅ 删除: templates/reports/")
            total_deleted += 1
        except:
            pass
    
    # 删除report目录中的Python文件
    if os.path.exists('report'):
        for file in os.listdir('report'):
            if file.endswith('.py'):
                file_path = os.path.join('report', file)
                try:
                    os.remove(file_path)
                    print(f"✅ 删除: {file_path}")
                    total_deleted += 1
                except:
                    pass
    
    print(f"\n总计删除: {total_deleted}+ 个文件/目录")

def main():
    print("=" * 120)
    print("清理所有临时文件")
    print("=" * 120)
    
    delete_temp_files()
    
    print("\n" + "=" * 120)
    print("清理完成！")
    print("=" * 120)
    print("\n已删除:")
    print("  ✅ accounting_data/        (所有会计测试数据)")
    print("  ✅ report/                 (报告生成器)")
    print("  ✅ output/                 (输出文件)")
    print("  ✅ logs/                   (日志文件)")
    print("  ✅ static/cheok*           (CHEOK相关文件)")
    print("  ✅ scripts/*report*.py     (报告生成脚本)")
    print("  ✅ templates/*report*      (报告模板)")
    print("\n保留:")
    print("  ✓  docparser_templates/sample_pdfs/  (银行样本PDF)")
    print("  ✓  test_pdfs/                        (测试PDF)")
    print("  ✓  所有备份目录")
    print("=" * 120)

if __name__ == '__main__':
    main()
