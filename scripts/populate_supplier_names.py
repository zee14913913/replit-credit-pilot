#!/usr/bin/env python3
"""
为INFINITE交易填充supplier_name字段
Populate supplier_name field for INFINITE transactions
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_db
from services.ledger_classifier import LedgerClassifier


def populate_supplier_names():
    """为所有INFINITE交易填充supplier_name"""
    
    print("="*80)
    print("为INFINITE交易填充supplier_name字段")
    print("="*80)
    
    classifier = LedgerClassifier()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：获取所有INFINITE交易
        print("\n步骤1: 查询所有INFINITE交易...")
        cursor.execute('''
            SELECT id, description, supplier_name
            FROM transactions
            WHERE owner_flag = 'INFINITE'
        ''')
        
        infinite_txns = cursor.fetchall()
        print(f"   找到 {len(infinite_txns)} 条INFINITE交易")
        
        # 步骤2：检查当前supplier_name状态
        cursor.execute('''
            SELECT COUNT(*) as cnt
            FROM transactions
            WHERE owner_flag = 'INFINITE'
              AND (supplier_name IS NULL OR supplier_name = '')
        ''')
        null_count = cursor.fetchone()['cnt']
        
        print(f"   其中 {null_count} 条没有supplier_name")
        
        if null_count == 0:
            print("   所有INFINITE交易都已有supplier_name，无需处理")
            return
        
        # 步骤3：使用分类器提取supplier_name
        print("\n步骤2: 使用分类器提取supplier_name...")
        update_stats = {
            'matched': 0,
            'not_matched': 0,
            'already_set': 0
        }
        
        suppliers_found = {}
        
        for txn in infinite_txns:
            txn_id = txn['id']
            description = txn['description']
            current_supplier = txn['supplier_name']
            
            # 如果已经有supplier_name，跳过
            if current_supplier and current_supplier.strip():
                update_stats['already_set'] += 1
                continue
            
            # 使用分类器识别supplier
            is_supplier, supplier_name = classifier.is_infinite_supplier(description)
            
            if is_supplier and supplier_name:
                # 更新supplier_name
                cursor.execute('''
                    UPDATE transactions
                    SET supplier_name = ?
                    WHERE id = ?
                ''', (supplier_name, txn_id))
                
                update_stats['matched'] += 1
                
                # 统计每个supplier的数量
                if supplier_name not in suppliers_found:
                    suppliers_found[supplier_name] = 0
                suppliers_found[supplier_name] += 1
            else:
                update_stats['not_matched'] += 1
        
        conn.commit()
        
        # 步骤3：显示结果
        print("\n步骤3: 填充结果...")
        print(f"   ✅ 匹配并更新: {update_stats['matched']} 条")
        print(f"   ⏭️  已有supplier_name: {update_stats['already_set']} 条")
        print(f"   ⚠️  未匹配到supplier: {update_stats['not_matched']} 条")
        
        if suppliers_found:
            print("\n步骤4: 找到的供应商分布:")
            for supplier, count in sorted(suppliers_found.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {supplier}: {count} 笔交易")
        
        # 步骤5：验证更新后的状态
        print("\n步骤5: 验证更新后的状态...")
        cursor.execute('''
            SELECT COUNT(*) as cnt
            FROM transactions
            WHERE owner_flag = 'INFINITE'
              AND supplier_name IS NOT NULL
              AND supplier_name != ''
        ''')
        filled_count = cursor.fetchone()['cnt']
        
        cursor.execute('''
            SELECT COUNT(*) as cnt
            FROM transactions
            WHERE owner_flag = 'INFINITE'
        ''')
        total_count = cursor.fetchone()['cnt']
        
        fill_rate = (filled_count / total_count * 100) if total_count > 0 else 0
        
        print(f"   📊 填充率: {filled_count}/{total_count} ({fill_rate:.1f}%)")
        
        # 步骤6：显示未匹配的交易示例
        if update_stats['not_matched'] > 0:
            print("\n步骤6: 未匹配交易示例（前10条）:")
            cursor.execute('''
                SELECT id, transaction_date, description, amount
                FROM transactions
                WHERE owner_flag = 'INFINITE'
                  AND (supplier_name IS NULL OR supplier_name = '')
                LIMIT 10
            ''')
            
            unmatched = cursor.fetchall()
            for txn in unmatched:
                print(f"   ID {txn['id']}: {txn['transaction_date']} | {txn['description'][:50]} | RM{txn['amount']:.2f}")
        
        print("\n" + "="*80)
        print("✅ supplier_name填充完成！")
        print("="*80)
        print("📊 总结:")
        print(f"   - INFINITE交易总数: {total_count}")
        print(f"   - 成功填充: {update_stats['matched']} 条")
        print(f"   - 填充率: {fill_rate:.1f}%")
        print(f"   - 识别供应商数: {len(suppliers_found)} 个")
        print("="*80)


if __name__ == "__main__":
    populate_supplier_names()
