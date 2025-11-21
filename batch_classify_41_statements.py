
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

def get_all_statements():
    """获取所有账单"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, s.statement_date, c.bank_name, c.card_number_last4, cu.name as customer_name
        FROM statements s
        JOIN credit_cards c ON s.card_id = c.id
        JOIN customers cu ON s.customer_id = cu.id
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
        suppliers_list=['7SL', 'Dinas Raub', 'SYC Hainan', 'Ai Smart Tech', 'HUAWEI', 'Pasar Raya', 'Puchong Herbs'],
        gz_bank_accounts=['INFINITE GZ SDN BHD', 'INFINITE GZ'],
        customer_name=customer_name
    )
    
    # 获取交易
    transactions = get_statement_transactions(statement_id)
    
    # 准备分类数据
    classify_data = []
    for txn in transactions:
        # 判断交易类型
        if txn['credit_amount'] > 0:
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
    
    # 更新数据库
    updated = classifier.update_database_classifications(result['results'])
    
    return {
        'total': result['total'],
        'classified': result['classified'],
        'summary': result['summary'],
        'updated': updated
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
    print(f"✅ 找到 {len(statements)} 份账单")
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
    
    # 逐个处理账单
    for idx, stmt in enumerate(statements, 1):
        print(f"[{idx}/{len(statements)}] 处理账单:")
        print(f"  客户: {stmt['customer_name']}")
        print(f"  银行: {stmt['bank_name']} ({stmt['card_number_last4']})")
        print(f"  日期: {stmt['statement_date']}")
        
        try:
            # 分类交易
            result = classify_transactions(stmt['id'], stmt['customer_name'])
            
            print(f"  交易数: {result['total']}")
            print(f"  分类成功: {result['classified']}")
            print(f"  数据库更新: {result['updated']}")
            print(f"  分类汇总:")
            for category, count in result['summary'].items():
                print(f"    - {category}: {count}")
                total_stats[category] += count
            
            total_transactions += result['total']
            total_updated += result['updated']
            
            print("  ✅ 成功")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        print()
    
    # 最终报告
    print("=" * 80)
    print("最终分类报告")
    print("=" * 80)
    print(f"账单总数: {len(statements)}")
    print(f"交易总数: {total_transactions}")
    print(f"更新记录: {total_updated}")
    print()
    print("分类汇总:")
    for category, count in total_stats.items():
        percentage = (count * 100.0 / total_transactions) if total_transactions > 0 else 0
        print(f"  {category}: {count} ({percentage:.1f}%)")
    print()
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 生成JSON报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'statements_count': len(statements),
        'transactions_total': total_transactions,
        'records_updated': total_updated,
        'classification_summary': total_stats
    }
    
    import json
    with open('classification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("✅ 报告已保存到 classification_report.json")

if __name__ == '__main__':
    main()
