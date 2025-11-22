"""
Chang Choon Chow 详细分类表格报告生成器
按银行、月份生成详细的消费、付款、转账、汇总表
"""
import sqlite3
from decimal import Decimal
from collections import defaultdict
from datetime import datetime
import os

# Supplier List（7个供应商）
SUPPLIER_LIST = ['7SL', 'DINAS', 'RAUB SYC HAINAN', 'AI SMART TECH', 'HUAWEI', 'PASAR RAYA', 'PUCHONG HERBS']

# GZ关键词（付款识别）
GZ_PAYMENT_KEYWORDS = ['GZ', 'KENG CHOW', 'INFINITE']

# 转账关键词
TRANSFER_KEYWORDS = ['TRANSFER', 'IBFT', 'IBG', 'DUITNOW', 'FPX']

def is_supplier(description):
    """检查是否为Supplier消费"""
    desc_upper = description.upper()
    for supplier in SUPPLIER_LIST:
        if supplier.upper() in desc_upper:
            return True, supplier
    return False, None

def is_gz_payment(description):
    """检查是否为GZ付款"""
    desc_upper = description.upper()
    for keyword in GZ_PAYMENT_KEYWORDS:
        if keyword in desc_upper:
            return True
    return False

def classify_transaction(description, amount):
    """
    分类交易
    返回: (type, subtype, details)
    """
    desc_upper = description.upper()
    
    # 1. 检查是否为付款
    if 'PAYMENT' in desc_upper or 'THANK YOU' in desc_upper or amount < 0:
        if is_gz_payment(description):
            return 'GZ_PAYMENT', 'DIRECT', {'source': 'GZ账户直接付款'}
        else:
            return 'OWNER_PAYMENT', None, {'source': 'Owner账户付款'}
    
    # 2. 检查是否为转账
    if any(kw in desc_upper for kw in TRANSFER_KEYWORDS):
        if 'KENG CHOW' in desc_upper:
            return 'TRANSFER', 'TO_COMPANY', {'purpose': 'Card Due Assist'}
        else:
            return 'TRANSFER', 'TO_PERSONAL', {'purpose': 'Card Due Assist'}
    
    # 3. 检查是否为Supplier消费
    is_sup, supplier_name = is_supplier(description)
    if is_sup:
        fee = amount * Decimal('0.01')  # 1% Fee
        return 'GZ_EXPENSE', 'SUPPLIER', {'supplier': supplier_name, 'fee': fee}
    
    # 4. 其他消费归为Owner
    return 'OWNER_EXPENSE', None, {}

