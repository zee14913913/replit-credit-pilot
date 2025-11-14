"""
财务健康评分引擎
基于多维度指标计算客户财务健康度（0-100分）
Safe for AI V3 Stable Baseline
"""
import sqlite3
from typing import Dict, Any


class HealthEngine:
    def __init__(self):
        self.db_path = "db/smart_loan_manager.db"
    
    def calculate_health_score(self, customer_id: int) -> Dict[str, Any]:
        """
        计算财务健康评分
        
        评分维度：
        1. 信用利用率 (30分): 余额/额度比例
        2. 还款能力 (25分): 还款额/支出额比例
        3. 债务趋势 (25分): 余额变化趋势
        4. 数据完整性 (20分): 有效账单月份数量
        
        Returns:
            {
                "total_score": 85,
                "breakdown": {...},
                "grade": "优秀",
                "health_status": "健康"
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. 获取信用卡信息（额度）
        cursor.execute("""
            SELECT SUM(credit_limit) as total_limit
            FROM credit_cards
            WHERE customer_id = ?
        """, (customer_id,))
        
        credit_row = cursor.fetchone()
        total_limit = credit_row["total_limit"] or 0
        
        # 2. 获取最新余额
        cursor.execute("""
            SELECT closing_balance_total
            FROM monthly_statements
            WHERE customer_id = ?
            ORDER BY statement_month DESC
            LIMIT 1
        """, (customer_id,))
        
        balance_row = cursor.fetchone()
        current_balance = balance_row["closing_balance_total"] if balance_row else 0
        
        # 3. 获取最近6个月数据
        cursor.execute("""
            SELECT 
                closing_balance_total,
                owner_expenses + gz_expenses as total_expenses,
                owner_payments + gz_payments as total_payments
            FROM monthly_statements
            WHERE customer_id = ?
            ORDER BY statement_month DESC
            LIMIT 6
        """, (customer_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                "error": "No data found",
                "total_score": 0,
                "grade": "无数据"
            }
        
        # 计算各维度得分
        score_breakdown = {}
        
        # 1. 信用利用率得分 (30分)
        utilization_score = self._calc_utilization_score(current_balance, total_limit)
        score_breakdown["utilization"] = {
            "score": utilization_score,
            "max": 30,
            "description": "信用利用率",
            "value": f"{round(current_balance / total_limit * 100, 1)}%" if total_limit > 0 else "N/A"
        }
        
        # 2. 还款能力得分 (25分)
        avg_expenses = sum(row["total_expenses"] for row in rows) / len(rows)
        avg_payments = sum(row["total_payments"] for row in rows) / len(rows)
        payment_score = self._calc_payment_score(avg_payments, avg_expenses)
        score_breakdown["payment_ability"] = {
            "score": payment_score,
            "max": 25,
            "description": "还款能力",
            "value": f"{round(avg_payments / avg_expenses * 100, 1)}%" if avg_expenses > 0 else "N/A"
        }
        
        # 3. 债务趋势得分 (25分)
        first_balance = rows[-1]["closing_balance_total"]
        last_balance = rows[0]["closing_balance_total"]
        trend_score = self._calc_trend_score(first_balance, last_balance)
        score_breakdown["debt_trend"] = {
            "score": trend_score,
            "max": 25,
            "description": "债务趋势",
            "value": "下降" if last_balance < first_balance else "上升"
        }
        
        # 4. 数据完整性得分 (20分)
        data_score = min(len(rows) * 3.33, 20)  # 6个月数据满分
        score_breakdown["data_completeness"] = {
            "score": round(data_score, 1),
            "max": 20,
            "description": "数据完整性",
            "value": f"{len(rows)}个月"
        }
        
        # 总分
        total_score = (
            utilization_score + 
            payment_score + 
            trend_score + 
            data_score
        )
        total_score = round(total_score, 1)
        
        # 评级
        grade = self._get_grade(total_score)
        health_status = self._get_health_status(total_score)
        
        return {
            "total_score": total_score,
            "breakdown": score_breakdown,
            "grade": grade,
            "health_status": health_status,
            "current_balance": round(current_balance, 2),
            "credit_limit": round(total_limit, 2)
        }
    
    def _calc_utilization_score(self, balance: float, limit: float) -> float:
        """
        信用利用率得分
        0-30%: 30分
        30-50%: 20分
        50-70%: 10分
        70-100%: 5分
        """
        if limit <= 0:
            return 15  # 无信用额度，给中等分
        
        utilization = balance / limit
        
        if utilization <= 0.3:
            return 30
        elif utilization <= 0.5:
            return 20
        elif utilization <= 0.7:
            return 10
        else:
            return 5
    
    def _calc_payment_score(self, payments: float, expenses: float) -> float:
        """
        还款能力得分
        还款/支出 >= 1.2: 25分
        >= 1.0: 20分
        >= 0.8: 15分
        >= 0.5: 10分
        < 0.5: 5分
        """
        if expenses <= 0:
            return 15
        
        ratio = payments / expenses
        
        if ratio >= 1.2:
            return 25
        elif ratio >= 1.0:
            return 20
        elif ratio >= 0.8:
            return 15
        elif ratio >= 0.5:
            return 10
        else:
            return 5
    
    def _calc_trend_score(self, first_balance: float, last_balance: float) -> float:
        """
        债务趋势得分
        余额下降 > 10%: 25分
        余额下降 0-10%: 20分
        余额稳定: 15分
        余额上升 0-10%: 10分
        余额上升 > 10%: 5分
        """
        if first_balance <= 0:
            return 15
        
        change_pct = (last_balance - first_balance) / first_balance * 100
        
        if change_pct < -10:
            return 25
        elif change_pct < 0:
            return 20
        elif change_pct < 10:
            return 15
        elif change_pct < 20:
            return 10
        else:
            return 5
    
    def _get_grade(self, score: float) -> str:
        """评级"""
        if score >= 90:
            return "优秀"
        elif score >= 75:
            return "良好"
        elif score >= 60:
            return "中等"
        elif score >= 40:
            return "较差"
        else:
            return "警告"
    
    def _get_health_status(self, score: float) -> str:
        """健康状态"""
        if score >= 80:
            return "健康"
        elif score >= 60:
            return "正常"
        elif score >= 40:
            return "需关注"
        else:
            return "高风险"
