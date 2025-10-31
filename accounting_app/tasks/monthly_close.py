"""
月结任务模块
在Replit上通过外部定时器触发（因为没有原生cron）
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal

from ..models import BankStatement, Company
from ..routes.invoices import auto_generate_invoices
from ..schemas import AutoInvoiceGenerate


def run_monthly_close(db: Session, company_id: int, month: str):
    """
    执行月结任务
    
    步骤：
    1. 检查本月是否还有未匹配的银行流水
    2. 自动生成本月的试算表（Trial Balance）
    3. 根据自动发票规则生成当月发票
    
    返回：月结报告
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return {
            "success": False,
            "error": f"Company {company_id} not found"
        }
    
    # 1. 检查未匹配的银行流水
    unmatched_count = db.query(func.count(BankStatement.id)).filter(
        BankStatement.company_id == company_id,
        BankStatement.statement_month == month,
        BankStatement.matched == False
    ).scalar()
    
    # 2. 计算试算表（简化版）
    trial_balance = calculate_trial_balance(db, company_id, month)
    
    # 3. 自动生成发票
    invoice_result = None
    try:
        request = AutoInvoiceGenerate(company_id=company_id, month=month)
        invoice_result = auto_generate_invoices(request, db)
    except Exception as e:
        invoice_result = {"error": str(e)}
    
    return {
        "success": True,
        "company_id": company_id,
        "company_name": company.company_name,
        "month": month,
        "completed_at": datetime.now().isoformat(),
        "unmatched_transactions": unmatched_count,
        "trial_balance": trial_balance,
        "auto_invoices": invoice_result
    }


def calculate_trial_balance(db: Session, company_id: int, month: str):
    """
    计算试算表
    
    TODO: 实际应从journal_entry_lines汇总
    这里返回简化版示例
    """
    return {
        "period": month,
        "total_debits": 100000.00,
        "total_credits": 100000.00,
        "balanced": True,
        "note": "Trial balance calculation is simplified in this version"
    }
