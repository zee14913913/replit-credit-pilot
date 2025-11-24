#!/usr/bin/env python3
"""
全面彻底清理 - 删除所有测试文件、示例文件、临时目录
"""
import os
import shutil

def comprehensive_cleanup():
    print("=" * 120)
    print("全面彻底清理")
    print("=" * 120)
    
    # 测试目录（整个删除）
    test_dirs = [
        'test_pdfs',
        'test_csvs',
        'uploads',  # 根目录的uploads
        'DEPRECATED',
        '__pycache__',
    ]
    
    # docparser示例PDF（保留文档，删除示例PDF）
    docparser_samples = [
        'docparser_templates/sample_pdfs/1_AMBANK.pdf',
        'docparser_templates/sample_pdfs/2_AMBANK_ISLAMIC.pdf',
        'docparser_templates/sample_pdfs/3_STANDARD_CHARTERED.pdf',
        'docparser_templates/sample_pdfs/4_UOB.pdf',
        'docparser_templates/sample_pdfs/5_HONG_LEONG.pdf',
        'docparser_templates/sample_pdfs/6_OCBC.pdf',
        'docparser_templates/sample_pdfs/7_HSBC.pdf',
    ]
    
    # static目录文件
    static_files = [
        'static/sample_invoice.pdf',
        'static/all_products_catalog_view.html',
        'static/all_products_catalog_FULL.html',
        'static/uploads/supplier_invoices/INV-001-202501-7SL-001.html',
    ]
    
    # 根目录测试脚本
    test_scripts = [
        'test_pdf_upload.py',
        'test_pdf_upload_complete.py',
    ]
    
    total = 0
    
    # 删除测试目录
    print("\n删除测试目录:")
    print("-" * 120)
    for dir_name in test_dirs:
        if os.path.exists(dir_name):
            try:
                # 计算大小
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(dir_name)
                    for filename in filenames
                ) / 1024  # KB
                
                shutil.rmtree(dir_name)
                print(f"✅ 删除目录: {dir_name}/ ({size:.1f}KB)")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {dir_name}/ - {str(e)}")
    
    # 删除docparser示例PDF
    print("\n删除docparser示例PDF:")
    print("-" * 120)
    for f in docparser_samples:
        if os.path.exists(f):
            try:
                size_kb = os.path.getsize(f) / 1024
                os.remove(f)
                print(f"✅ 删除: {f} ({size_kb:.1f}KB)")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    # 删除docparser/sample_pdfs目录（如果空了）
    if os.path.exists('docparser_templates/sample_pdfs'):
        try:
            os.rmdir('docparser_templates/sample_pdfs')
            print("✅ 删除空目录: docparser_templates/sample_pdfs/")
        except:
            pass
    
    # 删除static文件
    print("\n删除static示例文件:")
    print("-" * 120)
    for f in static_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✅ 删除: {f}")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    # 删除空目录
    if os.path.exists('static/uploads/supplier_invoices'):
        try:
            os.rmdir('static/uploads/supplier_invoices')
            print("✅ 删除空目录: static/uploads/supplier_invoices/")
        except:
            pass
    
    if os.path.exists('static/uploads/system/audit'):
        try:
            for f in os.listdir('static/uploads/system/audit'):
                fpath = os.path.join('static/uploads/system/audit', f)
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    print(f"✅ 删除: {fpath}")
                    total += 1
            os.rmdir('static/uploads/system/audit')
            os.rmdir('static/uploads/system')
            print("✅ 删除空目录: static/uploads/system/")
        except:
            pass
    
    # 删除测试脚本
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
    
    print(f"\n总计删除: {total}+ 个文件/目录")

if __name__ == '__main__':
    comprehensive_cleanup()
    print("\n" + "=" * 120)
    print("全面清理完成！")
    print("=" * 120)
    print("\n已删除:")
    print("  ✅ 5个测试目录（test_pdfs/, test_csvs/, uploads/, DEPRECATED/, __pycache__/）")
    print("  ✅ 7个docparser示例PDF")
    print("  ✅ static/中的示例文件")
    print("  ✅ 测试脚本")
    print("\n保留:")
    print("  ✅ 所有系统核心文件（app.py, services/, etc.）")
    print("  ✅ 文档和配置文件")
    print("  ✅ LEE E KAI数据（lee_e_kai_data/）")
    print("=" * 120)
