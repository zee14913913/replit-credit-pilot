"""
月结任务模块
在Replit上通过外部定时器触发（因为没有原生cron）
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from decimal import Decimal

from ..models import BankStatement, Company, JournalEntry, JournalEntryLine, ChartOfAccounts
from ..routes.invoices import auto_generate_invoices
from ..schemas import AutoInvoiceGenerate
from ..services.management_report_generator import ManagementReportGenerator
from ..services.file_storage_manager import AccountingFileStorageManager
import json
import logging

logger = logging.getLogger(__name__)


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
    
    # 4. 生成并保存Management Report（新增自动化任务）
    management_report_result = None
    try:
        logger.info(f"月结任务：开始生成Management Report (company_id={company_id}, month={month})")
        
        report_generator = ManagementReportGenerator(db, company_id)
        report_data = report_generator.generate_monthly_report(month, include_details=True)
        
        # 保存Management Report JSON到FileStorageManager
        report_path = AccountingFileStorageManager.generate_management_report_path(
            company_id=company_id,
            report_month=month,
            file_extension='json'
        )
        
        report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
        success = AccountingFileStorageManager.save_text_content(report_path, report_json)
        
        if success:
            logger.info(f"Management Report已保存到: {report_path}")
            management_report_result = {
                "success": True,
                "report_path": report_path,
                "balance_sheet_balanced": report_data.get('balance_sheet_summary', {}).get('balance_check') == 0,
                "total_revenue": report_data.get('pnl_summary', {}).get('total_revenue'),
                "total_expenses": report_data.get('pnl_summary', {}).get('total_expenses')
            }
        else:
            management_report_result = {"success": False, "error": "文件保存失败"}
            
    except Exception as e:
        logger.error(f"生成Management Report失败: {str(e)}", exc_info=True)
        management_report_result = {"success": False, "error": str(e)}
    
    return {
        "success": True,
        "company_id": company_id,
        "company_name": company.company_name,
        "month": month,
        "completed_at": datetime.now().isoformat(),
        "unmatched_transactions": unmatched_count,
        "trial_balance": trial_balance,
        "auto_invoices": invoice_result,
        "management_report": management_report_result
    }


def calculate_trial_balance(db: Session, company_id: int, month: str):
    """
    计算试算表 - 从真实的journal_entry_lines汇总
    
    返回：
    - 每个会计科目的借方、贷方、余额
    - 总借方、总贷方
    - 是否平衡
    """
    # 解析月份范围（YYYY-MM）
    year, month_num = map(int, month.split('-'))
    start_date = datetime(year, month_num, 1)
    if month_num == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month_num + 1, 1)
    
    # 查询本月所有的journal_entry_lines
    lines = db.query(
        JournalEntryLine.account_id,
        ChartOfAccounts.account_code,
        ChartOfAccounts.account_name,
        func.sum(JournalEntryLine.debit_amount).label('total_debit'),
        func.sum(JournalEntryLine.credit_amount).label('total_credit')
    ).join(
        JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
    ).join(
        ChartOfAccounts, JournalEntryLine.account_id == ChartOfAccounts.id
    ).filter(
        and_(
            JournalEntry.company_id == company_id,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date < end_date
        )
    ).group_by(
        JournalEntryLine.account_id,
        ChartOfAccounts.account_code,
        ChartOfAccounts.account_name
    ).all()
    
    # 汇总账户余额
    accounts = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')
    
    for line in lines:
        debit = Decimal(str(line.total_debit or 0))
        credit = Decimal(str(line.total_credit or 0))
        balance = debit - credit
        
        accounts.append({
            "account_code": line.account_code,
            "account_name": line.account_name,
            "debit": float(debit),
            "credit": float(credit),
            "balance": float(balance)
        })
        
        total_debits += debit
        total_credits += credit
    
    # 检查借贷平衡
    is_balanced = abs(total_debits - total_credits) < Decimal('0.01')
    
    return {
        "period": month,
        "accounts": accounts,
        "total_debits": float(total_debits),
        "total_credits": float(total_credits),
        "balanced": is_balanced,
        "variance": float(total_debits - total_credits)
    }
