"""
LoanEligibilityEngine - 贷款资格计算引擎
基于标准化收入和月结单债务计算DSR/DSRC
"""
import sqlite3
from typing import Dict, Optional
from ..services.income_service import IncomeService
from sqlalchemy.orm import Session


class LoanEligibilityEngine:
    """
    贷款资格计算引擎
    
    功能：
    1. 从 IncomeStandardizer 获取 dsr_income, dsrc_income
    2. 从 monthly_statements 计算 total_monthly_debt
    3. 计算 DSR/DSRC 比率
    4. 评估资格状态（Eligible/Borderline/Not Eligible）
    """
    
    DB_PATH = "db/smart_loan_manager.db"
    
    @classmethod
    def calculate(
        cls,
        db: Session,
        customer_id: int,
        company_id: int = 1
    ) -> Dict:
        """
        计算客户贷款资格
        
        Args:
            db: SQLAlchemy Session (用于 IncomeService)
            customer_id: 客户ID
            company_id: 公司ID
            
        Returns:
            {
                "customer_id": 客户ID,
                "dsr_income": DSR计算用收入,
                "dsrc_income": DSRC计算用收入,
                "best_source": 收入来源,
                "income_confidence": 收入置信度,
                "total_monthly_debt": 月度债务总额,
                "dsr_ratio": DSR比率,
                "dsrc_ratio": DSRC比率,
                "eligibility_status": 资格状态,
                "recommended_loan_amount": 建议贷款额度
            }
        """
        
        income_data = IncomeService.get_customer_income(db, customer_id, company_id)
        
        if not income_data:
            return {
                "customer_id": customer_id,
                "error": "未找到收入数据，请先上传收入证明文件",
                "dsr_income": 0.0,
                "dsrc_income": 0.0,
                "best_source": None,
                "income_confidence": 0.0,
                "total_monthly_debt": 0.0,
                "dsr_ratio": 0.0,
                "dsrc_ratio": 0.0,
                "eligibility_status": "No Income Data",
                "recommended_loan_amount": 0.0
            }
        
        dsr_income = income_data.get("dsr_income", 0.0)
        dsrc_income = income_data.get("dsrc_income", 0.0)
        best_source = income_data.get("best_source")
        income_confidence = income_data.get("confidence", 0.0)
        
        total_monthly_debt = cls._calculate_monthly_debt(customer_id)
        
        dsr_ratio = total_monthly_debt / dsr_income if dsr_income > 0 else 0.0
        dsrc_ratio = total_monthly_debt / dsrc_income if dsrc_income > 0 else 0.0
        
        eligibility_status = cls._determine_eligibility(dsr_ratio)
        
        recommended_loan_amount = dsrc_income * 8 if dsrc_income > 0 else 0.0
        
        return {
            "customer_id": customer_id,
            "dsr_income": round(dsr_income, 2),
            "dsrc_income": round(dsrc_income, 2),
            "best_source": best_source,
            "income_confidence": round(income_confidence, 4),
            "total_monthly_debt": round(total_monthly_debt, 2),
            "dsr_ratio": round(dsr_ratio, 4),
            "dsrc_ratio": round(dsrc_ratio, 4),
            "eligibility_status": eligibility_status,
            "recommended_loan_amount": round(recommended_loan_amount, 2)
        }
    
    @classmethod
    def _calculate_monthly_debt(cls, customer_id: int) -> float:
        """
        从 monthly_statements 计算月度债务
        
        债务计算公式：
        - min_payment = closing_balance_total * 0.05
        - total_monthly_debt = owner_payments + gz_payments + min_payment
        
        Args:
            customer_id: 客户ID
            
        Returns:
            月度债务总额
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    closing_balance_total,
                    owner_payments,
                    gz_payments
                FROM monthly_statements
                WHERE customer_id = ?
                ORDER BY statement_month DESC
                LIMIT 1
            ''', (customer_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return 0.0
            
            closing_balance_total = result[0] or 0.0
            owner_payments = result[1] or 0.0
            gz_payments = result[2] or 0.0
            
            min_payment = closing_balance_total * 0.05
            
            total_monthly_debt = owner_payments + gz_payments + min_payment
            
            return total_monthly_debt
            
        except Exception as e:
            print(f"Error calculating monthly debt: {e}")
            return 0.0
    
    @classmethod
    def _determine_eligibility(cls, dsr_ratio: float) -> str:
        """
        根据DSR比率确定资格状态
        
        DSR规则:
        - DSR ≤ 0.6 → Eligible
        - 0.6 < DSR ≤ 0.8 → Borderline
        - DSR > 0.8 → Not Eligible
        
        Args:
            dsr_ratio: DSR比率
            
        Returns:
            资格状态
        """
        if dsr_ratio <= 0.6:
            return "Eligible"
        elif dsr_ratio <= 0.8:
            return "Borderline"
        else:
            return "Not Eligible"
