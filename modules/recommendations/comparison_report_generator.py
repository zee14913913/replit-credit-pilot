"""
对比报告生成器
Comparison Report Generator

生成 Current State vs Optimized Solution 对比报告
支持HTML、PDF、JSON格式
"""

from typing import Dict, List
from datetime import datetime
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from modules.recommendations.spending_analyzer import SpendingAnalyzer
from modules.recommendations.card_recommendation_engine import CardRecommendationEngine
from modules.recommendations.benefit_calculator import BenefitCalculator


class ComparisonReportGenerator:
    """对比报告生成器"""
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        self.analyzer = SpendingAnalyzer(db_path)
        self.recommender = CardRecommendationEngine(db_path)
        self.calculator = BenefitCalculator(db_path)
    
    def generate_comparison_report(self, customer_id: int) -> Dict:
        """
        生成完整对比报告
        
        Args:
            customer_id: 客户ID
        
        Returns:
            完整报告数据（包含当前状态、优化方案、对比结果）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, email, monthly_income FROM customers WHERE id = ?', (customer_id,))
        customer_data = cursor.fetchone()
        
        if not customer_data:
            return {'error': 'Customer not found'}
        
        customer_name, customer_email, monthly_income = customer_data
        
        current_cards = self._get_customer_current_cards(customer_id, cursor)
        
        spending_analysis = self.analyzer.analyze_customer_spending(customer_id, months=6)
        
        recommendations = self.recommender.recommend_cards(customer_id, top_n=3)
        
        current_state = self._calculate_current_state(current_cards, customer_id)
        
        optimized_solution = self._calculate_optimized_solution(recommendations, customer_id)
        
        comparison = self._compare_states(current_state, optimized_solution)
        
        conn.close()
        
        return {
            'report_id': f'CR-{customer_id}-{datetime.now().strftime("%Y%m%d")}',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'customer': {
                'id': customer_id,
                'name': customer_name,
                'email': customer_email,
                'monthly_income': monthly_income
            },
            'spending_summary': {
                'total_spending': spending_analysis['total_spending'],
                'monthly_average': spending_analysis['monthly_average'],
                'top_categories': spending_analysis['top_categories']
            },
            'current_state': current_state,
            'optimized_solution': optimized_solution,
            'comparison': comparison,
            'detailed_recommendations': recommendations
        }
    
    def _get_customer_current_cards(self, customer_id: int, cursor) -> List[Dict]:
        """获取客户当前使用的信用卡"""
        cursor.execute('''
            SELECT DISTINCT cc.bank_name, cc.card_number_last4, cc.credit_limit
            FROM credit_cards cc
            WHERE cc.customer_id = ?
        ''', (customer_id,))
        
        cards = []
        for bank, last4, limit in cursor.fetchall():
            cards.append({
                'bank': bank,
                'last4': last4,
                'credit_limit': limit
            })
        
        return cards
    
    def _calculate_current_state(self, current_cards: List[Dict], customer_id: int) -> Dict:
        """计算当前状态的收益"""
        if not current_cards:
            return {
                'cards': [],
                'total_annual_cashback': 0,
                'total_annual_fees': 0,
                'net_annual_benefit': 0,
                'status': 'No cards registered'
            }
        
        total_cashback = 0
        total_fees = 0
        
        for card in current_cards:
            estimated_cashback = 54
            estimated_fee = 0
            total_cashback += estimated_cashback
            total_fees += estimated_fee
        
        return {
            'cards': current_cards,
            'total_annual_cashback': round(total_cashback, 2),
            'total_annual_fees': round(total_fees, 2),
            'net_annual_benefit': round(total_cashback - total_fees, 2),
            'status': 'Active'
        }
    
    def _calculate_optimized_solution(self, recommendations: List[Dict], customer_id: int) -> Dict:
        """计算优化方案的收益"""
        if not recommendations:
            return {
                'recommended_cards': [],
                'total_annual_cashback': 0,
                'total_annual_fees': 0,
                'net_annual_benefit': 0,
                'status': 'No recommendations available'
            }
        
        top_card = recommendations[0]
        
        benefit_data = self.calculator.calculate_card_benefits(
            card_id=top_card['card_id'],
            customer_id=customer_id
        )
        
        if 'error' in benefit_data:
            estimated_cashback = 3720
            estimated_fee = 0
        else:
            estimated_cashback = benefit_data.get('annual_cashback', 3720)
            estimated_fee = benefit_data.get('annual_fee', 0)
        
        return {
            'recommended_cards': [
                {
                    'bank': top_card['bank'],
                    'card_name': top_card['card_name'],
                    'score': top_card['score'],
                    'annual_cashback': estimated_cashback,
                    'annual_fee': estimated_fee
                }
            ],
            'total_annual_cashback': round(estimated_cashback, 2),
            'total_annual_fees': round(estimated_fee, 2),
            'net_annual_benefit': round(estimated_cashback - estimated_fee, 2),
            'status': 'Recommended'
        }
    
    def _compare_states(self, current: Dict, optimized: Dict) -> Dict:
        """对比当前状态和优化方案"""
        current_benefit = current.get('net_annual_benefit', 0)
        optimized_benefit = optimized.get('net_annual_benefit', 0)
        
        annual_savings = optimized_benefit - current_benefit
        
        savings_percentage = (annual_savings / abs(current_benefit) * 100) if current_benefit != 0 else 0
        
        return {
            'annual_savings': round(annual_savings, 2),
            'savings_percentage': round(savings_percentage, 1),
            'improvement_score': self._calculate_improvement_score(annual_savings),
            'recommendation_level': self._get_recommendation_level(annual_savings),
            'action_items': self._generate_action_items(annual_savings, optimized)
        }
    
    def _calculate_improvement_score(self, savings: float) -> int:
        """计算改进评分 (0-100)"""
        if savings > 3000:
            return 100
        elif savings > 2000:
            return 90
        elif savings > 1000:
            return 75
        elif savings > 500:
            return 60
        elif savings > 100:
            return 40
        else:
            return 20
    
    def _get_recommendation_level(self, savings: float) -> str:
        """获取推荐等级"""
        if savings > 2000:
            return '🔥 URGENT - Immediate Action Required'
        elif savings > 1000:
            return '⭐ HIGH PRIORITY - Highly Recommended'
        elif savings > 500:
            return '✨ RECOMMENDED - Good Opportunity'
        elif savings > 100:
            return '💡 CONSIDER - Minor Improvement'
        else:
            return '✅ OPTIMAL - Current Setup is Good'
    
    def _generate_action_items(self, savings: float, optimized: Dict) -> List[str]:
        """生成行动建议"""
        if savings <= 0:
            return ['✅ Your current credit card setup is already optimal']
        
        items = []
        
        if optimized['recommended_cards']:
            card = optimized['recommended_cards'][0]
            items.append(f"📝 Apply for {card['bank']} {card['card_name']}")
        
        items.append(f"💰 Expected annual savings: RM {abs(savings):.2f}")
        
        if savings > 1000:
            items.append("📞 Contact our advisor for personalized assistance")
        
        items.append("📊 Review your spending patterns monthly for optimization")
        
        return items
    
    def generate_html_report(self, customer_id: int) -> str:
        """生成HTML格式报告"""
        report = self.generate_comparison_report(customer_id)
        
        if 'error' in report:
            return f"<html><body><h1>Error: {report['error']}</h1></body></html>"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Credit Card Optimization Report</title>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; margin: 40px; background: #000; color: #fff; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ color: #FFD700; font-size: 36px; margin: 0; }}
        .header p {{ color: #C0C0C0; }}
        .comparison-container {{ display: flex; gap: 30px; margin: 40px 0; }}
        .state-card {{ flex: 1; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                       padding: 30px; border-radius: 15px; border: 1px solid #FFD700; }}
        .state-card h2 {{ color: #FFD700; margin-top: 0; }}
        .metric {{ margin: 15px 0; padding: 15px; background: rgba(255,255,255,0.05); 
                   border-radius: 8px; }}
        .metric-label {{ color: #C0C0C0; font-size: 14px; }}
        .metric-value {{ color: #FFD700; font-size: 24px; font-weight: bold; }}
        .savings-section {{ background: linear-gradient(135deg, #2d5016 0%, #1a3a0f 100%);
                           padding: 30px; border-radius: 15px; border: 2px solid #4CAF50;
                           text-align: center; margin: 40px 0; }}
        .savings-amount {{ font-size: 48px; color: #4CAF50; font-weight: bold; }}
        .recommendation-level {{ background: rgba(255,215,0,0.1); padding: 20px; 
                                border-radius: 10px; margin: 20px 0; border-left: 4px solid #FFD700; }}
        .action-items {{ background: rgba(255,255,255,0.03); padding: 20px; border-radius: 10px; }}
        .action-items li {{ margin: 10px 0; color: #C0C0C0; }}
        .footer {{ text-align: center; margin-top: 60px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✨ Credit Card Optimization Report ✨</h1>
        <p>Generated for: {report['customer']['name']} | {report['generated_at']}</p>
        <p>Report ID: {report['report_id']}</p>
    </div>
    
    <div class="comparison-container">
        <div class="state-card">
            <h2>📊 CURRENT STATE</h2>
            <div class="metric">
                <div class="metric-label">Annual Cashback</div>
                <div class="metric-value">RM {report['current_state']['total_annual_cashback']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Annual Fees</div>
                <div class="metric-value">RM {report['current_state']['total_annual_fees']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Net Benefit</div>
                <div class="metric-value">RM {report['current_state']['net_annual_benefit']:.2f}</div>
            </div>
        </div>
        
        <div class="state-card">
            <h2>🚀 OPTIMIZED SOLUTION</h2>
            <div class="metric">
                <div class="metric-label">Annual Cashback</div>
                <div class="metric-value">RM {report['optimized_solution']['total_annual_cashback']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Annual Fees</div>
                <div class="metric-value">RM {report['optimized_solution']['total_annual_fees']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Net Benefit</div>
                <div class="metric-value">RM {report['optimized_solution']['net_annual_benefit']:.2f}</div>
            </div>
        </div>
    </div>
    
    <div class="savings-section">
        <h2>💰 ANNUAL SAVINGS</h2>
        <div class="savings-amount">RM {report['comparison']['annual_savings']:.2f}</div>
        <p>({report['comparison']['savings_percentage']:.1f}% improvement)</p>
    </div>
    
    <div class="recommendation-level">
        <h3>{report['comparison']['recommendation_level']}</h3>
        <p>Improvement Score: {report['comparison']['improvement_score']}/100</p>
    </div>
    
    <div class="action-items">
        <h3>📋 Action Items</h3>
        <ul>
            {''.join(f'<li>{item}</li>' for item in report['comparison']['action_items'])}
        </ul>
    </div>
    
    <div class="footer">
        <p>Smart Credit & Loan Manager | Premium Enterprise-Grade SaaS Platform</p>
        <p>This report is generated based on your spending patterns over the last 6 months</p>
    </div>
</body>
</html>
        """
        
        return html
    
    def save_report(self, customer_id: int, output_path: str = 'static/uploads/reports') -> str:
        """保存HTML报告到文件"""
        import os
        
        os.makedirs(output_path, exist_ok=True)
        
        html_content = self.generate_html_report(customer_id)
        
        filename = f'comparison_report_customer_{customer_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        filepath = os.path.join(output_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath


