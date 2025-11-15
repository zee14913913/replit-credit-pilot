"""
INFINITE GZ 信用卡系统 - 分类引擎
按照任务书第5-9节规范实现自动分类逻辑

主要功能：
1. 消费分类（Owner's Expenses / GZ's Expenses）
2. 付款分类（Owner Payment / GZ Direct / GZ Indirect）
3. 转账分类（Card Due Assist / Loan-Credit Assist）
4. Supplier自动识别
5. 1% Fee自动计算
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/smart_loan_manager.db')

class InfiniteGZClassificationEngine:
    """INFINITE GZ 分类引擎核心类"""
    
    def __init__(self):
        self.supplier_list_cache = None
        self.gz_bank_list_cache = None
    
    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(DB_PATH)
    
    # ========== 任务书第5节：消费分类 ==========
    
    def load_supplier_list(self) -> List[str]:
        """
        加载Supplier白名单
        任务书第5.1节：Supplier List → 全部归类为 GZ's Expenses
        """
        if self.supplier_list_cache is not None:
            return self.supplier_list_cache
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT supplier_name 
            FROM supplier_list 
            WHERE is_active = 1
        ''')
        
        suppliers = [row[0].lower() for row in cursor.fetchall()]
        conn.close()
        
        self.supplier_list_cache = suppliers
        return suppliers
    
    def classify_expense_owner(self, description: str) -> Tuple[str, bool, Optional[str]]:
        """
        分类消费归属
        
        任务书第5节规则：
        - 若消费商户命中 Supplier List → expense_owner = "GZ's Expenses"
        - 非 Supplier 消费 → expense_owner = "Owner's Expenses"
        
        Returns:
            (expense_owner, is_supplier, matched_supplier_name)
        """
        supplier_list = self.load_supplier_list()
        description_lower = description.lower()
        
        # 检查是否命中Supplier List
        for supplier in supplier_list:
            if supplier in description_lower:
                return ("GZ's Expenses", True, supplier)
        
        # 非Supplier消费
        return ("Owner's Expenses", False, None)
    
    def calculate_supplier_fee(self, amount: float, fee_percentage: float = 0.01) -> float:
        """
        计算Supplier 1% Fee
        
        任务书第6节：supplier_fee = amount * 0.01
        """
        return round(amount * fee_percentage, 2)
    
    # ========== 任务书第8节：付款分类 ==========
    
    def load_gz_bank_list(self) -> List[str]:
        """
        加载GZ银行白名单
        任务书第16节：9个GZ银行账户
        """
        if self.gz_bank_list_cache is not None:
            return self.gz_bank_list_cache
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT full_account_identifier 
            FROM gz_bank_list 
            WHERE is_active = 1
        ''')
        
        gz_banks = [row[0].lower() for row in cursor.fetchall()]
        conn.close()
        
        self.gz_bank_list_cache = gz_banks
        return gz_banks
    
    def classify_payment_type(
        self, 
        description: str, 
        amount: float,
        customer_id: int,
        statement_month: str,
        has_gz_transfer: bool = False
    ) -> Tuple[str, bool]:
        """
        分类付款类型
        
        任务书第8节：付款分类（Payment Classification）
        
        三种类型：
        1. Owner's Payment - 客户自己付款
        2. GZ's Payment (Direct) - GZ直接向银行付款
        3. GZ's Payment (Indirect) - GZ转账给客户→客户付款
        
        Returns:
            (payment_type, verified)
        """
        gz_banks = self.load_gz_bank_list()
        description_lower = description.lower()
        
        # 8.2 GZ's Payment (Direct)
        # 来源银行账户 ∈ GZ Bank List
        for gz_bank in gz_banks:
            if gz_bank in description_lower:
                return ("GZ Direct", True)
        
        # 8.3 GZ's Payment (Indirect)
        # 当月存在GZ→客户转账 + 任意CR
        if has_gz_transfer:
            return ("GZ Indirect", True)
        
        # 8.1 Owner's Payment（默认）
        return ("Owner Payment", False)
    
    # ========== 任务书第9节：转账分类 ==========
    
    def classify_transfer_purpose(
        self,
        customer_id: int,
        amount: float,
        transfer_date: str,
        has_credit_card_cr_this_month: bool
    ) -> Tuple[str, str, bool]:
        """
        分类转账用途
        
        任务书第9节：区分 代付 vs 借贷
        
        (A) Card Due Assist（代付）：
            - GZ→客户的资金用于客户信用卡 CR
            - 不产生利息
            - 进入 GZ's Payment
        
        (B) Loan / Credit Assist（借贷）：
            - GZ→客户的资金不是用于信用卡
            - 产生利息
            - 进入 Loan Outstanding
        
        Returns:
            (purpose, affects, generates_interest)
        """
        # 判断：若当月有信用卡CR，则视为Card Due Assist
        if has_credit_card_cr_this_month:
            return (
                "Card Due Assist",
                "GZ's Payment",
                False  # 不产生利息
            )
        else:
            # 不是用于信用卡，归类为借贷
            return (
                "Loan-Credit Assist",
                "Loan Outstanding",
                True  # 产生利息
            )
    
    # ========== 批量分类处理 ==========
    
    def classify_transaction_batch(
        self, 
        transactions: List[Dict]
    ) -> List[Dict]:
        """
        批量分类交易
        
        输入格式：
        [{
            'customer_id': int,
            'date': str,
            'description': str,
            'amount': float,
            'record_type': str,
            'statement_month': str,
            'bank_name': str,
            'card_last4': str
        }, ...]
        
        输出：增加分类字段
        - expense_owner
        - payment_type
        - is_supplier_transaction
        - supplier_name
        - supplier_fee
        - verified
        """
        classified_transactions = []
        
        for trans in transactions:
            classified = trans.copy()
            
            if trans['record_type'] == 'spend':
                # 消费分类
                expense_owner, is_supplier, supplier_name = self.classify_expense_owner(
                    trans['description']
                )
                classified['expense_owner'] = expense_owner
                classified['is_supplier_transaction'] = 1 if is_supplier else 0
                classified['supplier_name'] = supplier_name
                
                # 如果是Supplier，计算1% fee
                if is_supplier:
                    classified['supplier_fee'] = self.calculate_supplier_fee(trans['amount'])
                else:
                    classified['supplier_fee'] = 0
                
            elif trans['record_type'] == 'payment':
                # 付款分类（需要额外检查是否有GZ转账）
                # 这里简化处理，实际需要查询gz_transfer_records表
                payment_type, verified = self.classify_payment_type(
                    trans['description'],
                    trans['amount'],
                    trans['customer_id'],
                    trans['statement_month'],
                    has_gz_transfer=False  # TODO: 实际需要查询
                )
                classified['payment_type'] = payment_type
                classified['verified'] = 1 if verified else 0
            
            classified_transactions.append(classified)
        
        return classified_transactions
    
    # ========== 数据库操作 ==========
    
    def save_classified_transaction(self, transaction: Dict) -> int:
        """
        保存分类后的交易到数据库
        
        任务书第4节：月度账单表必须包含所有字段
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monthly_statement_transactions (
                customer_id, statement_month, bank_name, card_last4,
                date, description, amount, record_type, source_doc_type,
                expense_owner, payment_type, category,
                verified, is_supplier_transaction, supplier_name, supplier_fee,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction['customer_id'],
            transaction['statement_month'],
            transaction['bank_name'],
            transaction['card_last4'],
            transaction['date'],
            transaction['description'],
            transaction['amount'],
            transaction['record_type'],
            transaction.get('source_doc_type', 'CC Statement'),
            transaction.get('expense_owner'),
            transaction.get('payment_type'),
            transaction.get('category'),
            transaction.get('verified', 0),
            transaction.get('is_supplier_transaction', 0),
            transaction.get('supplier_name'),
            transaction.get('supplier_fee', 0),
            datetime.now(),
            datetime.now()
        ))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return transaction_id
    
    def get_customer_receiving_accounts(self, customer_id: int) -> List[str]:
        """
        获取客户收款账户
        用于匹配GZ转账记录
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT receiving_account_1, receiving_account_2 
            FROM customers 
            WHERE id = ?
        ''', (customer_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            accounts = [acc for acc in row if acc]
            return accounts
        return []


# ========== 工具函数 ==========

def classify_single_transaction(
    customer_id: int,
    date: str,
    description: str,
    amount: float,
    record_type: str,
    statement_month: str,
    bank_name: str,
    card_last4: str,
    source_doc_type: str = 'CC Statement'
) -> Dict:
    """
    分类单笔交易（便捷函数）
    """
    engine = InfiniteGZClassificationEngine()
    
    transaction = {
        'customer_id': customer_id,
        'date': date,
        'description': description,
        'amount': amount,
        'record_type': record_type,
        'statement_month': statement_month,
        'bank_name': bank_name,
        'card_last4': str(card_last4),
        'source_doc_type': source_doc_type
    }
    
    classified = engine.classify_transaction_batch([transaction])
    return classified[0]


# ========== 测试代码 ==========

if __name__ == '__main__':
    print("=" * 80)
    print("INFINITE GZ 分类引擎测试")
    print("=" * 80)
    
    engine = InfiniteGZClassificationEngine()
    
    # 测试1：Supplier消费分类
    print("\n[测试1] Supplier消费分类:")
    test_transactions = [
        {
            'customer_id': 1,
            'date': '2025-01-15',
            'description': '7sl KEDAI RUNCIT',
            'amount': 500.00,
            'record_type': 'spend',
            'statement_month': '2025-01',
            'bank_name': 'Maybank',
            'card_last4': '1234'
        },
        {
            'customer_id': 1,
            'date': '2025-01-16',
            'description': 'STARBUCKS COFFEE',
            'amount': 25.50,
            'record_type': 'spend',
            'statement_month': '2025-01',
            'bank_name': 'Maybank',
            'card_last4': '1234'
        }
    ]
    
    classified = engine.classify_transaction_batch(test_transactions)
    for trans in classified:
        print(f"  描述: {trans['description']}")
        print(f"  归属: {trans.get('expense_owner', 'N/A')}")
        print(f"  是否Supplier: {'是' if trans.get('is_supplier_transaction') else '否'}")
        if trans.get('supplier_name'):
            print(f"  Supplier: {trans['supplier_name']}")
            print(f"  1% Fee: RM {trans.get('supplier_fee', 0):.2f}")
        print()
    
    # 测试2：Supplier列表
    print("[测试2] Supplier白名单:")
    suppliers = engine.load_supplier_list()
    for supplier in suppliers:
        print(f"  • {supplier}")
    
    # 测试3：GZ银行白名单
    print("\n[测试3] GZ银行白名单:")
    gz_banks = engine.load_gz_bank_list()
    for bank in gz_banks:
        print(f"  • {bank}")
    
    print("\n" + "=" * 80)
    print("✅ 分类引擎测试完成！")
    print("=" * 80)
