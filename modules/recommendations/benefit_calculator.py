"""
收益计算器
Benefit Calculator for Credit Card Recommendations

计算信用卡返现收益、福利价值和年度节省金额
"""

from typing import Dict, List
import re
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from modules.recommendations.spending_analyzer import SpendingAnalyzer


class BenefitCalculator:
    """信用卡收益计算器"""
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        self.analyzer = SpendingAnalyzer(db_path)
    
    def calculate_card_benefits(self, card_id: int, customer_id: int) -> Dict:
        """
        计算单张信用卡的收益
        
        Args:
            card_id: 信用卡产品ID
            customer_id: 客户ID
        
        Returns:
            收益详情字典
        """
        spending_profile = self.analyzer.get_spending_profile(customer_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bank_name, card_name, benefits, usage_tips
            FROM credit_card_products
            WHERE id = ?
        ''', (card_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'error': 'Card not found'}
        
        bank, card_name, benefits, tips = result
        
        cashback_rates = self._extract_cashback_rates(benefits, tips)
        
        annual_cashback = self._calculate_annual_cashback(spending_profile, cashback_rates)
        annual_fee = self._extract_annual_fee(benefits, card_name)
        benefit_value = self._calculate_benefit_value(benefits, spending_profile)
        
        net_benefit = annual_cashback + benefit_value - annual_fee
        
        return {
            'card_id': card_id,
            'bank': bank,
            'card_name': card_name,
            'annual_cashback': round(annual_cashback, 2),
            'annual_fee': round(annual_fee, 2),
            'benefit_value': round(benefit_value, 2),
            'net_annual_benefit': round(net_benefit, 2),
            'cashback_breakdown': self._get_cashback_breakdown(spending_profile, cashback_rates)
        }
    
    def compare_benefits(self, current_card_id: int, recommended_card_id: int, customer_id: int) -> Dict:
        """
        对比两张卡的收益
        
        Args:
            current_card_id: 当前卡ID
            recommended_card_id: 推荐卡ID
            customer_id: 客户ID
        
        Returns:
            对比结果
        """
        current = self.calculate_card_benefits(current_card_id, customer_id)
        recommended = self.calculate_card_benefits(recommended_card_id, customer_id)
        
        if 'error' in current or 'error' in recommended:
            return {'error': 'Card not found'}
        
        savings = recommended['net_annual_benefit'] - current['net_annual_benefit']
        
        return {
            'current_card': {
                'bank': current['bank'],
                'card_name': current['card_name'],
                'annual_benefit': current['net_annual_benefit']
            },
            'recommended_card': {
                'bank': recommended['bank'],
                'card_name': recommended['card_name'],
                'annual_benefit': recommended['net_annual_benefit']
            },
            'annual_savings': round(savings, 2),
            'savings_percentage': round((savings / abs(current['net_annual_benefit']) * 100) 
                                       if current['net_annual_benefit'] != 0 else 0, 1),
            'recommendation': self._get_recommendation_message(savings)
        }
    
    def _extract_cashback_rates(self, benefits: str, tips: str) -> Dict:
        """从福利描述中提取返现比率"""
        if not benefits:
            return {}
        
        text = (benefits + ' ' + (tips or '')).lower()
        rates = {}
        
        cashback_patterns = [
            (r'(\d+)%\s*返现', 'general'),
            (r'(\d+)%\s*cashback', 'general'),
        ]
        
        for pattern, category in cashback_patterns:
            matches = re.findall(pattern, text)
            if matches:
                rate = max([int(m) for m in matches])
                rates[category] = rate / 100
        
        if '5%' in text or '10%' in text or '15%' in text:
            rates['general'] = 0.05
        elif '3%' in text or '8%' in text:
            rates['general'] = 0.03
        elif '2%' in text:
            rates['general'] = 0.02
        elif '1%' in text:
            rates['general'] = 0.01
        else:
            rates['general'] = 0.005
        
        return rates
    
    def _calculate_annual_cashback(self, spending_profile: Dict, cashback_rates: Dict) -> float:
        """计算年度返现金额"""
        monthly_spending = spending_profile.get('total_monthly', 0)
        annual_spending = monthly_spending * 12
        
        cashback_rate = cashback_rates.get('general', 0.005)
        
        annual_cashback = annual_spending * cashback_rate
        
        cap_monthly = 50
        cap_annual = cap_monthly * 12
        
        return min(annual_cashback, cap_annual)
    
    def _extract_annual_fee(self, benefits: str, card_name: str) -> float:
        """提取年费"""
        if not benefits:
            return 100
        
        text = (benefits + ' ' + card_name).lower()
        
        if '终身免年费' in text or 'lifetime free' in text or '免年费' in text:
            return 0
        
        fee_patterns = [
            r'rm\s*(\d+)',
            r'年费.*?(\d+)',
        ]
        
        for pattern in fee_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return float(matches[0])
        
        if 'platinum' in text or 'infinite' in text:
            return 300
        elif 'gold' in text:
            return 150
        else:
            return 100
    
    def _calculate_benefit_value(self, benefits: str, spending_profile: Dict) -> float:
        """计算额外福利价值"""
        if not benefits:
            return 0
        
        text = benefits.lower()
        value = 0
        
        if 'lounge' in text or '贵宾厅' in text:
            value += 200
        
        if 'insurance' in text or '保险' in text or 'takaful' in text:
            value += 150
        
        if '积分' in text or 'points' in text:
            value += 100
        
        return value
    
    def _get_cashback_breakdown(self, spending_profile: Dict, cashback_rates: Dict) -> Dict:
        """获取返现明细"""
        rate = cashback_rates.get('general', 0.005)
        
        breakdown = {}
        for category, monthly_amount in spending_profile.items():
            if category != 'total_monthly' and monthly_amount > 0:
                annual_cashback = monthly_amount * 12 * rate
                breakdown[category] = round(annual_cashback, 2)
        
        return breakdown
    
    def _get_recommendation_message(self, savings: float) -> str:
        """生成推荐消息"""
        if savings > 1000:
            return f'🚀 强烈推荐更换！每年可节省RM {abs(savings):.2f}'
        elif savings > 500:
            return f'✨ 建议更换，每年可节省RM {abs(savings):.2f}'
        elif savings > 100:
            return f'💡 可考虑更换，每年可节省RM {abs(savings):.2f}'
        elif savings > 0:
            return f'✅ 略有优化，每年可节省RM {abs(savings):.2f}'
        else:
            return f'⚠️ 当前卡片更优，无需更换'


if __name__ == "__main__":
    calc = BenefitCalculator()
    
    print("💰 收益计算器测试\n")
    
    benefit = calc.calculate_card_benefits(card_id=1, customer_id=1)
    
    if 'error' not in benefit:
        print(f"信用卡：{benefit['bank']} - {benefit['card_name']}")
        print(f"年度返现：RM {benefit['annual_cashback']:,.2f}")
        print(f"年费：RM {benefit['annual_fee']:,.2f}")
        print(f"福利价值：RM {benefit['benefit_value']:,.2f}")
        print(f"净收益：RM {benefit['net_annual_benefit']:,.2f}")
    else:
        print("未找到信用卡")
    
    print("\n🔄 对比测试")
    comparison = calc.compare_benefits(current_card_id=1, recommended_card_id=2, customer_id=1)
    
    if 'error' not in comparison:
        print(f"当前卡：{comparison['current_card']['card_name']} - RM {comparison['current_card']['annual_benefit']:.2f}/年")
        print(f"推荐卡：{comparison['recommended_card']['card_name']} - RM {comparison['recommended_card']['annual_benefit']:.2f}/年")
        print(f"年度节省：RM {comparison['annual_savings']:.2f}")
        print(f"{comparison['recommendation']}")