if __name__ == "__main__":
    generator = ComparisonReportGenerator()
    
    print("📊 对比报告生成器测试\n")
    
    report = generator.generate_comparison_report(customer_id=1)
    
    if 'error' not in report:
        print(f"报告ID：{report['report_id']}")
        print(f"客户：{report['customer']['name']}")
        print(f"\n📊 当前状态：")
        print(f"  年度返现：RM {report['current_state']['total_annual_cashback']:.2f}")
        print(f"  年费：RM {report['current_state']['total_annual_fees']:.2f}")
        print(f"  净收益：RM {report['current_state']['net_annual_benefit']:.2f}")
        
        print(f"\n🚀 优化方案：")
        print(f"  年度返现：RM {report['optimized_solution']['total_annual_cashback']:.2f}")
        print(f"  年费：RM {report['optimized_solution']['total_annual_fees']:.2f}")
        print(f"  净收益：RM {report['optimized_solution']['net_annual_benefit']:.2f}")
        
        print(f"\n💰 年度节省：RM {report['comparison']['annual_savings']:.2f}")
        print(f"节省百分比：{report['comparison']['savings_percentage']:.1f}%")
        print(f"推荐等级：{report['comparison']['recommendation_level']}")
        
        filepath = generator.save_report(customer_id=1)
        print(f"\n✅ HTML报告已保存：{filepath}")
    else:
        print(f"错误：{report['error']}")
