"""
Business Loan Engine Service

提供企业贷款（SME Loan）评估功能，基于 DSCR（Debt Service Coverage Ratio）计算

⚠️ 收入来源：仅从 JournalEntry 会计账目获取
⚠️ 债务来源：仅从 CTOS 报告获取（通过API参数传入）
⚠️ 不再从 monthly_statements 的信用卡字段推导收入或债务

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
import sqlite3

from accounting_app.models import (
    Customer,
    JournalEntry,
    JournalEntryLine,
    ChartOfAccounts
)


class BusinessLoanEngine:
    """企业贷款计算引擎（基于DSCR）"""
    
    DB_PATH = "db/smart_loan_manager.db"
    
    @classmethod
    def calculate_dscr(
        cls,
        db: Session,
        customer_id: int,
        company_id: int = 1,
        annual_commitment: Optional[float] = None
    ) -> Dict:
        """
        计算企业贷款资格（基于DSCR）
        
        DSCR (Debt Service Coverage Ratio) = Operating Income / Annual Commitment
        
        ⚠️ 收入：从 JournalEntry 会计账目获取
        ⚠️ 债务：从 CTOS 报告获取（API参数）
        
        分类规则：
        - DSCR ≥ 1.25 → Eligible
        - 1.00 ≤ DSCR < 1.25 → Borderline
        - DSCR < 1.00 → Not Eligible
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            company_id: 公司ID
            annual_commitment: 年度承诺还款（从CTOS报告获取，必填）
            
        Returns:
            {
                "customer_id": int,
                "income": float,
                "commitment": float,
                "dscr": float,
                "eligibility_status": str,
                "max_debt_service": float,
                "available_capacity": float,
                "max_annual_loan": float,
                "max_monthly_loan": float
            }
        """
        # 从会计账目获取营业收入
        operating_income = cls._get_operating_income(db, customer_id, company_id)
        
        if operating_income is None or operating_income <= 0:
            return {
                "customer_id": customer_id,
                "error": "无法获取企业营业收入数据",
                "operating_income": 0.0,
                "annual_debt_service": 0.0,
                "monthly_debt_service": 0.0,
                "dscr": None,
                "eligibility_status": "Not Eligible - No Operating Income",
                "max_debt_service": 0.0,
                "available_capacity": 0.0,
                "max_annual_loan": 0.0,
                "max_monthly_loan": 0.0
            }
        
        # ⚠️ 债务数据必须从CTOS报告获取
        if annual_commitment is None:
            return {
                "customer_id": customer_id,
                "error": "missing_commitment_data",
                "message": "Debt commitment is required based on CTOS.",
                "income": round(operating_income, 2),
                "commitment": 0.0,
                "dscr": None,
                "eligibility": "Missing Commitment Data",
                "data_source": "journal",
                "threshold": 1.25,
                "threshold_type": "Standard",
                "available_capacity": 0.0
            }
        
        # ⚠️ Zero-Debt 保护
        if annual_commitment == 0:
            max_capacity = operating_income * 0.8
            return {
                "customer_id": customer_id,
                "income": round(operating_income, 2),
                "commitment": 0.0,
                "dscr": float("inf"),
                "eligibility": "Eligible (Zero Debt)",
                "eligibility_status": "Eligible (Zero Debt)",
                "data_source": "journal",
                "threshold": 1.25,
                "threshold_type": "Standard",
                "available_capacity": round(max_capacity, 2),
                "max_annual_loan": round(max_capacity, 2),
                "max_monthly_loan": round(max_capacity / 12, 2)
            }
        
        dscr = operating_income / annual_commitment
        monthly_commitment = annual_commitment / 12
        eligibility_status = cls._determine_eligibility(dscr)
        
        max_commitment_capacity = operating_income * 0.8
        
        available_capacity = max(0, max_commitment_capacity - annual_commitment)
        
        max_annual_loan = available_capacity
        max_monthly_loan = available_capacity / 12 if available_capacity > 0 else 0.0
        
        return {
            "customer_id": customer_id,
            "income": round(operating_income, 2),
            "commitment": round(annual_commitment, 2),
            "dscr": round(dscr, 4) if dscr != float('inf') else 999.9999,
            "eligibility": eligibility_status,
            "eligibility_status": eligibility_status,
            "data_source": "journal",
            "threshold": 1.25,
            "threshold_type": "Standard",
            "available_capacity": round(available_capacity, 2),
            "max_annual_loan": round(max_annual_loan, 2),
            "max_monthly_loan": round(max_monthly_loan, 2)
        }
    
    @classmethod
    def _get_operating_income(
        cls,
        db: Session,
        customer_id: int,
        company_id: int
    ) -> Optional[float]:
        """
        获取企业营业收入
        
        从以下来源提取（优先级从高到低）：
        1. JournalEntry的收入科目汇总（过去12个月）- 最准确
        2. Customer表的annual_income字段（如果有）
        3. 从IncomeService获取的dsrc_income × 12（个人转企业）
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            company_id: 公司ID
            
        Returns:
            年度营业收入，如果无法获取则返回None
        """
        try:
            period_end = datetime.now()
            period_start = period_end - timedelta(days=365)
            
            income_query = (
                db.query(
                    func.sum(JournalEntryLine.credit_amount - JournalEntryLine.debit_amount).label('total_income')
                )
                .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
                .join(ChartOfAccounts, ChartOfAccounts.id == JournalEntryLine.account_id)
                .filter(
                    ChartOfAccounts.company_id == company_id,
                    JournalEntry.company_id == company_id,
                    JournalEntry.entry_date >= period_start,
                    JournalEntry.entry_date < period_end,
                    JournalEntry.status == 'posted',
                    ChartOfAccounts.account_type == 'income'
                )
            )
            
            result = income_query.first()
            
            if result and result.total_income:
                total_income = float(Decimal(str(result.total_income)))
                if total_income > 0:
                    return total_income
            
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return None
            
            if hasattr(customer, 'annual_income') and customer.annual_income:
                return float(customer.annual_income)
            
            try:
                from accounting_app.services.income_service import IncomeService
                
                income_data = IncomeService.get_customer_income(
                    db=db,
                    customer_id=customer_id,
                    company_id=company_id
                )
                
                if income_data:
                    dsrc_income = income_data.get("dsrc_income") or 0.0
                    if dsrc_income > 0:
                        return dsrc_income * 12
            except Exception as e:
                print(f"无法从IncomeService获取收入: {e}")
            
            return None
            
        except Exception as e:
            print(f"获取营业收入失败: {e}")
            return None
    
    
    @classmethod
    def _determine_eligibility(cls, dscr: float) -> str:
        """
        根据DSCR确定资格状态
        
        规则：
        - DSCR ≥ 1.25 → Eligible
        - 1.00 ≤ DSCR < 1.25 → Borderline
        - DSCR < 1.00 → Not Eligible
        
        Args:
            dscr: DSCR比率
            
        Returns:
            资格状态
        """
        if dscr >= 1.25:
            return "Eligible"
        elif dscr >= 1.00:
            return "Borderline"
        else:
            return "Not Eligible"
