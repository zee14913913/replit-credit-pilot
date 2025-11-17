#!/usr/bin/env python3
"""
账目计算逻辑
按照业务规则进行分类和结算
"""
import json
import re
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from decimal import Decimal


class BalanceCalculator:
    """账目计算器"""
    
    def __init__(self, rules_path: str = "config/business_rules.json"):
        """初始化"""
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = json.load(f)
        
        self.classification_rules = self.rules['classification_rules']
        self.calculation_rules = self.rules['calculation_rules']
        self.suppliers = self.classification_rules['categories']['suppliers']['supplier_list']
        self.gz_keywords = self.classification_rules['categories']['gz']['keywords']
    
    def classify_transaction(self, transaction: Dict[str, Any], payment_note: str = "") -> str:
        """
        分类单笔交易
        
        Args:
            transaction: 交易记录
            payment_note: Payment备注
        
        Returns:
            分类结果: 'owners', 'gz', 'suppliers'
        """
        description = transaction.get('description', '').upper()
        
        # 优先级1：供应商匹配
        for supplier in self.suppliers:
            if supplier.upper() in description:
                return 'suppliers'
        
        # 优先级2：GZ关键词匹配
        payment_note_upper = payment_note.upper()
        for keyword in self.gz_keywords:
            if keyword.upper() in payment_note_upper:
                return 'gz'
        
        # 优先级3：默认为Owners
        return 'owners'
    
    def classify_payment(self, payment: Dict[str, Any], payment_note: str = "") -> str:
        """
        分类还款
        
        Args:
            payment: 还款记录
            payment_note: Payment备注
        
        Returns:
            分类结果: 'owners', 'gz'
        """
        payment_note_upper = payment_note.upper()
        
        # GZ关键词匹配
        for keyword in self.gz_keywords:
            if keyword.upper() in payment_note_upper:
                return 'gz'
        
        # 默认为Owners
        return 'owners'
    
    def calculate_supplier_fee(self, amount: float) -> float:
        """计算供应商1%手续费"""
        if not self.calculation_rules['supplier_fee']['enabled']:
            return 0.0
        
        rate = self.calculation_rules['supplier_fee']['rate']
        return round(amount * rate, 2)
    
    def categorize_transactions(self, transactions: List[Dict[str, Any]], 
                                payment_notes: Optional[Dict[str, str]] = None) -> Dict[str, List[Dict]]:
        """
        批量分类交易
        
        Args:
            transactions: 交易列表
            payment_notes: Payment备注字典 {transaction_id: note}
        
        Returns:
            分类结果字典
        """
        payment_notes = payment_notes or {}
        
        categorized = {
            'owners_expenses': [],
            'gz_expenses': [],
            'suppliers': [],
            'owners_payment': [],
            'gz_payment': []
        }
        
        for txn in transactions:
            txn_id = txn.get('id', '')
            payment_note = payment_notes.get(txn_id, '')
            amount = float(txn.get('amount', 0))
            is_credit = txn.get('is_credit', False)
            
            if is_credit:
                # 还款分类
                category = self.classify_payment(txn, payment_note)
                if category == 'gz':
                    categorized['gz_payment'].append(txn)
                else:
                    categorized['owners_payment'].append(txn)
            else:
                # 消费分类
                category = self.classify_transaction(txn, payment_note)
                
                if category == 'suppliers':
                    # 计算1%手续费
                    fee = self.calculate_supplier_fee(amount)
                    txn['supplier_fee'] = fee
                    categorized['suppliers'].append(txn)
                elif category == 'gz':
                    categorized['gz_expenses'].append(txn)
                else:
                    categorized['owners_expenses'].append(txn)
        
        return categorized
    
    def calculate_totals(self, categorized: Dict[str, List[Dict]]) -> Dict[str, float]:
        """
        计算各分类总金额
        
        Args:
            categorized: 分类后的交易
        
        Returns:
            总金额字典
        """
        totals = {}
        
        for category, transactions in categorized.items():
            total = sum(float(txn.get('amount', 0)) for txn in transactions)
            totals[category] = round(total, 2)
        
        # 计算供应商手续费总额
        supplier_fee_total = sum(
            float(txn.get('supplier_fee', 0)) 
            for txn in categorized.get('suppliers', [])
        )
        totals['supplier_fee_total'] = round(supplier_fee_total, 2)
        
        return totals
    
    def calculate_outstanding_balance(self, 
                                     previous_balance: float,
                                     categorized: Dict[str, List[Dict]],
                                     totals: Dict[str, float]) -> Dict[str, float]:
        """
        计算Outstanding Balance
        
        Formula: Previous Balance + Expenses - Payments
        
        Args:
            previous_balance: 上期余额
            categorized: 分类后的交易
            totals: 各分类总金额
        
        Returns:
            余额详情
        """
        # 总消费 = Owners Expenses + GZ Expenses + Suppliers + Supplier Fee
        total_expenses = (
            totals.get('owners_expenses', 0) +
            totals.get('gz_expenses', 0) +
            totals.get('suppliers', 0) +
            totals.get('supplier_fee_total', 0)
        )
        
        # 总还款 = Owners Payment + GZ Payment
        total_payments = (
            totals.get('owners_payment', 0) +
            totals.get('gz_payment', 0)
        )
        
        # Outstanding Balance
        outstanding_balance = previous_balance + total_expenses - total_payments
        
        return {
            'previous_balance': round(previous_balance, 2),
            'total_expenses': round(total_expenses, 2),
            'total_payments': round(total_payments, 2),
            'outstanding_balance': round(outstanding_balance, 2),
            'owners_balance': round(
                totals.get('owners_expenses', 0) - totals.get('owners_payment', 0), 2
            ),
            'gz_balance': round(
                totals.get('gz_expenses', 0) - totals.get('gz_payment', 0), 2
            ),
            'suppliers_balance': round(
                totals.get('suppliers', 0) + totals.get('supplier_fee_total', 0), 2
            )
        }
    
    def verify_balance(self, calculated_balance: float, 
                      bank_balance: float, 
                      tolerance: Optional[float] = None) -> Tuple[bool, float]:
        """
        验证计算结果与银行账单
        
        Args:
            calculated_balance: 计算的余额
            bank_balance: 银行账单余额
            tolerance: 容差（默认从配置读取）
        
        Returns:
            (是否匹配, 差异)
        """
        tolerance_value = tolerance if tolerance is not None else self.calculation_rules['balance_verification']['tolerance']
        
        difference = abs(calculated_balance - bank_balance)
        is_match = difference <= tolerance_value
        
        return is_match, round(difference, 2)
    
    def generate_summary_report(self, 
                               categorized: Dict[str, List[Dict]],
                               totals: Dict[str, float],
                               balances: Dict[str, float]) -> Dict[str, Any]:
        """
        生成汇总报告
        
        Args:
            categorized: 分类后的交易
            totals: 各分类总金额
            balances: 余额详情
        
        Returns:
            汇总报告
        """
        return {
            'transaction_counts': {
                category: len(transactions)
                for category, transactions in categorized.items()
            },
            'category_totals': totals,
            'balances': balances,
            'summary': {
                'total_transactions': sum(
                    len(transactions) 
                    for transactions in categorized.values()
                ),
                'total_expenses': balances['total_expenses'],
                'total_payments': balances['total_payments'],
                'net_change': balances['outstanding_balance'] - balances['previous_balance']
            }
        }


