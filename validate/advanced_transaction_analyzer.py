"""
高级交易分析器 - Advanced Transaction Analyzer
用于区分客户和GZ的消费/付款，并计算各自的余额
"""

from db.database import get_db
import json

class AdvancedTransactionAnalyzer:
    
    # 7个特定供应商（INFINITE GZ的消费）
    GZ_SUPPLIERS = [
        '7sl', 'Dinas', 'Raub Syc Hainan', 
        'Ai Smart Tech', 'Huawei', 'Pasar Raya', 'Puchong Herbs'
    ]
    
    def setup_customer_classification(self, customer_id, classification_rules):
        """
        为客户设置自定义分类规则
        
        Args:
            customer_id: 客户ID
            classification_rules: 分类规则列表
                [
                    {
                        'category_name': '个人消费',
                        'category_type': 'debit',
                        'keywords': ['personal', '个人'],
                        'auto_assign_to': 'customer'
                    },
                    ...
                ]
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            for rule in classification_rules:
                cursor.execute('''
                    INSERT OR REPLACE INTO customer_classification_config 
                    (customer_id, category_name, category_type, keywords, auto_assign_to)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    rule['category_name'],
                    rule['category_type'],
                    json.dumps(rule.get('keywords', [])),
                    rule.get('auto_assign_to', 'customer')
                ))
            
            conn.commit()
            return True
    
    def classify_transaction_advanced(self, transaction_id):
        """
        高级分类：区分客户和GZ的交易
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取交易详情
            cursor.execute('''
                SELECT t.*, s.card_id, cc.customer_id
                FROM transactions t
                JOIN statements s ON t.statement_id = s.id
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE t.id = ?
            ''', (transaction_id,))
            
            tx = dict(cursor.fetchone())
            description = tx['description'].lower() if tx['description'] else ''
            
            # 默认归属客户
            belongs_to = 'customer'
            user_name = None
            purpose = None
            
            # 检查是否为GZ供应商消费
            is_gz_supplier = any(
                supplier.lower() in description 
                for supplier in self.GZ_SUPPLIERS
            )
            
            if is_gz_supplier:
                belongs_to = 'gz'
                user_name = 'INFINITE GZ'
                purpose = 'Supplier Purchase'
            else:
                # 检查客户自定义规则
                cursor.execute('''
                    SELECT * FROM customer_classification_config
                    WHERE customer_id = ? AND is_active = 1
                ''', (tx['customer_id'],))
                
                rules = [dict(row) for row in cursor.fetchall()]
                
                for rule in rules:
                    keywords = json.loads(rule['keywords']) if rule['keywords'] else []
                    if any(kw.lower() in description for kw in keywords):
                        belongs_to = rule['auto_assign_to']
                        break
            
            # 更新交易
            cursor.execute('''
                UPDATE transactions 
                SET belongs_to = ?,
                    user_name = ?,
                    purpose = ?
                WHERE id = ?
            ''', (belongs_to, user_name, purpose, transaction_id))
            
            conn.commit()
            return {'belongs_to': belongs_to, 'user_name': user_name, 'purpose': purpose}
    
    def batch_classify_statement_advanced(self, statement_id):
        """
        批量高级分类账单的所有交易
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM transactions WHERE statement_id = ?
            ''', (statement_id,))
            
            transactions = cursor.fetchall()
            
            for tx in transactions:
                self.classify_transaction_advanced(tx['id'])
            
            return len(transactions)
    
    def analyze_statement_balance(self, statement_id):
        """
        分析账单余额：区分客户和GZ的消费/付款
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取账单信息
            cursor.execute('''
                SELECT s.*, cc.customer_id, s.previous_balance
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE s.id = ?
            ''', (statement_id,))
            
            statement = dict(cursor.fetchone())
            customer_id = statement['customer_id']
            previous_balance = statement.get('previous_balance', 0) or 0
            
            # 客户消费（Debit）= previous_balance + 客户的消费交易
            cursor.execute('''
                SELECT COALESCE(SUM(ABS(amount)), 0) as total
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'debit' 
                AND belongs_to = 'customer'
            ''', (statement_id,))
            customer_debit_transactions = cursor.fetchone()['total']
            customer_debit_total = previous_balance + customer_debit_transactions
            
            # 客户付款（Credit）
            cursor.execute('''
                SELECT COALESCE(SUM(ABS(amount)), 0) as total
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'credit' 
                AND belongs_to = 'customer'
            ''', (statement_id,))
            customer_credit_total = cursor.fetchone()['total']
            
            # GZ消费（Debit）
            cursor.execute('''
                SELECT COALESCE(SUM(ABS(amount)), 0) as total
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'debit' 
                AND belongs_to = 'gz'
            ''', (statement_id,))
            gz_debit_total = cursor.fetchone()['total']
            
            # GZ付款（Credit）
            cursor.execute('''
                SELECT COALESCE(SUM(ABS(amount)), 0) as total
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'credit' 
                AND belongs_to = 'gz'
            ''', (statement_id,))
            gz_credit_total = cursor.fetchone()['total']
            
            # Merchant Fee (1% on GZ suppliers)
            cursor.execute('''
                SELECT COALESCE(SUM(supplier_fee), 0) as total
                FROM transactions
                WHERE statement_id = ?
            ''', (statement_id,))
            merchant_fee_total = cursor.fetchone()['total']
            
            # 计算余额
            customer_balance = customer_debit_total - customer_credit_total
            gz_balance = gz_debit_total - gz_credit_total
            statement_total = statement.get('total_amount', 0) or 0
            
            # 保存分析结果
            cursor.execute('''
                INSERT OR REPLACE INTO statement_balance_analysis 
                (statement_id, customer_id, 
                 customer_previous_balance, customer_debit_total, customer_credit_total, customer_balance,
                 gz_debit_total, gz_credit_total, gz_balance,
                 merchant_fee_total, statement_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                statement_id, customer_id,
                previous_balance, customer_debit_total, customer_credit_total, customer_balance,
                gz_debit_total, gz_credit_total, gz_balance,
                merchant_fee_total, statement_total
            ))
            
            conn.commit()
            
            return {
                'statement_id': statement_id,
                'customer': {
                    'previous_balance': previous_balance,
                    'debit_total': customer_debit_total,
                    'credit_total': customer_credit_total,
                    'balance': customer_balance
                },
                'gz': {
                    'debit_total': gz_debit_total,
                    'credit_total': gz_credit_total,
                    'balance': gz_balance
                },
                'merchant_fee_total': merchant_fee_total,
                'statement_total': statement_total
            }
    
    def get_detailed_breakdown(self, statement_id):
        """
        获取详细的交易明细（按消费和付款分组）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 消费明细（Customer）
            cursor.execute('''
                SELECT 
                    transaction_date as date,
                    user_name,
                    purpose,
                    amount,
                    'customer' as belongs_to
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'debit'
                AND belongs_to = 'customer'
                ORDER BY transaction_date
            ''', (statement_id,))
            customer_debit = [dict(row) for row in cursor.fetchall()]
            
            # 消费明细（GZ）
            cursor.execute('''
                SELECT 
                    transaction_date as date,
                    user_name,
                    purpose,
                    amount,
                    supplier_fee,
                    'gz' as belongs_to
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'debit'
                AND belongs_to = 'gz'
                ORDER BY transaction_date
            ''', (statement_id,))
            gz_debit = [dict(row) for row in cursor.fetchall()]
            
            # 付款明细（Customer）
            cursor.execute('''
                SELECT 
                    transaction_date as date,
                    payment_user as user_name,
                    description as purpose,
                    amount,
                    'customer' as belongs_to
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'credit'
                AND belongs_to = 'customer'
                ORDER BY transaction_date
            ''', (statement_id,))
            customer_credit = [dict(row) for row in cursor.fetchall()]
            
            # 付款明细（GZ）
            cursor.execute('''
                SELECT 
                    transaction_date as date,
                    payment_user as user_name,
                    description as purpose,
                    amount,
                    'gz' as belongs_to
                FROM transactions
                WHERE statement_id = ? 
                AND transaction_type = 'credit'
                AND belongs_to = 'gz'
                ORDER BY transaction_date
            ''', (statement_id,))
            gz_credit = [dict(row) for row in cursor.fetchall()]
            
            return {
                'debit': {
                    'customer': customer_debit,
                    'gz': gz_debit
                },
                'credit': {
                    'customer': customer_credit,
                    'gz': gz_credit
                }
            }
    
    def get_monthly_summary(self, customer_id, month):
        """
        获取客户某月的综合汇总
        
        Args:
            customer_id: 客户ID
            month: 月份，格式 'YYYY-MM'
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取该月所有账单
            cursor.execute('''
                SELECT s.id, s.statement_date, s.due_date, cc.bank_name, cc.card_type
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ?
                AND strftime('%Y-%m', s.statement_date) = ?
            ''', (customer_id, month))
            
            statements = [dict(row) for row in cursor.fetchall()]
            
            # 汇总所有账单
            total_customer_debit = 0
            total_customer_credit = 0
            total_gz_debit = 0
            total_gz_credit = 0
            total_merchant_fee = 0
            
            statement_summaries = []
            
            for stmt in statements:
                analysis = self.analyze_statement_balance(stmt['id'])
                statement_summaries.append({
                    'statement': stmt,
                    'analysis': analysis
                })
                
                total_customer_debit += analysis['customer']['debit_total']
                total_customer_credit += analysis['customer']['credit_total']
                total_gz_debit += analysis['gz']['debit_total']
                total_gz_credit += analysis['gz']['credit_total']
                total_merchant_fee += analysis['merchant_fee_total']
            
            return {
                'customer_id': customer_id,
                'month': month,
                'statements': statement_summaries,
                'summary': {
                    'customer': {
                        'total_debit': total_customer_debit,
                        'total_credit': total_customer_credit,
                        'balance': total_customer_debit - total_customer_credit
                    },
                    'gz': {
                        'total_debit': total_gz_debit,
                        'total_credit': total_gz_credit,
                        'balance': total_gz_debit - total_gz_credit
                    },
                    'merchant_fee_total': total_merchant_fee
                }
            }


# 便捷函数
def classify_statement(statement_id):
    """分类账单交易"""
    analyzer = AdvancedTransactionAnalyzer()
    return analyzer.batch_classify_statement_advanced(statement_id)

def analyze_balance(statement_id):
    """分析余额"""
    analyzer = AdvancedTransactionAnalyzer()
    return analyzer.analyze_statement_balance(statement_id)

def get_breakdown(statement_id):
    """获取明细"""
    analyzer = AdvancedTransactionAnalyzer()
    return analyzer.get_detailed_breakdown(statement_id)

def get_monthly_report(customer_id, month):
    """获取月度报告"""
    analyzer = AdvancedTransactionAnalyzer()
    return analyzer.get_monthly_summary(customer_id, month)
