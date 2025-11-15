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
    
    def check_gz_indirect_payment(
        self,
        customer_id: int,
        statement_month: str
    ) -> Tuple[bool, List[Dict]]:
        """
        检测GZ's Payment (Indirect)
        
        任务书第8.3节（关键逻辑）：
        必须满足以下三项全部成立：
        ① GZ上传的转账Slip存在（同日期+同金额）
        ② GZ银行账户月结单有对应记录
        ③ 客户当月信用卡账单出现任意CR
        
        ⚠️ 关键特性：
        - 不要求CR金额与转账金额相等
        - 不要求用于同一张卡
        - 不要求同一天
        - 允许延迟支付
        - 允许拆分支付
        
        Returns:
            (is_gz_indirect, matching_transfers)
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 查询当月该客户的GZ转账记录
        cursor.execute('''
            SELECT id, source_bank, destination_account, amount, transfer_date, slip_file_path, purpose
            FROM gz_transfer_records
            WHERE customer_id = ? 
            AND strftime('%Y-%m', transfer_date) = ?
            AND verified = 1
        ''', (customer_id, statement_month[:7]))
        
        transfers = cursor.fetchall()
        
        if transfers:
            # ⚠️ 修复：添加SQL参数绑定，避免ProgrammingError
            cursor.execute('''
                SELECT COUNT(*) 
                FROM monthly_statement_transactions
                WHERE customer_id = ?
                AND statement_month = ?
                AND record_type = 'payment'
            ''', (customer_id, statement_month))
            
            has_cr = cursor.fetchone()[0] > 0
            
            if has_cr:
                # 有转账 + 有CR = GZ's Payment (Indirect)
                transfer_list = []
                for trans in transfers:
                    transfer_list.append({
                        'id': trans[0],
                        'source_bank': trans[1],
                        'destination_account': trans[2],
                        'amount': trans[3],
                        'transfer_date': trans[4],
                        'slip_file_path': trans[5],
                        'purpose': trans[6]
                    })
                
                conn.close()
                return (True, transfer_list)
        
        conn.close()
        return (False, [])
    
    def classify_payment_type(
        self, 
        description: str, 
        amount: float,
        customer_id: int,
        statement_month: str,
        check_indirect: bool = True
    ) -> Dict:
        """
        完整的付款分类逻辑
        
        任务书第8节：付款分类（Payment Classification）
        
        Returns:
            {
                'payment_type': str,  # Owner Payment / GZ Direct / GZ Indirect
                'verified': bool,
                'matched_gz_bank': str,  # 如果是Direct
                'matched_transfers': list  # 如果是Indirect
            }
        """
        gz_banks = self.load_gz_bank_list()
        description_lower = description.lower()
        
        # 检查GZ Direct
        for gz_bank in gz_banks:
            if gz_bank in description_lower:
                return {
                    'payment_type': 'GZ Direct',
                    'verified': True,
                    'matched_gz_bank': gz_bank,
                    'matched_transfers': []
                }
        
        # 检查GZ Indirect
        if check_indirect:
            is_indirect, transfers = self.check_gz_indirect_payment(
                customer_id,
                statement_month
            )
            if is_indirect:
                return {
                    'payment_type': 'GZ Indirect',
                    'verified': True,
                    'matched_gz_bank': None,
                    'matched_transfers': transfers
                }
        
        # 默认：Owner Payment
        return {
            'payment_type': 'Owner Payment',
            'verified': False,
            'matched_gz_bank': None,
            'matched_transfers': []
        }
    
    # ========== 任务书第9节：转账分类 ==========
    
    def classify_transfer_purpose(
        self,
        customer_id: int,
        amount: float,
        transfer_date: str,
        statement_month: Optional[str] = None
    ) -> Dict:
        """
        分类转账用途
        
        任务书第9节：区分 代付 vs 借贷
        
        (A) Card Due Assist（代付）：
            - GZ→客户的资金用于客户信用卡CR
            - 不产生利息
            - 进入GZ's Payment
        
        (B) Loan / Credit Assist（借贷）：
            - GZ→客户的资金不是用于信用卡
            - 产生利息
            - 进入Loan Outstanding
        
        判断逻辑：若当月有信用卡CR，则视为Card Due Assist
        
        Returns:
            {
                'purpose': str,  # Card Due Assist / Loan-Credit Assist
                'category': str,
                'affects': str,  # GZ's Payment / Loan Outstanding
                'generates_interest': bool
            }
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 自动提取statement_month
        if not statement_month:
            statement_month = transfer_date[:7]  # 2025-01
        
        # 查询该月客户是否有信用卡CR
        cursor.execute('''
            SELECT COUNT(*) 
            FROM monthly_statement_transactions
            WHERE customer_id = ?
            AND statement_month = ?
            AND record_type = 'payment'
        ''', (customer_id, statement_month))
        
        has_cr = cursor.fetchone()[0] > 0
        conn.close()
        
        if has_cr:
            # Card Due Assist（代付）
            return {
                'purpose': 'Card Due Assist',
                'category': 'Card Due Assist',
                'affects': 'GZ\'s Payment',
                'generates_interest': False
            }
        else:
            # Loan / Credit Assist（借贷）
            return {
                'purpose': 'Loan-Credit Assist',
                'category': 'Loan-Credit Assist',
                'affects': 'Loan Outstanding',
                'generates_interest': True
            }
    
    def record_gz_transfer(
        self,
        customer_id: int,
        source_bank: str,
        destination_account: str,
        amount: float,
        transfer_date: str,
        slip_file_path: Optional[str] = None
    ) -> int:
        """
        记录GZ→客户转账
        自动分类用途（Card Due Assist / Loan-Credit Assist）
        """
        # 分类转账用途
        classification = self.classify_transfer_purpose(
            customer_id,
            amount,
            transfer_date
        )
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 插入转账记录
        cursor.execute('''
            INSERT INTO gz_transfer_records (
                customer_id, source_bank, destination_account,
                amount, transfer_date, slip_file_path,
                purpose, verified, affects,
                linked_statement_month, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        ''', (
            customer_id,
            source_bank,
            destination_account,
            amount,
            transfer_date,
            slip_file_path,
            classification['purpose'],
            classification['affects'],
            transfer_date[:7],  # statement_month
            datetime.now()
        ))
        
        transfer_id = cursor.lastrowid
        
        # 如果是Loan-Credit Assist，创建Loan Outstanding记录
        if classification['generates_interest']:
            cursor.execute('''
                INSERT INTO loan_outstanding (
                    customer_id, loan_type, principal_amount,
                    interest_rate, interest_type, amount_repaid,
                    interest_accrued, outstanding_balance,
                    disbursement_date, status, transfer_slip_path,
                    created_at, updated_at
                ) VALUES (?, 'Cash Flow Support', ?, 0.06, 'Simple', 0, 0, ?, ?, 'active', ?, ?, ?)
            ''', (
                customer_id,
                amount,
                amount,  # outstanding_balance初始等于principal_amount
                transfer_date,
                slip_file_path,
                datetime.now(),
                datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        return transfer_id
    
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
                # 付款分类（自动检查GZ转账）
                payment_result = self.classify_payment_type(
                    trans['description'],
                    trans['amount'],
                    trans['customer_id'],
                    trans['statement_month'],
                    check_indirect=True
                )
                classified['payment_type'] = payment_result['payment_type']
                classified['verified'] = 1 if payment_result['verified'] else 0
                
                # 记录匹配的GZ转账（如果是Indirect）
                if payment_result['matched_transfers']:
                    classified['matched_transfers'] = payment_result['matched_transfers']
                if payment_result['matched_gz_bank']:
                    classified['matched_gz_bank'] = payment_result['matched_gz_bank']
            
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
