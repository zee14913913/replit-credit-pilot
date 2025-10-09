"""
客户等级体系 (Customer Tier System)
Silver → Gold → Platinum

等级权益：
- Silver: 基础报告查看
- Gold: 自动提醒 + 优化建议
- Platinum: VIP代付 + 贷款方案 + 专属顾问

升级条件：
1. 财务健康评分
2. 账户活跃度
3. 服务使用时长
4. 月度消费金额
"""

from db.database import get_db
from datetime import datetime, timedelta
import json

class CustomerTierSystem:
    
    TIERS = {
        'Silver': {
            'min_score': 0,
            'min_months': 0,
            'min_monthly_spending': 0,
            'benefits': [
                '基础月度报告',
                '交易分类查看',
                '账单上传'
            ],
            'fee_discount': 0
        },
        'Gold': {
            'min_score': 70,
            'min_months': 3,
            'min_monthly_spending': 5000,
            'benefits': [
                'Silver所有权益',
                '自动还款提醒',
                '财务优化建议',
                '预算管理工具',
                '10% 服务费折扣'
            ],
            'fee_discount': 0.1
        },
        'Platinum': {
            'min_score': 85,
            'min_months': 6,
            'min_monthly_spending': 15000,
            'benefits': [
                'Gold所有权益',
                'VIP账单代付服务',
                '贷款优化方案',
                '专属财务顾问',
                '现金流预测引擎',
                '20% 服务费折扣',
                '优先客服支持'
            ],
            'fee_discount': 0.2
        }
    }
    
    def calculate_customer_tier(self, customer_id):
        """计算客户等级"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 获取财务健康评分
        cursor.execute('''
            SELECT score
            FROM financial_health_scores
            WHERE customer_id = ?
            ORDER BY score_date DESC
            LIMIT 1
        ''', (customer_id,))
        score_data = cursor.fetchone()
        current_score = score_data['score'] if score_data else 0
        
        # 获取客户注册时长（月数）
        cursor.execute('''
            SELECT created_date
            FROM customers
            WHERE id = ?
        ''', (customer_id,))
        customer = cursor.fetchone()
        
        if customer and customer['created_date']:
            created_date = datetime.strptime(customer['created_date'], '%Y-%m-%d')
            months_active = (datetime.now() - created_date).days / 30
        else:
            months_active = 0
        
        # 获取平均月度消费
        cursor.execute('''
            SELECT AVG(monthly_spending) as avg_spending
            FROM (
                SELECT strftime('%Y-%m', transaction_date) as month,
                       SUM(amount) as monthly_spending
                FROM transactions
                WHERE customer_id = ?
                AND transaction_date >= date('now', '-6 months')
                GROUP BY strftime('%Y-%m', transaction_date)
            )
        ''', (customer_id,))
        spending_data = cursor.fetchone()
        avg_monthly_spending = spending_data['avg_spending'] if spending_data and spending_data['avg_spending'] else 0
        
        # 判断等级
        tier = self._determine_tier(current_score, months_active, avg_monthly_spending)
        
        # 获取下一等级所需条件
        next_tier_requirements = self._get_next_tier_requirements(
            tier, current_score, months_active, avg_monthly_spending
        )
        
        # 保存等级历史
        self._save_tier_history(cursor, customer_id, tier, current_score, 
                                months_active, avg_monthly_spending)
        
        conn.commit()
        conn.close()
        
        return {
            'current_tier': tier,
            'tier_benefits': self.TIERS[tier]['benefits'],
            'fee_discount': self.TIERS[tier]['fee_discount'],
            'metrics': {
                'financial_score': round(current_score, 1),
                'months_active': round(months_active, 1),
                'avg_monthly_spending': round(avg_monthly_spending, 2)
            },
            'next_tier_requirements': next_tier_requirements
        }
    
    def _determine_tier(self, score, months, spending):
        """判断等级"""
        # 从高到低检查
        if (score >= self.TIERS['Platinum']['min_score'] and
            months >= self.TIERS['Platinum']['min_months'] and
            spending >= self.TIERS['Platinum']['min_monthly_spending']):
            return 'Platinum'
        
        if (score >= self.TIERS['Gold']['min_score'] and
            months >= self.TIERS['Gold']['min_months'] and
            spending >= self.TIERS['Gold']['min_monthly_spending']):
            return 'Gold'
        
        return 'Silver'
    
    def _get_next_tier_requirements(self, current_tier, score, months, spending):
        """获取升级到下一等级所需条件"""
        if current_tier == 'Platinum':
            return None  # 已是最高等级
        
        next_tier = 'Gold' if current_tier == 'Silver' else 'Platinum'
        requirements = self.TIERS[next_tier]
        
        gaps = []
        
        if score < requirements['min_score']:
            gaps.append({
                'metric': '财务健康评分',
                'current': round(score, 1),
                'required': requirements['min_score'],
                'gap': round(requirements['min_score'] - score, 1)
            })
        
        if months < requirements['min_months']:
            gaps.append({
                'metric': '活跃月数',
                'current': round(months, 1),
                'required': requirements['min_months'],
                'gap': round(requirements['min_months'] - months, 1)
            })
        
        if spending < requirements['min_monthly_spending']:
            gaps.append({
                'metric': '平均月度消费',
                'current': round(spending, 2),
                'required': requirements['min_monthly_spending'],
                'gap': round(requirements['min_monthly_spending'] - spending, 2)
            })
        
        return {
            'next_tier': next_tier,
            'gaps': gaps,
            'estimated_months_to_upgrade': self._estimate_upgrade_time(gaps)
        }
    
    def _estimate_upgrade_time(self, gaps):
        """估算升级所需月数"""
        max_months = 0
        
        for gap in gaps:
            if gap['metric'] == '活跃月数':
                max_months = max(max_months, gap['gap'])
            elif gap['metric'] == '财务健康评分':
                # 假设每月可提升5分
                max_months = max(max_months, gap['gap'] / 5)
            elif gap['metric'] == '平均月度消费':
                # 假设每月可增加10%
                current = gap['current']
                required = gap['required']
                if current > 0:
                    months_needed = 0
                    while current < required and months_needed < 24:
                        current *= 1.1
                        months_needed += 1
                    max_months = max(max_months, months_needed)
        
        return round(max_months)
    
    def _save_tier_history(self, cursor, customer_id, tier, score, months, spending):
        """保存等级历史"""
        cursor.execute('''
            INSERT INTO customer_tier_history
            (customer_id, tier, financial_score, months_active, avg_monthly_spending, tier_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            customer_id,
            tier,
            score,
            months,
            spending,
            datetime.now().strftime('%Y-%m-%d')
        ))
    
    def get_tier_progression(self, customer_id):
        """获取等级进展历史"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tier, tier_date, financial_score
            FROM customer_tier_history
            WHERE customer_id = ?
            ORDER BY tier_date DESC
            LIMIT 12
        ''', (customer_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        return [
            {
                'tier': h['tier'],
                'date': h['tier_date'],
                'score': h['financial_score']
            }
            for h in reversed(history)
        ]
    
    def apply_tier_discount(self, customer_id, original_fee):
        """应用等级折扣"""
        tier_data = self.calculate_customer_tier(customer_id)
        discount = tier_data['fee_discount']
        
        discounted_fee = original_fee * (1 - discount)
        saved_amount = original_fee - discounted_fee
        
        return {
            'original_fee': round(original_fee, 2),
            'discount_rate': discount * 100,
            'discounted_fee': round(discounted_fee, 2),
            'saved_amount': round(saved_amount, 2),
            'tier': tier_data['current_tier']
        }
