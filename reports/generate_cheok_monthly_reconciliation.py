#!/usr/bin/env python3
"""
CHEOK JUN YOON 月度对账报告生成器

逻辑说明：
- 5月报告 = 5月信用卡账单(statement_date=2025-05) + 4月储蓄账户转账
- 6月报告 = 6月信用卡账单(statement_date=2025-06) + 5月储蓄账户转账
- 依此类推...

对账账户：
1. Infinite GZ (Hong Leong *4645)
2. AI Smart Tech - Alliance *5540
3. AI Smart Tech - Public Bank *9009  
4. Tan Zee Liang (GX *8388)
5. YEO CHEE WANG (OCBC *1484, GX *8373, UOB *1842)
6. TEO YOK CHU & YEO CHEE WANG (OCBC *1489)

分类系统：
- OWNER消费 (owner_expenses)
- OWNER付款 (owner_payments)
- INFINITE消费 (gz_expenses)
- INFINITE付款 (gz_payments)
- OWNER余额 (owner_balance)
- INFINITE余额 (gz_balance)
"""

import sqlite3
from datetime import datetime
from collections import defaultdict


def get_db_connection():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_supplier_merchants():
    """获取供应商关键词列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT supplier_name FROM supplier_config WHERE is_active = 1")
    suppliers = [row[0].lower() for row in cursor.fetchall()]
    
    conn.close()
    return suppliers


def classify_transaction(description, amount, suppliers):
    """
    分类交易为6大类
    返回: (category, is_supplier, supplier_name)
    """
    desc_lower = description.lower() if description else ""
    
    # 检查是否为供应商消费
    matched_supplier = None
    for supplier in suppliers:
        if supplier in desc_lower:
            matched_supplier = supplier
            break
    
    # 退款/付款（负数金额）
    if amount < 0:
        if matched_supplier:
            return ('gz_payments', True, matched_supplier)
        else:
            return ('owner_payments', False, None)
    
    # 消费（正数金额）
    else:
        if matched_supplier:
            return ('gz_expenses', True, matched_supplier)
        else:
            return ('owner_expenses', False, None)


def get_credit_card_statements(customer_id, month_str):
    """
    获取指定月份的所有信用卡账单
    month_str格式: '2025-05'
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id,
            s.statement_date,
            s.previous_balance,
            s.statement_total,
            cc.bank_name,
            cc.card_number_last4
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.customer_id = ?
          AND strftime('%Y-%m', s.statement_date) = ?
        ORDER BY s.statement_date, cc.bank_name
    """, (customer_id, month_str))
    
    statements = cursor.fetchall()
    conn.close()
    
    return statements


def get_statement_transactions(statement_id):
    """获取账单的所有交易"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            transaction_date,
            description,
            amount
        FROM transactions
        WHERE statement_id = ?
        ORDER BY transaction_date, id
    """, (statement_id,))
    
    transactions = cursor.fetchall()
    conn.close()
    
    return transactions


def get_savings_transfers(month_str):
    """
    获取指定月份的储蓄账户转账记录
    仅包括对CHEOK JUN YOON的转账
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 相关账户ID
    account_ids = [19, 21, 22, 14, 10, 13, 16, 18]  # Infinite GZ, AI Smart, TZL, YCW账户
    
    cursor.execute(f"""
        SELECT 
            st.transaction_date,
            st.description,
            st.amount,
            sa.account_holder_name,
            sa.bank_name,
            sa.account_number_last4
        FROM savings_transactions st
        JOIN savings_statements ss ON st.savings_statement_id = ss.id
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        WHERE sa.id IN ({','.join('?' * len(account_ids))})
          AND strftime('%Y-%m', st.transaction_date) = ?
          AND st.description LIKE '%CHEOK%'
        ORDER BY st.transaction_date
    """, account_ids + [month_str])
    
    transfers = cursor.fetchall()
    conn.close()
    
    return transfers


