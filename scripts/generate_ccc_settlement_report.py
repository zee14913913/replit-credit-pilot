#!/usr/bin/env python3
"""
INFINITE GZ - Chang Choon Chow结算报告生成器
==========================================
生成完整的Owner/GZ分离结算报告，包含：
- 月度汇总表
- Owner消费/付款明细
- GZ消费/付款明细
- Supplier明细（7家公司）
- 1% Fee计算
- 最终GZ OS Balance
"""

import sys
sys.path.insert(0, '.')

from db.database import get_db
from decimal import Decimal
import json
from datetime import datetime

class CCCSettlementReportGenerator:
    """Chang Choon Chow结算报告生成器"""
    
    def __init__(self):
        self.customer_name = 'CHANG CHOON CHOW'
        self.supplier_list = ['7SL', 'DINAS', 'RAUB SYC HAINAN', 'AI SMART TECH', 
                             'HUAWEI', 'PASAR RAYA', 'PUCHONG HERBS']
    
    def generate_report(self):
        """生成完整结算报告"""
        
        print("=" * 100)
        print("🏦 INFINITE GZ - Chang Choon Chow 结算报告生成器")
        print("=" * 100)
        
        # 1. 获取月度汇总
        monthly_summary = self._get_monthly_summary()
        
        if not monthly_summary:
            print("\n❌ 未找到数据！请先运行 process_uploaded_json.py")
            return
        
        # 2. 获取交易明细
        transactions = self._get_all_transactions()
        
        # 3. 分类统计
        stats = self._calculate_statistics(monthly_summary, transactions)
        
        # 4. 生成报告
        self._print_summary_report(stats)
        self._print_monthly_breakdown(monthly_summary)
        self._print_supplier_breakdown(transactions)
        
        # 5. 保存JSON报告
        self._save_json_report(stats, monthly_summary, transactions)
        
        print("\n" + "=" * 100)
        print("✅ 报告生成完成！")
        print("=" * 100)
    
    def _get_monthly_summary(self):
        """获取月度汇总数据"""
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    bank_name,
                    statement_month,
                    previous_balance_total,
                    closing_balance_total,
                    owner_expenses,
                    owner_payments,
                    gz_expenses,
                    gz_payments,
                    transaction_count
                FROM monthly_statements
                WHERE customer_id = (
                    SELECT id FROM customers WHERE name LIKE ? LIMIT 1
                )
                ORDER BY statement_month, bank_name
            """, (f'%{self.customer_name}%',))
            
            rows = cursor.fetchall()
            
            return [{
                'id': row[0],
                'bank_name': row[1],
                'statement_month': row[2],
                'previous_balance': row[3],
                'closing_balance': row[4],
                'owner_expenses': row[5],
                'owner_payments': row[6],
                'gz_expenses': row[7],
                'gz_payments': row[8],
                'transaction_count': row[9]
            } for row in rows]
    
    def _get_all_transactions(self):
        """获取所有交易明细"""
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    t.id,
                    t.transaction_date,
                    t.description,
                    t.amount,
                    t.category,
                    ms.bank_name,
                    ms.statement_month
                FROM transactions t
                JOIN monthly_statements ms ON t.monthly_statement_id = ms.id
                WHERE ms.customer_id = (
                    SELECT id FROM customers WHERE name LIKE ? LIMIT 1
                )
                ORDER BY t.transaction_date
            """, (f'%{self.customer_name}%',))
            
            rows = cursor.fetchall()
            
            return [{
                'id': row[0],
                'date': row[1],
                'description': row[2],
                'amount': row[3],
                'category': row[4],
                'bank': row[5],
                'month': row[6]
            } for row in rows]
    
    def _calculate_statistics(self, monthly_summary, transactions):
        """计算统计数据"""
        
        total_owner_expenses = Decimal('0')
        total_owner_payments = Decimal('0')
        total_gz_expenses = Decimal('0')
        total_gz_payments = Decimal('0')
        
        for record in monthly_summary:
            total_owner_expenses += Decimal(str(record['owner_expenses'] or 0))
            total_owner_payments += Decimal(str(record['owner_payments'] or 0))
            total_gz_expenses += Decimal(str(record['gz_expenses'] or 0))
            total_gz_payments += Decimal(str(record['gz_payments'] or 0))
        
        # 计算Supplier费用
        supplier_fees = Decimal('0')
        supplier_transactions = []
        
        for txn in transactions:
            desc_upper = txn['description'].upper()
            for supplier in self.supplier_list:
                if supplier.upper() in desc_upper:
                    amount = Decimal(str(txn['amount']))
                    fee = amount * Decimal('0.01')
                    supplier_fees += fee
                    supplier_transactions.append({
                        **txn,
                        'supplier': supplier,
                        'fee': float(fee)
                    })
                    break
        
        # 计算GZ OS Balance
        gz_os_balance = total_gz_expenses - total_gz_payments + supplier_fees
        
        return {
            'total_owner_expenses': float(total_owner_expenses),
            'total_owner_payments': float(total_owner_payments),
            'total_gz_expenses': float(total_gz_expenses),
            'total_gz_payments': float(total_gz_payments),
            'supplier_fees': float(supplier_fees),
            'gz_os_balance': float(gz_os_balance),
            'total_months': len(monthly_summary),
            'total_transactions': len(transactions),
            'supplier_transactions': supplier_transactions
        }
    
    def _print_summary_report(self, stats):
        """打印汇总报告"""
        
        print("\n" + "=" * 100)
        print("📊 CHANG CHOON CHOW 结算汇总报告")
        print("=" * 100)
        print(f"报告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"处理月份数: {stats['total_months']} 个月")
        print(f"总交易笔数: {stats['total_transactions']} 笔")
        print("=" * 100)
        
        print("\n【Owner账户】")
        print(f"  消费合计: RM {stats['total_owner_expenses']:,.2f}")
        print(f"  付款合计: RM {stats['total_owner_payments']:,.2f}")
        print(f"  净额: RM {(stats['total_owner_expenses'] - stats['total_owner_payments']):,.2f}")
        
        print("\n【GZ账户】")
        print(f"  消费合计: RM {stats['total_gz_expenses']:,.2f}")
        print(f"  付款合计: RM {stats['total_gz_payments']:,.2f}")
        print(f"  Supplier Fees (1%): RM {stats['supplier_fees']:,.2f}")
        print(f"  Supplier交易数: {len(stats['supplier_transactions'])} 笔")
        
        print("\n" + "=" * 100)
        print(f"【GZ Outstanding Balance】: RM {stats['gz_os_balance']:,.2f}")
        print("=" * 100)
    
    def _print_monthly_breakdown(self, monthly_summary):
        """打印月度明细"""
        
        print("\n" + "=" * 100)
        print("📅 月度明细表")
        print("=" * 100)
        print(f"{'月份':<12} {'银行':<20} {'Owner消费':<15} {'Owner付款':<15} "
              f"{'GZ消费':<15} {'GZ付款':<15} {'交易数':<10}")
        print("-" * 100)
        
        for record in monthly_summary:
            print(f"{record['statement_month']:<12} "
                  f"{record['bank_name']:<20} "
                  f"RM {record['owner_expenses']:>10,.2f}  "
                  f"RM {record['owner_payments']:>10,.2f}  "
                  f"RM {record['gz_expenses']:>10,.2f}  "
                  f"RM {record['gz_payments']:>10,.2f}  "
                  f"{record['transaction_count']:>8}")
    
    def _print_supplier_breakdown(self, transactions):
        """打印Supplier明细"""
        
        print("\n" + "=" * 100)
        print("🏢 Supplier明细表（7家公司）")
        print("=" * 100)
        
        for supplier in self.supplier_list:
            supplier_txns = [t for t in transactions 
                           if supplier.upper() in t['description'].upper()]
            
            if supplier_txns:
                total_amount = sum(Decimal(str(t['amount'])) for t in supplier_txns)
                total_fee = total_amount * Decimal('0.01')
                
                print(f"\n【{supplier}】")
                print(f"  交易笔数: {len(supplier_txns)} 笔")
                print(f"  消费总额: RM {total_amount:,.2f}")
                print(f"  1% Fee: RM {total_fee:,.2f}")
    
    def _save_json_report(self, stats, monthly_summary, transactions):
        """保存JSON格式报告"""
        
        report = {
            'report_date': datetime.now().isoformat(),
            'customer_name': self.customer_name,
            'summary': stats,
            'monthly_breakdown': monthly_summary,
            'supplier_breakdown': self._get_supplier_breakdown(transactions)
        }
        
        output_file = 'ccc_settlement_report.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 JSON报告已保存: {output_file}")


def main():
    generator = CCCSettlementReportGenerator()
    generator.generate_report()


if __name__ == '__main__':
    main()
