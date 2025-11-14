"""
Loan Product Engine Service

提供多贷款产品模拟功能，包括：
- 等额本息（Flat Rate）
- 等额本金（Reducing Balance）
- 信用贷款（Credit Loan）
- 商业贷款（Commercial Loan）

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from typing import Dict, List, Optional
import math


class LoanProductEngine:
    """贷款产品计算引擎"""
    
    PRODUCTS = [
        {
            "name": "Flat Rate Personal Loan",
            "interest_rate": 0.08,
            "tenure_months": 60,
            "loan_type": "flat"
        },
        {
            "name": "Reducing Balance Personal Loan",
            "interest_rate": 0.065,
            "tenure_months": 60,
            "loan_type": "reducing"
        },
        {
            "name": "Credit Loan (Short Term)",
            "interest_rate": 0.095,
            "tenure_months": 36,
            "loan_type": "flat"
        },
        {
            "name": "Housing Loan (Reducing)",
            "interest_rate": 0.045,
            "tenure_months": 360,
            "loan_type": "reducing"
        },
        {
            "name": "Commercial Loan",
            "interest_rate": 0.055,
            "tenure_months": 120,
            "loan_type": "reducing"
        }
    ]
    
    @classmethod
    def calculate_monthly_payment_flat(
        cls,
        principal: float,
        annual_rate: float,
        tenure_months: int
    ) -> Dict[str, float]:
        """
        计算等额本息（Flat Rate）月供
        
        公式：
        - 总利息 = 本金 × 年利率 × 年数
        - 月供 = (本金 + 总利息) / 总月数
        
        Args:
            principal: 贷款本金
            annual_rate: 年利率（小数形式，如 0.08 = 8%）
            tenure_months: 贷款期限（月）
            
        Returns:
            {
                "monthly_payment": 月供,
                "total_interest": 总利息,
                "total_cost": 贷款总成本
            }
        """
        if principal <= 0 or tenure_months <= 0:
            return {
                "monthly_payment": 0.0,
                "total_interest": 0.0,
                "total_cost": 0.0
            }
        
        tenure_years = tenure_months / 12
        total_interest = principal * annual_rate * tenure_years
        total_cost = principal + total_interest
        monthly_payment = total_cost / tenure_months
        
        return {
            "monthly_payment": round(monthly_payment, 2),
            "total_interest": round(total_interest, 2),
            "total_cost": round(total_cost, 2)
        }
    
    @classmethod
    def calculate_monthly_payment_reducing(
        cls,
        principal: float,
        annual_rate: float,
        tenure_months: int
    ) -> Dict[str, float]:
        """
        计算等额本金（Reducing Balance）月供
        
        公式（使用复利计算）：
        - 月利率 = 年利率 / 12
        - 月供 = 本金 × [月利率 × (1 + 月利率)^月数] / [(1 + 月利率)^月数 - 1]
        
        Args:
            principal: 贷款本金
            annual_rate: 年利率（小数形式，如 0.065 = 6.5%）
            tenure_months: 贷款期限（月）
            
        Returns:
            {
                "monthly_payment": 月供,
                "total_interest": 总利息,
                "total_cost": 贷款总成本
            }
        """
        if principal <= 0 or tenure_months <= 0:
            return {
                "monthly_payment": 0.0,
                "total_interest": 0.0,
                "total_cost": 0.0
            }
        
        if annual_rate == 0:
            monthly_payment = principal / tenure_months
            return {
                "monthly_payment": round(monthly_payment, 2),
                "total_interest": 0.0,
                "total_cost": round(principal, 2)
            }
        
        monthly_rate = annual_rate / 12
        
        numerator = monthly_rate * math.pow(1 + monthly_rate, tenure_months)
        denominator = math.pow(1 + monthly_rate, tenure_months) - 1
        monthly_payment = principal * (numerator / denominator)
        
        total_cost = monthly_payment * tenure_months
        total_interest = total_cost - principal
        
        return {
            "monthly_payment": round(monthly_payment, 2),
            "total_interest": round(total_interest, 2),
            "total_cost": round(total_cost, 2)
        }
    
    @classmethod
    def calculate_tenure_options(
        cls,
        principal: float,
        annual_rate: float,
        loan_type: str = "reducing"
    ) -> List[Dict]:
        """
        计算不同期限的贷款选项
        
        Args:
            principal: 贷款本金
            annual_rate: 年利率
            loan_type: 贷款类型（"flat" 或 "reducing"）
            
        Returns:
            [
                {
                    "tenure_months": 36,
                    "monthly_payment": xxx,
                    "total_interest": xxx,
                    "total_cost": xxx
                },
                ...
            ]
        """
        tenure_options = [12, 24, 36, 48, 60, 84, 120, 180, 240, 300, 360]
        results = []
        
        for tenure in tenure_options:
            if loan_type == "flat":
                calculation = cls.calculate_monthly_payment_flat(
                    principal, annual_rate, tenure
                )
            else:
                calculation = cls.calculate_monthly_payment_reducing(
                    principal, annual_rate, tenure
                )
            
            results.append({
                "tenure_months": tenure,
                **calculation
            })
        
        return results
    
    @classmethod
    def simulate_all_products(
        cls,
        loan_amount: float,
        custom_products: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        模拟所有贷款产品
        
        Args:
            loan_amount: 贷款金额
            custom_products: 自定义产品列表（可选）
            
        Returns:
            [
                {
                    "name": "产品名称",
                    "interest_rate": 利率,
                    "tenure_months": 期限,
                    "monthly_payment": 月供,
                    "total_interest": 总利息,
                    "total_cost": 总成本
                },
                ...
            ]
        """
        products = custom_products or cls.PRODUCTS
        results = []
        
        for product in products:
            loan_type = product.get("loan_type", "reducing")
            
            if loan_type == "flat":
                calculation = cls.calculate_monthly_payment_flat(
                    loan_amount,
                    product["interest_rate"],
                    product["tenure_months"]
                )
            else:
                calculation = cls.calculate_monthly_payment_reducing(
                    loan_amount,
                    product["interest_rate"],
                    product["tenure_months"]
                )
            
            results.append({
                "name": product["name"],
                "interest_rate": product["interest_rate"],
                "tenure_months": product["tenure_months"],
                **calculation
            })
        
        return results
