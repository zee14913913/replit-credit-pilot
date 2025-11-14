"""
LoanEligibilityEngine - 贷款资格计算引擎
基于标准化收入和CTOS commitment计算DSR/DSRC

⚠️ 债务来源：
- 仅从 CTOS 报告获取（通过API参数传入）
- 不再从 monthly_statements 的信用卡字段推导
"""
import sqlite3
from typing import Dict, Optional
from ..services.income_service import IncomeService
from sqlalchemy.orm import Session


class LoanEligibilityEngine:
    """
    贷款资格计算引擎（基于CTOS commitment）
    
    功能：
    1. 从 IncomeService 获取 dsr_income, dsrc_income
    2. 使用 CTOS 报告的 monthly_debt（API参数）
    3. 计算 DSR/DSRC 比率
    4. 评估资格状态（Eligible/Borderline/Not Eligible）
    
    ⚠️ 债务来源：仅从 CTOS 报告获取，不再从 monthly_statements 推导
    """
    
    DB_PATH = "db/smart_loan_manager.db"
    
    @classmethod
    def calculate(
        cls,
        db: Session,
        customer_id: int,
        company_id: int = 1,
        monthly_debt: Optional[float] = None
    ) -> Dict:
        """
        计算客户贷款资格（基于CTOS commitment）
        
        Args:
            db: SQLAlchemy Session (用于 IncomeService)
            customer_id: 客户ID
            company_id: 公司ID
            monthly_debt: 月度债务（从CTOS报告获取，必填）
            
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
        
        dsr_income = income_data.get("dsr_income") or 0.0
        dsrc_income = income_data.get("dsrc_income") or 0.0
        best_source = income_data.get("best_source")
        income_confidence = income_data.get("confidence", 0.0)
        
        # ⚠️ 债务数据必须从CTOS报告获取
        if monthly_debt is None:
            return {
                "customer_id": customer_id,
                "error": "missing_commitment_data",
                "message": "月度债务数据缺失，请上传CTOS报告或手动输入commitment数据",
                "dsr_income": round(dsr_income, 2),
                "dsrc_income": round(dsrc_income, 2),
                "best_source": best_source,
                "income_confidence": round(income_confidence, 4),
                "total_monthly_debt": 0.0,
                "dsr_ratio": None,
                "dsrc_ratio": None,
                "eligibility_status": "Missing Commitment Data",
                "recommended_loan_amount": 0.0
            }
        
        total_monthly_debt = monthly_debt
        
        invalid_dsr_income = dsr_income <= 0
        invalid_dsrc_income = dsrc_income <= 0
        
        if invalid_dsr_income:
            return {
                "customer_id": customer_id,
                "dsr_income": round(dsr_income, 2),
                "dsrc_income": round(dsrc_income, 2),
                "best_source": best_source,
                "income_confidence": round(income_confidence, 4),
                "total_monthly_debt": round(total_monthly_debt, 2),
                "dsr_ratio": None,
                "dsrc_ratio": None,
                "eligibility_status": "Not Eligible - Invalid Income",
                "recommended_loan_amount": 0.0
            }
        
        dsr_ratio = total_monthly_debt / dsr_income
        dsrc_ratio = total_monthly_debt / dsrc_income if not invalid_dsrc_income else None
        
        eligibility_status = cls._determine_eligibility(dsr_ratio)
        
        recommended_loan_amount = dsrc_income * 8 if not invalid_dsrc_income else 0.0
        
        return {
            "customer_id": customer_id,
            "dsr_income": round(dsr_income, 2),
            "dsrc_income": round(dsrc_income, 2),
            "best_source": best_source,
            "income_confidence": round(income_confidence, 4),
            "total_monthly_debt": round(total_monthly_debt, 2),
            "dsr_ratio": round(dsr_ratio, 4) if dsr_ratio is not None else None,
            "dsrc_ratio": round(dsrc_ratio, 4) if dsrc_ratio is not None else None,
            "eligibility_status": eligibility_status,
            "recommended_loan_amount": round(recommended_loan_amount, 2)
        }
    
    
    @classmethod
    def _determine_eligibility(cls, dsr_ratio: float) -> str:
        """
        根据DSR比率确定资格状态
        
        DSR规则:
        - DSR ≤ 0.6 → Eligible
        - 0.6 < DSR ≤ 0.8 → Borderline
        - DSR > 0.8 → Not Eligible
        
        Args:
            dsr_ratio: DSR比率（必须是有效值，无效收入在调用前已处理）
            
        Returns:
            资格状态
        """
        if dsr_ratio <= 0.6:
            return "Eligible"
        elif dsr_ratio <= 0.8:
            return "Borderline"
        else:
            return "Not Eligible"
