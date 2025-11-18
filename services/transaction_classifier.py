"""
交易分类器 - Transaction Classifier
自动分类624笔未分类交易为: Owners Expenses, GZs Expenses, Suppliers, Owners Payment, GZs Payment
"""

import re
from typing import Dict, List, Optional, Tuple
import sqlite3


class TransactionClassifier:
    """智能交易分类器"""
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        
        # 供应商关键词（7个主要供应商）
        self.suppliers = [
            'HUAWEI', 'APPLE', 'XIAOMI', 'OPPO', 'VIVO', 'SAMSUNG', 'REALME'
        ]
        
        # GZ银行列表（9间银行）
        self.gz_banks = [
            'GX BANK', 'GXBANK',  # INFINITE GZ - Tan Zee Liang
            'MAYBANK',  # Yeo Chee Wang
            'UOB',  # Yeo Chee Wang
            'OCBC',  # Yeo Chee Wang + Teo Yok Chu
            'HONG LEONG', 'HLB',  # Infinite GZ Sdn Bhd
            'PUBLIC BANK', 'PBB',  # Ai Smart Tech
            'ALLIANCE BANK', 'ALLIANCE'  # Ai Smart Tech
        ]
        
        # GZ持卡人关键词
        self.gz_cardholders = [
            'INFINITE', 'GZ', 'TAN ZEE LIANG', 'YEO CHEE WANG',
            'TEO YOK CHU', 'AI SMART TECH', 'INFINITE GZ'
        ]
        
        # 付款关键词
        self.payment_keywords = [
            'PAYMENT', 'BAYARAN', 'DIRECT DEBIT', 'AUTO DEBIT',
            'BANK TRANSFER', 'ONLINE PAYMENT', 'PAYMENT RECEIVED'
        ]
        
        # 费用关键词
        self.fee_keywords = [
            'FEE', 'CHARGE', 'INTEREST', 'YURAN', 'FAEDAH',
            'LATE PAYMENT', 'ANNUAL FEE', 'SERVICE CHARGE'
        ]
    
    def is_supplier_transaction(self, description: str) -> bool:
        """判断是否为供应商交易"""
        desc_upper = description.upper()
        return any(supplier in desc_upper for supplier in self.suppliers)
    
    def is_gz_cardholder(self, cardholder: str, bank_name: str = '') -> bool:
        """判断是否为GZ持卡人"""
        cardholder_upper = cardholder.upper() if cardholder else ''
        bank_upper = bank_name.upper() if bank_name else ''
        
        # 检查持卡人名称
        if any(kw in cardholder_upper for kw in self.gz_cardholders):
            return True
        
        # 检查银行是否在GZ银行列表
        if any(bank in bank_upper for bank in self.gz_banks):
            return True
        
        return False
    
    def is_payment(self, description: str, amount: float) -> bool:
        """判断是否为付款交易"""
        desc_upper = description.upper()
        
        # 负数金额通常是付款或退款
        if amount < 0:
            return True
        
        # 包含付款关键词
        if any(kw in desc_upper for kw in self.payment_keywords):
            return True
        
        return False
    
    def classify_single_transaction(self, description: str, amount: float, 
                                   cardholder: str, bank_name: str = '') -> str:
        """
        分类单个交易
        
        Args:
            description: 交易描述
            amount: 金额
            cardholder: 持卡人
            bank_name: 银行名称
            
        Returns:
            分类结果: 'Owners Expenses', 'GZs Expenses', 'Suppliers', 
                      'Owners Payment', 'GZs Payment', 'Others'
        """
        is_gz = self.is_gz_cardholder(cardholder, bank_name)
        is_supplier = self.is_supplier_transaction(description)
        is_payment_txn = self.is_payment(description, amount)
        
        # 分类逻辑
        if is_supplier:
            # 供应商交易
            return 'Suppliers'
        elif is_payment_txn:
            # 付款交易
            return 'GZs Payment' if is_gz else 'Owners Payment'
        else:
            # 其他消费
            return 'GZs Expenses' if is_gz else 'Owners Expenses'
    
    def reclassify_all_transactions(self) -> Dict:
        """
        重新分类所有交易
        
        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有需要分类的交易
        cursor.execute("""
            SELECT 
                t.id,
                t.description,
                t.amount,
                t.category as old_category,
                cc.card_holder_name,
                cc.bank_name
            FROM transactions t
            LEFT JOIN statements s ON t.statement_id = s.id
            LEFT JOIN credit_cards cc ON s.card_id = cc.id
            WHERE t.category IS NULL OR t.category = '' OR t.category = 'Uncategorized'
        """)
        
        transactions = cursor.fetchall()
        
        stats = {
            'total': len(transactions),
            'reclassified': 0,
            'by_category': {
                'Owners Expenses': 0,
                'GZs Expenses': 0,
                'Suppliers': 0,
                'Owners Payment': 0,
                'GZs Payment': 0,
                'Others': 0
            },
            'errors': []
        }
        
        for txn in transactions:
            try:
                # 分类
                new_category = self.classify_single_transaction(
                    description=txn['description'] or '',
                    amount=txn['amount'] or 0,
                    cardholder=txn['card_holder_name'] or '',
                    bank_name=txn['bank_name'] or ''
                )
                
                # 更新数据库
                cursor.execute("""
                    UPDATE transactions 
                    SET category = ?
                    WHERE id = ?
                """, (new_category, txn['id']))
                
                stats['reclassified'] += 1
                stats['by_category'][new_category] += 1
                
            except Exception as e:
                stats['errors'].append({
                    'transaction_id': txn['id'],
                    'error': str(e)
                })
        
        conn.commit()
        conn.close()
        
        return stats
    
    def get_classification_preview(self, limit: int = 100) -> List[Dict]:
        """
        获取分类预览（不修改数据库）
        
        Args:
            limit: 限制数量
            
        Returns:
            交易列表及建议分类
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.id,
                t.description,
                t.amount,
                t.category as old_category,
                cc.card_holder_name,
                cc.bank_name,
                s.statement_date
            FROM transactions t
            LEFT JOIN statements s ON t.statement_id = s.id
            LEFT JOIN credit_cards cc ON s.card_id = cc.id
            WHERE t.category IS NULL OR t.category = '' OR t.category = 'Uncategorized'
            ORDER BY s.statement_date DESC
            LIMIT ?
        """, (limit,))
        
        transactions = cursor.fetchall()
        conn.close()
        
        result = []
        for txn in transactions:
            new_category = self.classify_single_transaction(
                description=txn['description'] or '',
                amount=txn['amount'] or 0,
                cardholder=txn['card_holder_name'] or '',
                bank_name=txn['bank_name'] or ''
            )
            
            result.append({
                'id': txn['id'],
                'description': txn['description'],
                'amount': txn['amount'],
                'old_category': txn['old_category'] or 'Uncategorized',
                'new_category': new_category,
                'cardholder': txn['card_holder_name'],
                'bank': txn['bank_name'],
                'date': txn['statement_date']
            })
        
        return result


# 全局实例
_classifier_instance = None

def get_classifier() -> TransactionClassifier:
    """获取分类器单例"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = TransactionClassifier()
    return _classifier_instance
