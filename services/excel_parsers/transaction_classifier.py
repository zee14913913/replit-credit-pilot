"""
30+智能交易分类系统
==================
自动将银行交易/信用卡消费分类到预定义类别

分类体系：
1. 收入类：薪资、利息、股息、退款
2. 支出类：银行费用、转账、ATM提款
3. 账单类：水电费、通讯费、网购、外卖
4. 消费类：汽油费、保险、贷款还款
5. 其他：投资、教育、医疗、政府税费
"""

import re
from typing import Dict, Tuple, List


class TransactionClassifier:
    """交易智能分类器"""
    
    def __init__(self):
        self.classification_rules = self._load_classification_rules()
    
    def _load_classification_rules(self) -> Dict:
        """加载分类规则"""
        return {
            'INCOME': {
                '薪资收入': [
                    'SALARY', 'GAJI', 'PAYROLL', 'INCOME', 'UPAH'
                ],
                '利息收入': [
                    'INTEREST', 'FAEDAH', 'INT CREDIT'
                ],
                '股息收入': [
                    'DIVIDEND', 'DIVIDEN'
                ],
                '退款': [
                    'REFUND', 'RETURN', 'REVERSAL', 'BAYARAN BALIK'
                ]
            },
            'EXPENSES': {
                '银行费用': [
                    'BANK CHARGE', 'SERVICE CHARGE', 'FEE', 'YURAN',
                    'ANNUAL FEE', 'MAINTENANCE FEE'
                ],
                '转账': [
                    'TRANSFER', 'TFR', 'PINDAHAN', 'IBFT', 'IBG',
                    'INTERBANK', 'ONLINE TRANSFER'
                ],
                'ATM提款': [
                    'ATM', 'WITHDRAWAL', 'CASH', 'PENGELUARAN'
                ]
            },
            'BILLS': {
                '水电费': [
                    'TNB', 'TENAGA NASIONAL', 'SYABAS', 'AIR SELANGOR',
                    'ELECTRIC', 'WATER', 'UTILITY'
                ],
                '通讯费': [
                    'MAXIS', 'CELCOM', 'DIGI', 'UNIFI', 'TIME',
                    'TELCO', 'MOBILE', 'INTERNET', 'BROADBAND'
                ],
                '网购': [
                    'SHOPEE', 'LAZADA', 'GRAB', 'FOODPANDA',
                    'AMAZON', 'TAOBAO', 'ONLINE SHOPPING'
                ],
                '外卖': [
                    'GRABFOOD', 'FOODPANDA', 'DELIVEROO', 'FOOD DELIVERY'
                ]
            },
            'CONSUMPTION': {
                '汽油费': [
                    'PETRONAS', 'SHELL', 'PETRON', 'CALTEX', 'BHP',
                    'PETROL', 'FUEL', 'MINYAK'
                ],
                '保险': [
                    'INSURANCE', 'INSURANS', 'TAKAFUL', 'PRUDENTIAL',
                    'AIA', 'GREAT EASTERN', 'ZURICH'
                ],
                '贷款还款': [
                    'LOAN REPAYMENT', 'PINJAMAN', 'MORTGAGE', 'CAR LOAN',
                    'PERSONAL LOAN', 'ASB LOAN', 'PTPTN'
                ],
                '超市购物': [
                    'TESCO', 'AEON', 'GIANT', 'JAYA GROCER',
                    'VILLAGE GROCER', 'SUPERMARKET', 'PASAR RAYA'
                ]
            },
            'CREDIT_CARD': {
                'Card Due Assist': [
                    'CREDIT CARD PAYMENT', 'CC PAYMENT', 'MINIMUM PAYMENT'
                ],
                'Purchases': [
                    'PURCHASE', 'RETAIL', 'POS', 'CONTACTLESS'
                ],
                'Cash Advance': [
                    'CASH ADVANCE', 'ATM WITHDRAWAL'
                ],
                'Finance Charges': [
                    'INTEREST', 'LATE PAYMENT FEE', 'FINANCE CHARGE'
                ]
            },
            'OTHERS': {
                '投资': [
                    'ASB', 'ASN', 'ASNB', 'INVESTMENT', 'UNIT TRUST',
                    'STOCKS', 'SHARES'
                ],
                '教育': [
                    'SCHOOL', 'UNIVERSITY', 'TUITION', 'EDUCATION'
                ],
                '医疗': [
                    'HOSPITAL', 'CLINIC', 'PHARMACY', 'MEDICAL', 'HEALTH'
                ],
                '政府税费': [
                    'LHDN', 'INCOME TAX', 'QUIT RENT', 'ASSESSMENT',
                    'JPJ', 'ROAD TAX'
                ]
            }
        }
    
    def classify(self, description: str, amount: float = 0) -> Tuple[str, str]:
        """
        分类单笔交易
        
        Args:
            description: 交易描述
            amount: 交易金额（正数=收入，负数=支出）
            
        Returns:
            (主分类, 子分类)
        """
        description_upper = description.upper()
        
        for main_category, subcategories in self.classification_rules.items():
            for sub_category, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword.upper() in description_upper:
                        return main_category, sub_category
        
        if amount > 0:
            return 'INCOME', '其他收入'
        else:
            return 'EXPENSES', '其他支出'
    
    def classify_credit_card_transaction(self, description: str) -> Tuple[str, str]:
        """
        分类信用卡交易
        
        Args:
            description: 交易描述
            
        Returns:
            (主分类, 子分类)
        """
        description_upper = description.upper()
        
        if any(kw in description_upper for kw in ['PAYMENT', 'THANK YOU']):
            return 'Payment', '还款'
        
        if any(kw in description_upper for kw in ['INTEREST', 'FINANCE CHARGE', 'LATE FEE']):
            return 'Finance Charges', '利息费用'
        
        if any(kw in description_upper for kw in ['CASH ADVANCE', 'ATM']):
            return 'Cash Advance', '现金预借'
        
        if any(kw in description_upper for kw in ['INSTALMENT', 'FLEXI', 'BALANCE TRANSFER']):
            return 'Instalment Details', '分期付款'
        
        return 'Purchases', '消费'
    
    def get_category_summary(self, transactions: List[Dict]) -> Dict:
        """
        生成分类汇总统计
        
        Args:
            transactions: 交易列表
            
        Returns:
            分类汇总字典
        """
        summary = {}
        
        for txn in transactions:
            category = txn.get('category', 'OTHERS')
            sub_category = txn.get('sub_category', '其他')
            amount = abs(txn.get('amount', 0))
            
            if category not in summary:
                summary[category] = {}
            
            if sub_category not in summary[category]:
                summary[category][sub_category] = {
                    'count': 0,
                    'amount': 0
                }
            
            summary[category][sub_category]['count'] += 1
            summary[category][sub_category]['amount'] += amount
        
        return summary
