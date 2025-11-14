"""
AI预测引擎服务
基于 monthly_statements 表历史数据预测未来3个月财务趋势
Safe for AI V3 Stable Baseline
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any


class PredictEngine:
    def __init__(self):
        self.db_path = "db/smart_loan_manager.db"
    
    def predict_next_3_months(self, customer_id: int) -> Dict[str, Any]:
        """
        基于历史数据预测未来3个月的财务状况
        
        Returns:
            {
                "historical": [...],  # 历史12个月数据
                "predictions": [...], # 未来3个月预测
                "confidence": 0.85,   # 预测置信度
                "summary": {...}      # 汇总信息
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取最近12个月的历史数据
        cursor.execute("""
            SELECT 
                statement_month,
                closing_balance_total,
                owner_expenses + gz_expenses as total_expenses,
                owner_payments + gz_payments as total_payments,
                previous_balance_total
            FROM monthly_statements
            WHERE customer_id = ?
            ORDER BY statement_month DESC
            LIMIT 12
        """, (customer_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                "error": "No historical data found",
                "historical": [],
                "predictions": [],
                "confidence": 0
            }
        
        # 转换为字典列表
        historical = [dict(row) for row in rows]
        historical.reverse()  # 按时间正序
        
        # 计算平均值用于预测
        avg_expenses = sum(h["total_expenses"] for h in historical) / len(historical)
        avg_payments = sum(h["total_payments"] for h in historical) / len(historical)
        
        # 计算趋势斜率（简化线性回归）
        if len(historical) >= 3:
            recent_3_expenses = [h["total_expenses"] for h in historical[-3:]]
            expense_trend = (recent_3_expenses[-1] - recent_3_expenses[0]) / 3
        else:
            expense_trend = 0
        
        # 生成未来3个月预测
        predictions = []
        last_balance = historical[-1]["closing_balance_total"]
        last_month = historical[-1]["statement_month"]
        
        for i in range(1, 4):
            # 计算下一个月份
            next_month = self._get_next_month(last_month, i)
            
            # 预测支出（带趋势）
            predicted_expenses = avg_expenses + (expense_trend * i)
            predicted_payments = avg_payments
            
            # 预测余额
            predicted_balance = last_balance + predicted_expenses - predicted_payments
            
            predictions.append({
                "statement_month": next_month,
                "predicted_expenses": round(predicted_expenses, 2),
                "predicted_payments": round(predicted_payments, 2),
                "predicted_balance": round(predicted_balance, 2),
                "confidence": self._calculate_confidence(historical)
            })
        
        # 汇总信息
        summary = {
            "avg_monthly_expenses": round(avg_expenses, 2),
            "avg_monthly_payments": round(avg_payments, 2),
            "expense_trend": "上升" if expense_trend > 0 else "下降",
            "trend_value": round(expense_trend, 2)
        }
        
        return {
            "historical": historical[-6:],  # 只返回最近6个月
            "predictions": predictions,
            "confidence": self._calculate_confidence(historical),
            "summary": summary
        }
    
    def _get_next_month(self, base_month: str, offset: int) -> str:
        """
        计算下一个月份
        base_month: "2024-11"
        offset: 1 -> "2024-12"
        """
        year, month = map(int, base_month.split('-'))
        
        for _ in range(offset):
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        return f"{year}-{month:02d}"
    
    def _calculate_confidence(self, historical: List[Dict]) -> float:
        """
        计算预测置信度
        基于数据完整性和稳定性
        """
        if len(historical) < 3:
            return 0.5
        elif len(historical) < 6:
            return 0.7
        elif len(historical) < 12:
            return 0.85
        else:
            # 计算方差来判断数据稳定性
            expenses = [h["total_expenses"] for h in historical]
            avg = sum(expenses) / len(expenses)
            variance = sum((x - avg) ** 2 for x in expenses) / len(expenses)
            
            # 方差小说明数据稳定，置信度高
            if variance < avg * 0.2:
                return 0.95
            elif variance < avg * 0.5:
                return 0.85
            else:
                return 0.75
