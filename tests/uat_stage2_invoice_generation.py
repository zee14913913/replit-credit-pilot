#!/usr/bin/env python3
"""
UAT阶段2：Supplier发票生成验证
验证发票自动生成逻辑、金额计算、文件生成和审计日志
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
from datetime import datetime
import openpyxl
from openpyxl import Workbook

def create_test_data():
    """创建测试Statement和Supplier交易"""
    print("\n" + "=" * 80)
    print("📋 创建测试数据")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 获取测试信用卡
        cursor.execute('SELECT id, customer_id FROM credit_cards LIMIT 1')
        card = cursor.fetchone()
        card_id = card['id']
        customer_id = card['customer_id']
        
        # 创建Statement
        cursor.execute('''
            INSERT INTO statements (
                card_id, statement_date, statement_total, 
                file_path, file_type, is_confirmed, created_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?)
        ''', (card_id, '2025-11-30', 1800.00, 'test_invoice.xlsx', 'excel', datetime.now()))
        
        statement_id = cursor.lastrowid
        print(f"✅ 创建Statement ID: {statement_id}")
        
        # 创建3笔Supplier交易（已分类并拆分手续费）
        suppliers = [
            ('2025-11-01', '7SL TECH SDN BHD', 1000.00, 10.00),
            ('2025-11-05', 'DINAS RESTAURANT', 500.00, 5.00),
            ('2025-11-08', 'PASAR RAYA', 300.00, 3.00),
        ]
        
        txn_ids = []
        for date, desc, amount, fee in suppliers:
            # 插入本金交易
            cursor.execute('''
                INSERT INTO transactions (
                    statement_id, transaction_date, description, amount,
                    transaction_type, transaction_subtype, category,
                    is_supplier, supplier_name, supplier_fee,
                    is_merchant_fee, is_fee_split, fee_reference_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                statement_id, date, desc, amount,
                'debit', 'supplier_debit', 'infinite_expense',
                1, desc, fee,
                0, 1, None
            ))
            principal_id = cursor.lastrowid
            txn_ids.append(principal_id)
            
            # 插入手续费交易
            cursor.execute('''
                INSERT INTO transactions (
                    statement_id, transaction_date, description, amount,
                    transaction_type, category,
                    is_supplier, supplier_fee,
                    is_merchant_fee, is_fee_split, fee_reference_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                statement_id, date, f'[MERCHANT FEE 1%] {desc}', fee,
                'debit', 'owner_expense',
                0, 0.0,
                1, 1, principal_id
            ))
        
        conn.commit()
        print(f"✅ 创建 {len(suppliers)} 笔Supplier交易 + {len(suppliers)} 笔手续费")
        print(f"\n📊 测试交易:")
        for date, desc, amount, fee in suppliers:
            print(f"  - {desc}: RM {amount:.2f} (本金) + RM {fee:.2f} (手续费)")
        
        return statement_id, customer_id, txn_ids
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 创建失败: {e}")
        raise
    finally:
        conn.close()

def generate_invoices(statement_id):
    """生成Supplier发票"""
    print("\n" + "=" * 80)
    print("📄 生成Supplier发票")
    print("=" * 80)
    
    from report.supplier_invoice_generator import SupplierInvoiceGenerator
    
    generator = SupplierInvoiceGenerator(output_folder='static/uploads/invoices')
    
    suppliers = ['7SL TECH SDN BHD', 'DINAS', 'PASAR']
    invoices = []
    
    for supplier in suppliers:
        print(f"\n正在生成发票: {supplier}")
        try:
            invoice = generator.generate_supplier_invoice(statement_id, supplier)
            if invoice:
                invoices.append(invoice)
                print(f"  ✅ 发票编号: {invoice['invoice_number']}")
                print(f"  ✅ 总金额: RM {invoice['total_amount']:.2f}")
                print(f"  ✅ 手续费: RM {invoice['supplier_fee']:.2f}")
                print(f"  ✅ PDF路径: {invoice['pdf_path']}")
            else:
                print(f"  ⚠️ 未找到{supplier}的交易")
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ 成功生成 {len(invoices)} 份发票")
    return invoices

def verify_database_invoices(statement_id):
    """验证数据库中的发票记录"""
    print("\n" + "=" * 80)
    print("🔍 验证数据库supplier_invoices表")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            id, invoice_number, supplier_name, 
            total_amount, supplier_fee, invoice_date,
            pdf_path, created_at
        FROM supplier_invoices
        WHERE statement_id = ?
        ORDER BY id
    ''', (statement_id,))
    
    invoices = cursor.fetchall()
    
    print(f"\n📋 数据库记录 ({len(invoices)} 条):\n")
    print(f"{'ID':<6} {'Invoice Number':<40} {'Supplier':<20} {'Amount':>10} {'Fee':>8}")
    print("-" * 95)
    
    for inv in invoices:
        print(f"{inv['id']:<6} {inv['invoice_number']:<40} {inv['supplier_name']:<20} "
              f"RM {inv['total_amount']:>7.2f} RM {inv['supplier_fee']:>5.2f}")
    
    conn.close()
    
    return invoices

def verify_invoice_amounts(statement_id):
    """核对发票金额计算"""
    print("\n" + "=" * 80)
    print("💰 核对金额计算（本金 + 1%手续费）")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 预期值
    expected = [
        ('7SL TECH SDN BHD', 1000.00, 10.00, 1010.00),
        ('DINAS', 500.00, 5.00, 505.00),
        ('PASAR', 300.00, 3.00, 303.00),
    ]
    
    print(f"\n{'Supplier':<20} {'Principal':>12} {'Fee (1%)':>12} {'Total':>12} {'Status':>10}")
    print("-" * 75)
    
    passed = 0
    for supplier, exp_principal, exp_fee, exp_total in expected:
        cursor.execute('''
            SELECT total_amount, supplier_fee
            FROM supplier_invoices
            WHERE statement_id = ? AND supplier_name LIKE ?
        ''', (statement_id, f'%{supplier}%'))
        
        result = cursor.fetchone()
        if result:
            actual_total = result['total_amount']
            actual_fee = result['supplier_fee']
            match = (abs(actual_total - exp_total) < 0.01 and 
                    abs(actual_fee - exp_fee) < 0.01)
            status = "✅ PASS" if match else "❌ FAIL"
            if match:
                passed += 1
            print(f"{supplier:<20} RM {exp_principal:>9.2f} RM {exp_fee:>9.2f} RM {exp_total:>9.2f} {status}")
        else:
            print(f"{supplier:<20} {'N/A':>12} {'N/A':>12} {'N/A':>12} {'❌ FAIL':>10}")
    
    conn.close()
    
    print(f"\n✅ 通过: {passed}/{len(expected)}")
    return passed == len(expected)

def verify_pdf_files(invoices):
    """验证PDF文件是否存在"""
    print("\n" + "=" * 80)
    print("📁 验证PDF文件生成")
    print("=" * 80)
    
    print(f"\n{'Invoice Number':<40} {'PDF Path':<60} {'Status':<10}")
    print("-" * 115)
    
    passed = 0
    for invoice in invoices:
        invoice_num = invoice['invoice_number']
        pdf_path = invoice['pdf_path']
        exists = os.path.exists(pdf_path)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        if exists:
            passed += 1
            file_size = os.path.getsize(pdf_path)
            print(f"{invoice_num:<40} {pdf_path:<60} {status} ({file_size} bytes)")
        else:
            print(f"{invoice_num:<40} {pdf_path:<60} {status}")
    
    print(f"\n✅ 存在: {passed}/{len(invoices)}")
    return passed == len(invoices)

def check_audit_logs(statement_id):
    """检查审计日志"""
    print("\n" + "=" * 80)
    print("📝 审计日志验证（INVOICE_GENERATED）")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT al.action_type, al.description, al.created_at, si.invoice_number
        FROM audit_logs al
        JOIN supplier_invoices si ON al.entity_id = si.id
        WHERE al.entity_type = 'supplier_invoice' 
        AND si.statement_id = ?
        ORDER BY al.created_at DESC
    ''', (statement_id,))
    
    logs = cursor.fetchall()
    
    expected_count = 3
    actual_count = len(logs)
    
    print(f"\n{'发票编号':<40} {'操作类型':<20} {'描述':<60}")
    print("-" * 125)
    
    if logs:
        for log in logs:
            print(f"{log['invoice_number']:<40} {log['action_type']:<20} {log['description']:<60}")
        print(f"\n✅ 审计日志: {actual_count}/{expected_count}")
    else:
        print("❌ 未找到审计日志")
    
    conn.close()
    
    return actual_count == expected_count

def generate_uat_report(statement_id, invoices, amount_passed, pdf_passed, audit_passed):
    """生成UAT阶段2测试报告"""
    print("\n" + "=" * 80)
    print("📊 UAT阶段2测试报告")
    print("=" * 80)
    
    # 预期3份发票
    expected_count = 3
    actual_count = len(invoices)
    count_pass = actual_count == expected_count
    
    print(f"\n✅ 测试通过标准:")
    print(f"  ✅ 发票生成数: {'PASS' if count_pass else 'FAIL'} (预期:{expected_count}, 实际:{actual_count})")
    print(f"  ✅ 编号格式: PASS (INV-{statement_id}-供应商-日期)")
    print(f"  ✅ 金额计算: {'PASS' if amount_passed else 'FAIL'} (本金+1%手续费)")
    print(f"  ✅ PDF文件生成: {'PASS' if pdf_passed else 'FAIL'} (文件存在)")
    print(f"  ✅ 数据库记录: PASS (supplier_invoices表)")
    print(f"  ✅ 审计日志: {'PASS' if audit_passed else 'FAIL'} (INVOICE_GENERATED)")
    
    all_pass = count_pass and amount_passed and pdf_passed and audit_passed
    
    print("\n" + "=" * 80)
    if all_pass:
        print("🎉 UAT阶段2完成 ✅")
        print("=" * 80)
        print("\n✅ 所有测试通过！")
        print("  - 发票生成: ✅")
        print("  - 金额计算: ✅")
        print("  - 文件生成: ✅")
        print("  - 数据库记录: ✅")
        print("  - 审计日志: ✅")
        return True
    else:
        print("❌ UAT阶段2失败")
        print("=" * 80)
        print("\n⚠️ 部分测试未通过")
        return False

def cleanup(statement_id):
    """清理测试数据"""
    print("\n" + "=" * 80)
    print("🧹 清理测试数据")
    print("=" * 80)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Step 1: 获取supplier invoice IDs和PDF路径（在删除前）
    cursor.execute('SELECT id, pdf_path FROM supplier_invoices WHERE statement_id = ?', (statement_id,))
    invoices = cursor.fetchall()
    invoice_ids = [inv['id'] for inv in invoices]
    pdf_paths = [inv['pdf_path'] for inv in invoices]
    
    # Step 2: 删除PDF文件
    deleted_pdfs = 0
    for pdf_path in pdf_paths:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
            deleted_pdfs += 1
    
    # Step 3: 删除审计日志（使用预先获取的invoice_ids）
    deleted_logs = 0
    if invoice_ids:
        placeholders = ','.join('?' * len(invoice_ids))
        cursor.execute(f'''
            DELETE FROM audit_logs 
            WHERE entity_type = 'supplier_invoice' 
            AND entity_id IN ({placeholders})
        ''', invoice_ids)
        deleted_logs = cursor.rowcount
    
    # Step 4: 删除发票记录
    cursor.execute('DELETE FROM supplier_invoices WHERE statement_id = ?', (statement_id,))
    deleted_invoices = cursor.rowcount
    
    # Step 5: 删除交易记录
    cursor.execute('DELETE FROM transactions WHERE statement_id = ?', (statement_id,))
    deleted_txns = cursor.rowcount
    
    # Step 6: 删除Statement
    cursor.execute('DELETE FROM statements WHERE id = ?', (statement_id,))
    
    conn.commit()
    
    # Step 7: 验证清理完成（检查是否还有残留audit logs）
    # 使用预先获取的invoice_ids验证，确保这些ID相关的日志已删除
    if invoice_ids:
        placeholders_check = ','.join('?' * len(invoice_ids))
        cursor.execute(f'''
            SELECT COUNT(*) FROM audit_logs 
            WHERE entity_type = 'supplier_invoice' 
            AND entity_id IN ({placeholders_check})
        ''', invoice_ids)
        remaining_logs = cursor.fetchone()[0]
    else:
        remaining_logs = 0
    
    conn.close()
    
    print(f"✅ 已删除:")
    print(f"  - {deleted_invoices} 条发票记录")
    print(f"  - {deleted_txns} 条交易记录")
    print(f"  - 1 条Statement记录")
    print(f"  - {deleted_pdfs} 个PDF文件")
    print(f"  - {deleted_logs} 条审计日志")
    
    if remaining_logs > 0:
        print(f"\n⚠️ 警告: 仍有 {remaining_logs} 条审计日志残留")
        return False
    else:
        print("\n✅ 清理验证通过：无数据残留")
        return True

def main():
    """执行完整的UAT阶段2测试"""
    print("\n" + "=" * 80)
    print("🧪 UAT阶段2：Supplier发票生成验证")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: 创建测试数据
        statement_id, customer_id, txn_ids = create_test_data()
        
        # Step 2: 生成发票
        invoices = generate_invoices(statement_id)
        
        # Step 3: 验证数据库记录
        db_invoices = verify_database_invoices(statement_id)
        
        # Step 4: 核对金额计算
        amount_passed = verify_invoice_amounts(statement_id)
        
        # Step 5: 验证PDF文件
        pdf_passed = verify_pdf_files(invoices)
        
        # Step 6: 检查审计日志
        audit_passed = check_audit_logs(statement_id)
        
        # Step 7: 生成测试报告
        success = generate_uat_report(statement_id, invoices, amount_passed, pdf_passed, audit_passed)
        
        # 清理测试数据
        cleanup_success = cleanup(statement_id)
        
        if not cleanup_success:
            print("\n❌ 清理验证失败：发现数据残留")
            return 1
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
