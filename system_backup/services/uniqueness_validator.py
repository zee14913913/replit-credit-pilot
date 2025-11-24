"""
唯一性验证服务
确保数据不重复：
1. 同名客户不重复（大小写无关）
2. 同客户+同银行+同卡号只能有一张信用卡
3. 同卡+同月份只能有一份账单
4. 同储蓄账户+同月份只能有一份账单
"""

from db.database import get_db
from datetime import datetime

class UniquenessValidator:
    """唯一性验证器"""
    
    @staticmethod
    def check_duplicate_customer(customer_name):
        """
        检查是否有重复客户（大小写无关）
        Returns: (exists, customer_id, existing_name) 或 (False, None, None)
        """
        with get_db() as conn:
            cursor = conn.cursor()
            result = cursor.execute('''
                SELECT id, name FROM customers 
                WHERE UPPER(TRIM(name)) = UPPER(TRIM(?))
                LIMIT 1
            ''', (customer_name,)).fetchone()
            
            if result:
                return (True, result['id'], result['name'])
            return (False, None, None)
    
    @staticmethod
    def check_duplicate_credit_card(customer_id, bank_name, card_last4):
        """
        检查是否有重复信用卡（同客户+同银行+同卡号后4位）
        Returns: (exists, card_id, existing_bank_name) 或 (False, None, None)
        """
        with get_db() as conn:
            cursor = conn.cursor()
            result = cursor.execute('''
                SELECT id, bank_name FROM credit_cards
                WHERE customer_id = ? 
                  AND UPPER(TRIM(bank_name)) = UPPER(TRIM(?))
                  AND TRIM(card_number_last4) = TRIM(?)
                LIMIT 1
            ''', (customer_id, bank_name, card_last4)).fetchone()
            
            if result:
                return (True, result['id'], result['bank_name'])
            return (False, None, None)
    
    @staticmethod
    def check_duplicate_statement(card_id, statement_date):
        """
        检查是否有重复信用卡账单（同卡+同年月）
        Returns: (exists, statement_id, existing_date) 或 (False, None, None)
        """
        # 提取年月（YYYY-MM）
        try:
            year_month = statement_date[:7]  # 取前7个字符 "2025-01"
        except:
            year_month = statement_date
        
        with get_db() as conn:
            cursor = conn.cursor()
            # 查找同卡且同年月的账单
            result = cursor.execute('''
                SELECT id, statement_date FROM statements
                WHERE card_id = ? 
                  AND substr(statement_date, 1, 7) = ?
                LIMIT 1
            ''', (card_id, year_month)).fetchone()
            
            if result:
                return (True, result['id'], result['statement_date'])
            return (False, None, None)
    
    @staticmethod
    def check_duplicate_savings_statement(account_id, statement_date):
        """
        检查是否有重复储蓄账户账单（同账户+同年月）
        Returns: (exists, statement_id, existing_date) 或 (False, None, None)
        """
        try:
            year_month = statement_date[:7]
        except:
            year_month = statement_date
        
        with get_db() as conn:
            cursor = conn.cursor()
            result = cursor.execute('''
                SELECT id, statement_date FROM savings_statements
                WHERE savings_account_id = ? 
                  AND substr(statement_date, 1, 7) = ?
                LIMIT 1
            ''', (account_id, year_month)).fetchone()
            
            if result:
                return (True, result['id'], result['statement_date'])
            return (False, None, None)
    
    @staticmethod
    def get_or_create_customer(customer_name):
        """
        获取或创建客户（防止重复）
        Returns: customer_id
        """
        # 先检查是否存在
        exists, customer_id, existing_name = UniquenessValidator.check_duplicate_customer(customer_name)
        
        if exists:
            return customer_id
        
        # 不存在则创建
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO customers (name) VALUES (?)',
                (customer_name.strip(),)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_or_create_credit_card(customer_id, bank_name, card_last4, credit_limit=0):
        """
        获取或创建信用卡（防止重复）
        Returns: (card_id, is_new)
        """
        # 先检查是否存在
        exists, card_id, existing_bank = UniquenessValidator.check_duplicate_credit_card(
            customer_id, bank_name, card_last4
        )
        
        if exists:
            return (card_id, False)
        
        # 不存在则创建
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, credit_limit)
                VALUES (?, ?, ?, ?)
            ''', (customer_id, bank_name.strip(), card_last4.strip(), credit_limit))
            conn.commit()
            return (cursor.lastrowid, True)
    
    @staticmethod
    def validate_statement_upload(card_id, statement_date):
        """
        验证账单上传是否允许
        Returns: {
            'allowed': bool,
            'reason': str,
            'existing_statement_id': int or None,
            'action': 'create' or 'update'
        }
        """
        exists, stmt_id, existing_date = UniquenessValidator.check_duplicate_statement(
            card_id, statement_date
        )
        
        if exists:
            return {
                'allowed': True,  # 允许，但是update而非create
                'reason': f'该卡已有{existing_date[:7]}月的账单（ID: {stmt_id}），将更新现有记录',
                'existing_statement_id': stmt_id,
                'action': 'update'
            }
        
        return {
            'allowed': True,
            'reason': '新账单，可以创建',
            'existing_statement_id': None,
            'action': 'create'
        }
    
    @staticmethod
    def validate_savings_statement_upload(account_id, statement_date):
        """
        验证储蓄账户账单上传是否允许
        Returns: {
            'allowed': bool,
            'reason': str,
            'existing_statement_id': int or None,
            'action': 'create' or 'update'
        }
        """
        exists, stmt_id, existing_date = UniquenessValidator.check_duplicate_savings_statement(
            account_id, statement_date
        )
        
        if exists:
            return {
                'allowed': True,
                'reason': f'该账户已有{existing_date[:7]}月的账单（ID: {stmt_id}），将更新现有记录',
                'existing_statement_id': stmt_id,
                'action': 'update'
            }
        
        return {
            'allowed': True,
            'reason': '新账单，可以创建',
            'existing_statement_id': None,
            'action': 'create'
        }