def generate_detailed_report():
    """生成详细报告"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查询所有Chang Choon Chow的交易
    cursor.execute("""
        SELECT 
            t.transaction_date,
            t.description,
            t.amount,
            t.category,
            m.bank_name,
            m.statement_month,
            m.id as monthly_statement_id
        FROM transactions t
        JOIN monthly_statements m ON t.monthly_statement_id = m.id
        WHERE m.customer_id = 10
        ORDER BY m.statement_month, m.bank_name, t.transaction_date
    """)
    
    transactions = cursor.fetchall()
    
    # 按银行和月份分组
    grouped = defaultdict(lambda: defaultdict(list))
    
    for txn in transactions:
        bank = txn['bank_name']
        month = txn['statement_month']
        grouped[bank][month].append(txn)
    
    # 生成报告
    report_dir = 'reports/CCC_Detailed_Reports'
    os.makedirs(report_dir, exist_ok=True)
    
    # 生成总报告文件
    total_report = []
    total_report.append("=" * 120)
    total_report.append("Chang Choon Chow 详细分类表格报告")
    total_report.append("=" * 120)
    total_report.append(f"客户代码: Be_rich_CCC")
    total_report.append(f"客户姓名: Chang Choon Chow")
    total_report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    total_report.append(f"交易总笔数: {len(transactions)}笔")
    total_report.append("=" * 120)
    total_report.append("")
    
    # 汇总统计
    grand_total = {
        'owner_expenses': Decimal('0'),
        'gz_expenses': Decimal('0'),
        'owner_payments': Decimal('0'),
        'gz_payments': Decimal('0'),
        'transfers': Decimal('0'),
        'fees': Decimal('0')
    }
    
    # 按银行生成报告
    banks = sorted(grouped.keys())
    
    for bank in banks:
        total_report.append("")
        total_report.append("=" * 120)
        total_report.append(f"🏦 银行: {bank}")
        total_report.append("=" * 120)
        
        months = sorted(grouped[bank].keys())
        
        for month in months:
            txns = grouped[bank][month]
            
            total_report.append("")
            total_report.append(f"📅 月份: {month}")
            total_report.append("-" * 120)
            
            # 分类交易
            owner_expenses = []
            gz_expenses = []
            owner_payments = []
            gz_payments = []
            transfers = []
            
            month_stats = {
                'owner_expenses': Decimal('0'),
                'gz_expenses': Decimal('0'),
                'owner_payments': Decimal('0'),
                'gz_payments': Decimal('0'),
                'transfers': Decimal('0'),
                'total_fees': Decimal('0')
            }
            
            for txn in txns:
                amount = abs(Decimal(str(txn['amount'])))
                txn_type, subtype, details = classify_transaction(txn['description'], amount)
                
                txn_data = {
                    'date': txn['transaction_date'],
                    'description': txn['description'],
                    'amount': amount
                }
                
                if txn_type == 'OWNER_EXPENSE':
                    owner_expenses.append(txn_data)
                    month_stats['owner_expenses'] += amount
                    
                elif txn_type == 'GZ_EXPENSE':
                    txn_data['supplier'] = details.get('supplier', 'Unknown')
                    txn_data['fee'] = details.get('fee', Decimal('0'))
                    gz_expenses.append(txn_data)
                    month_stats['gz_expenses'] += amount
                    month_stats['total_fees'] += txn_data['fee']
                    
                elif txn_type == 'OWNER_PAYMENT':
                    owner_payments.append(txn_data)
                    month_stats['owner_payments'] += amount
                    
                elif txn_type == 'GZ_PAYMENT':
                    txn_data['payment_type'] = subtype
                    gz_payments.append(txn_data)
                    month_stats['gz_payments'] += amount
                    
                elif txn_type == 'TRANSFER':
                    txn_data['transfer_type'] = subtype
                    txn_data['purpose'] = details.get('purpose', 'Unknown')
                    transfers.append(txn_data)
                    month_stats['transfers'] += amount
            
            # 生成消费记录表
            if owner_expenses or gz_expenses:
                total_report.append("")
                total_report.append("📋 消费记录表:")
                total_report.append(f"{'日期':<12} {'描述/商户':<45} {'金额 (RM)':<12} {'类型':<25} {'Supplier':<20} {'1% Fee':<10}")
                total_report.append("-" * 120)
                
                for exp in owner_expenses:
                    total_report.append(f"{exp['date']:<12} {exp['description']:<45} {exp['amount']:>11.2f} {'Owner Expenses':<25} {'-':<20} {'-':<10}")
                
                for exp in gz_expenses:
                    fee_str = f"RM {exp['fee']:.2f}"
                    total_report.append(f"{exp['date']:<12} {exp['description']:<45} {exp['amount']:>11.2f} {'GZ Expenses - Supplier':<25} {exp['supplier']:<20} {fee_str:<10}")
            
            # 生成付款记录表
            if owner_payments or gz_payments:
                total_report.append("")
                total_report.append("💳 付款记录表:")
                total_report.append(f"{'日期':<12} {'描述':<45} {'金额 (RM)':<12} {'付款方式':<30}")
                total_report.append("-" * 120)
                
                for pay in owner_payments:
                    total_report.append(f"{pay['date']:<12} {pay['description']:<45} {pay['amount']:>11.2f} {'Owner Payment':<30}")
                
                for pay in gz_payments:
                    payment_type = 'GZ Direct Payment' if pay['payment_type'] == 'DIRECT' else 'GZ Indirect Payment'
                    total_report.append(f"{pay['date']:<12} {pay['description']:<45} {pay['amount']:>11.2f} {payment_type:<30}")
            
            # 生成转账记录表
            if transfers:
                total_report.append("")
                total_report.append("💰 转账记录表:")
                total_report.append(f"{'日期':<12} {'描述':<45} {'金额 (RM)':<12} {'转账类型':<30} {'用途':<20}")
                total_report.append("-" * 120)
                
                for trf in transfers:
                    transfer_type = '转至公司KENG CHOW' if trf['transfer_type'] == 'TO_COMPANY' else '转至客户私人账户'
                    total_report.append(f"{trf['date']:<12} {trf['description']:<45} {trf['amount']:>11.2f} {transfer_type:<30} {trf['purpose']:<20}")
            
            # 生成每月汇总表
            total_report.append("")
            total_report.append("📊 每月汇总表:")
            total_report.append("-" * 120)
            total_report.append(f"本月Owner消费总额:        RM {month_stats['owner_expenses']:>12,.2f}")
            total_report.append(f"本月GZ Supplier消费总额:  RM {month_stats['gz_expenses']:>12,.2f}")
            total_report.append(f"本月Supplier 1% Fee:      RM {month_stats['total_fees']:>12,.2f}")
            total_report.append(f"本月Owner付款总额:        RM {month_stats['owner_payments']:>12,.2f}")
            total_report.append(f"本月GZ付款总额:           RM {month_stats['gz_payments']:>12,.2f}")
            total_report.append(f"本月转账总额:             RM {month_stats['transfers']:>12,.2f}")
            total_report.append("-" * 120)
            
            # 累计到总统计
            for key in grand_total:
                grand_total[key] += month_stats.get(key, Decimal('0'))
    
    # 生成最终汇总
    total_report.append("")
    total_report.append("=" * 120)
    total_report.append("🎯 最终汇总统计")
    total_report.append("=" * 120)
    total_report.append(f"Owner消费总额:        RM {grand_total['owner_expenses']:>12,.2f}")
    total_report.append(f"GZ Supplier消费总额:  RM {grand_total['gz_expenses']:>12,.2f}")
    total_report.append(f"Supplier 1% Fee总额:  RM {grand_total['fees']:>12,.2f}")
    total_report.append(f"Owner付款总额:        RM {grand_total['owner_payments']:>12,.2f}")
    total_report.append(f"GZ付款总额:           RM {grand_total['gz_payments']:>12,.2f}")
    total_report.append(f"转账总额:             RM {grand_total['transfers']:>12,.2f}")
    total_report.append("=" * 120)
    
    # 保存报告
    report_file = f'{report_dir}/CCC_Complete_Detailed_Report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(total_report))
    
    print(f"✅ 详细报告已生成: {report_file}")
    print(f"✅ 共处理 {len(transactions)} 笔交易")
    print(f"✅ 覆盖 {len(banks)} 家银行")
    
    # 同时输出到控制台（前500行）
    print("\n" + "=" * 120)
    print("报告预览（前500行）:")
    print("=" * 120)
    for line in total_report[:500]:
        print(line)
    
    if len(total_report) > 500:
        print(f"\n... 报告太长，省略 {len(total_report) - 500} 行 ...")
        print(f"\n完整报告请查看: {report_file}")
    
    conn.close()
    return report_file

if __name__ == '__main__':
    generate_detailed_report()
