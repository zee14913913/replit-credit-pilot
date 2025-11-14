"""
Loan Affordability Engine Service

个人贷款承受能力计算引擎
基于 Phase A (收入系统) + CTOS Commitment 计算可承受的最大贷款额度

⚠️ 债务来源：
- 仅从 CTOS 报告获取（通过API参数传入）
- 不再从 monthly_statements 的信用卡字段推导

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
import sqlite3
import math

from accounting_app.models import Customer
from accounting_app.services.income_service import IncomeService


class LoanAffordabilityEngine:
    """个人贷款承受能力计算引擎"""
    
    DB_PATH = "db/smart_loan_manager.db"
    
    # 马来西亚银行真实 DSR 标准
    RECOMMENDED_DSR_LIMIT = 0.75
    MAX_DSR_LIMIT = 0.85
    
    # 标准贷款利率（用于反推贷款金额）
    DEFAULT_ANNUAL_RATE = 0.065  # 6.5% reducing balance
    
    @classmethod
    def calculate_affordability(
        cls,
        db: Session,
        customer_id: int,
        company_id: int = 1,
        monthly_commitment: Optional[float] = None
    ) -> Dict:
        """
        计算客户可承受的最大贷款额度（基于CTOS commitment）
        
        流程：
        1. 从 IncomeService 获取收入数据
        2. 使用CTOS报告的当前承诺还款（API参数）
        3. 计算可承受月供（推荐和严格限制）
        4. 反推各期限的最大贷款金额
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            company_id: 公司ID
            monthly_commitment: 当前月度承诺还款（从CTOS报告获取，必填）
            
        Returns:
            {
                "customer_id": int,
                "income": float,
                "commitment": float,
                "recommended_dsr_limit": float,
                "max_dsr_limit": float,
                "max_monthly_payment_recommended": float,
                "max_monthly_payment_strict": float,
                "affordability": {
                    "tenure_12": float,
                    "tenure_24": float,
                    "tenure_36": float,
                    "tenure_60": float,
                    "tenure_84": float
                },
                "income_source": str,
                "confidence": float
            }
        """
        # 1. 获取客户验证
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "客户不存在"}
        
        # 2. 获取收入数据
        income_data = IncomeService.get_customer_income(db, customer_id, company_id)
        if not income_data:
            return {"error": "无法获取客户收入数据"}
        
        dsr_income = income_data.get("dsr_income", 0.0)
        dsrc_income = income_data.get("dsrc_income", 0.0)
        best_source = income_data.get("best_source", "unknown")
        confidence = income_data.get("confidence", 0.0)
        
        if dsr_income <= 0:
            return {"error": "客户收入无效"}
        
        # 3. 验证当前月度承诺还款（必须从CTOS获取）
        if monthly_commitment is None:
            return {
                "error": "missing_commitment_data",
                "message": "Debt commitment is required based on CTOS.",
                "customer_id": customer_id,
                "income": round(dsr_income, 2),
                "commitment": 0.0,
                "data_source": best_source,
                "confidence": round(confidence, 4)
            }
        
        # ⚠️ Zero-Debt 保护
        if monthly_commitment == 0:
            max_capacity_recommended = dsr_income * cls.RECOMMENDED_DSR_LIMIT
            max_capacity_strict = dsr_income * cls.MAX_DSR_LIMIT
            
            affordability = {}
            tenures = [12, 24, 36, 60, 84]
            for tenure in tenures:
                max_loan = cls._reverse_calculate_max_loan(
                    monthly_payment=max_capacity_recommended,
                    annual_rate=cls.DEFAULT_ANNUAL_RATE,
                    tenure_months=tenure
                )
                affordability[f"tenure_{tenure}"] = round(max_loan, 2)
            
            return {
                "customer_id": customer_id,
                "income": round(dsr_income, 2),
                "commitment": 0.0,
                "eligibility": "Eligible (Zero Debt)",
                "recommended_dsr_limit": cls.RECOMMENDED_DSR_LIMIT,
                "max_dsr_limit": cls.MAX_DSR_LIMIT,
                "max_monthly_payment_recommended": round(max_capacity_recommended, 2),
                "max_monthly_payment_strict": round(max_capacity_strict, 2),
                "affordability": affordability,
                "data_source": best_source,
                "threshold": cls.RECOMMENDED_DSR_LIMIT,
                "threshold_type": "Standard",
                "available_capacity": round(max_capacity_recommended, 2),
                "confidence": round(confidence, 4)
            }
        
        # 4. 计算可承受月供
        max_monthly_payment_recommended = dsr_income * cls.RECOMMENDED_DSR_LIMIT - monthly_commitment
        max_monthly_payment_strict = dsr_income * cls.MAX_DSR_LIMIT - monthly_commitment
        
        # 确保不为负数
        max_monthly_payment_recommended = max(0.0, max_monthly_payment_recommended)
        max_monthly_payment_strict = max(0.0, max_monthly_payment_strict)
        
        # 5. 反推各期限的最大贷款金额（使用推荐DSR限制）
        affordability = {}
        tenures = [12, 24, 36, 60, 84]
        
        for tenure in tenures:
            max_loan = cls._reverse_calculate_max_loan(
                monthly_payment=max_monthly_payment_recommended,
                annual_rate=cls.DEFAULT_ANNUAL_RATE,
                tenure_months=tenure
            )
            affordability[f"tenure_{tenure}"] = round(max_loan, 2)
        
        return {
            "customer_id": customer_id,
            "income": round(dsr_income, 2),
            "commitment": round(monthly_commitment, 2),
            "dsr_income": round(dsr_income, 2),
            "dsrc_income": round(dsrc_income, 2),
            "current_monthly_debt": round(monthly_commitment, 2),
            "recommended_dsr_limit": cls.RECOMMENDED_DSR_LIMIT,
            "max_dsr_limit": cls.MAX_DSR_LIMIT,
            "max_monthly_payment_recommended": round(max_monthly_payment_recommended, 2),
            "max_monthly_payment_strict": round(max_monthly_payment_strict, 2),
            "affordability": affordability,
            "data_source": best_source,
            "income_source": best_source,
            "threshold": cls.RECOMMENDED_DSR_LIMIT,
            "threshold_type": "Standard",
            "available_capacity": round(max_monthly_payment_recommended, 2),
            "confidence": round(confidence, 4)
        }
    
    
    @classmethod
    def _reverse_calculate_max_loan(
        cls,
        monthly_payment: float,
        annual_rate: float,
        tenure_months: int
    ) -> float:
        """
        反推最大贷款金额（Reducing Balance）
        
        已知：月供、年利率、期限
        求：最大贷款本金
        
        公式反推：
        monthly_payment = principal × [r × (1+r)^n] / [(1+r)^n - 1]
        
        principal = monthly_payment × [(1+r)^n - 1] / [r × (1+r)^n]
        
        Args:
            monthly_payment: 可承受月供
            annual_rate: 年利率
            tenure_months: 贷款期限（月）
            
        Returns:
            最大贷款本金
        """
        if monthly_payment <= 0 or tenure_months <= 0:
            return 0.0
        
        if annual_rate == 0:
            # 无利息情况
            return monthly_payment * tenure_months
        
        monthly_rate = annual_rate / 12
        
        # (1 + r)^n
        power_term = math.pow(1 + monthly_rate, tenure_months)
        
        # [(1+r)^n - 1] / [r × (1+r)^n]
        denominator = monthly_rate * power_term
        numerator = power_term - 1
        
        if denominator == 0:
            return 0.0
        
        principal = monthly_payment * (numerator / denominator)
        
        return principal
