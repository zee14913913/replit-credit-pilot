"""
财务健康评分系统 (Financial Health Score)
类似CTOS，但更直观：0-100分评分系统

评分维度：
1. 还款及时率 (35%) - 是否准时还款
2. DSR债务收入比 (25%) - 债务占收入比例
3. 信用卡使用率 (20%) - 信用额度使用情况
4. 账单分类健康度 (10%) - 消费分类是否合理
5. 财务稳定性 (10%) - 收支波动情况
"""

from db.database import get_db
from datetime import datetime, timedelta
import json

class FinancialHealthScore:
    
    def calculate_score(self, customer_id):
        """计算客户财务健康评分 (0-100)"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 获取客户基本信息
        cursor.execute('''
            SELECT monthly_income, total_debt, credit_score
            FROM customers
            WHERE id = ?
        ''', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return None
            
        monthly_income = customer['monthly_income'] or 0
        total_debt = customer['total_debt'] or 0
        credit_score = customer['credit_score'] or 0
        
        # 维度1: 还款及时率 (35分)
        payment_score = self._calculate_payment_timeliness(cursor, customer_id)
        
        # 维度2: DSR债务收入比 (25分)
        dsr_score = self._calculate_dsr_score(monthly_income, total_debt)
        
        # 维度3: 信用卡使用率 (20分)
        utilization_score = self._calculate_utilization_score(cursor, customer_id)
        
        # 维度4: 账单分类健康度 (10分)
        category_score = self._calculate_category_health(cursor, customer_id)
        
        # 维度5: 财务稳定性 (10分)
        stability_score = self._calculate_financial_stability(cursor, customer_id)
        
        # 总分
        total_score = (
            payment_score * 0.35 +
            dsr_score * 0.25 +
            utilization_score * 0.20 +
            category_score * 0.10 +
            stability_score * 0.10
        )
        
        # 识别弱点维度
        weak_dimensions = self._identify_weak_dimensions({
            'payment_timeliness': payment_score,
            'dsr': dsr_score,
            'utilization': utilization_score,
            'category_health': category_score,
            'stability': stability_score
        })
        
        # 生成优化建议
        optimization_suggestions = self._generate_suggestions(weak_dimensions, {
            'dsr': monthly_income / total_debt if total_debt > 0 else 0,
            'income': monthly_income,
            'debt': total_debt
        })
        
        # 计算潜在贷款额度
        loan_range = self._calculate_loan_range(monthly_income, total_debt, total_score)
        
        # 计算优化后的收益
        gain_share_net = self._calculate_optimization_gain(cursor, customer_id, weak_dimensions)
        
        # 保存评分历史
        self._save_score_history(cursor, customer_id, total_score, weak_dimensions, 
                                 optimization_suggestions, loan_range, gain_share_net)
        
        conn.commit()
        conn.close()
        
        return {
            'total_score': round(total_score, 1),
            'score_breakdown': {
                'payment_timeliness': round(payment_score, 1),
                'dsr': round(dsr_score, 1),
                'utilization': round(utilization_score, 1),
                'category_health': round(category_score, 1),
                'stability': round(stability_score, 1)
            },
            'weak_dimensions': weak_dimensions,
            'optimization_suggestions': optimization_suggestions,
            'loan_range': loan_range,
            'gain_share_net': gain_share_net,
            'rating': self._get_rating(total_score)
        }
    
    def _calculate_payment_timeliness(self, cursor, customer_id):
        """计算还款及时率 (0-100)"""
        # 获取过去12个月的还款记录
        cursor.execute('''
            SELECT COUNT(*) as total_payments,
                   SUM(CASE WHEN paid_on_time = 1 THEN 1 ELSE 0 END) as on_time_payments
            FROM reminders
            WHERE customer_id = ?
            AND created_date >= date('now', '-12 months')
            AND status = 'paid'
        ''', (customer_id,))
        
        result = cursor.fetchone()
        if not result or result['total_payments'] == 0:
            return 70  # 默认中等分数
        
        on_time_rate = result['on_time_payments'] / result['total_payments']
        return on_time_rate * 100
    
    def _calculate_dsr_score(self, monthly_income, total_debt):
        """计算DSR评分 (0-100)"""
        if monthly_income == 0:
            return 0
        
        dsr = total_debt / monthly_income
        
        # DSR评分标准
        if dsr <= 0.3:  # ≤30% 优秀
            return 100
        elif dsr <= 0.5:  # 30-50% 良好
            return 90 - (dsr - 0.3) * 100
        elif dsr <= 0.7:  # 50-70% 一般
            return 70 - (dsr - 0.5) * 100
        else:  # >70% 需要改善
            return max(0, 50 - (dsr - 0.7) * 50)
    
    def _calculate_utilization_score(self, cursor, customer_id):
        """计算信用卡使用率评分 (0-100)"""
        cursor.execute('''
            SELECT credit_limit, current_balance
            FROM credit_cards
            WHERE customer_id = ?
        ''', (customer_id,))
        
        cards = cursor.fetchall()
        if not cards:
            return 70  # 默认分数
        
        total_limit = sum(card['credit_limit'] or 0 for card in cards)
        total_balance = sum(card['current_balance'] or 0 for card in cards)
        
        if total_limit == 0:
            return 0
        
        utilization = total_balance / total_limit
        
        # 使用率评分标准
        if utilization <= 0.3:  # ≤30% 优秀
            return 100
        elif utilization <= 0.5:  # 30-50% 良好
            return 90 - (utilization - 0.3) * 100
        elif utilization <= 0.75:  # 50-75% 需注意
            return 70 - (utilization - 0.5) * 80
        else:  # >75% 危险
            return max(0, 50 - (utilization - 0.75) * 100)
    
    def _calculate_category_health(self, cursor, customer_id):
        """计算消费分类健康度 (0-100)"""
        cursor.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE customer_id = ?
            AND transaction_date >= date('now', '-3 months')
            GROUP BY category
        ''', (customer_id,))
        
        categories = cursor.fetchall()
        if not categories:
            return 70
        
        total_spending = sum(cat['total'] for cat in categories)
        if total_spending == 0:
            return 70
        
        # 检查是否有过度消费类别（如娱乐、购物等超过30%）
        high_risk_categories = ['Entertainment', 'Shopping', 'Others']
        high_risk_spending = sum(
            cat['total'] for cat in categories 
            if cat['category'] in high_risk_categories
        )
        
        high_risk_ratio = high_risk_spending / total_spending
        
        if high_risk_ratio <= 0.2:  # ≤20% 健康
            return 100
        elif high_risk_ratio <= 0.4:  # 20-40% 一般
            return 80 - (high_risk_ratio - 0.2) * 100
        else:  # >40% 需要改善
            return max(50, 60 - (high_risk_ratio - 0.4) * 50)
    
    def _calculate_financial_stability(self, cursor, customer_id):
        """计算财务稳定性 (0-100)"""
        cursor.execute('''
            SELECT strftime('%Y-%m', transaction_date) as month,
                   SUM(amount) as monthly_spending
            FROM transactions
            WHERE customer_id = ?
            AND transaction_date >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', transaction_date)
        ''', (customer_id,))
        
        monthly_data = cursor.fetchall()
        if len(monthly_data) < 3:
            return 70
        
        spendings = [m['monthly_spending'] for m in monthly_data]
        avg_spending = sum(spendings) / len(spendings)
        
        # 计算波动率（标准差 / 平均值）
        variance = sum((s - avg_spending) ** 2 for s in spendings) / len(spendings)
        std_dev = variance ** 0.5
        volatility = std_dev / avg_spending if avg_spending > 0 else 0
        
        # 波动率评分
        if volatility <= 0.15:  # ≤15% 非常稳定
            return 100
        elif volatility <= 0.3:  # 15-30% 稳定
            return 90 - (volatility - 0.15) * 200
        else:  # >30% 不稳定
            return max(50, 70 - (volatility - 0.3) * 100)
    
    def _identify_weak_dimensions(self, scores):
        """识别弱点维度（<70分）"""
        weak = []
        dimension_names = {
            'payment_timeliness': '还款及时率',
            'dsr': 'DSR债务比',
            'utilization': '信用卡使用率',
            'category_health': '消费分类健康度',
            'stability': '财务稳定性'
        }
        
        for dim, score in scores.items():
            if score < 70:
                weak.append({
                    'dimension': dimension_names[dim],
                    'score': round(score, 1),
                    'severity': 'high' if score < 50 else 'medium'
                })
        
        return weak
    
    def _generate_suggestions(self, weak_dimensions, financial_data):
        """生成优化建议"""
        suggestions = []
        
        for weak in weak_dimensions:
            if weak['dimension'] == '还款及时率':
                suggestions.append({
                    'area': '还款管理',
                    'suggestion': '建议启用自动还款提醒服务，避免逾期罚款',
                    'potential_saving': 500  # RM
                })
            
            elif weak['dimension'] == 'DSR债务比':
                # 计算债务整合可节省金额
                current_interest = financial_data['debt'] * 0.18  # 假设18%年利率
                optimized_interest = financial_data['debt'] * 0.08  # 整合后8%
                saving = current_interest - optimized_interest
                
                suggestions.append({
                    'area': '债务整合',
                    'suggestion': f'您的DSR过高，建议债务整合可节省年利息约RM {saving:.2f}',
                    'potential_saving': saving
                })
            
            elif weak['dimension'] == '信用卡使用率':
                suggestions.append({
                    'area': '信用额度优化',
                    'suggestion': '建议申请额度提升或余额转移，降低使用率以提升信用分数',
                    'potential_saving': 0
                })
            
            elif weak['dimension'] == '消费分类健康度':
                suggestions.append({
                    'area': '消费习惯',
                    'suggestion': '建议减少非必要开支（娱乐、购物），增加储蓄比例',
                    'potential_saving': financial_data['income'] * 0.15  # 可节省15%收入
                })
        
        return suggestions
    
    def _calculate_loan_range(self, monthly_income, total_debt, score):
        """计算可贷款额度范围"""
        if score >= 80:
            multiplier = 8  # 优秀：8倍月收入
        elif score >= 70:
            multiplier = 6  # 良好：6倍月收入
        elif score >= 60:
            multiplier = 4  # 一般：4倍月收入
        else:
            multiplier = 2  # 需改善：2倍月收入
        
        max_loan = monthly_income * multiplier
        
        # 扣除现有债务
        available_loan = max(0, max_loan - total_debt)
        
        return {
            'min': available_loan * 0.3,
            'max': available_loan,
            'recommended': available_loan * 0.6
        }
    
    def _calculate_optimization_gain(self, cursor, customer_id, weak_dimensions):
        """计算优化后的收益（客户获得 + 我们分成 + 客户净收益）"""
        total_potential_gain = 0
        
        # 从建议中累计潜在节省
        for weak in weak_dimensions:
            if weak['dimension'] == 'DSR债务比':
                # 债务整合节省
                cursor.execute('''
                    SELECT SUM(current_balance * 0.10) as potential_saving
                    FROM credit_cards
                    WHERE customer_id = ?
                ''', (customer_id,))
                result = cursor.fetchone()
                if result and result['potential_saving']:
                    total_potential_gain += result['potential_saving']
        
        # 50/50分成
        customer_gain = total_potential_gain * 0.5
        our_share = total_potential_gain * 0.5
        customer_net = customer_gain  # 客户净收益
        
        return {
            'total_gain': round(total_potential_gain, 2),
            'customer_gain': round(customer_gain, 2),
            'our_share': round(our_share, 2),
            'customer_net': round(customer_net, 2)
        }
    
    def _save_score_history(self, cursor, customer_id, score, weak_dimensions, 
                           suggestions, loan_range, gain_share):
        """保存评分历史"""
        cursor.execute('''
            INSERT INTO financial_health_scores 
            (customer_id, score, weak_dimensions, optimization_suggestions, 
             loan_range, potential_gain, score_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_id,
            score,
            json.dumps(weak_dimensions),
            json.dumps(suggestions),
            json.dumps(loan_range),
            gain_share['total_gain'],
            datetime.now().strftime('%Y-%m-%d')
        ))
    
    def _get_rating(self, score):
        """获取评级"""
        if score >= 90:
            return {'grade': 'A+', 'label': '优秀', 'color': 'success'}
        elif score >= 80:
            return {'grade': 'A', 'label': '良好', 'color': 'success'}
        elif score >= 70:
            return {'grade': 'B', 'label': '中等', 'color': 'warning'}
        elif score >= 60:
            return {'grade': 'C', 'label': '需改善', 'color': 'warning'}
        else:
            return {'grade': 'D', 'label': '需紧急改善', 'color': 'danger'}
    
    def get_score_trend(self, customer_id, months=6):
        """获取评分趋势（过去N个月）"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT score, score_date
            FROM financial_health_scores
            WHERE customer_id = ?
            ORDER BY score_date DESC
            LIMIT ?
        ''', (customer_id, months))
        
        scores = cursor.fetchall()
        conn.close()
        
        return [
            {'date': s['score_date'], 'score': s['score']}
            for s in reversed(scores)
        ]