def generate_monthly_report(customer_id, month_str):
    """
    生成月度对账报告
    
    参数:
        customer_id: 客户ID
        month_str: 账单月份 (例如 '2025-05')
    
    返回:
        report_data: 报告数据字典
    """
    # 获取供应商列表
    suppliers = get_supplier_merchants()
    
    # 获取当月信用卡账单
    statements = get_credit_card_statements(customer_id, month_str)
    
    # 计算上个月（转账月份）
    year, month = month_str.split('-')
    prev_month = int(month) - 1
    if prev_month == 0:
        prev_month = 12
        year = str(int(year) - 1)
    transfer_month = f"{year}-{str(prev_month).zfill(2)}"
    
    # 获取上个月的储蓄账户转账
    transfers = get_savings_transfers(transfer_month)
    
    # 统计数据
    report = {
        'month': month_str,
        'transfer_month': transfer_month,
        'customer': 'CHEOK JUN YOON',
        'statements': [],
        'summary': {
            'owner_expenses': 0,
            'owner_payments': 0,
            'gz_expenses': 0,
            'gz_payments': 0,
            'owner_balance': 0,
            'gz_balance': 0,
            'total_closing_balance': 0,
        },
        'supplier_details': defaultdict(lambda: {'expenses': 0, 'payments': 0, 'net': 0}),
        'transfers': [],
        'total_transfers': 0,
        'net_position': 0,
    }
    
    # 处理每张账单
    for stmt in statements:
        stmt_data = {
            'statement_id': stmt['id'],
            'statement_date': stmt['statement_date'],
            'bank': stmt['bank_name'],
            'card_last4': stmt['card_number_last4'],
            'previous_balance': stmt['previous_balance'] or 0,
            'closing_balance': stmt['statement_total'] or 0,
            'categories': {
                'owner_expenses': 0,
                'owner_payments': 0,
                'gz_expenses': 0,
                'gz_payments': 0,
            },
            'transactions': []
        }
        
        # 处理交易
        transactions = get_statement_transactions(stmt['id'])
        
        for txn in transactions:
            category, is_supplier, supplier_name = classify_transaction(
                txn['description'], 
                txn['amount'], 
                suppliers
            )
            
            txn_data = {
                'date': txn['transaction_date'],
                'description': txn['description'],
                'amount': txn['amount'],
                'category': category,
                'is_supplier': is_supplier,
                'supplier': supplier_name
            }
            
            stmt_data['transactions'].append(txn_data)
            stmt_data['categories'][category] += abs(txn['amount'])
            
            # 更新供应商明细
            if is_supplier and supplier_name:
                if txn['amount'] > 0:
                    report['supplier_details'][supplier_name]['expenses'] += txn['amount']
                else:
                    report['supplier_details'][supplier_name]['payments'] += abs(txn['amount'])
        
        # 计算账单的OWNER和INFINITE余额
        owner_net = stmt_data['categories']['owner_expenses'] - stmt_data['categories']['owner_payments']
        gz_net = stmt_data['categories']['gz_expenses'] - stmt_data['categories']['gz_payments']
        
        stmt_data['owner_balance'] = owner_net
        stmt_data['gz_balance'] = gz_net
        
        # 汇总到总计
        report['summary']['owner_expenses'] += stmt_data['categories']['owner_expenses']
        report['summary']['owner_payments'] += stmt_data['categories']['owner_payments']
        report['summary']['gz_expenses'] += stmt_data['categories']['gz_expenses']
        report['summary']['gz_payments'] += stmt_data['categories']['gz_payments']
        report['summary']['owner_balance'] += owner_net
        report['summary']['gz_balance'] += gz_net
        report['summary']['total_closing_balance'] += stmt_data['closing_balance']
        
        report['statements'].append(stmt_data)
    
    # 处理储蓄账户转账
    for transfer in transfers:
        transfer_data = {
            'date': transfer['transaction_date'],
            'description': transfer['description'],
            'amount': abs(transfer['amount']),  # 转账金额（取绝对值）
            'account': f"{transfer['account_holder_name']} - {transfer['bank_name']} *{transfer['account_number_last4']}"
        }
        
        report['transfers'].append(transfer_data)
        report['total_transfers'] += abs(transfer['amount'])
    
    # 计算供应商净额
    for supplier, data in report['supplier_details'].items():
        data['net'] = data['expenses'] - data['payments']
    
    # 计算净头寸
    # 正数 = 我们多用了客户的卡，需要补款给客户
    # 负数 = 我们多付了款给客户，客户欠我们钱
    supplier_net_expense = sum(data['net'] for data in report['supplier_details'].values())
    report['net_position'] = supplier_net_expense - report['total_transfers']
    
    return report


