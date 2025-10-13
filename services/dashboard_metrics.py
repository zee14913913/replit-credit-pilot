"""
Dashboard Metrics Service
计算客户和信用卡的关键财务指标
"""

from db.database import get_db
from datetime import datetime
from typing import Dict, List, Optional


def get_customer_monthly_metrics(customer_id: int, year_month: str) -> Dict:
    """
    获取客户的月度财务指标
    
    Args:
        customer_id: 客户ID
        year_month: 年月格式 "2025-09"
        
    Returns:
        {
            'total_consumption': 客户当月总消费,
            'total_payment': 客户当月总付款,
            'monthly_balance': 当月净欠款 (消费-付款),
            'cumulative_balance': 客户累计欠款总余额,
            'card_metrics': [每张卡的详细指标],
            'period': '2025-09'
        }
    """
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. 客户当月总消费
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) as total
            FROM consumption_records
            WHERE customer_id = ?
              AND strftime('%Y-%m', Statement_Date) = ?
        ''', (customer_id, year_month))
        
        total_consumption = cursor.fetchone()[0]
        
        # 2. 客户当月总付款
        cursor.execute('''
            SELECT COALESCE(SUM(PaymentAmount), 0) as total
            FROM payment_records
            WHERE customer_id = ?
              AND strftime('%Y-%m', PaymentDate) = ?
        ''', (customer_id, year_month))
        
        total_payment = cursor.fetchone()[0]
        
        # 3. 客户累计欠款总余额 (所有时间的消费 - 所有时间的付款)
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) as total_consume
            FROM consumption_records
            WHERE customer_id = ?
        ''', (customer_id,))
        
        all_time_consumption = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COALESCE(SUM(PaymentAmount), 0) as total_paid
            FROM payment_records
            WHERE customer_id = ?
        ''', (customer_id,))
        
        all_time_payment = cursor.fetchone()[0]
        
        cumulative_balance = all_time_consumption - all_time_payment
        
        # 4. 获取所有信用卡的指标
        cursor.execute('''
            SELECT id, bank_name, card_number_last4
            FROM credit_cards
            WHERE customer_id = ?
        ''', (customer_id,))
        
        cards = cursor.fetchall()
        card_metrics = []
        
        for card_id, bank_name, last4 in cards:
            card_data = get_card_monthly_metrics(customer_id, card_id, year_month)
            card_metrics.append({
                'card_id': card_id,
                'bank_name': bank_name,
                'last_four_digits': last4,
                'display_name': f"{bank_name} ****{last4}",
                **card_data
            })
        
        return {
            'total_consumption': round(total_consumption, 2),
            'total_payment': round(total_payment, 2),
            'monthly_balance': round(total_consumption - total_payment, 2),
            'cumulative_balance': round(cumulative_balance, 2),
            'card_metrics': card_metrics,
            'period': year_month
        }


def get_card_monthly_metrics(customer_id: int, card_id: int, year_month: str) -> Dict:
    """
    获取单张信用卡的月度指标
    
    Returns:
        {
            'monthly_consumption': 当月总消费,
            'monthly_payment': 当月总付款,
            'monthly_balance': 当月净欠款,
            'cumulative_balance': 该卡累计欠款余额,
            'cumulative_points': 该卡累计积分,
            'statement_balance': 该月账单总欠款 (如有账单)
        }
    """
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. 该卡当月总消费（通过 statement_id 关联）
        cursor.execute('''
            SELECT COALESCE(SUM(c.Amount), 0) as total
            FROM consumption_records c
            INNER JOIN statements s ON c.statement_id = s.id
            WHERE c.customer_id = ? AND s.card_id = ?
              AND strftime('%Y-%m', c.Statement_Date) = ?
        ''', (customer_id, card_id, year_month))
        
        monthly_consumption = cursor.fetchone()[0]
        
        # 2. 该卡当月总付款（通过 statement_id 关联）
        cursor.execute('''
            SELECT COALESCE(SUM(p.PaymentAmount), 0) as total
            FROM payment_records p
            INNER JOIN statements s ON p.statement_id = s.id
            WHERE p.customer_id = ? AND s.card_id = ?
              AND strftime('%Y-%m', p.PaymentDate) = ?
        ''', (customer_id, card_id, year_month))
        
        monthly_payment = cursor.fetchone()[0]
        
        # 3. 该卡累计欠款余额（通过 statement_id 关联）
        cursor.execute('''
            SELECT COALESCE(SUM(c.Amount), 0) as total_consume
            FROM consumption_records c
            INNER JOIN statements s ON c.statement_id = s.id
            WHERE c.customer_id = ? AND s.card_id = ?
        ''', (customer_id, card_id))
        
        card_all_consumption = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COALESCE(SUM(p.PaymentAmount), 0) as total_paid
            FROM payment_records p
            INNER JOIN statements s ON p.statement_id = s.id
            WHERE p.customer_id = ? AND s.card_id = ?
        ''', (customer_id, card_id))
        
        card_all_payment = cursor.fetchone()[0]
        
        cumulative_balance = card_all_consumption - card_all_payment
        
        # 4. 该卡累计积分（获取最新的累计积分）
        cursor.execute('''
            SELECT COALESCE(MAX(points_cumulative), 0) as total_points
            FROM points_tracking
            WHERE customer_id = ? AND card_id = ?
        ''', (customer_id, card_id))
        
        cumulative_points = cursor.fetchone()[0]
        
        # 5. 该月账单总欠款 (从statements表获取)
        cursor.execute('''
            SELECT statement_total
            FROM statements
            WHERE card_id = ?
              AND strftime('%Y-%m', statement_date) = ?
            ORDER BY statement_date DESC
            LIMIT 1
        ''', (card_id, year_month))
        
        stmt_result = cursor.fetchone()
        statement_balance = stmt_result[0] if stmt_result else 0.0
        
        return {
            'monthly_consumption': round(monthly_consumption, 2),
            'monthly_payment': round(monthly_payment, 2),
            'monthly_balance': round(monthly_consumption - monthly_payment, 2),
            'cumulative_balance': round(cumulative_balance, 2),
            'cumulative_points': int(cumulative_points),
            'statement_balance': round(statement_balance, 2) if statement_balance else 0.0
        }


def get_all_cards_summary(customer_id: int, year_month: str) -> List[Dict]:
    """
    获取客户所有信用卡的汇总信息（用于仪表板显示）
    """
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, bank_name, card_number_last4
            FROM credit_cards
            WHERE customer_id = ?
            ORDER BY bank_name, card_number_last4
        ''', (customer_id,))
        
        cards = cursor.fetchall()
        summary = []
        
        for card_id, bank_name, last4 in cards:
            metrics = get_card_monthly_metrics(customer_id, card_id, year_month)
            
            summary.append({
                'card_id': card_id,
                'bank_name': bank_name,
                'last_four_digits': last4,
                'display_name': f"{bank_name} ****{last4}",
                'monthly_consumption': metrics['monthly_consumption'],
                'monthly_payment': metrics['monthly_payment'],
                'monthly_balance': metrics['monthly_balance'],
                'cumulative_balance': metrics['cumulative_balance'],
                'cumulative_points': metrics['cumulative_points'],
                'statement_balance': metrics['statement_balance']
            })
        
        return summary
