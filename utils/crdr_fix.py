"""
CR/DR 自动修正模块
智能识别交易类型并自动修正 Credit/Debit 分类错误
"""

import re
from typing import Dict, List


class CRDRFixer:
    """CR/DR 自动修正处理器"""
    
    def __init__(self):
        # 关键词映射
        self.payment_keywords = [
            'payment', 'refund', 'rebate', 'bayaran', 'returned',
            'payment rec', 'payment received', 'thank you', 'thanks',
            'cash rebate', 'reversal', 'adjustment credit', 'credit adjustment'
        ]
        
        self.purchase_keywords = [
            'purchase', 'spending', 'transaction', 'merchant',
            'retail', 'pembelian', 'mall', 'store', 'shop',
            'lazada', 'shopee', 'grab', 'tng', 'boost'
        ]
        
        self.fee_keywords = [
            'fee', 'charge', 'interest', 'late payment', 'annual fee',
            'service tax', 'management fee', 'finance charge', 'yuran',
            'late charge', 'overlimit', 'paper statement'
        ]
    
    def fix_transaction(self, transaction: Dict) -> Dict:
        """
        修正单条交易的 CR/DR 分类
        
        逻辑:
        1. 分析交易描述，判断应该是 CR 还是 DR
        2. 如果实际分类与应有分类矛盾，自动交换 CR/DR 的值
        
        Args:
            transaction: 交易记录字典
                {
                    "transaction_description": "Payment Received",
                    "amount_CR": 0.0,
                    "amount_DR": 1000.0
                }
        
        Returns:
            修正后的交易记录
        """
        description = transaction.get('transaction_description', '').lower()
        amount_cr = float(transaction.get('amount_CR', 0))
        amount_dr = float(transaction.get('amount_DR', 0))
        
        # 判断应该的交易类型
        should_be_credit = self._is_credit_transaction(description)
        should_be_debit = self._is_debit_transaction(description)
        
        # 当前分类状态
        is_currently_credit = amount_cr > 0 and amount_dr == 0
        is_currently_debit = amount_dr > 0 and amount_cr == 0
        
        # 修正逻辑1: 应该是 Credit 但被标记为 Debit
        if should_be_credit and is_currently_debit:
            transaction['amount_CR'] = amount_dr
            transaction['amount_DR'] = 0.0
            transaction['_auto_corrected'] = True
            transaction['_correction_reason'] = 'Payment/Refund should be CR'
        
        # 修正逻辑2: 应该是 Debit 但被标记为 Credit
        elif should_be_debit and is_currently_credit:
            transaction['amount_DR'] = amount_cr
            transaction['amount_CR'] = 0.0
            transaction['_auto_corrected'] = True
            transaction['_correction_reason'] = 'Purchase/Fee should be DR'
        
        # 修正逻辑3: 两者都有值（异常情况）
        elif amount_cr > 0 and amount_dr > 0:
            # 根据描述决定保留哪一个
            if should_be_credit:
                transaction['amount_DR'] = 0.0
                transaction['_auto_corrected'] = True
                transaction['_correction_reason'] = 'Kept CR, removed DR'
            elif should_be_debit:
                transaction['amount_CR'] = 0.0
                transaction['_auto_corrected'] = True
                transaction['_correction_reason'] = 'Kept DR, removed CR'
            else:
                # 默认保留较大的值
                if amount_cr > amount_dr:
                    transaction['amount_DR'] = 0.0
                else:
                    transaction['amount_CR'] = 0.0
                transaction['_auto_corrected'] = True
                transaction['_correction_reason'] = 'Kept larger amount'
        
        return transaction
    
    def _is_credit_transaction(self, description: str) -> bool:
        """判断是否应该是 Credit 交易（还款/退款）"""
        return any(keyword in description for keyword in self.payment_keywords)
    
    def _is_debit_transaction(self, description: str) -> bool:
        """判断是否应该是 Debit 交易（消费/费用）"""
        return (
            any(keyword in description for keyword in self.purchase_keywords) or
            any(keyword in description for keyword in self.fee_keywords)
        )
    
    def fix_all_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """
        批量修正所有交易的 CR/DR 分类
        
        Args:
            transactions: 交易列表
        
        Returns:
            修正后的交易列表
        """
        return [self.fix_transaction(t) for t in transactions]
    
    def validate_balance(self, 
                        previous_balance: float,
                        current_balance: float,
                        transactions: List[Dict]) -> Dict:
        """
        验证余额一致性
        
        公式: previous_balance + sum(DR) - sum(CR) = current_balance
        
        Args:
            previous_balance: 上期余额
            current_balance: 本期余额
            transactions: 交易列表
        
        Returns:
            验证结果字典:
            {
                "is_valid": True/False,
                "calculated_balance": float,
                "actual_balance": float,
                "difference": float,
                "total_dr": float,
                "total_cr": float,
                "message": str
            }
        """
        if not transactions:
            return {
                "is_valid": False,
                "calculated_balance": previous_balance,
                "actual_balance": current_balance,
                "difference": abs(current_balance - previous_balance),
                "total_dr": 0.0,
                "total_cr": 0.0,
                "message": "No transactions to validate"
            }
        
        # 计算 DR 和 CR 总和
        total_dr = sum(float(t.get('amount_DR', 0)) for t in transactions)
        total_cr = sum(float(t.get('amount_CR', 0)) for t in transactions)
        
        # 计算预期余额
        calculated_balance = previous_balance + total_dr - total_cr
        
        # 计算差异（允许 0.02 的浮点数误差）
        difference = abs(calculated_balance - current_balance)
        is_valid = difference < 0.02
        
        return {
            "is_valid": is_valid,
            "calculated_balance": round(calculated_balance, 2),
            "actual_balance": round(current_balance, 2),
            "difference": round(difference, 2),
            "total_dr": round(total_dr, 2),
            "total_cr": round(total_cr, 2),
            "message": "Balance verified" if is_valid else f"Mismatch: RM{difference:.2f}"
        }
    
    def auto_fix_balance_mismatch(self,
                                   previous_balance: float,
                                   current_balance: float,
                                   transactions: List[Dict]) -> Dict:
        """
        自动修复余额不匹配问题
        
        策略:
        1. 先检查是否有 CR/DR 分类错误
        2. 尝试交换可疑交易的 CR/DR
        3. 重新验证
        
        Args:
            previous_balance: 上期余额
            current_balance: 本期余额
            transactions: 交易列表
        
        Returns:
            {
                "fixed": True/False,
                "transactions": List[Dict],  # 修正后的交易
                "validation": Dict  # 验证结果
            }
        """
        # 先执行标准的 CR/DR 修正
        fixed_transactions = self.fix_all_transactions(transactions)
        
        # 验证修正后的结果
        validation = self.validate_balance(previous_balance, current_balance, fixed_transactions)
        
        if validation['is_valid']:
            return {
                "fixed": True,
                "transactions": fixed_transactions,
                "validation": validation
            }
        
        # 如果仍然不匹配，尝试更激进的修正
        # （例如：查找金额接近差异值的交易，尝试交换其 CR/DR）
        difference = validation['difference']
        
        for transaction in fixed_transactions:
            amount_cr = transaction.get('amount_CR', 0)
            amount_dr = transaction.get('amount_DR', 0)
            
            # 如果某个交易的金额接近差异值，尝试交换
            if abs(amount_dr - difference) < 0.02 or abs(amount_cr - difference) < 0.02:
                if amount_dr > 0:
                    transaction['amount_CR'] = amount_dr
                    transaction['amount_DR'] = 0.0
                    transaction['_auto_corrected'] = True
                    transaction['_correction_reason'] = 'Balance mismatch fix'
                elif amount_cr > 0:
                    transaction['amount_DR'] = amount_cr
                    transaction['amount_CR'] = 0.0
                    transaction['_auto_corrected'] = True
                    transaction['_correction_reason'] = 'Balance mismatch fix'
                
                # 重新验证
                validation = self.validate_balance(previous_balance, current_balance, fixed_transactions)
                if validation['is_valid']:
                    return {
                        "fixed": True,
                        "transactions": fixed_transactions,
                        "validation": validation
                    }
        
        # 无法自动修复
        return {
            "fixed": False,
            "transactions": fixed_transactions,
            "validation": validation
        }
