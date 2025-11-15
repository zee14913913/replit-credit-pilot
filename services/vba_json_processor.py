"""
VBA JSON数据处理服务
处理VBA客户端上传的标准JSON数据并入库到SQLite
"""

import sys
sys.path.insert(0, '.')

from db.database import get_db, log_audit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VBAJSONProcessor:
    """VBA JSON数据处理器"""
    
    def __init__(self):
        self.supported_types = ['credit_card', 'bank_statement']
    
    def process_json(self, json_data, user_id=None, filename=''):
        """
        处理VBA JSON数据并入库
        
        Args:
            json_data: VBA解析后的JSON对象
            user_id: 当前用户ID（可选）
            filename: 原始文件名（用于记录）
            
        Returns:
            dict: 处理结果 {
                'success': bool,
                'message': str,
                'statement_id': int,
                'transaction_count': int
            }
        """
        doc_type = json_data.get('document_type')
        
        if doc_type == 'credit_card':
            return self._process_credit_card(json_data, user_id, filename)
        elif doc_type == 'bank_statement':
            return self._process_bank_statement(json_data, user_id, filename)
        else:
            return {
                'success': False,
                'message': f'不支持的document_type: {doc_type}'
            }
    
    def _process_credit_card(self, json_data, user_id, filename):
        """处理信用卡账单JSON"""
        try:
            account_info = json_data.get('account_info', {})
            transactions = json_data.get('transactions', [])
            summary = json_data.get('summary', {})
            
            # 提取关键信息
            owner_name = account_info.get('owner_name', 'Unknown')
            bank_name = account_info.get('bank', 'Unknown')
            card_last_4 = account_info.get('card_last_4', '0000')
            card_type = account_info.get('card_type', 'Unknown')
            statement_date = account_info.get('statement_date', '')
            card_limit = float(account_info.get('card_limit', 0))
            previous_balance = float(account_info.get('previous_balance', 0))
            closing_balance = float(account_info.get('closing_balance', 0))
            
            # 计算statement_month (YYYY-MM格式)
            statement_month = self._parse_statement_month(statement_date)
            
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 1. 查找或创建客户
                customer_id = self._find_or_create_customer(cursor, owner_name)
                
                # 2. 查找或创建信用卡
                card_id = self._find_or_create_credit_card(
                    cursor, customer_id, bank_name, card_last_4, 
                    card_type, card_limit
                )
                
                # 3. 创建或更新月度账单
                monthly_statement_id = self._find_or_create_monthly_statement(
                    cursor, customer_id, bank_name, statement_month,
                    statement_date, previous_balance, closing_balance
                )
                
                # 4. 关联卡片到月度账单
                self._link_card_to_monthly_statement(
                    cursor, monthly_statement_id, card_id, card_last_4,
                    card_type, previous_balance, closing_balance, card_limit
                )
                
                # 5. 插入交易明细
                transaction_count = self._insert_transactions(
                    cursor, monthly_statement_id, transactions
                )
                
                # 6. 更新月度账单统计
                self._update_monthly_statement_stats(
                    cursor, monthly_statement_id, transaction_count, summary
                )
                
                conn.commit()
                
                # 记录审计日志
                if user_id:
                    log_audit(
                        user_id, 
                        'VBA_JSON_UPLOAD', 
                        'monthly_statement', 
                        monthly_statement_id,
                        f'VBA上传信用卡账单: {bank_name} - {statement_month} ({filename})',
                        None
                    )
                
                logger.info(f"✅ 信用卡账单入库成功: {bank_name} {statement_month}, {transaction_count}笔交易")
                
                return {
                    'success': True,
                    'message': '信用卡账单入库成功',
                    'statement_id': monthly_statement_id,
                    'transaction_count': transaction_count,
                    'bank': bank_name,
                    'month': statement_month
                }
        
        except Exception as e:
            logger.error(f"信用卡账单入库失败: {e}")
            return {
                'success': False,
                'message': f'入库失败: {str(e)}'
            }
    
    def _process_bank_statement(self, json_data, user_id, filename):
        """处理银行流水JSON"""
        try:
            account_info = json_data.get('account_info', {})
            transactions = json_data.get('transactions', [])
            summary = json_data.get('summary', {})
            
            # 提取关键信息
            account_holder = account_info.get('account_holder', 'Unknown')
            bank_name = json_data.get('bank_detected', account_info.get('bank', 'Unknown'))
            account_number = account_info.get('account_number', 'N/A')
            account_type = account_info.get('account_type', 'Unknown')
            statement_date = account_info.get('statement_date', '')
            opening_balance = float(account_info.get('opening_balance', 0))
            closing_balance = float(account_info.get('closing_balance', 0))
            
            # 计算statement_month
            statement_month = self._parse_statement_month(statement_date)
            
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 1. 查找或创建客户
                customer_id = self._find_or_create_customer(cursor, account_holder)
                
                # 2. 创建或更新月度账单（银行流水也使用monthly_statements）
                monthly_statement_id = self._find_or_create_monthly_statement(
                    cursor, customer_id, bank_name, statement_month,
                    statement_date, opening_balance, closing_balance
                )
                
                # 3. 插入交易明细
                transaction_count = self._insert_transactions(
                    cursor, monthly_statement_id, transactions
                )
                
                # 4. 更新月度账单统计
                self._update_monthly_statement_stats(
                    cursor, monthly_statement_id, transaction_count, summary
                )
                
                conn.commit()
                
                # 记录审计日志
                if user_id:
                    log_audit(
                        user_id,
                        'VBA_JSON_UPLOAD',
                        'monthly_statement',
                        monthly_statement_id,
                        f'VBA上传银行流水: {bank_name} - {statement_month} ({filename})',
                        None
                    )
                
                logger.info(f"✅ 银行流水入库成功: {bank_name} {statement_month}, {transaction_count}笔交易")
                
                return {
                    'success': True,
                    'message': '银行流水入库成功',
                    'statement_id': monthly_statement_id,
                    'transaction_count': transaction_count,
                    'bank': bank_name,
                    'month': statement_month
                }
        
        except Exception as e:
            logger.error(f"银行流水入库失败: {e}")
            return {
                'success': False,
                'message': f'入库失败: {str(e)}'
            }
    
    def _find_or_create_customer(self, cursor, name):
        """查找或创建客户"""
        # 先尝试查找现有客户
        cursor.execute(
            "SELECT id FROM customers WHERE name = ? COLLATE NOCASE LIMIT 1",
            (name,)
        )
        row = cursor.fetchone()
        
        if row:
            return row[0]
        
        # 创建新客户
        email = f"{name.lower().replace(' ', '_')}@vba.upload"
        cursor.execute(
            """INSERT INTO customers (name, email, phone, created_at) 
               VALUES (?, ?, ?, ?)""",
            (name, email, 'N/A', datetime.now())
        )
        return cursor.lastrowid
    
    def _find_or_create_credit_card(self, cursor, customer_id, bank_name, 
                                    card_last_4, card_type, card_limit):
        """查找或创建信用卡"""
        # 先查找现有卡片
        cursor.execute(
            """SELECT id FROM credit_cards 
               WHERE customer_id = ? AND bank_name = ? AND card_number_last4 = ?
               LIMIT 1""",
            (customer_id, bank_name, card_last_4)
        )
        row = cursor.fetchone()
        
        if row:
            # 更新信用额度
            cursor.execute(
                """UPDATE credit_cards 
                   SET credit_limit = ?, card_type = ?
                   WHERE id = ?""",
                (card_limit, card_type, row[0])
            )
            return row[0]
        
        # 创建新卡片
        cursor.execute(
            """INSERT INTO credit_cards 
               (customer_id, bank_name, card_number_last4, card_type, credit_limit, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (customer_id, bank_name, card_last_4, card_type, card_limit, datetime.now())
        )
        return cursor.lastrowid
    
    def _find_or_create_monthly_statement(self, cursor, customer_id, bank_name,
                                          statement_month, statement_date,
                                          previous_balance, closing_balance):
        """查找或创建月度账单"""
        # 确保monthly_statements表存在
        cursor.execute(
            """SELECT name FROM sqlite_master 
               WHERE type='table' AND name='monthly_statements'"""
        )
        if not cursor.fetchone():
            # 表不存在，创建它
            self._create_monthly_statements_table(cursor)
        
        # 查找现有月度账单
        cursor.execute(
            """SELECT id FROM monthly_statements
               WHERE customer_id = ? AND bank_name = ? AND statement_month = ?
               LIMIT 1""",
            (customer_id, bank_name, statement_month)
        )
        row = cursor.fetchone()
        
        if row:
            # 更新余额
            cursor.execute(
                """UPDATE monthly_statements
                   SET previous_balance_total = ?, 
                       closing_balance_total = ?,
                       period_end_date = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (previous_balance, closing_balance, statement_date, datetime.now(), row[0])
            )
            return row[0]
        
        # 创建新月度账单
        cursor.execute(
            """INSERT INTO monthly_statements
               (customer_id, bank_name, statement_month, period_end_date,
                previous_balance_total, closing_balance_total, 
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (customer_id, bank_name, statement_month, statement_date,
             previous_balance, closing_balance, datetime.now(), datetime.now())
        )
        return cursor.lastrowid
    
    def _link_card_to_monthly_statement(self, cursor, monthly_statement_id, card_id,
                                       card_last_4, card_type, previous_balance,
                                       closing_balance, credit_limit):
        """关联卡片到月度账单"""
        # 确保monthly_statement_cards表存在
        cursor.execute(
            """SELECT name FROM sqlite_master 
               WHERE type='table' AND name='monthly_statement_cards'"""
        )
        if not cursor.fetchone():
            self._create_monthly_statement_cards_table(cursor)
        
        # 检查是否已存在
        cursor.execute(
            """SELECT id FROM monthly_statement_cards
               WHERE monthly_statement_id = ? AND card_id = ?
               LIMIT 1""",
            (monthly_statement_id, card_id)
        )
        row = cursor.fetchone()
        
        if row:
            # 更新
            cursor.execute(
                """UPDATE monthly_statement_cards
                   SET previous_balance = ?, closing_balance = ?, credit_limit = ?
                   WHERE id = ?""",
                (previous_balance, closing_balance, credit_limit, row[0])
            )
        else:
            # 插入
            cursor.execute(
                """INSERT INTO monthly_statement_cards
                   (monthly_statement_id, card_id, card_last4, card_type,
                    previous_balance, closing_balance, credit_limit, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (monthly_statement_id, card_id, card_last_4, card_type,
                 previous_balance, closing_balance, credit_limit, datetime.now())
            )
    
    def _insert_transactions(self, cursor, monthly_statement_id, transactions):
        """插入交易明细"""
        count = 0
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(transactions)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        has_monthly_statement_id = 'monthly_statement_id' in columns
        has_statement_id = 'statement_id' in columns
        statement_id_not_null = False
        
        if has_statement_id:
            # 检查statement_id是否NOT NULL
            for col in cursor.execute("PRAGMA table_info(transactions)").fetchall():
                if col[1] == 'statement_id' and col[3] == 1:  # col[3] is notnull flag
                    statement_id_not_null = True
                    break
        
        # 如果statement_id是NOT NULL但我们要用monthly_statement_id，需要创建临时statement
        temp_statement_id = None
        if statement_id_not_null and has_monthly_statement_id:
            # 创建一个临时statement记录作为兼容
            cursor.execute(
                """INSERT INTO statements 
                   (card_id, statement_date, statement_total, file_path, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (1, datetime.now().strftime('%Y-%m-%d'), 0.0, 'VBA_UPLOAD', datetime.now())
            )
            temp_statement_id = cursor.lastrowid
        
        for txn in transactions:
            # 提取交易数据
            txn_date = txn.get('date', '')
            description = txn.get('description', '')
            
            # 信用卡: amount, dr, cr
            # 银行流水: debit, credit
            debit = float(txn.get('dr', txn.get('debit', 0)))
            credit = float(txn.get('cr', txn.get('credit', 0)))
            amount = float(txn.get('amount', debit if debit > 0 else credit))
            
            category = txn.get('category', 'Uncategorized')
            sub_category = txn.get('sub_category', '')
            
            # 构建SQL
            if has_monthly_statement_id:
                # 新架构：同时插入statement_id和monthly_statement_id
                if temp_statement_id:
                    cursor.execute(
                        """INSERT INTO transactions
                           (statement_id, monthly_statement_id, transaction_date, description, 
                            amount, category, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (temp_statement_id, monthly_statement_id, txn_date, description, amount, 
                         f"{category} - {sub_category}", datetime.now())
                    )
                else:
                    cursor.execute(
                        """INSERT INTO transactions
                           (monthly_statement_id, transaction_date, description, 
                            amount, category, created_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (monthly_statement_id, txn_date, description, amount, 
                         f"{category} - {sub_category}", datetime.now())
                    )
            else:
                # 旧架构：只有statement_id
                if not temp_statement_id:
                    # 创建临时statement
                    cursor.execute(
                        """INSERT INTO statements 
                           (card_id, statement_date, statement_total, file_path, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (1, datetime.now().strftime('%Y-%m-%d'), 0.0, 'VBA_UPLOAD', datetime.now())
                    )
                    temp_statement_id = cursor.lastrowid
                
                cursor.execute(
                    """INSERT INTO transactions
                       (statement_id, transaction_date, description, 
                        amount, category, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (temp_statement_id, txn_date, description, amount,
                     f"{category} - {sub_category}", datetime.now())
                )
            
            count += 1
        
        return count
    
    def _update_monthly_statement_stats(self, cursor, monthly_statement_id, 
                                       transaction_count, summary):
        """更新月度账单统计"""
        # 检查表是否存在transaction_count字段
        cursor.execute("PRAGMA table_info(monthly_statements)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'transaction_count' in columns:
            cursor.execute(
                """UPDATE monthly_statements
                   SET transaction_count = ?, updated_at = ?
                   WHERE id = ?""",
                (transaction_count, datetime.now(), monthly_statement_id)
            )
    
    def _parse_statement_month(self, statement_date):
        """
        解析账单日期，提取YYYY-MM格式
        支持格式: dd-mm-yyyy, yyyy-mm-dd, dd/mm/yyyy等
        """
        if not statement_date:
            return datetime.now().strftime('%Y-%m')
        
        # 尝试多种日期格式
        date_formats = [
            '%d-%m-%Y',  # 25-09-2024
            '%Y-%m-%d',  # 2024-09-25
            '%d/%m/%Y',  # 25/09/2024
            '%Y/%m/%d',  # 2024/09/25
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(statement_date.strip(), fmt)
                return dt.strftime('%Y-%m')
            except ValueError:
                continue
        
        # 无法解析，使用当前年月
        logger.warning(f"无法解析日期 '{statement_date}'，使用当前年月")
        return datetime.now().strftime('%Y-%m')
    
    def _create_monthly_statements_table(self, cursor):
        """创建monthly_statements表（如果不存在）"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                bank_name TEXT NOT NULL,
                statement_month TEXT NOT NULL,
                period_start_date TEXT,
                period_end_date TEXT,
                previous_balance_total REAL DEFAULT 0.0,
                closing_balance_total REAL DEFAULT 0.0,
                owner_balance REAL DEFAULT 0.0,
                gz_balance REAL DEFAULT 0.0,
                owner_expenses REAL DEFAULT 0.0,
                owner_payments REAL DEFAULT 0.0,
                gz_expenses REAL DEFAULT 0.0,
                gz_payments REAL DEFAULT 0.0,
                file_paths TEXT,
                card_count INTEGER DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                validation_score REAL,
                is_confirmed INTEGER DEFAULT 0,
                inconsistencies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(customer_id, bank_name, statement_month),
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created monthly_statements table")
    
    def _create_monthly_statement_cards_table(self, cursor):
        """创建monthly_statement_cards表（如果不存在）"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_statement_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monthly_statement_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                card_last4 TEXT NOT NULL,
                card_type TEXT,
                previous_balance REAL DEFAULT 0.0,
                closing_balance REAL DEFAULT 0.0,
                credit_limit REAL,
                original_statement_id INTEGER,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (monthly_statement_id) REFERENCES monthly_statements(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES credit_cards(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created monthly_statement_cards table")
