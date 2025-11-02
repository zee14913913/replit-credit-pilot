"""
Receipt Matcher Service
智能匹配收据到客户和信用卡
"""

import sqlite3
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

class ReceiptMatcher:
    
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
    
    def match_receipt(self, receipt_data: Dict) -> Dict:
        """
        智能匹配收据到客户和信用卡（已禁用自动匹配，需人工确认）
        
        Args:
            receipt_data: {
                'card_last4': str,
                'transaction_date': str,
                'amount': float,
                'merchant_name': str (可选)
            }
        
        Returns:
            dict: {
                'status': 'manual_review_required' | 'no_match' | 'multiple_matches',
                'customer_id': int,
                'card_id': int,
                'matched_transaction_id': int (可选),
                'confidence': float,
                'candidates': list (如果有多个匹配)
            }
        """
        result = {
            'status': 'no_match',
            'customer_id': None,
            'card_id': None,
            'matched_transaction_id': None,
            'confidence': 0.0,
            'candidates': []
        }
        
        card_last4 = receipt_data.get('card_last4')
        if not card_last4:
            return result
        
        # 步骤1: 根据卡号后4位找到信用卡
        cards = self._find_cards_by_last4(card_last4)
        
        if not cards:
            result['status'] = 'no_match'
            return result
        
        if len(cards) == 1:
            # 唯一匹配 - 但需要人工确认（不再自动匹配）
            card = cards[0]
            result['customer_id'] = card['customer_id']
            result['card_id'] = card['card_id']
            result['status'] = 'manual_review_required'  # 改为需要人工审核
            result['confidence'] = 0.8
            
            # 步骤2: 尝试匹配到具体交易
            if receipt_data.get('transaction_date') and receipt_data.get('amount'):
                transaction = self._find_matching_transaction(
                    card['card_id'],
                    receipt_data['transaction_date'],
                    receipt_data['amount'],
                    receipt_data.get('merchant_name')
                )
                
                if transaction:
                    result['matched_transaction_id'] = transaction['transaction_id']
                    result['confidence'] = min(1.0, result['confidence'] + transaction['match_score'])
            
            return result
        
        else:
            # 多个匹配 - 需要人工选择（禁用自动匹配）
            result['status'] = 'manual_review_required'  # 改为需要人工审核
            result['candidates'] = cards
            
            # 如果有日期和金额，找到最佳匹配候选（但不自动应用）
            if receipt_data.get('transaction_date') and receipt_data.get('amount'):
                best_match = self._find_best_match(cards, receipt_data)
                if best_match and best_match['confidence'] >= 0.9:
                    # 提供建议但不自动匹配
                    result['suggested_customer_id'] = best_match['customer_id']
                    result['suggested_card_id'] = best_match['card_id']
                    result['suggested_transaction_id'] = best_match.get('transaction_id')
                    result['confidence'] = best_match['confidence']
            
            return result
    
    def _find_cards_by_last4(self, card_last4: str) -> List[Dict]:
        """根据卡号后4位查找信用卡"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                cc.id as card_id,
                cc.customer_id,
                cc.card_number_last4,
                cc.card_type,
                cc.bank_name,
                c.name as customer_name
            FROM credit_cards cc
            JOIN customers c ON cc.customer_id = c.id
            WHERE cc.card_number_last4 = ?
        """, (card_last4,))
        
        cards = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return cards
    
    def _find_matching_transaction(
        self, 
        card_id: int, 
        transaction_date: str, 
        amount: float,
        merchant_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        查找匹配的交易记录
        允许日期±3天的误差，金额±1%的误差
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 解析日期
        try:
            target_date = datetime.strptime(transaction_date, '%Y-%m-%d')
        except ValueError:
            conn.close()
            return None
        
        # 日期范围：±3天
        date_start = (target_date - timedelta(days=3)).strftime('%Y-%m-%d')
        date_end = (target_date + timedelta(days=3)).strftime('%Y-%m-%d')
        
        # 金额范围：±1%
        amount_min = amount * 0.99
        amount_max = amount * 1.01
        
        cursor.execute("""
            SELECT 
                t.id as transaction_id,
                t.transaction_date,
                t.amount,
                t.description,
                ABS(JULIANDAY(?) - JULIANDAY(t.transaction_date)) as date_diff,
                ABS(t.amount - ?) as amount_diff
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            WHERE s.card_id = ?
                AND t.transaction_date BETWEEN ? AND ?
                AND t.amount BETWEEN ? AND ?
            ORDER BY date_diff ASC, amount_diff ASC
            LIMIT 1
        """, (transaction_date, amount, card_id, date_start, date_end, amount_min, amount_max))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            transaction = dict(row)
            
            # 计算匹配得分
            date_score = max(0, 1.0 - (transaction['date_diff'] / 3.0))  # 日期越近分数越高
            amount_score = max(0, 1.0 - (transaction['amount_diff'] / amount))  # 金额越接近分数越高
            
            # 如果有商家名称，检查是否匹配
            merchant_score = 0.0
            if merchant_name and transaction['description']:
                if merchant_name.lower() in transaction['description'].lower():
                    merchant_score = 0.2
            
            match_score = (date_score * 0.4 + amount_score * 0.4 + merchant_score)
            transaction['match_score'] = match_score
            
            return transaction
        
        return None
    
    def _find_best_match(self, cards: List[Dict], receipt_data: Dict) -> Optional[Dict]:
        """在多个候选卡中找到最佳匹配"""
        best_match = None
        best_score = 0.0
        
        for card in cards:
            transaction = self._find_matching_transaction(
                card['card_id'],
                receipt_data['transaction_date'],
                receipt_data['amount'],
                receipt_data.get('merchant_name')
            )
            
            if transaction and transaction['match_score'] > best_score:
                best_score = transaction['match_score']
                best_match = {
                    'customer_id': card['customer_id'],
                    'card_id': card['card_id'],
                    'transaction_id': transaction['transaction_id'],
                    'confidence': best_score
                }
        
        return best_match
    
    def get_customer_cards(self, customer_id: int) -> List[Dict]:
        """获取客户的所有信用卡"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id as card_id,
                card_type,
                card_number_last4,
                bank_name
            FROM credit_cards
            WHERE customer_id = ?
        """, (customer_id,))
        
        cards = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return cards
    
    def manual_match(
        self, 
        receipt_id: int, 
        customer_id: int, 
        card_id: int,
        transaction_id: Optional[int] = None
    ) -> bool:
        """手动匹配收据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE receipts
                SET customer_id = ?,
                    card_id = ?,
                    matched_transaction_id = ?,
                    match_status = 'manual_matched',
                    match_confidence = 1.0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (customer_id, card_id, transaction_id, receipt_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            
        except Exception as e:
            print(f"❌ 手动匹配失败: {e}")
            success = False
        finally:
            conn.close()
        
        return success


# 便捷函数
def match_receipt(receipt_data: Dict) -> Dict:
    """匹配单个收据"""
    matcher = ReceiptMatcher()
    return matcher.match_receipt(receipt_data)


# 测试代码
if __name__ == "__main__":
    matcher = ReceiptMatcher()
    
    # 测试数据
    test_receipt = {
        'card_last4': '4514',
        'transaction_date': '2024-10-15',
        'amount': 125.50,
        'merchant_name': 'STARBUCKS'
    }
    
    print("=== 测试智能匹配 ===")
    result = matcher.match_receipt(test_receipt)
    print(f"状态: {result['status']}")
    print(f"客户ID: {result['customer_id']}")
    print(f"卡ID: {result['card_id']}")
    print(f"匹配置信度: {result['confidence']:.2f}")
    
    if result['matched_transaction_id']:
        print(f"匹配到交易ID: {result['matched_transaction_id']}")
