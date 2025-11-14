"""
趋势分析引擎服务
生成支出、还款、余额趋势图表数据
Safe for AI V3 Stable Baseline
"""
import sqlite3
from typing import Dict, List, Any


class TrendEngine:
    def __init__(self):
        self.db_path = "db/smart_loan_manager.db"
    
    def get_trends(self, customer_id: int) -> Dict[str, Any]:
        """
        获取客户最近12个月的趋势数据
        
        Returns:
            {
                "labels": ["2024-01", "2024-02", ...],
                "expenses": [1000, 1200, ...],
                "payments": [1500, 1300, ...],
                "balances": [5000, 4700, ...]
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询最近12个月数据
        cursor.execute("""
            SELECT 
                statement_month,
                closing_balance_total,
                owner_expenses + gz_expenses as total_expenses,
                owner_payments + gz_payments as total_payments
            FROM monthly_statements
            WHERE customer_id = ?
            ORDER BY statement_month ASC
            LIMIT 12
        """, (customer_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                "labels": [],
                "expenses": [],
                "payments": [],
                "balances": [],
                "count": 0
            }
        
        # 提取数据
        labels = [row["statement_month"] for row in rows]
        expenses = [round(row["total_expenses"], 2) for row in rows]
        payments = [round(row["total_payments"], 2) for row in rows]
        balances = [round(row["closing_balance_total"], 2) for row in rows]
        
        # 计算趋势指标
        trend_analysis = self._analyze_trends(expenses, payments, balances)
        
        return {
            "labels": labels,
            "expenses": expenses,
            "payments": payments,
            "balances": balances,
            "count": len(rows),
            "trend_analysis": trend_analysis
        }
    
    def _analyze_trends(self, expenses: List[float], payments: List[float], balances: List[float]) -> Dict[str, Any]:
        """
        分析趋势特征
        """
        if len(expenses) < 2:
            return {}
        
        # 计算月环比
        expense_change = ((expenses[-1] - expenses[0]) / expenses[0] * 100) if expenses[0] > 0 else 0
        payment_change = ((payments[-1] - payments[0]) / payments[0] * 100) if payments[0] > 0 else 0
        balance_change = ((balances[-1] - balances[0]) / balances[0] * 100) if balances[0] > 0 else 0
        
        # 判断趋势方向
        expense_trend = "上升" if expense_change > 5 else ("下降" if expense_change < -5 else "稳定")
        payment_trend = "上升" if payment_change > 5 else ("下降" if payment_change < -5 else "稳定")
        balance_trend = "上升" if balance_change > 5 else ("下降" if balance_change < -5 else "稳定")
        
        return {
            "expense_change_pct": round(expense_change, 2),
            "payment_change_pct": round(payment_change, 2),
            "balance_change_pct": round(balance_change, 2),
            "expense_trend": expense_trend,
            "payment_trend": payment_trend,
            "balance_trend": balance_trend
        }
