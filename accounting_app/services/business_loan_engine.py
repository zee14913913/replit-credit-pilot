"""
Business Loan Engine Service

提供企业贷款（SME Loan）评估功能，基于 DSCR（Debt Service Coverage Ratio）计算

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
        company_id: int = 1
    ) -> Dict:
        """
        计算企业贷款资格（基于DSCR）
        
        DSCR (Debt Service Coverage Ratio) = Operating Income / Annual Debt Service
        
        分类规则：
        - DSCR ≥ 1.25 → Eligible
        - 1.00 ≤ DSCR < 1.25 → Borderline
        - DSCR < 1.00 → Not Eligible
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            company_id: 公司ID
            
        Returns:
            {
                "customer_id": int,
                "operating_income": float,
                "annual_debt_service": float,
                "monthly_debt_service": float,
                "dscr": float,
                "eligibility_status": str,
                "max_debt_service": float,
                "available_capacity": float,
                "max_annual_loan": float,
                "max_monthly_loan": float
            }
        """
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
        
        monthly_debt = cls._calculate_monthly_debt_service(customer_id)
        
        if monthly_debt is None or monthly_debt <= 0:
            max_capacity = operating_income * 0.8
            return {
                "customer_id": customer_id,
                "operating_income": round(operating_income, 2),
                "annual_debt_service": 0.0,
                "monthly_debt_service": 0.0,
                "dscr": None,
                "eligibility_status": "No Debt Data - Full Capacity Available",
                "max_debt_service": round(max_capacity, 2),
                "available_capacity": round(max_capacity, 2),
                "max_annual_loan": round(max_capacity, 2),
                "max_monthly_loan": round(max_capacity / 12, 2)
            }
        
        annual_debt_service = monthly_debt * 12
        dscr = operating_income / annual_debt_service
        eligibility_status = cls._determine_eligibility(dscr)
        
        max_debt_service = operating_income * 0.8
        
        available_capacity = max(0, max_debt_service - annual_debt_service)
        
        max_annual_loan = available_capacity
        max_monthly_loan = available_capacity / 12 if available_capacity > 0 else 0.0
        
        return {
            "customer_id": customer_id,
            "operating_income": round(operating_income, 2),
            "annual_debt_service": round(annual_debt_service, 2),
            "monthly_debt_service": round(monthly_debt, 2),
            "dscr": round(dscr, 4) if dscr != float('inf') else 999.9999,
            "eligibility_status": eligibility_status,
            "max_debt_service": round(max_debt_service, 2),
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
    def _calculate_monthly_debt_service(
        cls,
        customer_id: int
    ) -> Optional[float]:
        """
        计算月度债务服务
        
        从最新的月结单提取：
        - owner_payments（户主还款）
        - gz_payments（GZ还款）
        - min_payment = closing_balance_total × 0.05（最低还款）
        
        Args:
            customer_id: 客户ID
            
        Returns:
            月度债务服务总额，如果无月结单则返回None
        """
        conn = None
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
            
            if not result:
                return None
            
            closing_balance = result[0] or 0.0
            owner_payments = result[1] or 0.0
            gz_payments = result[2] or 0.0
            
            min_payment = closing_balance * 0.05
            
            total_monthly_debt = owner_payments + gz_payments + min_payment
            
            return total_monthly_debt
            
        except Exception as e:
            print(f"计算月度债务失败: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
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
