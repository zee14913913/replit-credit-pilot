"""
Document AI JSON 字段提取模块
从 Google Document AI 的 entities 中提取 16 个标准字段
"""

from typing import Dict, List, Any, Optional


class DocumentAIExtractor:
    """从 Document AI JSON 中提取信用卡账单字段"""
    
    def __init__(self):
        # 字段映射：Document AI entity type -> 标准字段名
        self.field_mapping = {
            'bank_name': ['bank_name', 'bank', 'issuer'],
            'customer_name': ['customer_name', 'cardholder_name', 'name'],
            'ic_no': ['ic_no', 'ic_number', 'nric', 'identification_number'],
            'card_type': ['card_type', 'card_product', 'product_type'],
            'card_no': ['card_no', 'card_number', 'account_number'],
            'credit_limit': ['credit_limit', 'credit_line', 'limit'],
            'statement_date': ['statement_date', 'billing_date', 'date'],
            'payment_due_date': ['payment_due_date', 'due_date', 'maturity_date'],
            'previous_balance': ['previous_balance', 'opening_balance', 'balance_brought_forward'],
            'current_balance': ['current_balance', 'new_balance', 'total_amount_due', 'closing_balance'],
            'minimum_payment': ['minimum_payment', 'minimum_amount_due', 'min_payment'],
            'earned_point': ['earned_point', 'points', 'reward_points', 'cashback']
        }
    
    def extract_fields(self, doc_ai_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 Document AI JSON 中提取所有字段
        
        Args:
            doc_ai_json: Document AI 返回的完整 JSON
                格式: {"entities": [{"type": "field_name", "mentionText": "value"}]}
        
        Returns:
            标准化的字段字典
        """
        entities = doc_ai_json.get('entities', [])
        
        result = {
            'bank_name': '',
            'customer_name': '',
            'ic_no': '',
            'card_type': '',
            'card_no': '',
            'credit_limit': '',
            'statement_date': '',
            'payment_due_date': '',
            'previous_balance': '',
            'current_balance': '',
            'minimum_payment': '',
            'earned_point': '',
            'transactions': []
        }
        
        # 提取基本字段
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            mention_text = entity.get('mentionText', '').strip()
            
            # 匹配标准字段名
            for standard_field, possible_types in self.field_mapping.items():
                if any(ptype in entity_type for ptype in possible_types):
                    if not result[standard_field]:  # 只取第一个匹配的值
                        result[standard_field] = mention_text
                    break
        
        # 提取交易表格
        result['transactions'] = self._extract_transactions(entities)
        
        return result
    
    def _extract_transactions(self, entities: List[Dict]) -> List[Dict]:
        """
        从 entities 中提取交易记录
        
        Document AI 通常会将表格识别为嵌套的 entities，
        格式类似: {"type": "line_item", "properties": [...]}
        """
        transactions = []
        
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            
            # 查找交易/line_item类型的实体
            if any(keyword in entity_type for keyword in ['transaction', 'line_item', 'purchase']):
                properties = entity.get('properties', [])
                
                transaction = {
                    'transaction_date': '',
                    'transaction_description': '',
                    'amount_CR': 0.0,
                    'amount_DR': 0.0,
                    'earned_point': ''
                }
                
                # 从 properties 中提取字段
                for prop in properties:
                    prop_type = prop.get('type', '').lower()
                    prop_value = prop.get('mentionText', '').strip()
                    
                    if 'date' in prop_type:
                        transaction['transaction_date'] = prop_value
                    elif 'description' in prop_type or 'merchant' in prop_type:
                        transaction['transaction_description'] = prop_value
                    elif 'amount' in prop_type or 'credit' in prop_type or 'debit' in prop_type:
                        # 判断是 CR 还是 DR（优先检查文本中的 CR/DR 标记）
                        amount = self._extract_number(prop_value)
                        prop_value_upper = prop_value.upper()
                        
                        if 'CR' in prop_value_upper or 'CREDIT' in prop_value_upper:
                            transaction['amount_CR'] = amount
                            transaction['amount_DR'] = 0.0
                        elif 'DR' in prop_value_upper or 'DEBIT' in prop_value_upper:
                            transaction['amount_DR'] = amount
                            transaction['amount_CR'] = 0.0
                        elif 'credit' in prop_type.lower():
                            transaction['amount_CR'] = amount
                            transaction['amount_DR'] = 0.0
                        elif 'debit' in prop_type.lower():
                            transaction['amount_DR'] = amount
                            transaction['amount_CR'] = 0.0
                        else:
                            # 默认为 DR（消费）
                            transaction['amount_DR'] = amount
                            transaction['amount_CR'] = 0.0
                    elif 'point' in prop_type:
                        transaction['earned_point'] = prop_value
                
                # 只添加有效的交易（至少有日期或金额）
                if transaction['transaction_date'] or transaction['amount_DR'] > 0 or transaction['amount_CR'] > 0:
                    transactions.append(transaction)
        
        return transactions
    
    def _extract_number(self, text: str) -> float:
        """从文本中提取数字（处理逗号、小数点）"""
        import re
        
        # 移除所有非数字字符（保留小数点和负号）
        cleaned = re.sub(r'[^\d.\-]', '', text)
        
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    
    def extract_from_text_blocks(self, doc_ai_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        备用方法：从 Document AI 的文本块中提取（如果 entities 为空）
        
        Args:
            doc_ai_json: Document AI JSON，包含 "text" 字段
        
        Returns:
            提取的字段字典
        """
        text = doc_ai_json.get('text', '')
        
        # 这里可以实现基于正则表达式的文本提取逻辑
        # 作为 entities 提取失败时的 fallback
        
        return {
            'bank_name': '',
            'customer_name': '',
            'ic_no': '',
            'card_type': '',
            'card_no': '',
            'credit_limit': '',
            'statement_date': '',
            'payment_due_date': '',
            'previous_balance': '',
            'current_balance': '',
            'minimum_payment': '',
            'earned_point': '',
            'transactions': []
        }