def print_report(report):
    """打印月度报告"""
    print("=" * 100)
    print(f"{report['customer']} - {report['month']} 月度对账报告")
    print("=" * 100)
    print()
    
    print(f"账单月份: {report['month']}")
    print(f"转账月份: {report['transfer_month']}")
    print(f"账单数量: {len(report['statements'])} 张")
    print()
    
    # 账单明细
    print("【信用卡账单明细】")
    print("-" * 100)
    
    for stmt in report['statements']:
        print(f"\n{stmt['bank']} *{stmt['card_last4']} - {stmt['statement_date']}")
        print(f"  期初余额: RM {stmt['previous_balance']:>12,.2f}")
        print(f"  期末余额: RM {stmt['closing_balance']:>12,.2f}")
        print(f"  OWNER消费: RM {stmt['categories']['owner_expenses']:>12,.2f}")
        print(f"  OWNER付款: RM {stmt['categories']['owner_payments']:>12,.2f}")
        print(f"  GZ消费:    RM {stmt['categories']['gz_expenses']:>12,.2f}")
        print(f"  GZ付款:    RM {stmt['categories']['gz_payments']:>12,.2f}")
        print(f"  OWNER余额: RM {stmt['owner_balance']:>12,.2f}")
        print(f"  GZ余额:    RM {stmt['gz_balance']:>12,.2f}")
    
    print()
    print("【6大分类汇总】")
    print("-" * 100)
    print(f"OWNER消费:  RM {report['summary']['owner_expenses']:>15,.2f}")
    print(f"OWNER付款:  RM {report['summary']['owner_payments']:>15,.2f}")
    print(f"GZ消费:     RM {report['summary']['gz_expenses']:>15,.2f}")
    print(f"GZ付款:     RM {report['summary']['gz_payments']:>15,.2f}")
    print("-" * 100)
    print(f"OWNER余额:  RM {report['summary']['owner_balance']:>15,.2f}")
    print(f"GZ余额:     RM {report['summary']['gz_balance']:>15,.2f}")
    print(f"总期末余额: RM {report['summary']['total_closing_balance']:>15,.2f}")
    
    # 供应商明细
    if report['supplier_details']:
        print()
        print("【供应商消费明细】")
        print("-" * 100)
        
        for supplier, data in sorted(report['supplier_details'].items()):
            print(f"{supplier}:")
            print(f"  消费: RM {data['expenses']:>12,.2f}")
            print(f"  付款: RM {data['payments']:>12,.2f}")
            print(f"  净额: RM {data['net']:>12,.2f}")
    
    # 转账记录
    print()
    print("【储蓄账户转账记录】")
    print("-" * 100)
    
    if report['transfers']:
        for transfer in report['transfers']:
            print(f"{transfer['date']} RM {transfer['amount']:>12,.2f} - {transfer['account']}")
            print(f"  {transfer['description']}")
    else:
        print("  无转账记录")
    
    print("-" * 100)
    print(f"转账总额: RM {report['total_transfers']:>15,.2f}")
    
    # 对账结果
    print()
    print("【对账结果】")
    print("=" * 100)
    
    supplier_net = sum(data['net'] for data in report['supplier_details'].values())
    
    print(f"供应商净消费: RM {supplier_net:>15,.2f}  (我们用客户卡消费的净额)")
    print(f"转账付款总额: RM {report['total_transfers']:>15,.2f}  (我们付给客户的钱)")
    print("-" * 100)
    print(f"净头寸:       RM {report['net_position']:>15,.2f}")
    
    if report['net_position'] > 0:
        print(f"\n✅ 我们需要补款给客户: RM {report['net_position']:,.2f}")
    elif report['net_position'] < 0:
        print(f"\n✅ 客户多收了我们的钱: RM {abs(report['net_position']):,.2f}")
    else:
        print(f"\n✅ 账目平衡，无需补款")
    
    print("=" * 100)
    print()


def main():
    """主函数 - 生成5-10月报告"""
    customer_id = 6  # CHEOK JUN YOON
    
    months = ['2025-05', '2025-06', '2025-07', '2025-08', '2025-09', '2025-10']
    
    for month in months:
        report = generate_monthly_report(customer_id, month)
        print_report(report)
        print("\n\n")


if __name__ == '__main__':
    main()
