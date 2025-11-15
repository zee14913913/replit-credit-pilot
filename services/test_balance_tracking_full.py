"""
INFINITE GZ 完整端到端余额追踪测试
测试流程：转账记录 → 付款分类 → 保存交易 → 自动分配余额 → 验证
"""

import sqlite3
import os
from datetime import datetime
from infinite_gz_classification_engine import InfiniteGZClassificationEngine

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/smart_loan_manager.db')

def setup_test():
    """设置测试"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清理测试数据
    cursor.execute("DELETE FROM gz_transfer_payment_links WHERE transfer_id IN (SELECT id FROM gz_transfer_records WHERE customer_id = 998)")
    cursor.execute("DELETE FROM gz_transfer_records WHERE customer_id = 998")
    cursor.execute("DELETE FROM monthly_statement_transactions WHERE customer_id = 998")
    
    # 插入测试客户
    cursor.execute('''
        INSERT OR IGNORE INTO customers (id, customer_code, name, email, phone, created_at)
        VALUES (998, 'TEST998', 'Full Test Customer', 'fulltest@test.com', '0199999999', ?)
    ''', (datetime.now(),))
    
    # 插入GZ转账（Card Due Assist，余额RM 1000）
    cursor.execute('''
        INSERT INTO gz_transfer_records (
            customer_id, source_bank, destination_account,
            amount, transfer_date, purpose, verified, affects,
            linked_statement_month, remaining_balance, created_at
        ) VALUES (998, 'YEO CHEE WANG MBB', 'TEST998 ACCOUNT', 1000.00, '2025-01-05', 
                  'Card Due Assist', 1, 'GZ OS Balance', '2025-01', 1000.00, ?)
    ''', (datetime.now(),))
    
    transfer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print("✓ 测试环境初始化完成")
    print(f"  客户ID: 998")
    print(f"  GZ转账ID: {transfer_id}")
    print(f"  初始余额: RM 1000.00\n")
    
    return transfer_id

def test_full_balance_tracking():
    """完整端到端测试"""
    
    print("=" * 80)
    print("INFINITE GZ 完整端到端余额追踪测试")
    print("=" * 80)
    print()
    
    transfer_id = setup_test()
    engine = InfiniteGZClassificationEngine()
    
    # 测试场景：客户分3次付款
    payments = [
        {'amount': 400.00, 'date': '2025-01-10', 'description': 'PAYMENT VIA FPX', 'card_last4': '1234'},
        {'amount': 300.00, 'date': '2025-01-15', 'description': 'PAYMENT ONLINE', 'card_last4': '1234'},
        {'amount': 300.00, 'date': '2025-01-20', 'description': 'PAYMENT ONLINE', 'card_last4': '1234'},
    ]
    
    print("【测试场景】客户分3次付款，消耗GZ转账余额\n")
    print("-" * 80)
    
    for i, payment in enumerate(payments, 1):
        print(f"\n步骤{i}：客户付款 RM {payment['amount']:.2f}（{payment['date']}）")
        
        # 1. 分类付款
        classification = engine.classify_payment_type(
            description=payment['description'],
            amount=payment['amount'],
            customer_id=998,
            statement_month='2025-01',
            payment_date=payment['date'],
            card_last4=payment['card_last4'],
            check_indirect=True
        )
        
        print(f"  → 分类: {classification['payment_type']}")
        print(f"  → 验证: {'是' if classification['verified'] else '否'}")
        
        # 2. 保存交易（自动分配余额）
        transaction = {
            'customer_id': 998,
            'statement_month': '2025-01',
            'bank_name': 'Maybank',
            'card_last4': payment['card_last4'],
            'date': payment['date'],
            'description': payment['description'],
            'amount': payment['amount'],
            'record_type': 'payment',
            'payment_type': classification['payment_type'],
            'verified': classification['verified'],
            'matched_transfer': classification.get('matched_transfer')
        }
        
        transaction_id = engine.save_classified_transaction(transaction)
        print(f"  → 交易ID: {transaction_id}（已保存并分配）")
        
        # 3. 验证余额更新
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT remaining_balance FROM gz_transfer_records WHERE id = ?', (transfer_id,))
        new_balance = cursor.fetchone()[0]
        print(f"  → 转账剩余余额: RM {new_balance:.2f}")
        conn.close()
    
    # 步骤4：再付一笔（余额已用完 → Owner Payment）
    print(f"\n步骤4：客户再付款 RM 200.00（余额已用完）")
    
    final_classification = engine.classify_payment_type(
        description='PAYMENT ONLINE',
        amount=200.00,
        customer_id=998,
        statement_month='2025-01',
        payment_date='2025-01-25',
        card_last4='1234',
        check_indirect=True
    )
    
    print(f"  → 分类: {final_classification['payment_type']}")
    print(f"  → 验证: {'是' if final_classification['verified'] else '否'}")
    
    if final_classification['payment_type'] == 'Owner Payment':
        print(f"  ✅ 正确！余额用完后自动切换为Owner Payment")
    else:
        print(f"  ❌ 错误！应该是Owner Payment")
    
    # 最终验证
    print("\n" + "=" * 80)
    print("最终验证结果")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查转账余额
    cursor.execute('SELECT remaining_balance FROM gz_transfer_records WHERE id = ?', (transfer_id,))
    final_balance = cursor.fetchone()[0]
    print(f"\nGZ转账最终余额: RM {final_balance:.2f}")
    print(f"  预期: RM 0.00（1000 - 400 - 300 - 300 = 0）")
    print(f"  结果: {'✅ 正确' if final_balance == 0 else '❌ 错误'}")
    
    # 检查分配记录
    cursor.execute('SELECT COUNT(*), SUM(allocated_amount) FROM gz_transfer_payment_links WHERE transfer_id = ?', (transfer_id,))
    count, total_allocated = cursor.fetchone()
    print(f"\n分配记录数量: {count}")
    print(f"  预期: 3笔分配")
    print(f"  结果: {'✅ 正确' if count == 3 else '❌ 错误'}")
    
    print(f"\n总分配金额: RM {total_allocated:.2f}")
    print(f"  预期: RM 1000.00")
    print(f"  结果: {'✅ 正确' if total_allocated == 1000 else '❌ 错误'}")
    
    # 检查付款类型分布
    cursor.execute('''
        SELECT payment_type, COUNT(*) 
        FROM monthly_statement_transactions 
        WHERE customer_id = 998
        GROUP BY payment_type
    ''')
    payment_stats = cursor.fetchall()
    
    print(f"\n付款类型分布:")
    for payment_type, count in payment_stats:
        print(f"  {payment_type}: {count}笔")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 完整端到端余额追踪测试完成！")
    print("=" * 80)

if __name__ == '__main__':
    test_full_balance_tracking()
