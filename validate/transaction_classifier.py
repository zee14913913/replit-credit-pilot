"""
Advanced Transaction Classification Service
用于区分消费交易（Debit）和付款交易（Credit）
"""

from db.database import get_db
import re

class TransactionClassifier:
    
    # 7个特定供应商（需要收取1%手续费）
    SUPPLIER_FEE_MERCHANTS = [
        '7sl', 'Dinas', 'Raub Syc Hainan', 
        'Ai Smart Tech', 'Huawei', 'Pasar Raya', 'Puchong Herbs'
    ]
    
    # Shop和Utilities商家
    SHOP_UTILITIES_MERCHANTS = ['Shopee', 'Lazada', 'TNB']
    
    # 付款关键词（用于识别Credit交易）
    PAYMENT_KEYWORDS = [
        'payment', 'bayaran', 'pembayaran', 'paid', 'pay',
        'transfer', 'pemindahan', 'autopay', 'auto-pay',
        'online payment', 'atm payment', 'bank transfer',
        'cash deposit', 'cheque deposit', 'giro',
        'direct debit', 'auto debit', 'fpx', 'duitnow'
    ]
    
    # Owner付款关键词
    OWNER_PAYMENT_KEYWORDS = [
        'owner', 'self', 'own account', 'my account',
        'principal', 'cardholder', 'pemegang kad'
    ]
    
    def classify_transaction(self, description, amount, merchant=None):
        """
        分类交易为Debit或Credit，并确定子类型
        
        Returns:
            dict: {
                'transaction_type': 'debit' or 'credit',
                'transaction_subtype': specific subtype,
                'supplier_fee': calculated fee (if applicable),
                'payment_user': who made payment (for credit transactions)
            }
        """
        result = {
            'transaction_type': 'debit',
            'transaction_subtype': 'others_debit',
            'supplier_fee': 0.0,
            'payment_user': None
        }
        
        description_lower = description.lower() if description else ''
        merchant_lower = merchant.lower() if merchant else ''
        
        # 检查是否为付款交易（Credit）
        is_payment = any(keyword in description_lower for keyword in self.PAYMENT_KEYWORDS)
        
        if is_payment or amount < 0:  # 负数金额通常表示付款/退款
            result['transaction_type'] = 'credit'
            
            # 确定是Owner还是3rd Party付款
            is_owner = any(keyword in description_lower for keyword in self.OWNER_PAYMENT_KEYWORDS)
            
            if is_owner or not any(word in description_lower for word in ['third party', '3rd party', 'pihak ketiga']):
                result['transaction_subtype'] = 'owner_credit'
                result['payment_user'] = 'Owner'
            else:
                result['transaction_subtype'] = '3rd_party_credit'
                # 尝试提取付款人姓名
                result['payment_user'] = self._extract_payment_user(description)
        
        else:  # Debit交易
            # 检查是否为特定供应商（需收取1%手续费）
            supplier_matched = None
            for supplier in self.SUPPLIER_FEE_MERCHANTS:
                if supplier.lower() in description_lower or supplier.lower() in merchant_lower:
                    supplier_matched = supplier
                    break
            
            if supplier_matched:
                result['transaction_subtype'] = 'supplier_debit'
                result['supplier_fee'] = abs(amount) * 0.01  # 1% fee
            
            # 检查是否为Shop/Utilities
            elif any(shop.lower() in description_lower or shop.lower() in merchant_lower 
                    for shop in self.SHOP_UTILITIES_MERCHANTS):
                result['transaction_subtype'] = 'shop_debit'
            
            else:
                result['transaction_subtype'] = 'others_debit'
        
        return result
    
    def _extract_payment_user(self, description):
        """尝试从描述中提取付款人姓名"""
        # 简单实现：查找"FROM"后面的词
        patterns = [
            r'from\s+([A-Z][A-Z\s]+)',
            r'by\s+([A-Z][A-Z\s]+)',
            r'pembayaran\s+oleh\s+([A-Z][A-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return '3rd Party'
    
    def classify_and_save(self, transaction_id):
        """
        分类交易并保存到数据库
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取交易详情
            cursor.execute('''
                SELECT description, amount, merchant 
                FROM transactions 
                WHERE id = ?
            ''', (transaction_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            description, amount, merchant = row['description'], row['amount'], row['merchant']
            
            # 分类
            classification = self.classify_transaction(description, amount, merchant)
            
            # 保存
            cursor.execute('''
                UPDATE transactions 
                SET transaction_type = ?,
                    transaction_subtype = ?,
                    supplier_fee = ?,
                    payment_user = ?,
                    is_processed = 1
                WHERE id = ?
            ''', (
                classification['transaction_type'],
                classification['transaction_subtype'],
                classification['supplier_fee'],
                classification['payment_user'],
                transaction_id
            ))
            
            conn.commit()
            return True
    
    def batch_classify_statement(self, statement_id):
        """
        批量分类某个账单的所有交易
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取所有未处理的交易
            cursor.execute('''
                SELECT id FROM transactions 
                WHERE statement_id = ? AND is_processed = 0
            ''', (statement_id,))
            
            transactions = cursor.fetchall()
            classified_count = 0
            
            for tx in transactions:
                if self.classify_and_save(tx['id']):
                    classified_count += 1
            
            return classified_count
    
    def get_statement_summary(self, statement_id):
        """
        获取账单的分类汇总
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 消费汇总
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN transaction_subtype = 'supplier_debit' THEN ABS(amount) ELSE 0 END) as supplier_debit,
                    SUM(CASE WHEN transaction_subtype = 'supplier_debit' THEN supplier_fee ELSE 0 END) as supplier_fee,
                    SUM(CASE WHEN transaction_subtype = 'shop_debit' THEN ABS(amount) ELSE 0 END) as shop_debit,
                    SUM(CASE WHEN transaction_subtype = 'others_debit' THEN ABS(amount) ELSE 0 END) as others_debit,
                    SUM(CASE WHEN transaction_type = 'debit' THEN ABS(amount) ELSE 0 END) as total_debit
                FROM transactions
                WHERE statement_id = ?
            ''', (statement_id,))
            
            debit_summary = dict(cursor.fetchone())
            
            # 付款汇总
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN transaction_subtype = 'owner_credit' THEN ABS(amount) ELSE 0 END) as owner_credit,
                    SUM(CASE WHEN transaction_subtype = '3rd_party_credit' THEN ABS(amount) ELSE 0 END) as third_party_credit,
                    SUM(CASE WHEN transaction_type = 'credit' THEN ABS(amount) ELSE 0 END) as total_credit
                FROM transactions
                WHERE statement_id = ?
            ''', (statement_id,))
            
            credit_summary = dict(cursor.fetchone())
            
            return {**debit_summary, **credit_summary}
    
    def get_supplier_transactions(self, statement_id):
        """
        获取所有Supplier交易（用于生成发票）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    transaction_date,
                    description,
                    merchant,
                    amount,
                    supplier_fee
                FROM transactions
                WHERE statement_id = ? AND transaction_subtype = 'supplier_debit'
                ORDER BY transaction_date
            ''', (statement_id,))
            
            return [dict(row) for row in cursor.fetchall()]


# 便捷函数
def classify_transaction(transaction_id):
    """分类单个交易"""
    classifier = TransactionClassifier()
    return classifier.classify_and_save(transaction_id)

def classify_statement(statement_id):
    """分类整个账单"""
    classifier = TransactionClassifier()
    return classifier.batch_classify_statement(statement_id)

def get_classification_summary(statement_id):
    """获取分类汇总"""
    classifier = TransactionClassifier()
    return classifier.get_statement_summary(statement_id)
