"""
Budget Management Service
Track spending against budget limits with alerts
"""

from typing import List, Dict, Optional
from db.database import get_db
from datetime import datetime, timedelta

class BudgetService:
    """Service for budget management and tracking"""
    
    def create_budget(self, customer_id: int, category: str, monthly_limit: float, 
                     alert_threshold: float = 80.0) -> int:
        """Create or update a budget for a category"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets 
                (customer_id, category, monthly_limit, alert_threshold, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (customer_id, category, monthly_limit, alert_threshold))
            conn.commit()
            return cursor.lastrowid
    
    def get_customer_budgets(self, customer_id: int) -> List[Dict]:
        """Get all budgets for a customer"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM budgets 
                WHERE customer_id = ? AND is_active = 1
                ORDER BY category
            ''', (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_budget_status(self, customer_id: int, month: Optional[str] = None) -> List[Dict]:
        """Get budget status with current spending"""
        
        if not month:
            month = datetime.now().strftime('%Y-%m')
        
        budgets = self.get_customer_budgets(customer_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            result = []
            for budget in budgets:
                # Get spending for this category this month
                cursor.execute('''
                    SELECT COALESCE(SUM(t.amount), 0) as spent, COUNT(*) as transaction_count
                    FROM transactions t
                    INNER JOIN statements s ON t.statement_id = s.id
                    INNER JOIN credit_cards cc ON s.card_id = cc.id
                    WHERE cc.customer_id = ? 
                      AND t.category = ?
                      AND strftime('%Y-%m', t.transaction_date) = ?
                      AND s.is_confirmed = 1
                ''', (customer_id, budget['category'], month))
                
                spent_row = cursor.fetchone()
                spent = spent_row[0] if spent_row else 0
                transaction_count = spent_row[1] if spent_row else 0
                
                utilization = (spent / budget['monthly_limit'] * 100) if budget['monthly_limit'] > 0 else 0
                remaining = budget['monthly_limit'] - spent
                
                status = 'safe'
                if utilization >= 100:
                    status = 'exceeded'
                elif utilization >= budget['alert_threshold']:
                    status = 'warning'
                
                result.append({
                    **budget,
                    'spent': spent,
                    'remaining': remaining,
                    'utilization': utilization,
                    'status': status,
                    'transaction_count': transaction_count,
                    'month': month
                })
            
            return result
    
    def delete_budget(self, budget_id: int, customer_id: int) -> bool:
        """Delete a budget"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM budgets 
                WHERE id = ? AND customer_id = ?
            ''', (budget_id, customer_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_budget_alerts(self, customer_id: int) -> List[Dict]:
        """Get budgets that need attention (over threshold or exceeded)"""
        statuses = self.get_budget_status(customer_id)
        return [s for s in statuses if s['status'] in ['warning', 'exceeded']]
    
    def get_budget_recommendations(self, customer_id: int) -> List[Dict]:
        """Get budget recommendations based on spending history"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get average spending by category over last 3 months
            cursor.execute('''
                SELECT t.category, 
                       AVG(monthly_total) as avg_monthly,
                       MAX(monthly_total) as max_monthly
                FROM (
                    SELECT t.category, 
                           strftime('%Y-%m', t.transaction_date) as month,
                           SUM(t.amount) as monthly_total
                    FROM transactions t
                    INNER JOIN statements s ON t.statement_id = s.id
                    INNER JOIN credit_cards cc ON s.card_id = cc.id
                    WHERE cc.customer_id = ? 
                      AND s.is_confirmed = 1
                      AND t.transaction_date >= date('now', '-3 months')
                    GROUP BY t.category, month
                ) t
                GROUP BY category
                HAVING count(*) >= 2
                ORDER BY avg_monthly DESC
            ''', (customer_id,))
            
            recommendations = []
            for row in cursor.fetchall():
                category = row[0]
                avg_monthly = row[1]
                max_monthly = row[2]
                
                # Recommend 10% buffer over max
                recommended_limit = max_monthly * 1.1
                
                recommendations.append({
                    'category': category,
                    'average_monthly': avg_monthly,
                    'peak_monthly': max_monthly,
                    'recommended_limit': recommended_limit,
                    'reasoning': f'Based on 3-month history (peak: RM {max_monthly:.2f})'
                })
            
            return recommendations
