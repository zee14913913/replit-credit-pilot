"""
智能交易分类引擎 - Transaction Classifier Engine
自动将信用卡账单交易分类为消费/付款，并识别供应商
"""

import re
from typing import Dict, List, Tuple, Optional
from db.database import get_db

class TransactionClassifier:
    """交易分类器"""
    
    # 预定义供应商列表（7个）
    PREDEFINED_SUPPLIERS = [
        '7sl',
        'Dinas',
        'Raub Syc Hainan',
        'AI Smart Tech',
        'Huawei',
        'Pasar Raya',
        'Puchong Herbs'
    ]
    
    # 付款关键词（用于识别付款交易）
    PAYMENT_KEYWORDS = [
        'payment', 'pay', 'transfer', 'online payment', 'mobile payment',
        'autopay', 'auto payment', 'bank transfer', 'fpx', 'duitnow',
        'cash deposit', 'cheque', 'payment received', 'cr', 'credit'
    ]
    
    # Owner付款关键词
    OWNER_KEYWORDS = [
        'owner', 'self', 'autopay', 'auto payment'
    ]
    
    def __init__(self):
        """初始化分类器"""
        self.supplier_fee_rate = 0.01  # 1% 手续费
    
    def classify_transaction(self, description: str, amount: float, 
                            transaction_type: str = None) -> Dict:
        """
        分类单个交易
        
        Args:
            description: 交易描述
            amount: 交易金额
            transaction_type: 交易类型（DR=debit, CR=credit）
            
        Returns:
            分类结果字典
        """
        description_lower = description.lower()
        
        # 1. 判断是消费还是付款
        is_payment = self._is_payment_transaction(description_lower, transaction_type, amount)
        
        if is_payment:
            # 付款交易分类
            return self._classify_payment(description, description_lower, amount)
        else:
            # 消费交易分类
            return self._classify_consumption(description, description_lower, amount)
    
    def _is_payment_transaction(self, description_lower: str, 
                               transaction_type: str, amount: float) -> bool:
        """判断是否为付款交易"""
        
        # 方法1: 通过交易类型判断（CR = Credit = 付款）
        if transaction_type and 'CR' in transaction_type.upper():
            return True
        
        # 方法2: 通过金额判断（正数通常是付款，负数是消费）
        # 但这取决于银行的记账方式，需要根据实际情况调整
        
        # 方法3: 通过关键词判断
        for keyword in self.PAYMENT_KEYWORDS:
            if keyword in description_lower:
                return True
        
        return False
    
    def _classify_consumption(self, description: str, 
                            description_lower: str, amount: float) -> Dict:
        """分类消费交易"""
        
        # 检查是否为Supplier Debit
        supplier_name = self._identify_supplier(description_lower)
        
        if supplier_name:
            # Supplier Debit
            supplier_fee = abs(amount) * self.supplier_fee_rate
            return {
                'record_type': 'consumption',
                'category': 'Supplier Debit',
                'supplier_name': supplier_name,
                'supplier_fee': round(supplier_fee, 2),
                'user_name': None  # 需要从其他地方获取
            }
        else:
            # Unclassified Debit
            return {
                'record_type': 'consumption',
                'category': 'Unclassified Debit',
                'supplier_name': None,
                'supplier_fee': 0.0,
                'user_name': None
            }
    
    def _classify_payment(self, description: str, 
                         description_lower: str, amount: float) -> Dict:
        """分类付款交易"""
        
        # 检查是否为Owner付款
        is_owner = self._is_owner_payment(description_lower)
        
        if is_owner:
            return {
                'record_type': 'payment',
                'category': 'Owner Credit',
                'payment_user': 'Owner'
            }
        else:
            # 尝试提取付款人名字
            payment_user = self._extract_payment_user(description)
            return {
                'record_type': 'payment',
                'category': '3rd Party Credit',
                'payment_user': payment_user or 'Unknown'
            }
    
    def _identify_supplier(self, description_lower: str) -> Optional[str]:
        """识别供应商名称"""
        for supplier in self.PREDEFINED_SUPPLIERS:
            supplier_lower = supplier.lower()
            if supplier_lower in description_lower:
                return supplier
        return None
    
    def _is_owner_payment(self, description_lower: str) -> bool:
        """判断是否为Owner付款"""
        for keyword in self.OWNER_KEYWORDS:
            if keyword in description_lower:
                return True
        return False
    
    def _extract_payment_user(self, description: str) -> Optional[str]:
        """从描述中提取付款人名字"""
        # 尝试提取人名（这里可以根据实际格式调整）
        # 例如: "PAYMENT BY JOHN DOE" -> "JOHN DOE"
        
        patterns = [
            r'payment by\s+([A-Z\s]+)',
            r'from\s+([A-Z\s]+)',
            r'transfer from\s+([A-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None


def classify_and_save_transactions(statement_id: int, customer_id: int) -> Dict:
    """
    分类并保存账单的所有交易
    
    Args:
        statement_id: 账单ID
        customer_id: 客户ID
        
    Returns:
        分类统计结果
    """
    classifier = TransactionClassifier()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取账单信息
        cursor.execute('''
            SELECT s.statement_date, s.card_full_number, s.due_date,
                   c.bank_name, c.card_number_last4
            FROM statements s
            JOIN credit_cards c ON s.card_id = c.id
            WHERE s.id = ?
        ''', (statement_id,))
        
        stmt_info = cursor.fetchone()
        if not stmt_info:
            return {'error': 'Statement not found'}
        
        statement_date, card_full_number, due_date, bank_name, card_last4 = stmt_info
        
        # 如果没有完整卡号，使用后四位
        if not card_full_number:
            card_full_number = f"****{card_last4}"
        
        # 获取所有交易
        cursor.execute('''
            SELECT id, transaction_date, description, amount, transaction_type
            FROM transactions
            WHERE statement_id = ?
            ORDER BY transaction_date
        ''', (statement_id,))
        
        transactions = cursor.fetchall()
        
        stats = {
            'total_transactions': len(transactions),
            'supplier_debit': 0,
            'unclassified_debit': 0,
            'third_party_credit': 0,
            'owner_credit': 0,
            'supplier_fees_total': 0.0
        }
        
        # 分类每个交易
        for txn in transactions:
            txn_id, txn_date, description, amount, txn_type = txn
            
            # 执行分类
            classification = classifier.classify_transaction(
                description, amount, txn_type
            )
            
            if classification['record_type'] == 'consumption':
                # 保存到消费记录表
                cursor.execute('''
                    INSERT INTO consumption_records 
                    (customer_id, statement_id, bank, card_full_number, 
                     statement_date, transaction_date, transaction_details,
                     suppliers_usage, user_name, amount, category, supplier_fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id, statement_id, bank_name, card_full_number,
                    statement_date, txn_date, description,
                    classification.get('supplier_name'),
                    classification.get('user_name'),
                    abs(amount), classification['category'],
                    classification.get('supplier_fee', 0.0)
                ))
                
                if classification['category'] == 'Supplier Debit':
                    stats['supplier_debit'] += 1
                    stats['supplier_fees_total'] += classification.get('supplier_fee', 0.0)
                else:
                    stats['unclassified_debit'] += 1
            
            else:  # payment
                # 保存到付款记录表
                cursor.execute('''
                    INSERT INTO payment_records
                    (customer_id, statement_id, bank, credit_card_full_number,
                     due_date, payment_date, payment_details, payment_user,
                     payment_amount, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id, statement_id, bank_name, card_full_number,
                    due_date, txn_date, description,
                    classification.get('payment_user'),
                    abs(amount), classification['category']
                ))
                
                if classification['category'] == 'Owner Credit':
                    stats['owner_credit'] += 1
                else:
                    stats['third_party_credit'] += 1
        
        conn.commit()
        
        return stats


def get_consumption_summary(customer_id: int, statement_id: int = None) -> List[Dict]:
    """
    获取消费汇总
    
    Args:
        customer_id: 客户ID
        statement_id: 账单ID（可选，None表示所有账单）
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT category, suppliers_usage, 
                   COUNT(*) as count,
                   SUM(amount) as total_amount,
                   SUM(supplier_fee) as total_fee
            FROM consumption_records
            WHERE customer_id = ?
        '''
        params = [customer_id]
        
        if statement_id:
            query += ' AND statement_id = ?'
            params.append(statement_id)
        
        query += ' GROUP BY category, suppliers_usage ORDER BY category, suppliers_usage'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        summary = []
        for row in results:
            category, supplier, count, total, fee = row
            summary.append({
                'category': category,
                'supplier': supplier or 'N/A',
                'count': count,
                'total_amount': round(total, 2),
                'total_fee': round(fee, 2)
            })
        
        return summary


def get_payment_summary(customer_id: int, statement_id: int = None) -> List[Dict]:
    """
    获取付款汇总
    
    Args:
        customer_id: 客户ID
        statement_id: 账单ID（可选）
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT category, payment_user,
                   COUNT(*) as count,
                   SUM(payment_amount) as total_amount
            FROM payment_records
            WHERE customer_id = ?
        '''
        params = [customer_id]
        
        if statement_id:
            query += ' AND statement_id = ?'
            params.append(statement_id)
        
        query += ' GROUP BY category, payment_user ORDER BY category'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        summary = []
        for row in results:
            category, user, count, total = row
            summary.append({
                'category': category,
                'payment_user': user or 'N/A',
                'count': count,
                'total_amount': round(total, 2)
            })
        
        return summary
