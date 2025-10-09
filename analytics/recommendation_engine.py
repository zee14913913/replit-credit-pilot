"""
个性化推荐引擎 (Personalized Recommendation Engine)
基于客户消费模式的智能推荐

推荐类型：
1. 信用卡推荐（基于消费类别）
2. 供应商优惠推荐
3. 分期付款建议
4. 积分使用建议
"""

from db.database import get_db
from datetime import datetime, timedelta
import json

class RecommendationEngine:
    
    def generate_recommendations(self, customer_id):
        """生成个性化推荐"""
        conn = get_db()
        cursor = conn.cursor()
        
        recommendations = []
        
        # 1. 基于消费模式推荐信用卡
        card_recommendations = self._recommend_credit_cards(cursor, customer_id)
        if card_recommendations:
            recommendations.extend(card_recommendations)
        
        # 2. 基于供应商消费推荐优惠
        supplier_recommendations = self._recommend_supplier_deals(cursor, customer_id)
        if supplier_recommendations:
            recommendations.extend(supplier_recommendations)
        
        # 3. 推荐分期付款
        installment_recommendations = self._recommend_installment(cursor, customer_id)
        if installment_recommendations:
            recommendations.extend(installment_recommendations)
        
        # 4. 积分使用建议
        points_recommendations = self._recommend_points_usage(cursor, customer_id)
        if points_recommendations:
            recommendations.extend(points_recommendations)
        
        conn.close()
        
        return {
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _recommend_credit_cards(self, cursor, customer_id):
        """基于消费模式推荐信用卡"""
        # 获取消费类别分布
        cursor.execute('''
            SELECT category, SUM(amount) as total_spending
            FROM transactions
            WHERE customer_id = ?
            AND transaction_date >= date('now', '-3 months')
            GROUP BY category
            ORDER BY total_spending DESC
            LIMIT 3
        ''', (customer_id,))
        
        top_categories = cursor.fetchall()
        recommendations = []
        
        # 推荐映射
        card_mapping = {
            'Dining': {
                'card': 'Maybank Islamic Visa Infinite',
                'benefit': '餐饮类别高达15%回扣',
                'potential_saving': 0
            },
            'Petrol': {
                'card': 'Petronas CIMB Credit Card',
                'benefit': '汽油类别每升RM0.50回扣',
                'potential_saving': 0
            },
            'Travel': {
                'card': 'HSBC Travel Credit Card',
                'benefit': '旅游类别10倍积分',
                'potential_saving': 0
            },
            'Shopping': {
                'card': 'Grab Mastercard',
                'benefit': '网购8%现金回扣',
                'potential_saving': 0
            }
        }
        
        for cat in top_categories:
            category = cat['category']
            spending = cat['total_spending']
            
            if category in card_mapping:
                card_info = card_mapping[category]
                # 估算节省（假设5%回扣）
                potential_saving = spending * 0.05
                
                recommendations.append({
                    'type': 'credit_card',
                    'priority': 'high',
                    'title': f"推荐：{card_info['card']}",
                    'description': f"您在{category}类别月均消费RM {spending/3:.2f}，使用此卡可获得{card_info['benefit']}",
                    'potential_saving': round(potential_saving, 2),
                    'action': '立即申请',
                    'category': category
                })
        
        return recommendations
    
    def _recommend_supplier_deals(self, cursor, customer_id):
        """推荐供应商优惠"""
        # 获取高频供应商
        cursor.execute('''
            SELECT supplier_name, SUM(amount) as total_spent, COUNT(*) as transactions
            FROM transactions
            WHERE customer_id = ?
            AND supplier_name IS NOT NULL
            AND transaction_date >= date('now', '-3 months')
            GROUP BY supplier_name
            HAVING total_spent > 1000
            ORDER BY total_spent DESC
            LIMIT 5
        ''', (customer_id,))
        
        suppliers = cursor.fetchall()
        recommendations = []
        
        for supplier in suppliers:
            # 假设有优惠信息（实际应该从优惠数据库读取）
            recommendations.append({
                'type': 'supplier_deal',
                'priority': 'medium',
                'title': f"{supplier['supplier_name']} 专属优惠",
                'description': f"您在{supplier['supplier_name']}累计消费RM {supplier['total_spent']:.2f}，现有专属返点优惠",
                'potential_saving': supplier['total_spent'] * 0.03,  # 3%返点
                'action': '查看详情',
                'supplier': supplier['supplier_name']
            })
        
        return recommendations
    
    def _recommend_installment(self, cursor, customer_id):
        """推荐分期付款"""
        # 查找大额单笔交易
        cursor.execute('''
            SELECT id, amount, description, transaction_date
            FROM transactions
            WHERE customer_id = ?
            AND amount > 3000
            AND transaction_date >= date('now', '-30 days')
            ORDER BY amount DESC
            LIMIT 3
        ''', (customer_id,))
        
        large_transactions = cursor.fetchall()
        recommendations = []
        
        for txn in large_transactions:
            # 计算分期后的每月还款
            months = 12
            monthly_payment = txn['amount'] / months
            
            recommendations.append({
                'type': 'installment',
                'priority': 'high',
                'title': f"RM {txn['amount']:.2f} 可分期付款",
                'description': f"{txn['description']}可申请{months}个月免息分期，每月仅需RM {monthly_payment:.2f}",
                'potential_saving': 0,  # 免息所以无额外成本
                'action': '申请分期',
                'transaction_id': txn['id'],
                'monthly_payment': round(monthly_payment, 2)
            })
        
        return recommendations
    
    def _recommend_points_usage(self, cursor, customer_id):
        """推荐积分使用"""
        # 获取积分总额
        cursor.execute('''
            SELECT SUM(points_earned) as total_points
            FROM transactions
            WHERE customer_id = ?
            AND points_earned > 0
        ''', (customer_id,))
        
        points_data = cursor.fetchone()
        total_points = points_data['total_points'] if points_data and points_data['total_points'] else 0
        
        if total_points > 10000:
            # 积分价值（假设1000积分=RM10）
            points_value = total_points / 100
            
            return [{
                'type': 'points_usage',
                'priority': 'medium',
                'title': f"您有 {int(total_points):,} 积分可使用",
                'description': f"积分价值约RM {points_value:.2f}，可兑换现金回扣、旅游优惠或礼品",
                'potential_saving': points_value,
                'action': '兑换积分',
                'points': int(total_points)
            }]
        
        return []
