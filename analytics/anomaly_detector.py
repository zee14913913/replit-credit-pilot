"""
AI异常检测系统 (Anomaly Detection System)
自动识别客户财务异常行为

检测类型：
1. 大额未分类消费
2. 多张卡透支警告
3. 异常消费模式
4. DSR突然上升
5. 还款逾期风险
"""

from db.database import get_db
from datetime import datetime, timedelta
import json

class AnomalyDetector:
    
    def detect_anomalies(self, customer_id):
        """检测所有异常"""
        conn = get_db()
        cursor = conn.cursor()
        
        anomalies = []
        
        # 1. 检测大额未分类消费
        large_uncategorized = self._detect_large_uncategorized(cursor, customer_id)
        if large_uncategorized:
            anomalies.extend(large_uncategorized)
        
        # 2. 检测信用卡透支
        overlimit_cards = self._detect_overlimit_cards(cursor, customer_id)
        if overlimit_cards:
            anomalies.extend(overlimit_cards)
        
        # 3. 检测异常消费模式
        unusual_spending = self._detect_unusual_spending(cursor, customer_id)
        if unusual_spending:
            anomalies.extend(unusual_spending)
        
        # 4. 检测DSR上升
        dsr_spike = self._detect_dsr_spike(cursor, customer_id)
        if dsr_spike:
            anomalies.append(dsr_spike)
        
        # 5. 检测逾期风险
        overdue_risk = self._detect_overdue_risk(cursor, customer_id)
        if overdue_risk:
            anomalies.extend(overdue_risk)
        
        # 保存异常记录
        for anomaly in anomalies:
            self._save_anomaly(cursor, customer_id, anomaly)
        
        conn.commit()
        conn.close()
        
        return {
            'total_anomalies': len(anomalies),
            'critical_count': len([a for a in anomalies if a['severity'] == 'critical']),
            'warning_count': len([a for a in anomalies if a['severity'] == 'warning']),
            'anomalies': anomalies
        }
    
    def _detect_large_uncategorized(self, cursor, customer_id):
        """检测大额未分类消费"""
        cursor.execute('''
            SELECT id, amount, description, transaction_date
            FROM transactions
            WHERE customer_id = ?
            AND (category IS NULL OR category = 'Others' OR category = '')
            AND amount > 500
            AND transaction_date >= date('now', '-30 days')
            ORDER BY amount DESC
        ''', (customer_id,))
        
        transactions = cursor.fetchall()
        anomalies = []
        
        for txn in transactions:
            anomalies.append({
                'type': 'large_uncategorized',
                'severity': 'critical' if txn['amount'] > 2000 else 'warning',
                'title': f"大额未分类消费：RM {txn['amount']:.2f}",
                'description': f"{txn['description']} ({txn['transaction_date']})",
                'amount': txn['amount'],
                'transaction_id': txn['id'],
                'action_required': '请立即分类此笔交易以便准确追踪财务状况',
                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return anomalies
    
    def _detect_overlimit_cards(self, cursor, customer_id):
        """检测透支信用卡"""
        cursor.execute('''
            SELECT card_name, credit_limit, current_balance
            FROM credit_cards
            WHERE customer_id = ?
            AND current_balance > credit_limit
        ''', (customer_id,))
        
        cards = cursor.fetchall()
        anomalies = []
        
        for card in cards:
            overlimit_amount = card['current_balance'] - card['credit_limit']
            utilization = (card['current_balance'] / card['credit_limit'] * 100) if card['credit_limit'] > 0 else 0
            
            anomalies.append({
                'type': 'card_overlimit',
                'severity': 'critical',
                'title': f"{card['card_name']} 已透支",
                'description': f"当前余额 RM {card['current_balance']:.2f}，超出额度 RM {overlimit_amount:.2f}",
                'amount': overlimit_amount,
                'card_name': card['card_name'],
                'utilization': round(utilization, 1),
                'action_required': '紧急：请立即还款以避免高额罚款和信用分数下降',
                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return anomalies
    
    def _detect_unusual_spending(self, cursor, customer_id):
        """检测异常消费模式"""
        # 获取过去6个月平均消费
        cursor.execute('''
            SELECT AVG(monthly_total) as avg_monthly
            FROM (
                SELECT strftime('%Y-%m', transaction_date) as month,
                       SUM(amount) as monthly_total
                FROM transactions
                WHERE customer_id = ?
                AND transaction_date >= date('now', '-6 months')
                AND transaction_date < date('now', '-1 month')
                GROUP BY strftime('%Y-%m', transaction_date)
            )
        ''', (customer_id,))
        
        avg_data = cursor.fetchone()
        if not avg_data or not avg_data['avg_monthly']:
            return []
        
        avg_monthly = avg_data['avg_monthly']
        
        # 获取本月消费
        cursor.execute('''
            SELECT SUM(amount) as current_month_total
            FROM transactions
            WHERE customer_id = ?
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')
        ''', (customer_id,))
        
        current_data = cursor.fetchone()
        current_month = current_data['current_month_total'] if current_data and current_data['current_month_total'] else 0
        
        # 如果本月消费超过平均值50%以上
        if current_month > avg_monthly * 1.5:
            increase_pct = ((current_month - avg_monthly) / avg_monthly * 100)
            
            return [{
                'type': 'unusual_spending',
                'severity': 'critical' if increase_pct > 100 else 'warning',
                'title': f"本月消费异常增加 {increase_pct:.0f}%",
                'description': f"本月消费 RM {current_month:.2f}，超过6个月平均 RM {avg_monthly:.2f}",
                'amount': current_month - avg_monthly,
                'increase_percentage': round(increase_pct, 1),
                'action_required': '建议检查本月消费明细，确认是否有大额非必要开支',
                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
        
        return []
    
    def _detect_dsr_spike(self, cursor, customer_id):
        """检测DSR突然上升"""
        cursor.execute('''
            SELECT monthly_income, total_debt
            FROM customers
            WHERE id = ?
        ''', (customer_id,))
        
        customer = cursor.fetchone()
        if not customer or not customer['monthly_income']:
            return None
        
        current_dsr = customer['total_debt'] / customer['monthly_income']
        
        # 如果DSR > 70%（危险水平）
        if current_dsr > 0.7:
            return {
                'type': 'high_dsr',
                'severity': 'critical',
                'title': f"DSR过高：{current_dsr*100:.1f}%",
                'description': f"您的债务收入比已达 {current_dsr*100:.1f}%，超过安全阈值70%",
                'dsr_value': round(current_dsr * 100, 1),
                'action_required': '强烈建议债务整合以降低DSR，否则将影响未来贷款批准',
                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return None
    
    def _detect_overdue_risk(self, cursor, customer_id):
        """检测逾期风险"""
        cursor.execute('''
            SELECT id, amount, due_date, card_name
            FROM reminders
            WHERE customer_id = ?
            AND status = 'pending'
            AND due_date <= date('now', '+7 days')
            ORDER BY due_date
        ''', (customer_id,))
        
        upcoming_payments = cursor.fetchall()
        anomalies = []
        
        for payment in upcoming_payments:
            days_until_due = (datetime.strptime(payment['due_date'], '%Y-%m-%d') - datetime.now()).days
            
            severity = 'critical' if days_until_due <= 3 else 'warning'
            
            anomalies.append({
                'type': 'overdue_risk',
                'severity': severity,
                'title': f"{payment['card_name']} 还款即将到期",
                'description': f"RM {payment['amount']:.2f} 将于 {days_until_due} 天后到期 ({payment['due_date']})",
                'amount': payment['amount'],
                'days_until_due': days_until_due,
                'due_date': payment['due_date'],
                'reminder_id': payment['id'],
                'action_required': '请尽快安排还款以避免逾期罚款',
                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return anomalies
    
    def _save_anomaly(self, cursor, customer_id, anomaly):
        """保存异常记录"""
        cursor.execute('''
            INSERT INTO financial_anomalies
            (customer_id, anomaly_type, severity, title, description, 
             amount, metadata, detected_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ''', (
            customer_id,
            anomaly['type'],
            anomaly['severity'],
            anomaly['title'],
            anomaly['description'],
            anomaly.get('amount', 0),
            json.dumps({k: v for k, v in anomaly.items() 
                       if k not in ['type', 'severity', 'title', 'description', 'amount']}),
            anomaly['detected_at']
        ))
    
    def get_active_anomalies(self, customer_id):
        """获取活跃的异常"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM financial_anomalies
            WHERE customer_id = ?
            AND status = 'active'
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1
                    WHEN 'warning' THEN 2
                    ELSE 3
                END,
                detected_at DESC
        ''', (customer_id,))
        
        anomalies = cursor.fetchall()
        conn.close()
        
        return [dict(a) for a in anomalies]
    
    def resolve_anomaly(self, anomaly_id, resolution_note=''):
        """解决异常"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE financial_anomalies
            SET status = 'resolved',
                resolution_note = ?,
                resolved_at = ?
            WHERE id = ?
        ''', (resolution_note, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), anomaly_id))
        
        conn.commit()
        conn.close()
