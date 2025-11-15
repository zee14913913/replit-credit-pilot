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
    
    def find_available_gz_transfers(
        self,
        customer_id: int,
        statement_month: str,
        payment_amount: float,
        payment_date: str
    ) -> List[Dict]:
        """
        查找可用的GZ转账（有剩余余额）
        
        完整余额追踪系统：
        - 仅返回Card Due Assist类型的转账
        - 仅返回有剩余余额的转账
        - 按转账日期排序（先使用旧的转账）
        
        Returns:
            List of available transfers with remaining_balance
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 查询可用的GZ转账（Card Due Assist + 有余额）
        # 允许±1个月的settlement window
        cursor.execute('''
            SELECT id, source_bank, destination_account, amount, 
                   transfer_date, slip_file_path, purpose, remaining_balance
            FROM gz_transfer_records
            WHERE customer_id = ? 
            AND purpose = 'Card Due Assist'
            AND verified = 1
            AND remaining_balance > 0
            AND (
                strftime('%Y-%m', transfer_date) = ?
                OR strftime('%Y-%m', transfer_date) = date(? || '-01', '-1 month', 'start of month')
                OR strftime('%Y-%m', transfer_date) = date(? || '-01', '+1 month', 'start of month')
            )
            ORDER BY transfer_date ASC
        ''', (customer_id, statement_month[:7], statement_month[:7], statement_month[:7]))
        
        transfers = cursor.fetchall()
        conn.close()
        
        transfer_list = []
        for trans in transfers:
            transfer_list.append({
                'id': trans[0],
                'source_bank': trans[1],
                'destination_account': trans[2],
                'amount': trans[3],
                'transfer_date': trans[4],
                'slip_file_path': trans[5],
                'purpose': trans[6],
                'remaining_balance': trans[7]
            })
        
        return transfer_list
    
    def match_payment_to_transfer(
        self,
        payment_amount: float,
        payment_description: str,
        card_last4: Optional[str],
        available_transfers: List[Dict]
    ) -> Optional[Dict]:
        """
        匹配付款到GZ转账
        
        匹配启发式（满足任意一项即可）：
        1. 金额相近（±20%容差）
        2. 描述包含GZ银行关键词
        
        ⭐ 关键约束：仅匹配 remaining_balance >= payment_amount 的转账
        防止余额变负数
        
        优先使用最早的转账（FIFO原则）
        
        Returns:
            Matched transfer dict or None
        """
        description_lower = payment_description.lower()
        gz_keywords = ['fpx', 'gz', 'yeo', 'tan', 'infinite']
        
        for transfer in available_transfers:
            # ⭐ 硬性约束：余额必须足够
            if transfer['remaining_balance'] < payment_amount:
                continue  # 跳过余额不足的转账
            
            # 启发式1：金额相近（±20%）
            amount_match = (
                payment_amount <= transfer['remaining_balance'] * 1.2 and
                payment_amount >= transfer['remaining_balance'] * 0.5
            )
            
            # 启发式2：描述包含GZ关键词
            description_match = any(kw in description_lower for kw in gz_keywords)
            
            # 如果任意启发式匹配，返回该转账
            if amount_match or description_match:
                return transfer
        
        # ⭐ 兜底：仅使用余额充足的最早转账
        for transfer in available_transfers:
            if transfer['remaining_balance'] >= payment_amount:
                return transfer
        
        # 无匹配
        return None
    
    def allocate_payment_to_transfer(
        self,
        transfer_id: int,
        transaction_id: int,
        allocated_amount: float,
        notes: Optional[str] = None
    ) -> bool:
        """
        分配付款到GZ转账，更新余额
        
        ⭐ 安全guard：防止余额变负数
        
        Returns:
            True if allocation successful, False if insufficient balance
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # ⭐ Guard 1：检查当前余额
            cursor.execute('''
                SELECT remaining_balance 
                FROM gz_transfer_records 
                WHERE id = ?
            ''', (transfer_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                print(f"❌ 转账记录不存在: ID {transfer_id}")
                return False
            
            current_balance = row[0]
            
            # ⭐ Guard 2：防止余额变负数
            if current_balance < allocated_amount:
                conn.close()
                print(f"❌ 余额不足: 剩余RM {current_balance:.2f}，需要RM {allocated_amount:.2f}")
                return False
            
            # 记录分配关联
            cursor.execute('''
                INSERT INTO gz_transfer_payment_links (
                    transfer_id, transaction_id, allocated_amount, notes
                ) VALUES (?, ?, ?, ?)
            ''', (transfer_id, transaction_id, allocated_amount, notes))
            
            # 更新转账剩余余额
            cursor.execute('''
                UPDATE gz_transfer_records
                SET remaining_balance = remaining_balance - ?
                WHERE id = ?
            ''', (allocated_amount, transfer_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ 分配失败: {e}")
            return False
    
    def check_gz_indirect_payment(
        self,
        customer_id: int,
        statement_month: str,
        payment_amount: float,
        payment_date: str,
        payment_description: str,
        card_last4: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        检测GZ's Payment (Indirect) - 完整余额追踪版本
        
        任务书第8.3节：
        - 查找可用的Card Due Assist转账
        - 应用匹配启发式
        - 仅标记可匹配的付款为Indirect
        
        Returns:
            (is_gz_indirect, matched_transfer)
        """
        # 查找可用的GZ转账
        available_transfers = self.find_available_gz_transfers(
            customer_id,
            statement_month,
            payment_amount,
            payment_date
        )
        
        if not available_transfers:
            return (False, None)
        
        # 匹配付款到转账
        matched_transfer = self.match_payment_to_transfer(
            payment_amount,
            payment_description,
            card_last4,
            available_transfers
        )
        
        if matched_transfer:
            return (True, matched_transfer)
        
        return (False, None)
    
    def classify_payment_type(
        self, 
        description: str, 
        amount: float,
        customer_id: int,
        statement_month: str,
        payment_date: str,
        card_last4: Optional[str] = None,
        check_indirect: bool = True
    ) -> Dict:
        """
        完整的付款分类逻辑 - 支持余额追踪
        
        任务书第8节：付款分类（Payment Classification）
        
        Returns:
            {
                'payment_type': str,  # Owner Payment / GZ Direct / GZ Indirect
                'verified': bool,
                'matched_gz_bank': str,  # 如果是Direct
                'matched_transfer': dict  # 如果是Indirect（单个匹配的转账）
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
                    'matched_transfer': None
                }
        
        # 检查GZ Indirect（完整余额追踪）
        if check_indirect:
            is_indirect, matched_transfer = self.check_gz_indirect_payment(
                customer_id,
                statement_month,
                amount,
                payment_date,
                description,
                card_last4
            )
            if is_indirect and matched_transfer:
                return {
                    'payment_type': 'GZ Indirect',
                    'verified': True,
                    'matched_gz_bank': None,
                    'matched_transfer': matched_transfer
                }
        
        # 默认：Owner Payment
        return {
            'payment_type': 'Owner Payment',
            'verified': False,
            'matched_gz_bank': None,
            'matched_transfer': None
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
            - 进入GZ OS Balance
        
        (B) Loan / Credit Assist（借贷）：
            - GZ→客户的资金不是用于信用卡
            - 产生利息
            - 进入Loan Outstanding
        
        判断逻辑：若当月有信用卡CR，则视为Card Due Assist
        
        Returns:
            {
                'purpose': str,  # Card Due Assist / Loan-Credit Assist
                'category': str,
                'affects': str,  # GZ OS Balance / Loan Outstanding
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
                'affects': 'GZ OS Balance',  # ⭐ 修复CHECK约束
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
        初始化remaining_balance = amount
        """
        # 分类转账用途
        classification = self.classify_transfer_purpose(
            customer_id,
            amount,
            transfer_date
        )
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 插入转账记录（包含remaining_balance）
        cursor.execute('''
            INSERT INTO gz_transfer_records (
                customer_id, source_bank, destination_account,
                amount, transfer_date, slip_file_path,
                purpose, verified, affects,
                linked_statement_month, remaining_balance, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
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
            amount,  # ⭐ 初始化remaining_balance = amount
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
            
            # 防御性编程：初始化所有可能的字段为默认值
            classified['expense_owner'] = None
            classified['payment_type'] = None
            classified['is_supplier_transaction'] = 0
            classified['supplier_name'] = None
            classified['supplier_fee'] = 0
            classified['verified'] = 0
            classified['matched_transfers'] = []
            classified['matched_gz_bank'] = None
            
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
                # 付款分类（完整余额追踪）
                payment_result = self.classify_payment_type(
                    trans['description'],
                    trans['amount'],
                    trans['customer_id'],
                    trans['statement_month'],
                    trans.get('date', trans.get('payment_date', '')),  # payment_date
                    trans.get('card_last4'),  # card_last4 (optional)
                    check_indirect=True
                )
                classified['payment_type'] = payment_result.get('payment_type', 'Owner Payment')
                classified['verified'] = 1 if payment_result.get('verified', False) else 0
                
                # 安全提取可选字段
                if payment_result.get('matched_transfer'):
                    classified['matched_transfer'] = payment_result['matched_transfer']
                if payment_result.get('matched_gz_bank'):
                    classified['matched_gz_bank'] = payment_result['matched_gz_bank']
            
            classified_transactions.append(classified)
        
        return classified_transactions
    
    # ========== 数据库操作 ==========
    
    def save_classified_transaction(self, transaction: Dict) -> int:
        """
        保存分类后的交易到数据库
        
        任务书第4节：月度账单表必须包含所有字段
        
        ⭐ 如果payment_type='GZ Indirect'，自动分配到GZ转账并更新余额
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
        
        # ⭐ 如果是GZ Indirect付款，自动分配到转账并更新余额
        if (transaction.get('payment_type') == 'GZ Indirect' and 
            transaction.get('matched_transfer')):
            
            matched_transfer = transaction['matched_transfer']
            allocated_amount = min(transaction['amount'], matched_transfer['remaining_balance'])
            
            allocation_success = self.allocate_payment_to_transfer(
                transfer_id=matched_transfer['id'],
                transaction_id=transaction_id,
                allocated_amount=allocated_amount,
                notes=f"Auto-allocated from payment on {transaction.get('date')}"
            )
            
            # ⭐ 处理分配失败（并发耗尽余额）
            if not allocation_success:
                print(f"⚠️ 分配失败！重新分类为Owner Payment（ID: {transaction_id}）")
                
                # 更新交易分类为Owner Payment
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE monthly_statement_transactions
                    SET payment_type = 'Owner Payment', verified = 0
                    WHERE id = ?
                ''', (transaction_id,))
                conn.commit()
                conn.close()
                
                print(f"✓ 交易已重新分类为Owner Payment")
        
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
