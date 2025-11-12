#!/usr/bin/env python3
"""
回归测试：验证批量处理中多个Supplier交易能共享同一个数据库连接
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
from services.owner_infinite_classifier import OwnerInfiniteClassifier

def test_multi_supplier_shared_connection():
    """
    🔥 CRITICAL: 测试多个Supplier交易在批量处理中共享连接
    """
    print("\n" + "=" * 80)
    print("🧪 TEST: Multi-Supplier Batch Processing with Shared Connection")
    print("=" * 80)
    
    classifier = OwnerInfiniteClassifier()
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 创建3个测试Supplier交易
    test_suppliers = [
        ('2025-11-12', '7SL TECH SDN BHD', 1000.00),
        ('2025-11-12', 'DINAS RESTAURANT', 500.00),
        ('2025-11-12', '7SL TECH SDN BHD', 2000.00),  # 同一个supplier
    ]
    
    txn_ids = []
    for date, desc, amount in test_suppliers:
        cursor.execute('''
            INSERT INTO transactions (
                statement_id, transaction_date, description, amount,
                transaction_type, is_merchant_fee, is_fee_split, category
            ) VALUES (999, ?, ?, ?, 'debit', 0, 0, NULL)
        ''', (date, desc, amount))
        txn_ids.append(cursor.lastrowid)
    
    conn.commit()
    print(f"✅ Created {len(txn_ids)} Supplier transactions")
    
    # 使用共享连接进行批量拆分
    print(f"\n🔍 Processing all Suppliers with SHARED connection...")
    split_count = 0
    fee_count = 0
    
    try:
        for txn_id in txn_ids:
            # 模拟batch_classify_statement的逻辑：
            # 1. 分类交易
            # 2. 使用相同的conn/cursor调用拆分
            
            split_result = classifier.classify_and_split_supplier_fee(txn_id, conn, cursor)
            
            if split_result['status'] == 'success':
                split_count += 1
                fee_count += 1
                print(f"  ✅ Txn {txn_id}: Split successful → Fee RM{split_result['fee_amount']}")
            else:
                print(f"  ⚠️ Txn {txn_id}: {split_result['status']} - {split_result['message']}")
        
        # 一次性commit（模拟batch的行为）
        conn.commit()
        print(f"\n✅ All operations committed successfully")
        
    except Exception as e:
        print(f"\n❌ ERROR during batch processing: {e}")
        conn.rollback()
        conn.close()
        return False
    
    # 验证：每个Supplier交易都应该生成一个手续费交易
    cursor.execute('''
        SELECT COUNT(*) FROM transactions 
        WHERE fee_reference_id IN (?, ?, ?)
    ''', tuple(txn_ids))
    
    actual_fee_count = cursor.fetchone()[0]
    
    print(f"\n📊 Verification:")
    print(f"  - Expected fee transactions: {len(txn_ids)}")
    print(f"  - Actual fee transactions: {actual_fee_count}")
    print(f"  - Split operations: {split_count}")
    
    # 验证金额
    cursor.execute('''
        SELECT SUM(amount) FROM transactions 
        WHERE fee_reference_id IN (?, ?, ?)
    ''', tuple(txn_ids))
    
    total_fees = cursor.fetchone()[0] or 0.0
    expected_fees = sum(amt * 0.01 for _, _, amt in test_suppliers)
    
    print(f"  - Expected total fees: RM {expected_fees:.2f}")
    print(f"  - Actual total fees: RM {total_fees:.2f}")
    
    # 清理
    cursor.execute('''
        DELETE FROM transactions 
        WHERE id IN (?, ?, ?) OR fee_reference_id IN (?, ?, ?)
    ''', tuple(txn_ids) + tuple(txn_ids))
    conn.commit()
    conn.close()
    
    # 断言
    success = (
        actual_fee_count == len(txn_ids) and
        split_count == len(txn_ids) and
        abs(total_fees - expected_fees) < 0.01
    )
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ✅ ✅ MULTI-SUPPLIER BATCH TEST PASSED!")
        print("=" * 80)
        print("\n🔒 VERIFIED:")
        print("  - Multiple Supplier transactions share same DB connection")
        print("  - No connection closed prematurely")
        print("  - All fee transactions created correctly")
        print("  - Atomic commit at the end")
        return True
    else:
        print("❌ ❌ ❌ MULTI-SUPPLIER BATCH TEST FAILED!")
        print("=" * 80)
        return False


if __name__ == '__main__':
    try:
        success = test_multi_supplier_shared_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
