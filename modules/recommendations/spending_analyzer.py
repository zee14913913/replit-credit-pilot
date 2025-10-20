"""
消费模式分析器
Spending Pattern Analyzer for Credit Card Recommendations

分析客户消费数据，识别消费习惯和模式，为信用卡推荐提供数据基础
"""

from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import sqlite3


class SpendingAnalyzer:
    """消费模式分析器"""
    
    CATEGORY_MAPPING = {
        'Food & Dining': ['dining', 'restaurant', 'food'],
        'Groceries': ['grocery', 'supermarket', 'mart'],
        'Petrol': ['petrol', 'fuel', 'gas_station'],
        'Online Shopping': ['online', 'ecommerce', 'lazada', 'shopee'],
        'Travel': ['travel', 'hotel', 'flight', 'airline'],
        'Entertainment': ['entertainment', 'movie', 'cinema'],
        'Transport': ['transport', 'grab', 'taxi', 'parking'],
        'Bills & Utilities': ['bills', 'utilities', 'telco'],
        'Healthcare': ['healthcare', 'medical', 'pharmacy'],
        'Insurance': ['insurance', 'takaful'],
        'Shopping': ['shopping', 'retail'],
        'Others': ['others', 'misc']
    }
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
    
    def analyze_customer_spending(self, customer_id: int, months: int = 6) -> Dict:
        """
        分析客户消费模式
        
        Args:
            customer_id: 客户ID
            months: 分析月份数（默认6个月）
        
        Returns:
            消费分析结果字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                t.category,
                SUM(t.amount) as total_amount,
                COUNT(*) as transaction_count,
                AVG(t.amount) as avg_amount
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
            AND t.transaction_date >= ?
            GROUP BY t.category
            ORDER BY total_amount DESC
        ''', (customer_id, cutoff_date))
        
        category_data = cursor.fetchall()
        
        total_spending = sum(row[1] for row in category_data)
        
        category_breakdown = {}
        for category, total, count, avg in category_data:
            category_breakdown[category or 'Others'] = {
                'total': round(total, 2),
                'count': count,
                'average': round(avg, 2),
                'percentage': round((total / total_spending * 100) if total_spending > 0 else 0, 2),
                'monthly_avg': round(total / months, 2)
            }
        
        monthly_spending = self._get_monthly_spending(customer_id, months, cursor)
        
        conn.close()
        
        return {
            'customer_id': customer_id,
            'analysis_period_months': months,
            'total_spending': round(total_spending, 2),
            'monthly_average': round(total_spending / months, 2) if months > 0 else 0,
            'category_breakdown': category_breakdown,
            'monthly_spending': monthly_spending,
            'top_categories': self._get_top_categories(category_breakdown, top_n=5)
        }
    
    def _get_monthly_spending(self, customer_id: int, months: int, cursor) -> List[Dict]:
        """获取每月消费明细"""
        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', t.transaction_date) as month,
                SUM(t.amount) as total
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            JOIN credit_cards cc ON s.card_id = cc.id
            WHERE cc.customer_id = ?
            AND t.transaction_date >= ?
            GROUP BY month
            ORDER BY month DESC
        ''', (customer_id, cutoff_date))
        
        return [{'month': row[0], 'total': round(row[1], 2)} for row in cursor.fetchall()]
    
    def _get_top_categories(self, category_breakdown: Dict, top_n: int = 5) -> List[Dict]:
        """获取消费最多的类别"""
        sorted_categories = sorted(
            category_breakdown.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        
        return [
            {
                'category': cat,
                'total': data['total'],
                'monthly_avg': data['monthly_avg'],
                'percentage': data['percentage']
            }
            for cat, data in sorted_categories[:top_n]
        ]
    
    def get_spending_profile(self, customer_id: int) -> Dict:
        """
        获取客户消费档案（用于信用卡匹配）
        
        Returns:
            {
                'dining': monthly_avg,
                'grocery': monthly_avg,
                'petrol': monthly_avg,
                'online': monthly_avg,
                'travel': monthly_avg,
                'total_monthly': total
            }
        """
        analysis = self.analyze_customer_spending(customer_id)
        category_breakdown = analysis['category_breakdown']
        
        profile = {
            'dining': category_breakdown.get('Food & Dining', {}).get('monthly_avg', 0),
            'grocery': category_breakdown.get('Groceries', {}).get('monthly_avg', 0),
            'petrol': category_breakdown.get('Petrol', {}).get('monthly_avg', 0),
            'online': category_breakdown.get('Online Shopping', {}).get('monthly_avg', 0) + 
                     category_breakdown.get('Shopping', {}).get('monthly_avg', 0) * 0.3,
            'travel': category_breakdown.get('Travel', {}).get('monthly_avg', 0),
            'entertainment': category_breakdown.get('Entertainment', {}).get('monthly_avg', 0),
            'transport': category_breakdown.get('Transport', {}).get('monthly_avg', 0),
            'bills': category_breakdown.get('Bills & Utilities', {}).get('monthly_avg', 0),
            'total_monthly': analysis['monthly_average']
        }
        
        return profile
    
    def get_customer_tier(self, customer_id: int) -> str:
        """
        根据消费水平判断客户层级
        
        Returns:
            'Silver', 'Gold', 或 'Platinum'
        """
        analysis = self.analyze_customer_spending(customer_id)
        monthly_avg = analysis['monthly_average']
        
        if monthly_avg >= 10000:
            return 'Platinum'
        elif monthly_avg >= 5000:
            return 'Gold'
        else:
            return 'Silver'


if __name__ == "__main__":
    analyzer = SpendingAnalyzer()
    
    result = analyzer.analyze_customer_spending(customer_id=1, months=6)
    print("📊 消费分析结果：")
    print(f"总消费：RM {result['total_spending']:,.2f}")
    print(f"月均消费：RM {result['monthly_average']:,.2f}")
    print(f"\n🏷️  Top 5 类别：")
    for cat in result['top_categories']:
        print(f"  • {cat['category']:20s} : RM {cat['monthly_avg']:8,.2f}/月 ({cat['percentage']:.1f}%)")
    
    profile = analyzer.get_spending_profile(customer_id=1)
    print(f"\n👤 消费档案：")
    for cat, amount in profile.items():
        if amount > 0:
            print(f"  • {cat:15s} : RM {amount:8,.2f}")
    
    tier = analyzer.get_customer_tier(customer_id=1)
    print(f"\n⭐ 客户层级：{tier}")
