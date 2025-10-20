"""
信用卡推荐引擎
Credit Card Recommendation Engine

基于客户消费模式智能推荐最优信用卡
使用100分制评分系统
"""

from typing import Dict, List, Tuple
import sqlite3
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from modules.recommendations.spending_analyzer import SpendingAnalyzer


class CardRecommendationEngine:
    """信用卡智能推荐引擎"""
    
    SCORING_WEIGHTS = {
        'cashback_match': 40,
        'annual_fee': 20,
        'benefits': 20,
        'eligibility': 20
    }
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        self.analyzer = SpendingAnalyzer(db_path)
    
    def recommend_cards(self, customer_id: int, top_n: int = 5) -> List[Dict]:
        """
        为客户推荐信用卡
        
        Args:
            customer_id: 客户ID
            top_n: 返回推荐数量
        
        Returns:
            推荐卡列表，按评分排序
        """
        spending_profile = self.analyzer.get_spending_profile(customer_id)
        customer_tier = self.analyzer.get_customer_tier(customer_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, bank_name, card_name, benefits, usage_tips
            FROM credit_card_products
            WHERE is_active = 1
        ''')
        
        all_cards = cursor.fetchall()
        
        cursor.execute('SELECT monthly_income FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        monthly_income = result[0] if result else 0
        
        conn.close()
        
        scored_cards = []
        
        for card_id, bank, name, benefits, tips in all_cards:
            score, breakdown = self._score_card(
                card_id, bank, name, benefits, tips,
                spending_profile, monthly_income, customer_tier
            )
            
            scored_cards.append({
                'card_id': card_id,
                'bank': bank,
                'card_name': name,
                'score': score,
                'score_breakdown': breakdown,
                'benefits': benefits,
                'usage_tips': tips
            })
        
        scored_cards.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_cards[:top_n]
    
    def _score_card(self, card_id: int, bank: str, name: str, benefits: str, 
                    tips: str, spending_profile: Dict, income: float, tier: str) -> Tuple[float, Dict]:
        """
        评分单张信用卡
        
        Returns:
            (总分, 评分明细)
        """
        cashback_score = self._score_cashback_match(benefits, tips, spending_profile)
        fee_score = self._score_annual_fee(benefits, name)
        benefit_score = self._score_benefits(benefits, tips)
        eligibility_score = self._score_eligibility(name, benefits, income, tier)
        
        total_score = (
            cashback_score * self.SCORING_WEIGHTS['cashback_match'] / 100 +
            fee_score * self.SCORING_WEIGHTS['annual_fee'] / 100 +
            benefit_score * self.SCORING_WEIGHTS['benefits'] / 100 +
            eligibility_score * self.SCORING_WEIGHTS['eligibility'] / 100
        )
        
        breakdown = {
            'cashback_match': round(cashback_score, 1),
            'annual_fee': round(fee_score, 1),
            'benefits': round(benefit_score, 1),
            'eligibility': round(eligibility_score, 1)
        }
        
        return round(total_score, 2), breakdown
    
    def _score_cashback_match(self, benefits: str, tips: str, profile: Dict) -> float:
        """评分返现/奖励匹配度 (0-100)"""
        if not benefits:
            return 30
        
        text = (benefits + ' ' + (tips or '')).lower()
        score = 0
        
        keywords = {
            'dining': ['餐饮', 'dining', 'restaurant', '餐厅'],
            'grocery': ['杂货', 'grocery', 'supermarket', '超市'],
            'petrol': ['加油', 'petrol', 'fuel', '油站'],
            'online': ['线上', 'online', '网购', 'ecommerce'],
            'travel': ['旅行', 'travel', 'hotel', 'flight', '海外'],
            'entertainment': ['娱乐', 'entertainment', 'movie', 'cinema'],
        }
        
        for category, kw_list in keywords.items():
            if profile.get(category, 0) > 0:
                if any(kw in text for kw in kw_list):
                    score += 15
        
        if '5%' in text or '10%' in text or '15%' in text:
            score += 20
        elif '3%' in text or '8%' in text:
            score += 15
        elif '返现' in text or 'cashback' in text or '积分' in text or 'points' in text:
            score += 10
        
        return min(score, 100)
    
    def _score_annual_fee(self, benefits: str, name: str) -> float:
        """评分年费（免年费得分更高）(0-100)"""
        if not benefits:
            return 50
        
        text = (benefits + ' ' + name).lower()
        
        if '终身免年费' in text or 'lifetime free' in text:
            return 100
        elif '免年费' in text or 'free' in text:
            return 90
        elif '首年免' in text or 'first year free' in text:
            return 70
        elif 'rm90' in text or 'rm100' in text or 'rm150' in text:
            return 60
        elif 'rm200' in text or 'rm300' in text:
            return 40
        elif 'rm500' in text or 'rm600' in text:
            return 20
        else:
            return 50
    
    def _score_benefits(self, benefits: str, tips: str) -> float:
        """评分额外福利 (0-100)"""
        if not benefits:
            return 30
        
        text = (benefits + ' ' + (tips or '')).lower()
        score = 0
        
        benefit_keywords = {
            'lounge': ['贵宾厅', 'lounge', 'plaza premium'],
            'insurance': ['保险', 'insurance', 'takaful'],
            'points': ['积分', 'points', 'rewards'],
            'miles': ['里程', 'miles', '航空'],
            'discounts': ['折扣', 'discount', '优惠'],
        }
        
        for benefit_type, kw_list in benefit_keywords.items():
            if any(kw in text for kw in kw_list):
                score += 20
        
        return min(score, 100)
    
    def _score_eligibility(self, name: str, benefits: str, income: float, tier: str) -> float:
        """评分资格匹配度 (0-100)"""
        text = (name + ' ' + (benefits or '')).lower()
        
        if 'platinum' in text or 'infinite' in text or 'world' in text:
            if tier == 'Platinum':
                return 100
            elif tier == 'Gold':
                return 70
            else:
                return 40
        elif 'gold' in text:
            if tier in ['Platinum', 'Gold']:
                return 100
            else:
                return 80
        elif 'classic' in text or 'basic' in text:
            return 100
        else:
            return 85
    
    def compare_current_vs_recommended(self, customer_id: int, current_card_ids: List[int]) -> Dict:
        """
        对比当前信用卡 vs 推荐信用卡
        
        Args:
            customer_id: 客户ID
            current_card_ids: 当前使用的信用卡ID列表（从credit_card_products表）
        
        Returns:
            对比结果
        """
        recommendations = self.recommend_cards(customer_id, top_n=3)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_cards = []
        for card_id in current_card_ids:
            cursor.execute('''
                SELECT bank_name, card_name, benefits
                FROM credit_card_products
                WHERE id = ?
            ''', (card_id,))
            result = cursor.fetchone()
            if result:
                current_cards.append({
                    'card_id': card_id,
                    'bank': result[0],
                    'card_name': result[1],
                    'benefits': result[2]
                })
        
        conn.close()
        
        return {
            'current_cards': current_cards,
            'recommended_cards': recommendations,
            'potential_improvement': self._calculate_improvement(current_cards, recommendations)
        }
    
    def _calculate_improvement(self, current: List[Dict], recommended: List[Dict]) -> Dict:
        """计算潜在改进空间"""
        if not recommended:
            return {'score_improvement': 0, 'message': 'No recommendations available'}
        
        current_avg_score = 60
        recommended_avg_score = recommended[0]['score'] if recommended else 60
        
        improvement = recommended_avg_score - current_avg_score
        
        return {
            'score_improvement': round(improvement, 2),
            'percentage': round((improvement / current_avg_score * 100) if current_avg_score > 0 else 0, 1),
            'message': self._get_improvement_message(improvement)
        }
    
    def _get_improvement_message(self, improvement: float) -> str:
        """根据改进幅度生成消息"""
        if improvement > 20:
            return '🚀 建议立即更换！可大幅提升返现收益'
        elif improvement > 10:
            return '✨ 推荐考虑更换，有较大优化空间'
        elif improvement > 5:
            return '💡 可以考虑更换，有一定优化空间'
        else:
            return '✅ 当前卡片已经较优，暂无需更换'


if __name__ == "__main__":
    engine = CardRecommendationEngine()
    
    print("🎯 信用卡推荐引擎测试\n")
    
    recommendations = engine.recommend_cards(customer_id=1, top_n=5)
    
    print(f"📋 为客户1推荐的Top 5信用卡：\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['bank']} - {rec['card_name'][:60]}")
        print(f"   评分：{rec['score']:.1f}/100")
        print(f"   详细评分：返现匹配{rec['score_breakdown']['cashback_match']:.0f} | "
              f"年费{rec['score_breakdown']['annual_fee']:.0f} | "
              f"福利{rec['score_breakdown']['benefits']:.0f} | "
              f"资格{rec['score_breakdown']['eligibility']:.0f}")
        print()
