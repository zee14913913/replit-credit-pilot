"""
OWNER vs INFINITE Classification Service
根据用户规则对信用卡交易进行分类：
1. 消费分类：OWNER Expenses vs INFINITE Expenses (Supplier)
2. 付款分类：OWNER Payment vs INFINITE Payment
3. 自动计算 INFINITE 消费的 1% 手续费
"""

import sqlite3
from typing import Dict, Tuple, Optional, List

class OwnerInfiniteClassifier:
    """
    核心分类引擎：区分 OWNER 和 INFINITE 的消费与付款
    """
    
    # 7个特定供应商（INFINITE Expenses）
    INFINITE_SUPPLIERS = [
        '7sl',
        'dinas',
        'raub syc hainan',
        'ai smart tech',
        'huawei',
        'pasar raya',
        'puchong herbs'
    ]
    
    # 供应商手续费率
    SUPPLIER_FEE_RATE = 0.01  # 1%
    
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self._load_supplier_config()
        self._load_customer_aliases()
    
    def _load_supplier_config(self):
        """从数据库加载供应商配置（可配置）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查supplier_config表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='supplier_config'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT supplier_name, is_active 
                    FROM supplier_config 
                    WHERE is_active = 1
                """)
                suppliers = cursor.fetchall()
                if suppliers:
                    self.infinite_suppliers = [s[0].lower() for s in suppliers]
                    return
        except Exception as e:
            print(f"Warning: Could not load supplier config: {e}")
        finally:
            conn.close()
        
        # 默认使用预定义列表
        self.infinite_suppliers = self.INFINITE_SUPPLIERS
    
    def _load_customer_aliases(self):
        """加载客户身份别名（用于识别 Owner Payment）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查customer_aliases表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='customer_aliases'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT customer_id, alias 
                    FROM customer_aliases 
                    WHERE is_active = 1
                """)
                aliases = cursor.fetchall()
                self.customer_aliases = {}  # {customer_id: [alias1, alias2, ...]}
                for customer_id, alias in aliases:
                    if customer_id not in self.customer_aliases:
                        self.customer_aliases[customer_id] = []
                    self.customer_aliases[customer_id].append(alias.lower())
            else:
                self.customer_aliases = {}
        except Exception as e:
            print(f"Warning: Could not load customer aliases: {e}")
            self.customer_aliases = {}
        finally:
            conn.close()
    
    def classify_expense(self, description: str, amount: float) -> Dict:
        """
        分类消费交易：OWNER Expenses vs INFINITE Expenses
        
        ⚠️ v5.1新规则：Supplier交易的1%手续费独立计入OWNER账户
        - Supplier本金 → infinite_expense（GZ支付）
        - 1%手续费 → owner_expense（客户支付）
        
        Returns:
            {
                'expense_type': 'owner' or 'infinite',
                'is_supplier': True/False,
                'supplier_name': str or None,
                'supplier_fee': float (1% for infinite expenses),
                'should_split_fee': bool (是否需要拆分手续费)
            }
        """
        if not description:
            return {
                'expense_type': 'owner',
                'is_supplier': False,
                'supplier_name': None,
                'supplier_fee': 0.0,
                'should_split_fee': False
            }
        
        description_lower = description.lower()
        
        # 检查是否匹配供应商名单
        for supplier in self.infinite_suppliers:
            if supplier in description_lower:
                supplier_fee = abs(amount) * self.SUPPLIER_FEE_RATE
                return {
                    'expense_type': 'infinite',
                    'is_supplier': True,
                    'supplier_name': supplier,
                    'supplier_fee': round(supplier_fee, 2),
                    'should_split_fee': True  # 需要拆分手续费
                }
        
        # 未匹配供应商 = OWNER Expenses
        return {
            'expense_type': 'owner',
            'is_supplier': False,
            'supplier_name': None,
            'supplier_fee': 0.0,
            'should_split_fee': False
        }
    
    def create_fee_transaction(self, original_txn: Dict) -> Dict:
        """
        为Supplier交易创建独立的1%手续费记录
        
        Args:
            original_txn: 原始Supplier交易记录
        
        Returns:
            手续费交易记录（owner_expense类型）
        """
        fee_amount = abs(original_txn['amount']) * self.SUPPLIER_FEE_RATE
        
        return {
            'statement_id': original_txn['statement_id'],
            'transaction_date': original_txn['transaction_date'],
            'description': f"{original_txn['description']} - Merchant Fee (1%)",
            'amount': round(fee_amount, 2),
            'category': 'owner_expense',  # 手续费归OWNER
            'transaction_type': 'fee',
            'supplier_fee': round(fee_amount, 2),
            'supplier_name': original_txn.get('supplier_name'),
            'is_supplier': False,  # 手续费本身不是Supplier交易
            'is_merchant_fee': True,  # 标记为手续费记录
            'fee_reference_id': original_txn['id'],  # 关联原始交易
            'is_fee_split': True
        }
    
    def classify_payment(self, description: str, customer_id: int, customer_name: str = None) -> Dict:
        """
        分类付款交易：OWNER Payment vs INFINITE Payment
        
        规则：
        1. 付款人为空 → OWNER Payment
        2. 付款人为客户本人（或客户别名）→ OWNER Payment  
        3. 其他所有付款人 → INFINITE Payment
        
        Returns:
            {
                'payment_type': 'owner' or 'infinite',
                'payer_name': str or None
            }
        """
        if not description:
            # 付款人为空 → OWNER Payment
            return {
                'payment_type': 'owner',
                'payer_name': None
            }
        
        description_lower = description.lower()
        
        # 检查是否包含客户本人姓名
        if customer_name:
            customer_name_lower = customer_name.lower()
            if customer_name_lower in description_lower:
                return {
                    'payment_type': 'owner',
                    'payer_name': customer_name
                }
        
        # 检查客户别名
        if customer_id in self.customer_aliases:
            for alias in self.customer_aliases[customer_id]:
                if alias in description_lower:
                    return {
                        'payment_type': 'owner',
                        'payer_name': alias
                    }
        
        # 提取付款人名称（尝试从描述中解析）
        payer_name = self._extract_payer_name(description)
        
        # 如果无法提取有效付款人（payer_name == None）→ OWNER Payment
        if payer_name is None:
            return {
                'payment_type': 'owner',
                'payer_name': None
            }
        
        # 有明确的第三方付款人 → INFINITE Payment
        return {
            'payment_type': 'infinite',
            'payer_name': payer_name
        }
    
    def _extract_payer_name(self, description: str) -> Optional[str]:
        """尝试从描述中提取付款人名称"""
        import re
        
        # 常见格式: "PAYMENT FROM XXX", "PAYMENT BY YYY", etc.
        # 如果无法提取有效付款人名称，返回 None（视为付款人为空）
        
        # 需要过滤的无效关键词（这些不是真正的付款人）
        INVALID_PAYER_KEYWORDS = [
            'thank', 'you', 'ib', 'online', 'atm', 'bank', 'received',
            'auto', 'autopay', 'giro', 'fpx', 'duitnow', 'transfer',
            'payment', 'bayaran', 'terima', 'cash', 'cheque'
        ]
        
        patterns = [
            r'FROM\s+([A-Z][A-Z\s]+)',
            r'BY\s+([A-Z][A-Z\s]+)',
            r'PAY(?:MENT)?\s+BY\s+([A-Z][A-Z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                payer = match.group(1).strip()
                # 过滤掉无效关键词
                payer_clean = payer.upper().replace('-', ' ').strip()
                
                # 检查是否为无效付款人
                is_invalid = any(keyword.upper() in payer_clean for keyword in INVALID_PAYER_KEYWORDS)
                
                if not is_invalid and len(payer_clean) > 3:
                    return payer
        
        # 无法提取有效付款人 → 返回None（视为付款人为空 = OWNER Payment）
        return None
    
    def classify_transaction(self, 
                           transaction_id: int,
                           description: str,
                           amount: float,
                           transaction_type: str,
                           customer_id: int,
                           customer_name: str = None) -> Dict:
        """
        完整分类单笔交易
        
        Args:
            transaction_id: 交易ID
            description: 交易描述
            amount: 交易金额（正数=支出，负数=收入/付款）
            transaction_type: 'debit' or 'credit'
            customer_id: 客户ID
            customer_name: 客户姓名
        
        Returns:
            {
                'transaction_id': int,
                'category': 'owner_expense' | 'infinite_expense' | 'owner_payment' | 'infinite_payment',
                'is_supplier': bool,
                'supplier_name': str or None,
                'supplier_fee': float,
                'payer_name': str or None
            }
        """
        result = {
            'transaction_id': transaction_id,
            'category': None,
            'is_supplier': False,
            'supplier_name': None,
            'supplier_fee': 0.0,
            'payer_name': None
        }
        
        # 判断是付款还是消费（支持多种transaction_type格式）
        is_payment = (
            transaction_type and 
            transaction_type.upper() in ['CREDIT', 'PAYMENT', 'CR']
        ) or amount < 0
        
        if is_payment:
            # 付款/还款交易
            payment_class = self.classify_payment(description, customer_id, customer_name)
            result['category'] = f"{payment_class['payment_type']}_payment"
            result['payer_name'] = payment_class['payer_name']
        
        else:  # debit
            # 消费交易
            expense_class = self.classify_expense(description, amount)
            result['category'] = f"{expense_class['expense_type']}_expense"
            result['is_supplier'] = expense_class['is_supplier']
            result['supplier_name'] = expense_class['supplier_name']
            result['supplier_fee'] = expense_class['supplier_fee']
        
        return result
    
    def batch_classify_statement(self, statement_id: int) -> Dict:
        """
        批量分类某个账单的所有交易
        
        Returns:
            {
                'classified_count': int,
                'owner_expenses': float,
                'infinite_expenses': float,
                'total_supplier_fees': float,
                'owner_payments': float,
                'infinite_payments': float
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取账单所属客户信息
        cursor.execute('''
            SELECT c.id, c.name
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            JOIN customers c ON cc.customer_id = c.id
            WHERE s.id = ?
        ''', (statement_id,))
        
        customer = cursor.fetchone()
        if not customer:
            conn.close()
            return {'error': 'Statement not found'}
        
        customer_id = customer['id']
        customer_name = customer['name']
        
        # 获取所有交易
        cursor.execute('''
            SELECT id, description, amount, transaction_type
            FROM transactions
            WHERE statement_id = ?
        ''', (statement_id,))
        
        transactions = cursor.fetchall()
        
        # 分类统计
        classified_count = 0
        owner_expenses = 0.0
        infinite_expenses = 0.0
        total_supplier_fees = 0.0
        owner_payments = 0.0
        infinite_payments = 0.0
        
        for txn in transactions:
            classification = self.classify_transaction(
                txn['id'],
                txn['description'],
                txn['amount'],
                txn['transaction_type'],
                customer_id,
                customer_name
            )
            
            # 更新数据库
            cursor.execute('''
                UPDATE transactions
                SET 
                    category = ?,
                    is_supplier = ?,
                    supplier_name = ?,
                    supplier_fee = ?,
                    payer_name = ?
                WHERE id = ?
            ''', (
                classification['category'],
                classification['is_supplier'],
                classification['supplier_name'],
                classification['supplier_fee'],
                classification['payer_name'],
                txn['id']
            ))
            
            # 累计统计
            if classification['category'] == 'owner_expense':
                owner_expenses += abs(txn['amount'])
            elif classification['category'] == 'infinite_expense':
                infinite_expenses += abs(txn['amount'])
                total_supplier_fees += classification['supplier_fee']
            elif classification['category'] == 'owner_payment':
                owner_payments += abs(txn['amount'])
            elif classification['category'] == 'infinite_payment':
                infinite_payments += abs(txn['amount'])
            
            classified_count += 1
        
        conn.commit()
        conn.close()
        
        return {
            'classified_count': classified_count,
            'owner_expenses': round(owner_expenses, 2),
            'infinite_expenses': round(infinite_expenses, 2),
            'total_supplier_fees': round(total_supplier_fees, 2),
            'owner_payments': round(owner_payments, 2),
            'infinite_payments': round(infinite_payments, 2)
        }


# 便捷函数
def classify_transaction(transaction_id: int, customer_id: int, customer_name: str = None):
    """分类单个交易"""
    classifier = OwnerInfiniteClassifier()
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT description, amount, transaction_type
        FROM transactions
        WHERE id = ?
    ''', (transaction_id,))
    
    txn = cursor.fetchone()
    conn.close()
    
    if not txn:
        return None
    
    return classifier.classify_transaction(
        transaction_id,
        txn['description'],
        txn['amount'],
        txn['transaction_type'],
        customer_id,
        customer_name
    )


def classify_statement(statement_id: int):
    """分类整个账单"""
    classifier = OwnerInfiniteClassifier()
    return classifier.batch_classify_statement(statement_id)
