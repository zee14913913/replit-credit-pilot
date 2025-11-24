#!/usr/bin/env python3
"""
删除剩余的客户数据文件 - 主要是根目录的临时处理脚本
"""
import os

def delete_remaining():
    print("=" * 120)
    print("删除剩余的客户相关文件")
    print("=" * 120)
    
    # 根目录的临时处理脚本
    root_files = [
        'batch_parse_google_ai.py',
        'test_processor.py',
        'batch_process_41_statements.py',
        'test_single_statement.py',
        'batch_upload_41_statements.py',
        'ambank_manual_parse.py',
        'batch_process_41_statements_fallback.py',
        'mac_pdf_processor.py',
        'mac_excel_processor.py',
    ]
    
    # scripts中剩余的客户相关脚本
    scripts_files = [
        'scripts/vba_pdf_processor_with_json.py',
        'scripts/process_uploaded_json.py',
        'scripts/batch_process_all_pdfs.py',
        'scripts/create_document_ai_schema.py',
        'scripts/verify_all_transactions.py',
        'scripts/analyze_bank_pdf_formats.py',
    ]
    
    total = 0
    
    print("\n删除根目录临时脚本:")
    print("-" * 120)
    for f in root_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✅ 删除: {f}")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    print("\n删除scripts中的处理脚本:")
    print("-" * 120)
    for f in scripts_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✅ 删除: {f}")
                total += 1
            except Exception as e:
                print(f"❌ 失败: {f} - {str(e)}")
    
    print(f"\n总计删除: {total} 个文件")

if __name__ == '__main__':
    delete_remaining()
    print("\n" + "=" * 120)
    print("清理完成！")
    print("=" * 120)
