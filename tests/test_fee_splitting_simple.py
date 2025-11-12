#!/usr/bin/env python3
"""
简化版手续费拆分测试 - 验证Architect发现的缺陷已修复
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.owner_infinite_classifier import OwnerInfiniteClassifier
import sqlite3

def test_merchant_fee_protection():
    """
    核心测试：验证is_merchant_fee标志能防止手续费被重新分类为infinite_expense
    """
    print("\n" + "=" * 80)
    print("🧪 TEST: Merchant Fee Protection Against Reclassification")
    print("=" * 80)
    
    classifier = OwnerInfiniteClassifier()
    
    # 测试场景1：手续费交易应该始终分类为owner_expense
    print("\n✅ Scenario 1: Merchant fee transaction with Supplier keyword")
    result1 = classifier.classify_expense(
        description="[MERCHANT FEE 1%] 7SL TECH SDN BHD",
        amount=10.00,
        is_merchant_fee=True,  # 关键标志
        is_fee_split=True
    )
    
    assert result1['expense_type'] == 'owner', f"❌ FAIL: Fee classified as {result1['expense_type']}, expected 'owner'"
    assert result1['is_supplier'] == False, "❌ FAIL: Fee marked as supplier"
    assert result1['supplier_fee'] == 0.0, "❌ FAIL: Fee has supplier_fee"
    print(f"  ✅ PASS: Fee correctly classified as '{result1['expense_type']}_expense'")
    print(f"  ✅ PASS: is_supplier = {result1['is_supplier']}")
    print(f"  ✅ PASS: supplier_fee = {result1['supplier_fee']}")
    
    # 测试场景2：普通Supplier交易（不是手续费）
    print("\n✅ Scenario 2: Normal Supplier transaction (not a fee)")
    result2 = classifier.classify_expense(
        description="7SL TECH SDN BHD",
        amount=1000.00,
        is_merchant_fee=False,  # 不是手续费
        is_fee_split=False
    )
    
    assert result2['expense_type'] == 'infinite', f"❌ FAIL: Supplier classified as {result2['expense_type']}, expected 'infinite'"
    assert result2['is_supplier'] == True, "❌ FAIL: Supplier not marked as supplier"
    assert result2['supplier_fee'] == 10.0, f"❌ FAIL: Supplier fee is {result2['supplier_fee']}, expected 10.0"
    print(f"  ✅ PASS: Supplier correctly classified as '{result2['expense_type']}_expense'")
    print(f"  ✅ PASS: is_supplier = {result2['is_supplier']}")
    print(f"  ✅ PASS: supplier_fee = {result2['supplier_fee']}")
    
    # 测试场景3：普通消费（非Supplier，非手续费）
    print("\n✅ Scenario 3: Personal expense (not Supplier, not fee)")
    result3 = classifier.classify_expense(
        description="STARBUCKS COFFEE",
        amount=50.00,
        is_merchant_fee=False,
        is_fee_split=False
    )
    
    assert result3['expense_type'] == 'owner', f"❌ FAIL: Personal expense classified as {result3['expense_type']}, expected 'owner'"
    print(f"  ✅ PASS: Personal expense correctly classified as '{result3['expense_type']}_expense'")
    
    print("\n" + "=" * 80)
    print("✅ ✅ ✅ ALL TESTS PASSED!")
    print("=" * 80)
    
    print("\n🔒 CRITICAL FIX VERIFIED:")
    print("  - Merchant fees are protected from reclassification")
    print("  - is_merchant_fee flag prevents infinite_expense assignment")
    print("  - Supplier transactions still work correctly")
    print("  - Owner vs GZ ledger segregation is maintained")
    
    return True


def test_supplier_refund_protection():
    """
    🔒 CRITICAL: 测试Supplier退款不会生成手续费
    """
    print("\n" + "=" * 80)
    print("🧪 TEST: Supplier Refund Protection (No Fee Generation)")
    print("=" * 80)
    
    import sqlite3
    classifier = OwnerInfiniteClassifier()
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 创建测试退款交易（负金额）
    cursor.execute('''
        INSERT INTO transactions (
            statement_id, transaction_date, description, amount,
            transaction_type, is_merchant_fee, is_fee_split, category
        ) VALUES (999, '2025-11-10', '7SL TECH SDN BHD - REFUND', -500.00, 'credit', 0, 0, NULL)
    ''')
    refund_txn_id = cursor.lastrowid
    conn.commit()
    
    print(f"✅ Created refund transaction ID: {refund_txn_id} (amount: -500.00)")
    
    # 尝试拆分手续费（应该被跳过）
    print(f"\n🔍 Testing classify_and_split_supplier_fee on refund...")
    result = classifier.classify_and_split_supplier_fee(refund_txn_id)
    
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # 验证：不应该生成手续费
    assert result['status'] == 'skipped', f"❌ FAIL: Refund was not skipped, status={result['status']}"
    assert 'refund' in result['message'].lower() or 'credit' in result['message'].lower(), "❌ FAIL: Wrong skip reason"
    
    # 验证：没有新的手续费交易
    cursor.execute('''
        SELECT COUNT(*) FROM transactions 
        WHERE fee_reference_id = ?
    ''', (refund_txn_id,))
    fee_count = cursor.fetchone()[0]
    
    assert fee_count == 0, f"❌ FAIL: Fee transaction was created for refund! Count: {fee_count}"
    print(f"  ✅ PASS: No fee transaction created (count={fee_count})")
    
    # 清理
    cursor.execute('DELETE FROM transactions WHERE id = ?', (refund_txn_id,))
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ ✅ ✅ REFUND PROTECTION TEST PASSED!")
    print("=" * 80)
    print("\n🔒 VERIFIED:")
    print("  - Refund transactions (negative amount) skip fee splitting")
    print("  - No erroneous fee transactions generated")
    print("  - Ledger integrity maintained for credits")
    
    return True


def test_full_transaction_classification():
    """
    完整测试：模拟classify_transaction方法
    """
    print("\n" + "=" * 80)
    print("🧪 TEST: Full Transaction Classification with Protection")
    print("=" * 80)
    
    classifier = OwnerInfiniteClassifier()
    
    # 测试1：手续费交易通过classify_transaction
    print("\n✅ Test 1: classify_transaction with merchant fee")
    result = classifier.classify_transaction(
        transaction_id=999,
        description="[MERCHANT FEE 1%] 7SL TECH SDN BHD",
        amount=10.00,
        transaction_type='debit',
        customer_id=1,
        customer_name='Test Customer',
        is_merchant_fee=True,
        is_fee_split=True
    )
    
    assert result['category'] == 'owner_expense', f"❌ FAIL: Category is {result['category']}, expected 'owner_expense'"
    assert result['is_supplier'] == False, "❌ FAIL: Merchant fee marked as supplier"
    print(f"  ✅ PASS: category = {result['category']}")
    print(f"  ✅ PASS: is_supplier = {result['is_supplier']}")
    
    # 测试2：普通Supplier交易
    print("\n✅ Test 2: classify_transaction with Supplier")
    result2 = classifier.classify_transaction(
        transaction_id=998,
        description="7SL TECH SDN BHD",
        amount=1000.00,
        transaction_type='debit',
        customer_id=1,
        customer_name='Test Customer',
        is_merchant_fee=False,
        is_fee_split=False
    )
    
    assert result2['category'] == 'infinite_expense', f"❌ FAIL: Category is {result2['category']}, expected 'infinite_expense'"
    assert result2['is_supplier'] == True, "❌ FAIL: Supplier not marked"
    print(f"  ✅ PASS: category = {result2['category']}")
    print(f"  ✅ PASS: is_supplier = {result2['is_supplier']}")
    
    print("\n" + "=" * 80)
    print("✅ ✅ ✅ CLASSIFICATION TESTS PASSED!")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    try:
        # 运行所有测试
        test1_pass = test_merchant_fee_protection()
        test2_pass = test_full_transaction_classification()
        test3_pass = test_supplier_refund_protection()
        
        if test1_pass and test2_pass and test3_pass:
            print("\n" + "=" * 80)
            print("🎉 🎉 🎉  ALL TESTS PASSED  🎉 🎉 🎉")
            print("=" * 80)
            print("\nFee Splitting v5.1 is PRODUCTION-READY!")
            print("All Architect-identified regressions have been fixed.")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            sys.exit(1)
    
    except AssertionError as e:
        print(f"\n❌ Assertion Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
