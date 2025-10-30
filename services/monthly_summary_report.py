"""
月度汇总报告服务
Monthly Summary Report Service

功能：
1. 按月份汇总同一客户所有信用卡的Supplier消费
2. 追踪该月为客户支付的所有款项
3. 生成月度对账报告，避免误会
"""

import sqlite3
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict

class MonthlySummaryReport:
    """月度汇总报告生成器"""
    
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
    
    def get_customer_monthly_summary(self, customer_id: int, year: int, month: int) -> Dict:
        """
        获取客户指定月份的汇总报告
        
        参数:
            customer_id: 客户ID
            year: 年份（如2025）
            month: 月份（1-12）
        
        返回:
            {
                'period': '2025-01',
                'customer_name': 'YEO CHEE WANG',
                'cards': [...],  # 该月所有有交易的信用卡
                'total_supplier_spending': 12500.00,  # 总Supplier消费
                'total_supplier_fee': 125.00,  # 总手续费(1%)
                'total_payments': 10000.00,  # 总付款额
                'net_balance': 2625.00,  # 净余额（消费+费用-付款）
                'card_details': [...],  # 每张卡的详细信息
                'payment_details': [...]  # 付款详情
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. 获取客户信息
        cursor.execute("SELECT name, customer_code FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return None
        
        # 2. 构建月份起始日期（用于匹配）
        month_start = f"{year}-{month:02d}-01"
        period_str = f"{year}-{month:02d}"
        
        # 3. 获取该月所有信用卡的INFINITE账本数据
        cursor.execute('''
            SELECT 
                iml.card_id,
                cc.bank_name,
                cc.card_number,
                cc.card_type,
                iml.month_start,
                iml.statement_id,
                iml.infinite_spend,
                iml.supplier_fee,
                iml.infinite_payments,
                iml.rolling_balance,
                iml.transfer_count,
                s.statement_date,
                s.statement_period
            FROM infinite_monthly_ledger iml
            JOIN credit_cards cc ON iml.card_id = cc.id
            LEFT JOIN statements s ON iml.statement_id = s.id
            WHERE iml.customer_id = ?
              AND substr(iml.month_start, 1, 7) = ?
            ORDER BY cc.bank_name, s.statement_date
        ''', (customer_id, period_str))
        
        card_ledgers = cursor.fetchall()
        
        # 4. 汇总数据
        total_supplier_spending = 0
        total_supplier_fee = 0
        total_infinite_payments = 0
        card_details = []
        
        for ledger in card_ledgers:
            card_info = {
                'card_id': ledger['card_id'],
                'bank_name': ledger['bank_name'],
                'card_number': ledger['card_number'],
                'card_type': ledger['card_type'],
                'statement_date': ledger['statement_date'],
                'statement_period': ledger['statement_period'],
                'infinite_spend': ledger['infinite_spend'],
                'supplier_fee': ledger['supplier_fee'],
                'infinite_payments': ledger['infinite_payments'],
                'rolling_balance': ledger['rolling_balance'],
                'transfer_count': ledger['transfer_count']
            }
            card_details.append(card_info)
            
            total_supplier_spending += ledger['infinite_spend']
            total_supplier_fee += ledger['supplier_fee']
            total_infinite_payments += ledger['infinite_payments']
        
        # 5. 获取该月的INFINITE转账详情
        cursor.execute('''
            SELECT 
                it.card_id,
                cc.bank_name,
                cc.card_number,
                it.transfer_date,
                it.payer_name,
                it.payee_name,
                it.amount,
                it.description
            FROM infinite_transfers it
            JOIN credit_cards cc ON it.card_id = cc.id
            WHERE it.customer_id = ?
              AND substr(it.month_start, 1, 7) = ?
            ORDER BY it.transfer_date
        ''', (customer_id, period_str))
        
        payment_details = []
        for transfer in cursor.fetchall():
            payment_details.append({
                'card_id': transfer['card_id'],
                'bank_name': transfer['bank_name'],
                'card_number': transfer['card_number'],
                'transfer_date': transfer['transfer_date'],
                'payer_name': transfer['payer_name'],
                'payee_name': transfer['payee_name'],
                'amount': transfer['amount'],
                'description': transfer['description']
            })
        
        # 6. 计算净余额
        total_spending_with_fee = total_supplier_spending + total_supplier_fee
        net_balance = total_spending_with_fee - total_infinite_payments
        
        conn.close()
        
        # 7. 返回汇总报告
        return {
            'period': period_str,
            'year': year,
            'month': month,
            'customer_id': customer_id,
            'customer_name': customer['name'],
            'customer_code': customer['customer_code'],
            'total_cards': len(card_details),
            'total_supplier_spending': total_supplier_spending,
            'total_supplier_fee': total_supplier_fee,
            'total_spending_with_fee': total_spending_with_fee,
            'total_payments': total_infinite_payments,
            'net_balance': net_balance,
            'card_details': card_details,
            'payment_details': payment_details
        }
    
    def get_customer_yearly_summary(self, customer_id: int, year: int) -> List[Dict]:
        """获取客户全年的月度汇总（1-12月）"""
        yearly_data = []
        
        for month in range(1, 13):
            summary = self.get_customer_monthly_summary(customer_id, year, month)
            if summary and summary['total_cards'] > 0:
                yearly_data.append(summary)
        
        return yearly_data
    
    def get_all_customers_monthly_summary(self, year: int, month: int) -> List[Dict]:
        """获取所有客户指定月份的汇总"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有有INFINITE账本记录的客户
        period_str = f"{year}-{month:02d}"
        cursor.execute('''
            SELECT DISTINCT customer_id
            FROM infinite_monthly_ledger
            WHERE substr(month_start, 1, 7) = ?
        ''', (period_str,))
        
        customer_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # 获取每个客户的月度汇总
        all_summaries = []
        for customer_id in customer_ids:
            summary = self.get_customer_monthly_summary(customer_id, year, month)
            if summary:
                all_summaries.append(summary)
        
        return all_summaries
    
    def generate_text_report(self, summary: Dict) -> str:
        """生成文本格式的月度汇总报告"""
        if not summary:
            return "无数据"
        
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append(f"月度汇总报告 - {summary['period']}")
        report_lines.append("=" * 100)
        report_lines.append(f"客户: {summary['customer_name']} ({summary['customer_code']})")
        report_lines.append(f"月份: {summary['year']}年{summary['month']}月")
        report_lines.append(f"信用卡数量: {summary['total_cards']}张")
        report_lines.append("=" * 100)
        
        # 信用卡详情
        report_lines.append("\n📊 信用卡详情：")
        report_lines.append("-" * 100)
        
        for i, card in enumerate(summary['card_details'], 1):
            report_lines.append(f"\n第{i}张卡：{card['bank_name']} - {card['card_number']}")
            report_lines.append(f"  账单日期: {card['statement_date']}")
            report_lines.append(f"  Supplier消费: RM {card['infinite_spend']:,.2f}")
            report_lines.append(f"  手续费(1%):  RM {card['supplier_fee']:,.2f}")
            report_lines.append(f"  付款金额:    RM {card['infinite_payments']:,.2f}")
            report_lines.append(f"  滚动余额:    RM {card['rolling_balance']:,.2f}")
            report_lines.append(f"  转账次数:    {card['transfer_count']}次")
        
        # 付款详情
        if summary['payment_details']:
            report_lines.append("\n\n💰 付款详情：")
            report_lines.append("-" * 100)
            
            for i, payment in enumerate(summary['payment_details'], 1):
                report_lines.append(f"\n第{i}笔付款：")
                report_lines.append(f"  日期: {payment['transfer_date']}")
                report_lines.append(f"  付款人: {payment['payer_name']}")
                report_lines.append(f"  收款人: {payment['payee_name']}")
                report_lines.append(f"  金额: RM {payment['amount']:,.2f}")
                report_lines.append(f"  信用卡: {payment['bank_name']} - {payment['card_number']}")
                if payment['description']:
                    report_lines.append(f"  说明: {payment['description']}")
        
        # 月度汇总
        report_lines.append("\n\n" + "=" * 100)
        report_lines.append("📈 月度汇总")
        report_lines.append("=" * 100)
        report_lines.append(f"Supplier消费总额:    RM {summary['total_supplier_spending']:,.2f}")
        report_lines.append(f"手续费总额(1%):      RM {summary['total_supplier_fee']:,.2f}")
        report_lines.append(f"消费合计(含费用):    RM {summary['total_spending_with_fee']:,.2f}")
        report_lines.append(f"付款总额:            RM {summary['total_payments']:,.2f}")
        report_lines.append("-" * 100)
        
        if summary['net_balance'] > 0:
            report_lines.append(f"应收余额:            RM {summary['net_balance']:,.2f}  ⚠️  客户需补款")
        elif summary['net_balance'] < 0:
            report_lines.append(f"应付余额:            RM {abs(summary['net_balance']):,.2f}  💰 我们需退款")
        else:
            report_lines.append(f"余额:                RM 0.00  ✅ 已结清")
        
        report_lines.append("=" * 100)
        
        return "\n".join(report_lines)


# 测试代码
if __name__ == '__main__':
    reporter = MonthlySummaryReport()
    
    # 示例：获取YEO CHEE WANG 2025年1月的汇总
    print("测试月度汇总报告...\n")
    
    # 首先获取YEO CHEE WANG的customer_id
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM customers WHERE name = 'YEO CHEE WANG'")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        customer_id = result[0]
        print(f"客户ID: {customer_id}\n")
        
        # 获取2025年1月的汇总
        summary = reporter.get_customer_monthly_summary(customer_id, 2025, 1)
        
        if summary:
            print(reporter.generate_text_report(summary))
        else:
            print("该月份暂无数据")
    else:
        print("客户不存在")
