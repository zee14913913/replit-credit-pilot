"""
现金流预测引擎 (Cashflow Prediction Engine)
基于客户账单 + 贷款 + 消费趋势，生成未来3/6/12个月的现金流预测

功能：
1. 预测未来收支情况
2. 对比"不优化 vs 采用优化方案"的差距
3. 可视化现金流走势图
"""

from db.database import get_db
from datetime import datetime, timedelta
import json

class CashflowPredictor:
    
    def predict_cashflow(self, customer_id, months=12):
        """预测未来N个月现金流"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 获取客户基本数据
        cursor.execute('''
            SELECT monthly_income, total_debt
            FROM customers
            WHERE id = ?
        ''', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return None
        
        monthly_income = customer['monthly_income'] or 0
        
        # 获取历史消费数据（过去6个月）
        historical_spending = self._get_historical_spending(cursor, customer_id)
        
        # 获取信用卡还款数据
        credit_payments = self._get_credit_card_payments(cursor, customer_id)
        
        # 获取贷款还款
        loan_payments = self._get_loan_payments(cursor, customer_id)
        
        # 生成未来N个月预测
        predictions = []
        current_date = datetime.now()
        
        for month_offset in range(months):
            month_date = current_date + timedelta(days=30 * month_offset)
            month_str = month_date.strftime('%Y-%m')
            
            # 预测当月支出（基于历史平均 + 趋势）
            predicted_spending = self._predict_monthly_spending(
                historical_spending, month_offset
            )
            
            # 预测当月信用卡还款
            predicted_credit_payment = sum(credit_payments.values())
            
            # 预测当月贷款还款
            predicted_loan_payment = sum(loan_payments.values())
            
            # 计算净现金流
            net_cashflow = (
                monthly_income - 
                predicted_spending - 
                predicted_credit_payment - 
                predicted_loan_payment
            )
            
            predictions.append({
                'month': month_str,
                'income': monthly_income,
                'spending': round(predicted_spending, 2),
                'credit_payment': round(predicted_credit_payment, 2),
                'loan_payment': round(predicted_loan_payment, 2),
                'net_cashflow': round(net_cashflow, 2),
                'cumulative_cashflow': 0  # 稍后计算
            })
        
        # 计算累计现金流
        cumulative = 0
        for pred in predictions:
            cumulative += pred['net_cashflow']
            pred['cumulative_cashflow'] = round(cumulative, 2)
        
        # 生成优化对比
        optimized_predictions = self._generate_optimized_scenario(
            predictions, cursor, customer_id
        )
        
        conn.close()
        
        return {
            'current_scenario': predictions,
            'optimized_scenario': optimized_predictions,
            'comparison': self._calculate_comparison(predictions, optimized_predictions)
        }
    
    def _get_historical_spending(self, cursor, customer_id):
        """获取历史消费数据"""
        cursor.execute('''
            SELECT strftime('%Y-%m', transaction_date) as month,
                   SUM(amount) as total_spending
            FROM transactions
            WHERE customer_id = ?
            AND transaction_date >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', transaction_date)
            ORDER BY month
        ''', (customer_id,))
        
        return {row['month']: row['total_spending'] for row in cursor.fetchall()}
    
    def _get_credit_card_payments(self, cursor, customer_id):
        """获取信用卡月还款额"""
        cursor.execute('''
            SELECT card_name, minimum_payment
            FROM credit_cards
            WHERE customer_id = ?
        ''', (customer_id,))
        
        return {row['card_name']: row['minimum_payment'] or 0 for row in cursor.fetchall()}
    
    def _get_loan_payments(self, cursor, customer_id):
        """获取贷款月还款额"""
        cursor.execute('''
            SELECT loan_type, monthly_installment
            FROM loans
            WHERE customer_id = ?
        ''', (customer_id,))
        
        return {row['loan_type']: row['monthly_installment'] or 0 for row in cursor.fetchall()}
    
    def _predict_monthly_spending(self, historical_data, month_offset):
        """预测月度支出（基于历史平均 + 趋势）"""
        if not historical_data:
            return 0
        
        values = list(historical_data.values())
        avg_spending = sum(values) / len(values)
        
        # 计算趋势（简单线性回归）
        if len(values) >= 3:
            trend = (values[-1] - values[0]) / len(values)
            predicted = avg_spending + (trend * month_offset)
            return max(0, predicted)
        
        return avg_spending
    
    def _generate_optimized_scenario(self, current_predictions, cursor, customer_id):
        """生成优化方案场景"""
        # 获取优化建议（从财务健康评分系统）
        cursor.execute('''
            SELECT optimization_suggestions, potential_gain
            FROM financial_health_scores
            WHERE customer_id = ?
            ORDER BY score_date DESC
            LIMIT 1
        ''', (customer_id,))
        
        score_data = cursor.fetchone()
        
        if not score_data:
            return current_predictions
        
        potential_monthly_saving = (score_data['potential_gain'] or 0) / 12
        
        # 复制当前预测并应用优化
        optimized = []
        for pred in current_predictions:
            optimized_pred = pred.copy()
            
            # 减少信用卡还款（通过债务整合）
            if potential_monthly_saving > 0:
                optimized_pred['credit_payment'] = max(
                    0, 
                    pred['credit_payment'] - potential_monthly_saving
                )
            
            # 重新计算净现金流
            optimized_pred['net_cashflow'] = (
                optimized_pred['income'] - 
                optimized_pred['spending'] - 
                optimized_pred['credit_payment'] - 
                optimized_pred['loan_payment']
            )
            
            optimized.append(optimized_pred)
        
        # 重新计算累计现金流
        cumulative = 0
        for pred in optimized:
            cumulative += pred['net_cashflow']
            pred['cumulative_cashflow'] = round(cumulative, 2)
        
        return optimized
    
    def _calculate_comparison(self, current, optimized):
        """计算优化对比"""
        current_total = sum(p['net_cashflow'] for p in current)
        optimized_total = sum(p['net_cashflow'] for p in optimized)
        
        improvement = optimized_total - current_total
        improvement_pct = (improvement / abs(current_total) * 100) if current_total != 0 else 0
        
        return {
            'current_total_cashflow': round(current_total, 2),
            'optimized_total_cashflow': round(optimized_total, 2),
            'total_improvement': round(improvement, 2),
            'improvement_percentage': round(improvement_pct, 1),
            'monthly_average_saving': round(improvement / len(current), 2)
        }
    
    def get_cashflow_chart_data(self, customer_id, months=12):
        """获取用于图表展示的现金流数据"""
        prediction = self.predict_cashflow(customer_id, months)
        
        if not prediction:
            return None
        
        return {
            'labels': [p['month'] for p in prediction['current_scenario']],
            'datasets': [
                {
                    'label': '当前方案净现金流',
                    'data': [p['net_cashflow'] for p in prediction['current_scenario']],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.1)'
                },
                {
                    'label': '优化方案净现金流',
                    'data': [p['net_cashflow'] for p in prediction['optimized_scenario']],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.1)'
                },
                {
                    'label': '当前方案累计现金流',
                    'data': [p['cumulative_cashflow'] for p in prediction['current_scenario']],
                    'borderColor': 'rgb(255, 159, 64)',
                    'backgroundColor': 'rgba(255, 159, 64, 0.1)',
                    'borderDash': [5, 5]
                },
                {
                    'label': '优化方案累计现金流',
                    'data': [p['cumulative_cashflow'] for p in prediction['optimized_scenario']],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                    'borderDash': [5, 5]
                }
            ],
            'comparison': prediction['comparison']
        }
