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
    # ⚠️ 绝对不允许修改此名单 - 遵循 ARCHITECT_CONSTRAINTS.md
    INFINITE_SUPPLIERS = [
        '7sl',
        'dinas',
        'raub syc hainan',
        'ai smart tech',
        'huawei',
        'pasarraya',
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
    
    def classify_expense(self, description: str, amount: float, is_merchant_fee: bool = False, is_fee_split: bool = False) -> Dict:
        """
        分类消费交易：OWNER Expenses vs INFINITE Expenses
        
        ⚠️ v5.1新规则：Supplier交易的1%手续费独立计入OWNER账户
        - Supplier本金 → infinite_expense（GZ支付）
        - 1%手续费 → owner_expense（客户支付）
        
        Args:
            description: 交易描述
            amount: 交易金额
            is_merchant_fee: 是否为手续费交易（防止重复分类）
            is_fee_split: 是否已拆分过
        
        Returns:
            {
                'expense_type': 'owner' or 'infinite',
                'is_supplier': True/False,
                'supplier_name': str or None,
                'supplier_fee': float (1% for infinite expenses),
                'should_split_fee': bool (是否需要拆分手续费)
            }
        """
        # 🔒 CRITICAL FIX: 如果是手续费交易，强制分类为owner_expense
        if is_merchant_fee:
            return {
                'expense_type': 'owner',
                'is_supplier': False,
                'supplier_name': None,
                'supplier_fee': 0.0,
                'should_split_fee': False
            }
        
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
        为Supplier交易创建独立的1%手续费记录（向后兼容方法）
        
        Args:
            original_txn: 原始Supplier交易记录
        
        Returns:
            手续费交易记录（owner_expense类型）
        """
        fee_amount = abs(original_txn['amount']) * self.SUPPLIER_FEE_RATE
        
        return {
            'statement_id': original_txn['statement_id'],
            'transaction_date': original_txn['transaction_date'],
            'description': f"[MERCHANT FEE 1%] {original_txn['description']}",
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
    
    def classify_and_split_supplier_fee(self, transaction_id: int, conn=None, cursor=None) -> Dict:
        """
        完整实现：Supplier交易拆分逻辑 v5.1
        
        规则：
        - Supplier本金 → infinite_expense（GZ支付）
        - 1%手续费 → owner_expense（Owner应付）
        - 生成两条交易：一条"本金"，一条"手续费"
        - 若已拆分（is_fee_split=True），跳过
        
        Args:
            transaction_id: 要处理的交易ID
            conn: 可选的外部数据库连接（用于原子性）
            cursor: 可选的外部游标（用于原子性）
        
        Returns:
            {
                'status': 'success' | 'skipped' | 'error',
                'principal_txn_id': int,
                'fee_txn_id': int or None,
                'principal_amount': float,
                'fee_amount': float,
                'message': str
            }
        """
        # 🔒 FIX: 支持外部DB连接以确保原子性
        external_conn = conn is not None
        if not external_conn:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        
        try:
            # 1. 获取原始交易
            cursor.execute('''
                SELECT * FROM transactions WHERE id = ?
            ''', (transaction_id,))
            
            txn = cursor.fetchone()
            if not txn:
                return {'status': 'error', 'message': 'Transaction not found'}
            
            # 2. 检查是否已拆分
            if txn['is_fee_split']:
                return {'status': 'skipped', 'message': 'Already split'}
            
            # 3. 检查金额是否为支出（amount > 0）- 🔒 FIX: 使用原始金额判断
            original_amount = float(txn['amount'])
            if original_amount <= 0:
                # 负数金额 = 退款/Credit，不拆分手续费
                return {'status': 'skipped', 'message': 'Refund/credit transaction, no fee split'}
            
            amount = abs(original_amount)  # 确保正数用于计算
            
            # 4. 检查是否为Supplier交易
            description = txn['description'] or ''
            if not self._is_supplier_txn(description):
                # 非Supplier，标记为owner_expense
                cursor.execute('''
                    UPDATE transactions
                    SET category = 'owner_expense',
                        is_supplier = 0,
                        supplier_name = NULL,
                        is_fee_split = 0,
                        is_merchant_fee = 0,
                        fee_reference_id = NULL
                    WHERE id = ?
                ''', (transaction_id,))
                if not external_conn:
                    conn.commit()
                return {'status': 'success', 'message': 'Classified as owner_expense'}
            
            # 5. 走Supplier逻辑：本金=INFINITE，手续费=OWNER
            supplier_name = self._find_supplier_name(description)
            principal = round(amount, 2)
            fee = round(amount * self.SUPPLIER_FEE_RATE, 2)
            
            # 6. 更新当前交易为"本金"（INFINITE）
            cursor.execute('''
                UPDATE transactions
                SET category = 'infinite_expense',
                    is_supplier = 1,
                    supplier_name = ?,
                    supplier_fee = ?,
                    is_fee_split = 1,
                    is_merchant_fee = 0,
                    fee_reference_id = NULL
                WHERE id = ?
            ''', (supplier_name, fee, transaction_id))
            
            # 7. 新增"手续费"一条（OWNER）
            cursor.execute('''
                INSERT INTO transactions (
                    statement_id, transaction_date, description, amount,
                    transaction_type, category, is_supplier, supplier_name,
                    supplier_fee, is_merchant_fee, is_fee_split, fee_reference_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                txn['statement_id'],
                txn['transaction_date'],
                f"[MERCHANT FEE 1%] {description}",
                fee,
                'purchase',
                'owner_expense',
                0,  # is_supplier
                None,  # supplier_name
                None,  # supplier_fee
                1,  # is_merchant_fee
                1,  # is_fee_split
                transaction_id  # fee_reference_id
            ))
            
            fee_txn_id = cursor.lastrowid
            
            # 8. 审计日志
            cursor.execute('''
                INSERT INTO audit_logs (
                    user_id, action_type, entity_type, entity_id, description
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                1,  # system user
                'FEE_SPLIT_APPLIED',
                'transactions',
                transaction_id,
                f'Fee split: Principal RM{principal}, Fee RM{fee}, Fee Txn ID {fee_txn_id}'
            ))
            
            # 🔒 FIX: 只在自己创建连接时commit
            if not external_conn:
                conn.commit()
            
            return {
                'status': 'success',
                'principal_txn_id': transaction_id,
                'fee_txn_id': fee_txn_id,
                'principal_amount': principal,
                'fee_amount': fee,
                'message': f'Split completed: Principal RM{principal} + Fee RM{fee}'
            }
        
        except Exception as e:
            # 🔒 FIX: 只在自己创建连接时rollback，外部连接由调用者处理
            if not external_conn:
                conn.rollback()
                conn.close()
            # 外部连接：通过异常传播错误给调用者
            raise
        
        finally:
            # 🔒 FIX: 只在自己创建连接时关闭
            if not external_conn and conn:
                try:
                    conn.close()
                except:
                    pass  # Connection可能已经关闭
    
    def _is_supplier_txn(self, description: str) -> bool:
        """检查是否为Supplier交易"""
        if not description:
            return False
        desc_lower = description.lower()
        return any(s in desc_lower for s in self.infinite_suppliers)
    
    def _find_supplier_name(self, description: str) -> str:
        """从描述中提取Supplier名称"""
        if not description:
            return None
        desc_lower = description.lower()
        for supplier in self.infinite_suppliers:
            if supplier in desc_lower:
                return supplier
        return None
    
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
        
        # 常见格式: "PAYMENT FROM XXX", "PAYMENT BY YYY", "THANK YOU, XXX", etc.
        # 如果无法提取有效付款人名称，返回 None（视为付款人为空）
        
        # 需要过滤的无效关键词（这些不是真正的付款人）
        INVALID_PAYER_KEYWORDS = [
            'ib', 'online', 'atm', 'bank', 'received',
            'auto', 'autopay', 'giro', 'fpx', 'duitnow', 'transfer',
            'payment', 'bayaran', 'terima', 'cash', 'cheque', 'pay'
        ]
        
        patterns = [
            r'THANK\s+YOU,?\s*([A-Z][A-Z\s\.]+?)(?:,|$)',  # 新增：THANK YOU, INFINITE GZ SDN. BH
            r'FROM\s+([A-Z][A-Z\s\.]+)',
            r'BY\s+([A-Z][A-Z\s\.]+)',
            r'PAY(?:MENT)?\s+BY\s+([A-Z][A-Z\s\.]+)',
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
                           customer_name: str = None,
                           is_merchant_fee: bool = False,
                           is_fee_split: bool = False) -> Dict:
        """
        完整分类单笔交易
        
        ⚠️ v5.1 FIX: 添加is_merchant_fee/is_fee_split防护，避免重复分类
        
        Args:
            transaction_id: 交易ID
            description: 交易描述
            amount: 交易金额（正数=支出，负数=收入/付款）
            transaction_type: 'debit' or 'credit'
            customer_id: 客户ID
            customer_name: 客户姓名
            is_merchant_fee: 是否为手续费交易（防护标志）
            is_fee_split: 是否已拆分过
        
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
            # 消费交易 - 传递防护标志
            expense_class = self.classify_expense(description, amount, is_merchant_fee, is_fee_split)
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
        
        # 获取所有交易（包含防护标志）
        cursor.execute('''
            SELECT id, description, amount, transaction_type, 
                   is_merchant_fee, is_fee_split
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
            # 🔒 FIX: 传递防护标志，避免手续费被重复分类
            # sqlite3.Row对象使用[]访问，不是.get()
            try:
                is_merchant_fee = bool(txn['is_merchant_fee']) if txn['is_merchant_fee'] is not None else False
            except (KeyError, IndexError):
                is_merchant_fee = False
            
            try:
                is_fee_split = bool(txn['is_fee_split']) if txn['is_fee_split'] is not None else False
            except (KeyError, IndexError):
                is_fee_split = False
            
            classification = self.classify_transaction(
                txn['id'],
                txn['description'],
                txn['amount'],
                txn['transaction_type'],
                customer_id,
                customer_name,
                is_merchant_fee=is_merchant_fee,
                is_fee_split=is_fee_split
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
            
            # 🔥 CRITICAL: 如果是Supplier交易且flags正确，执行手续费拆分
            if classification.get('is_supplier') and not is_fee_split and not is_merchant_fee and txn['amount'] > 0:
                try:
                    split_result = self.classify_and_split_supplier_fee(txn['id'], conn, cursor)
                    if split_result['status'] == 'success':
                        # 从拆分结果中调整聚合统计
                        fee_amount = split_result.get('fee_amount', 0.0)
                        owner_expenses += fee_amount  # 新生成的手续费交易是owner_expense
                        total_supplier_fees += fee_amount
                except Exception as e:
                    # 回滚并中止
                    conn.rollback()
                    conn.close()
                    return {'error': f'Fee split failed for txn {txn["id"]}: {str(e)}'}
            
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
    """
    分类单个交易（模块级helper）
    
    ⚠️ v5.1 FIX: 加载防护标志，避免手续费被重复分类
    """
    classifier = OwnerInfiniteClassifier()
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 🔒 FIX: 加载防护标志
    cursor.execute('''
        SELECT description, amount, transaction_type, 
               is_merchant_fee, is_fee_split
        FROM transactions
        WHERE id = ?
    ''', (transaction_id,))
    
    txn = cursor.fetchone()
    
    if not txn:
        conn.close()
        return None
    
    # 安全读取标志
    try:
        is_merchant_fee = bool(txn['is_merchant_fee']) if txn['is_merchant_fee'] is not None else False
    except (KeyError, IndexError):
        is_merchant_fee = False
    
    try:
        is_fee_split = bool(txn['is_fee_split']) if txn['is_fee_split'] is not None else False
    except (KeyError, IndexError):
        is_fee_split = False
    
    # 调用分类方法
    result = classifier.classify_transaction(
        transaction_id,
        txn['description'],
        txn['amount'],
        txn['transaction_type'],
        customer_id,
        customer_name,
        is_merchant_fee=is_merchant_fee,
        is_fee_split=is_fee_split
    )
    
    # 🔥 CRITICAL: 如果是Supplier交易且flags正确，执行手续费拆分
    if result and result.get('is_supplier') and not is_fee_split and not is_merchant_fee and txn['amount'] > 0:
        try:
            split_result = classifier.classify_and_split_supplier_fee(transaction_id, conn, cursor)
            conn.commit()
            # 增强返回值
            result['fee_split_status'] = split_result['status']
            result['fee_amount'] = split_result.get('fee_amount', 0.0)
        except Exception as e:
            conn.rollback()
            result['fee_split_status'] = 'error'
            result['fee_split_error'] = str(e)
    
    conn.close()
    return result


def classify_statement(statement_id: int):
    """分类整个账单"""
    classifier = OwnerInfiniteClassifier()
    return classifier.batch_classify_statement(statement_id)


def split_supplier_fees_batch(statement_id: int) -> Dict:
    """
    批量处理账单的所有Supplier交易手续费拆分
    
    Args:
        statement_id: 账单ID
    
    Returns:
        {
            'total_processed': int,
            'split_count': int,
            'skipped_count': int,
            'error_count': int,
            'total_principal': float,
            'total_fees': float,
            'details': List[Dict]
        }
    """
    import sqlite3
    
    classifier = OwnerInfiniteClassifier()
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取账单所有交易
    cursor.execute('''
        SELECT id, description, amount, category, is_fee_split
        FROM transactions
        WHERE statement_id = ?
        ORDER BY id ASC
    ''', (statement_id,))
    
    transactions = cursor.fetchall()
    conn.close()
    
    results = {
        'total_processed': 0,
        'split_count': 0,
        'skipped_count': 0,
        'error_count': 0,
        'total_principal': 0.0,
        'total_fees': 0.0,
        'details': []
    }
    
    for txn in transactions:
        result = classifier.classify_and_split_supplier_fee(txn['id'])
        results['total_processed'] += 1
        
        if result['status'] == 'success' and 'fee_txn_id' in result:
            results['split_count'] += 1
            results['total_principal'] += result.get('principal_amount', 0)
            results['total_fees'] += result.get('fee_amount', 0)
        elif result['status'] == 'skipped':
            results['skipped_count'] += 1
        elif result['status'] == 'error':
            results['error_count'] += 1
        
        results['details'].append({
            'txn_id': txn['id'],
            'description': txn['description'],
            'result': result
        })
    
    return results
