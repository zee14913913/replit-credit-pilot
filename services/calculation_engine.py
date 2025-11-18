"""
完整计算引擎 - Complete Calculation Engine
按照Ji-Suan文档实施Owners/GZ Expenses/Payments/Outstanding Balance计算公式
"""

import sqlite3
from typing import Dict, List, Optional


class CalculationEngine:
    """完整计算引擎 - 实施所有财务计算公式"""
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        
        # 7个供应商
        self.suppliers = ['HUAWEI', 'APPLE', 'XIAOMI', 'OPPO', 'VIVO', 'SAMSUNG', 'REALME']
        
        # 9间GZ银行
        self.gz_banks = [
            ('GX Bank', 'Tan Zee Liang'),  # 1. INFINITE GZ - Tan Zee Liang
            ('Maybank', 'Yeo Chee Wang'),  # 2. Yeo Chee Wang
            ('GX Bank', 'Yeo Chee Wang'),  # 3. Yeo Chee Wang
            ('UOB', 'Yeo Chee Wang'),      # 4. Yeo Chee Wang
            ('OCBC', 'Yeo Chee Wang'),     # 5. Yeo Chee Wang
            ('OCBC', 'Teo Yok Chu'),       # 6. Teo Yok Chu - Yeo Chee Wang
            ('Hong Leong Bank', 'Infinite GZ Sdn Bhd'),  # 7. Infinite GZ Sdn Bhd
            ('Public Bank', 'Ai Smart Tech'),  # 8. Ai Smart Tech
            ('Alliance Bank', 'Ai Smart Tech')  # 9. Ai Smart Tech
        ]
    
    def calculate_owners_expenses(self, customer_id: int, year: int, month: int) -> float:
        """
        计算 Owners Expenses = Owners信用卡的Suppliers消费
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            Owners Expenses总额
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取Owners信用卡的Suppliers交易
        cursor.execute("""
            SELECT SUM(t.amount) as total
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
              AND strftime('%Y', t.transaction_date) = ?
              AND strftime('%m', t.transaction_date) = ?
              AND t.category = 'Suppliers'
              AND cc.card_holder_name NOT LIKE '%INFINITE%'
              AND cc.card_holder_name NOT LIKE '%GZ%'
        """, (customer_id, str(year), f'{month:02d}'))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total'] if result and result['total'] else 0.0
    
    def calculate_gz_expenses(self, customer_id: int, year: int, month: int) -> float:
        """
        计算 GZs Expenses = Infinite GZ信用卡的Suppliers消费
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            GZs Expenses总额
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(t.amount) as total
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
              AND strftime('%Y', t.transaction_date) = ?
              AND strftime('%m', t.transaction_date) = ?
              AND t.category = 'Suppliers'
              AND (cc.card_holder_name LIKE '%INFINITE%' OR cc.card_holder_name LIKE '%GZ%')
        """, (customer_id, str(year), f'{month:02d}'))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total'] if result and result['total'] else 0.0
    
    def calculate_suppliers_total(self, customer_id: int, year: int, month: int) -> float:
        """
        计算 Suppliers = Suppliers Invoices + Merchant Receipts
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            Suppliers总费用
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Supplier Invoices
        cursor.execute("""
            SELECT SUM(total_amount + supplier_fee) as total
            FROM supplier_invoices
            WHERE customer_id = ?
              AND strftime('%Y', invoice_date) = ?
              AND strftime('%m', invoice_date) = ?
        """, (customer_id, str(year), f'{month:02d}'))
        
        invoices_total = cursor.fetchone()['total'] or 0.0
        
        # Merchant Receipts
        cursor.execute("""
            SELECT SUM(t.amount) as total
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
              AND strftime('%Y', t.transaction_date) = ?
              AND strftime('%m', t.transaction_date) = ?
              AND t.category = 'Suppliers'
        """, (customer_id, str(year), f'{month:02d}'))
        
        receipts_total = cursor.fetchone()['total'] or 0.0
        
        conn.close()
        
        return invoices_total + receipts_total
    
    def calculate_owners_payment(self, customer_id: int, year: int, month: int) -> float:
        """
        计算 Owners Payment = Owners的信用卡还款
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            Owners Payment总额
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(ABS(t.amount)) as total
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
              AND strftime('%Y', t.transaction_date) = ?
              AND strftime('%m', t.transaction_date) = ?
              AND t.category = 'Owners Payment'
        """, (customer_id, str(year), f'{month:02d}'))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total'] if result and result['total'] else 0.0
    
    def calculate_gz_payment(self, customer_id: int, year: int, month: int) -> float:
        """
        计算 GZs Payment = GZ的付款
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            GZs Payment总额
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(ABS(t.amount)) as total
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
              AND strftime('%Y', t.transaction_date) = ?
              AND strftime('%m', t.transaction_date) = ?
              AND t.category = 'GZs Payment'
        """, (customer_id, str(year), f'{month:02d}'))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total'] if result and result['total'] else 0.0
    
    def calculate_owners_outstanding(self, customer_id: int, year: int, month: int, 
                                    previous_balance: float = 0.0) -> float:
        """
        计算 Owners Os Bal = Owners Expenses - Owners Payment + Previous Balance
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            previous_balance: 上期余额
            
        Returns:
            Owners未结余额
        """
        expenses = self.calculate_owners_expenses(customer_id, year, month)
        payment = self.calculate_owners_payment(customer_id, year, month)
        
        return expenses - payment + previous_balance
    
    def calculate_gz_outstanding(self, customer_id: int, year: int, month: int) -> float:
        """
        计算 GZs Os Bal = INFINITE GZ + Suppliers Expenses - GZs Payment
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            GZ未结余额
        """
        infinite_gz = self.calculate_gz_expenses(customer_id, year, month)
        suppliers = self.calculate_suppliers_total(customer_id, year, month)
        payment = self.calculate_gz_payment(customer_id, year, month)
        
        return infinite_gz + suppliers - payment
    
    def get_complete_calculation(self, customer_id: int, year: int, month: int) -> Dict:
        """
        获取完整的计算结果
        
        Args:
            customer_id: 客户ID
            year: 年份
            month: 月份
            
        Returns:
            完整计算结果字典
        """
        result = {
            'customer_id': customer_id,
            'year': year,
            'month': month,
            'owners_expenses': self.calculate_owners_expenses(customer_id, year, month),
            'gz_expenses': self.calculate_gz_expenses(customer_id, year, month),
            'suppliers_total': self.calculate_suppliers_total(customer_id, year, month),
            'owners_payment': self.calculate_owners_payment(customer_id, year, month),
            'gz_payment': self.calculate_gz_payment(customer_id, year, month),
            'owners_outstanding': self.calculate_owners_outstanding(customer_id, year, month),
            'gz_outstanding': self.calculate_gz_outstanding(customer_id, year, month)
        }
        
        return result


# 全局实例
_engine_instance = None

def get_calculation_engine() -> CalculationEngine:
    """获取计算引擎单例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CalculationEngine()
    return _engine_instance
