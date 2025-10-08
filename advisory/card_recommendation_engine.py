"""
Credit Card Recommendation Engine
Analyzes customer spending habits and recommends optimal credit cards
"""

from typing import List, Dict, Tuple
from db.database import get_db
from datetime import datetime
import json

class CardRecommendationEngine:
    """智能信用卡推荐引擎"""
    
    def analyze_and_recommend(self, customer_id: int) -> List[Dict]:
        """分析客户消费习惯并推荐最佳信用卡"""
        
        # 1. Analyze spending patterns
        spending_patterns = self._analyze_spending_patterns(customer_id)
        
        # 2. Get customer income
        customer_info = self._get_customer_info(customer_id)
        
        # 3. Find suitable cards
        suitable_cards = self._find_suitable_cards(customer_info['monthly_income'])
        
        # 4. Calculate benefits for each card
        recommendations = []
        for card in suitable_cards:
            match_score, monthly_benefit, reasoning = self._calculate_card_benefit(
                card, spending_patterns
            )
            
            if match_score >= 50:  # Only recommend cards with 50+ match score
                recommendations.append({
                    'card_id': card['id'],
                    'bank_name': card['bank_name'],
                    'card_name': card['card_name'],
                    'match_score': match_score,
                    'estimated_monthly_benefit': monthly_benefit,
                    'annual_benefit': monthly_benefit * 12 - card['annual_fee'],
                    'annual_fee': card['annual_fee'],
                    'reasoning': reasoning,
                    'special_promotions': card['special_promotions']
                })
        
        # 5. Sort by annual benefit (descending)
        recommendations.sort(key=lambda x: x['annual_benefit'], reverse=True)
        
        # 6. Save top 3 recommendations to database
        self._save_recommendations(customer_id, recommendations[:3])
        
        return recommendations[:3]
    
    def _analyze_spending_patterns(self, customer_id: int) -> Dict:
        """分析客户消费模式"""
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get confirmed transactions from last 3 months
            cursor.execute('''
                SELECT t.category, SUM(t.amount) as total, COUNT(*) as count
                FROM transactions t
                INNER JOIN statements s ON t.statement_id = s.id
                INNER JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ? 
                  AND s.is_confirmed = 1
                  AND t.transaction_date >= date('now', '-3 months')
                GROUP BY t.category
            ''', (customer_id,))
            
            category_spending = {}
            total_spending = 0
            
            for row in cursor.fetchall():
                category = row['category']
                total = row['total']
                count = row['count']
                
                # Map categories to card benefit categories
                if 'Dining' in category or 'Food' in category:
                    key = 'dining'
                elif 'Transport' in category or 'Petrol' in category:
                    key = 'petrol'
                elif 'Grocery' in category or 'Supermarket' in category:
                    key = 'grocery'
                elif 'Shopping' in category or 'Online' in category:
                    key = 'online'
                elif 'Travel' in category or 'Flight' in category or 'Hotel' in category:
                    key = 'travel'
                else:
                    key = 'general'
                
                if key not in category_spending:
                    category_spending[key] = 0
                category_spending[key] += total
                total_spending += total
            
            # Calculate monthly average
            for key in category_spending:
                category_spending[key] = category_spending[key] / 3  # 3 months average
            
            category_spending['total'] = total_spending / 3
            
            return category_spending
    
    def _get_customer_info(self, customer_id: int) -> Dict:
        """获取客户信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    def _find_suitable_cards(self, monthly_income: float) -> List[Dict]:
        """查找符合收入要求的信用卡"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM credit_card_products
                WHERE min_income_requirement <= ? AND is_active = 1
                ORDER BY min_income_requirement DESC
            ''', (monthly_income,))
            return [dict(row) for row in cursor.fetchall()]
    
    def _calculate_card_benefit(self, card: Dict, spending: Dict) -> Tuple[float, float, str]:
        """计算信用卡收益和匹配度"""
        
        total_benefit = 0
        benefit_details = []
        
        # Calculate cashback benefits
        categories = ['dining', 'petrol', 'grocery', 'online', 'travel', 'general']
        
        for cat in categories:
            if cat in spending and spending[cat] > 0:
                cashback_rate = card.get(f'cashback_rate_{cat}', 0)
                points_rate = card.get(f'points_rate_{cat}', 0)
                
                # Cashback benefit
                if cashback_rate > 0:
                    cashback = spending[cat] * cashback_rate
                    # Apply monthly cap if exists
                    if card['cashback_cap_monthly'] > 0:
                        cashback = min(cashback, card['cashback_cap_monthly'])
                    total_benefit += cashback
                    if cashback > 10:  # Only mention significant benefits
                        benefit_details.append(f"{cat.title()}: RM{cashback:.2f}/month cashback")
                
                # Points benefit
                if points_rate > 0 and card['points_value'] > 0:
                    points = spending[cat] * points_rate
                    points_value = points * card['points_value']
                    total_benefit += points_value
                    if points_value > 10:
                        benefit_details.append(f"{cat.title()}: {int(points)} points (≈RM{points_value:.2f})")
        
        # Calculate match score (0-100)
        # Based on how well the card matches spending patterns
        if spending.get('total', 0) > 0:
            benefit_rate = total_benefit / spending['total']
            match_score = min(100, benefit_rate * 100 * 10)  # Scale up for visibility
        else:
            match_score = 0
        
        # Boost score for zero annual fee cards
        if card['annual_fee'] == 0:
            match_score = min(100, match_score * 1.1)
        
        # Generate reasoning
        reasoning = f"Based on your spending: {', '.join(benefit_details[:3])}"
        if card['annual_fee'] > 0:
            reasoning += f" | Annual fee: RM{card['annual_fee']}"
        else:
            reasoning += " | FREE - No annual fee!"
        
        return (match_score, total_benefit, reasoning)
    
    def _save_recommendations(self, customer_id: int, recommendations: List[Dict]):
        """保存推荐到数据库"""
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Delete old pending recommendations
            cursor.execute('''
                DELETE FROM card_recommendations 
                WHERE customer_id = ? AND status = 'pending'
            ''', (customer_id,))
            
            # Insert new recommendations
            for rec in recommendations:
                cursor.execute('''
                    INSERT INTO card_recommendations (
                        customer_id, card_product_id, match_score, 
                        estimated_monthly_benefit, recommendation_reason, 
                        spending_analysis, status
                    ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
                ''', (
                    customer_id, rec['card_id'], rec['match_score'],
                    rec['estimated_monthly_benefit'], rec['reasoning'],
                    json.dumps(rec)
                ))
            
            conn.commit()
