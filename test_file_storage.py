#!/usr/bin/env python3
"""
文件存储管理器测试脚本
Test File Storage Manager

测试统一文件存储架构的各项功能
"""
import os
import tempfile
from datetime import datetime
from services.file_storage_manager import FileStorageManager

def test_path_generation():
    """测试路径生成功能"""
    print("\n" + "=" * 80)
    print("测试路径生成功能")
    print("=" * 80)
    
    # 测试信用卡账单路径
    print("\n1. 信用卡账单路径生成:")
    cc_path = FileStorageManager.generate_credit_card_path(
        customer_code="Be_rich_CCC",
        bank_name="Maybank",
        card_last4="5678",
        statement_date=datetime(2025, 10, 15)
    )
    print(f"   路径: {cc_path}")
    print(f"   ✅ 格式正确" if "Be_rich_CCC/credit_cards/Maybank/2025-10" in cc_path else "   ❌ 格式错误")
    
    # 测试储蓄账户路径
    print("\n2. 储蓄账户月结单路径生成:")
    savings_path = FileStorageManager.generate_savings_path(
        customer_code="Be_rich_AA",
        bank_name="GX Bank",
        account_num="1761028205600",
        statement_date=datetime(2025, 10, 1)
    )
    print(f"   路径: {savings_path}")
    print(f"   ✅ 格式正确" if "Be_rich_AA/savings/GX_Bank/2025-10" in savings_path else "   ❌ 格式错误")
    
    # 测试收据路径
    print("\n3. 收据路径生成:")
    receipt_path = FileStorageManager.generate_receipt_path(
        customer_code="Be_rich_LWM",
        receipt_date=datetime(2025, 10, 15),
        merchant="Starbucks",
        amount=25.50,
        card_last4="1234",
        file_extension="jpg"
    )
    print(f"   路径: {receipt_path}")
    print(f"   ✅ 格式正确" if "receipts/payment_receipts/2025-10" in receipt_path else "   ❌ 格式错误")
    
    # 测试发票路径
    print("\n4. 发票路径生成:")
    invoice_path = FileStorageManager.generate_invoice_path(
        customer_code="Be_rich_CCC",
        invoice_type="supplier",
        party_name="ABC Supply",
        invoice_number="INV001",
        invoice_date=datetime(2025, 10, 20)
    )
    print(f"   路径: {invoice_path}")
    print(f"   ✅ 格式正确" if "invoices/supplier/2025-10" in invoice_path else "   ❌ 格式错误")
    
    # 测试报告路径
    print("\n5. 月度报告路径生成:")
    report_path = FileStorageManager.generate_report_path(
        customer_code="Be_rich_CCC",
        report_type="monthly",
        report_date=datetime(2025, 10, 1)
    )
    print(f"   路径: {report_path}")
    print(f"   ✅ 格式正确" if "reports/monthly/2025-10" in report_path else "   ❌ 格式错误")

def test_filename_sanitization():
    """测试文件名清理功能"""
    print("\n" + "=" * 80)
    print("测试文件名清理功能")
    print("=" * 80)
    
    test_cases = [
        ("Hong Leong Bank", "Hong_Leong_Bank"),
        ("ABC/Supply Co.", "ABCSupply_Co"),
        ("Test  Multiple   Spaces", "Test_Multiple_Spaces"),
        ("Special@#$Chars!", "SpecialChars"),
    ]
    
    for original, expected in test_cases:
        cleaned = FileStorageManager.sanitize_filename(original)
        status = "✅" if cleaned == expected else "❌"
        print(f"{status} '{original}' → '{cleaned}' (期望: '{expected}')")

def test_directory_operations():
    """测试目录操作"""
    print("\n" + "=" * 80)
    print("测试目录操作")
    print("=" * 80)
    
    # 创建临时测试路径
    test_path = "static/uploads/customers/TEST_CUSTOMER/credit_cards/Test_Bank/2025-10/test.pdf"
    
    print(f"\n测试路径: {test_path}")
    
    # 测试目录创建
    print("\n1. 测试目录创建:")
    directory = FileStorageManager.ensure_directory(test_path)
    if os.path.exists(directory):
        print(f"   ✅ 目录创建成功: {directory}")
    else:
        print(f"   ❌ 目录创建失败")
    
    # 清理测试目录
    import shutil
    if os.path.exists("static/uploads/customers/TEST_CUSTOMER"):
        shutil.rmtree("static/uploads/customers/TEST_CUSTOMER")
        print("\n2. 清理测试目录:")
        print("   ✅ 测试目录已清理")

def test_file_operations():
    """测试文件操作"""
    print("\n" + "=" * 80)
    print("测试文件操作")
    print("=" * 80)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("测试内容")
        temp_file = tmp.name
    
    test_dest = "static/uploads/customers/TEST_CUSTOMER/test_file.txt"
    
    try:
        # 测试保存文件
        print("\n1. 测试保存文件:")
        if FileStorageManager.save_file(temp_file, test_dest):
            print(f"   ✅ 文件保存成功")
            print(f"   文件存在: {FileStorageManager.file_exists(test_dest)}")
        else:
            print(f"   ❌ 文件保存失败")
        
        # 测试文件移动
        print("\n2. 测试文件移动:")
        new_dest = "static/uploads/customers/TEST_CUSTOMER/moved_file.txt"
        if FileStorageManager.move_file(test_dest, new_dest):
            print(f"   ✅ 文件移动成功")
            print(f"   旧路径存在: {FileStorageManager.file_exists(test_dest)}")
            print(f"   新路径存在: {FileStorageManager.file_exists(new_dest)}")
        else:
            print(f"   ❌ 文件移动失败")
        
        # 测试文件删除
        print("\n3. 测试文件删除:")
        if FileStorageManager.delete_file(new_dest, backup=False):
            print(f"   ✅ 文件删除成功")
            print(f"   文件存在: {FileStorageManager.file_exists(new_dest)}")
        else:
            print(f"   ❌ 文件删除失败")
            
    finally:
        # 清理
        import shutil
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists("static/uploads/customers/TEST_CUSTOMER"):
            shutil.rmtree("static/uploads/customers/TEST_CUSTOMER")
        print("\n4. 清理测试文件:")
        print("   ✅ 测试文件已清理")

def test_storage_stats():
    """测试存储统计功能"""
    print("\n" + "=" * 80)
    print("测试存储统计功能")
    print("=" * 80)
    
    # 使用实际客户测试（如果存在）
    print("\n获取客户 Be_rich_AA 的存储统计:")
    stats = FileStorageManager.get_storage_stats("Be_rich_AA")
    
    print(f"\n总文件数: {stats['total_files']}")
    print(f"总大小: {stats['total_size_mb']:.2f} MB")
    
    if stats['by_type']:
        print("\n按类型统计:")
        for file_type, type_stats in stats['by_type'].items():
            if type_stats['count'] > 0:
                print(f"  {file_type}: {type_stats['count']} 个文件, {type_stats['size_mb']:.2f} MB")

def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("文件存储管理器功能测试")
    print("=" * 80)
    
    test_path_generation()
    test_filename_sanitization()
    test_directory_operations()
    test_file_operations()
    test_storage_stats()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()
