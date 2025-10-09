"""
信用卡积分追踪服务
Track credit card points accumulation across statements
"""

from db.database import get_db
from datetime import datetime

class PointsTracker:
    
    def track_statement_points(self, statement_id, points_earned):
        """
        追踪账单积分
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取账单信息
            cursor.execute('''
                SELECT s.card_id, s.statement_date, s.card_full_number
                FROM statements s
                WHERE s.id = ?
            ''', (statement_id,))
            
            statement = cursor.fetchone()
            if not statement:
                return False
            
            card_id = statement['card_id']
            statement_date = statement['statement_date']
            
            # 获取上一期积分
            cursor.execute('''
                SELECT total_points 
                FROM card_points_tracker 
                WHERE card_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (card_id,))
            
            previous_row = cursor.fetchone()
            previous_points = previous_row['total_points'] if previous_row else 0.0
            
            # 计算新的总积分
            total_points = previous_points + points_earned
            
            # 插入新记录
            cursor.execute('''
                INSERT INTO card_points_tracker 
                (card_id, statement_id, previous_points, earned_points, total_points, statement_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (card_id, statement_id, previous_points, points_earned, total_points, statement_date))
            
            # 更新statement表
            cursor.execute('''
                UPDATE statements 
                SET points_earned = ?
                WHERE id = ?
            ''', (points_earned, statement_id))
            
            conn.commit()
            return True
    
    def get_card_points_history(self, card_id):
        """
        获取信用卡积分历史
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    cpt.*,
                    s.statement_date,
                    cc.bank_name,
                    cc.card_type
                FROM card_points_tracker cpt
                JOIN statements s ON cpt.statement_id = s.id
                JOIN credit_cards cc ON cpt.card_id = cc.id
                WHERE cpt.card_id = ?
                ORDER BY cpt.statement_date DESC
            ''', (card_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_total_points(self, customer_id):
        """
        获取客户所有信用卡的总积分
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    cc.id as card_id,
                    cc.bank_name,
                    cc.card_type,
                    cc.last_four,
                    COALESCE(MAX(cpt.total_points), 0) as total_points
                FROM credit_cards cc
                LEFT JOIN card_points_tracker cpt ON cc.id = cpt.card_id
                WHERE cc.customer_id = ?
                GROUP BY cc.id
                ORDER BY cc.bank_name
            ''', (customer_id,))
            
            cards_points = [dict(row) for row in cursor.fetchall()]
            
            # 计算总积分
            total_points = sum(card['total_points'] for card in cards_points)
            
            return {
                'cards': cards_points,
                'total_points': total_points
            }
    
    def suggest_points_redemption(self, total_points):
        """
        根据总积分推荐兑换方案
        """
        suggestions = []
        
        if total_points >= 100000:
            suggestions.append({
                'option': '国际机票',
                'points_required': 80000,
                'value': 'RM 2,000 - RM 3,000',
                'description': '兑换国际往返机票，如吉隆坡-东京'
            })
        
        if total_points >= 50000:
            suggestions.append({
                'option': '国内机票',
                'points_required': 40000,
                'value': 'RM 800 - RM 1,200',
                'description': '兑换马来西亚国内往返机票'
            })
        
        if total_points >= 30000:
            suggestions.append({
                'option': '酒店住宿',
                'points_required': 25000,
                'value': 'RM 600 - RM 1,000',
                'description': '兑换3-5晚酒店住宿'
            })
        
        if total_points >= 15000:
            suggestions.append({
                'option': '现金回扣',
                'points_required': 10000,
                'value': 'RM 100',
                'description': '直接兑换现金回扣到信用卡账户'
            })
        
        if total_points >= 5000:
            suggestions.append({
                'option': '购物礼券',
                'points_required': 5000,
                'value': 'RM 50',
                'description': '兑换商场/超市购物礼券'
            })
        
        if not suggestions:
            suggestions.append({
                'option': '继续累积',
                'points_required': 0,
                'value': f'当前 {int(total_points)} 积分',
                'description': '建议继续累积积分以获得更高价值的兑换选项'
            })
        
        return suggestions


def track_points(statement_id, points_earned):
    """便捷函数：追踪积分"""
    tracker = PointsTracker()
    return tracker.track_statement_points(statement_id, points_earned)

def get_points_summary(customer_id):
    """便捷函数：获取积分汇总"""
    tracker = PointsTracker()
    return tracker.get_customer_total_points(customer_id)

def get_redemption_suggestions(total_points):
    """便捷函数：获取兑换建议"""
    tracker = PointsTracker()
    return tracker.suggest_points_redemption(total_points)