def main():
    """测试函数"""
    print("="*80)
    print("账目计算逻辑测试")
    print("="*80)
    
    calculator = BalanceCalculator()
    
    # 测试数据
    test_transactions = [
        {
            'id': '1',
            'description': "MCDONALD'S-KOTA WARISAN SEPANG MY",
            'amount': 36.60,
            'is_credit': False
        },
        {
            'id': '2',
            'description': '7SL TRADING SDN BHD',
            'amount': 1000.00,
            'is_credit': False
        },
        {
            'id': '3',
            'description': 'DINAS ENTERPRISE',
            'amount': 500.00,
            'is_credit': False
        },
        {
            'id': '4',
            'description': 'PAYMENT RECEIVED',
            'amount': 2000.00,
            'is_credit': True
        }
    ]
    
    payment_notes = {
        '1': '',
        '2': '',
        '3': 'Payment on behalf of client ABC',
        '4': ''
    }
    
    # 分类交易
    categorized = calculator.categorize_transactions(test_transactions, payment_notes)
    
    print("\n📊 交易分类结果:")
    for category, txns in categorized.items():
        if txns:
            print(f"\n{category}:")
            for txn in txns:
                fee_info = f" (Fee: RM {txn.get('supplier_fee', 0):.2f})" if 'supplier_fee' in txn else ""
                print(f"   - {txn['description']}: RM {txn['amount']:.2f}{fee_info}")
    
    # 计算总额
    totals = calculator.calculate_totals(categorized)
    
    print("\n💰 各分类总金额:")
    for category, total in totals.items():
        print(f"   {category}: RM {total:.2f}")
    
    # 计算余额
    previous_balance = 5000.00
    balances = calculator.calculate_outstanding_balance(previous_balance, categorized, totals)
    
    print("\n📈 余额计算:")
    for key, value in balances.items():
        print(f"   {key}: RM {value:.2f}")
    
    # 生成汇总
    summary = calculator.generate_summary_report(categorized, totals, balances)
    
    print("\n📋 汇总报告:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    print("\n✅ 测试完成")
    print("="*80)


if __name__ == '__main__':
    main()
