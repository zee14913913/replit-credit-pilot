
#!/usr/bin/env python3
"""
批量分类 Infinite GZ 系统中的所有交易
使用 TransactionClassifier 自动分类为 Owner/GZ Expenses/Payment
"""

import sys
import sqlite3
from datetime import datetime
from services.transaction_classifier import TransactionClassifier

DB_PATH = 'db/smart_loan_manager.db'

# 7个主要供应商列表
SUPPLIERS_LIST = [
    '7SL',
    'Dinas Raub',
    'SYC Hainan',
    'Ai Smart Tech',
    'HUAWEI',
    'Pasar Raya',
    'Puchong Herbs'
]

# GZ公司银行账户
GZ_BANK_ACCOUNTS = [
    'INFINITE GZ SDN BHD',
    'INFINITE GZ',
    'GZ SDN BHD'
]

def get_all_statements():
    """获取所有账单"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, s.statement_date, c.bank_name, c.card_number_last4, u.name as customer_name
        FROM statements s
        JOIN credit_cards c ON s.card_id = c.id
        JOIN users u ON s.user_id = u.id
        WHERE s.is_confirmed = 1
        ORDER BY s.statement_date
    """)
    
    statements = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return statements

def get_statement_transactions(statement_id):
    """获取账单的所有交易"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            transaction_date,
            description,
            merchant,
            debit_amount,
            credit_amount,
            category
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date
    """, (statement_id,))
    
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return transactions

def classify_transactions(statement_id, customer_name):
    """分类账单的所有交易"""
    # 初始化分类器
    classifier = TransactionClassifier(
        db_path=DB_PATH,
        suppliers_list=SUPPLIERS_LIST,
        gz_bank_accounts=GZ_BANK_ACCOUNTS,
        customer_name=customer_name
    )
    
    # 获取交易
    transactions = get_statement_transactions(statement_id)
    
    # 准备分类数据
    classify_data = []
    for txn in transactions:
        # 判断交易类型
        if txn['credit_amount'] and txn['credit_amount'] > 0:
            txn_type = 'payment'
        else:
            txn_type = 'expense'
        
        classify_data.append({
            'id': txn['id'],
            'transaction_type': txn_type,
            'description': txn['description'] or '',
            'merchant_name': txn['merchant'] or txn['description'] or '',
            'payer_info': txn['description'] or ''
        })
    
    # 批量分类
    result = classifier.batch_classify_transactions(classify_data)
    
    # 更新数据库分类
    updated = classifier.update_database_classifications(result['results'])
    
    # 计算1%商家手续费
    merchant_fee_total = 0.0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for txn_result in result['results']:
        if txn_result.get('is_supplier') and txn_result.get('category') == "GZ's Expenses":
            # 获取交易金额
            cursor.execute('SELECT debit_amount FROM transactions WHERE id = ?', (txn_result['transaction_id'],))
            row = cursor.fetchone()
            if row and row[0]:
                fee = abs(row[0]) * 0.01
                merchant_fee_total += fee
                # 更新supplier_fee字段
                cursor.execute('UPDATE transactions SET supplier_fee = ? WHERE id = ?', 
                             (fee, txn_result['transaction_id']))
    
    conn.commit()
    conn.close()
    
    return {
        'total': result['total'],
        'classified': result['classified'],
        'summary': result['summary'],
        'updated': updated,
        'merchant_fee_total': merchant_fee_total
    }

def main():
    """主函数"""
    print("=" * 80)
    print("Infinite GZ 交易自动分类系统")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 获取所有账单
    statements = get_all_statements()
    print(f"✅ 找到 {len(statements)} 份已确认账单")
    print()
    
    # 分类统计
    total_stats = {
        "Owner's Expenses": 0,
        "GZ's Expenses": 0,
        "Owner's Payment": 0,
        "GZ's Payment": 0
    }
    
    total_transactions = 0
    total_updated = 0
    total_merchant_fees = 0.0
    
    # 详细报告数据
    detailed_report = []
    
    # 逐个处理账单
    for idx, stmt in enumerate(statements, 1):
        print(f"[{idx}/{len(statements)}] 处理账单:")
        print(f"  客户: {stmt['customer_name']}")
        print(f"  银行: {stmt['bank_name']} (****{stmt['card_number_last4']})")
        print(f"  日期: {stmt['statement_date']}")
        
        try:
            # 分类交易
            result = classify_transactions(stmt['id'], stmt['customer_name'])
            
            print(f"  交易数: {result['total']}")
            print(f"  分类成功: {result['classified']}")
            print(f"  数据库更新: {result['updated']}")
            print(f"  商家手续费: RM {result.get('merchant_fee_total', 0):.2f}")
            print(f"  分类汇总:")
            for category, count in result['summary'].items():
                print(f"    - {category}: {count}")
                total_stats[category] += count
            
            total_transactions += result['total']
            total_updated += result['updated']
            total_merchant_fees += result.get('merchant_fee_total', 0)
            
            # 保存详细报告
            detailed_report.append({
                'statement_id': stmt['id'],
                'customer_name': stmt['customer_name'],
                'bank_name': stmt['bank_name'],
                'card_last4': stmt['card_number_last4'],
                'statement_date': stmt['statement_date'],
                'total_transactions': result['total'],
                'classified': result['classified'],
                'merchant_fee': result.get('merchant_fee_total', 0),
                'summary': result['summary']
            })
            
            print("  ✅ 成功")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # 最终报告
    print("=" * 80)
    print("最终分类报告")
    print("=" * 80)
    print(f"账单总数: {len(statements)}")
    print(f"交易总数: {total_transactions}")
    print(f"更新记录: {total_updated}")
    print(f"商家手续费总额: RM {total_merchant_fees:.2f}")
    print()
    print("分类汇总:")
    for category, count in total_stats.items():
        percentage = (count * 100.0 / total_transactions) if total_transactions > 0 else 0
        print(f"  {category}: {count} ({percentage:.1f}%)")
    print()
    
    # 检查负数未结余额（预付款）
    print("检查预付款情况:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cu.name, c.bank_name, c.card_number_last4,
               SUM(CASE WHEN t.debit_amount IS NOT NULL THEN t.debit_amount ELSE 0 END) as total_debit,
               SUM(CASE WHEN t.credit_amount IS NOT NULL THEN t.credit_amount ELSE 0 END) as total_credit
        FROM customers cu
        JOIN credit_cards c ON cu.id = c.customer_id
        JOIN statements s ON c.id = s.card_id
        JOIN transactions t ON s.id = t.statement_id
        GROUP BY cu.id, c.id
        HAVING (total_credit - total_debit) > 0
    """)
    prepayments = cursor.fetchall()
    if prepayments:
        for row in prepayments:
            prepay_amount = row[4] - row[3]
            print(f"  {row[0]} - {row[1]} (****{row[2]}): RM {prepay_amount:.2f} 预付款")
    else:
        print("  无预付款")
    conn.close()
    
    print()
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 生成JSON报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'statements_count': len(statements),
        'transactions_total': total_transactions,
        'records_updated': total_updated,
        'merchant_fees_total': total_merchant_fees,
        'classification_summary': total_stats,
        'detailed_statements': detailed_report
    }
    
    import json
    with open('classification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("✅ 详细报告已保存到 classification_report.json")

if __name__ == '__main__':
    main()
