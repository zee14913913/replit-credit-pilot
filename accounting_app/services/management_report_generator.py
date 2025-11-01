"""
Management Report生成服务
为银行提供月度管理报表，包含P&L、Balance Sheet、Aging、数据质量指标
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models import (
    Company, ChartOfAccounts, JournalEntry, JournalEntryLine,
    SalesInvoice, PurchaseInvoice, BankStatement,
    POSReport, Customer, Supplier
)

logger = logging.getLogger(__name__)


class ManagementReportGenerator:
    """
    Management Report生成器
    
    核心功能：
    1. P&L摘要（收入、费用、净利润）
    2. Balance Sheet摘要（资产、负债、权益）
    3. Aging摘要（AR/AP账龄）
    4. 银行账户余额对账
    5. 数据质量指标（未匹配项、置信度）
    6. 未匹配项目详细列表
    """
    
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
    
    def generate_monthly_report(
        self, 
        period: str,  # Format: 'YYYY-MM'
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        生成月度Management Report
        
        Args:
            period: 报表期间 (例如: '2025-08')
            include_details: 是否包含详细数据
        
        Returns:
            完整的Management Report数据
        """
        logger.info(f"生成Management Report: company_id={self.company_id}, period={period}")
        
        # 解析期间
        year, month = map(int, period.split('-'))
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)
        
        # 1. 生成P&L摘要
        pnl_summary = self._generate_pnl_summary(period_start, period_end)
        
        # 2. 生成Balance Sheet摘要
        bs_summary = self._generate_balance_sheet_summary(period_end)
        
        # 3. 生成Aging摘要
        aging_summary = self._generate_aging_summary(period_end)
        
        # 4. 银行账户余额
        bank_balances = self._generate_bank_balances(period_end)
        
        # 5. 数据质量指标
        data_quality = self._generate_data_quality_metrics(period_start, period_end)
        
        # 6. 未匹配项目详细列表
        unreconciled_details = []
        if include_details and data_quality['unreconciled_count'] > 0:
            unreconciled_details = self._get_unreconciled_details()
        
        # 汇总报表
        report = {
            "company_id": self.company_id,
            "period": period,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "generated_at": datetime.now().isoformat(),
            
            # 核心财务数据
            "pnl_summary": pnl_summary,
            "balance_sheet_summary": bs_summary,
            "aging_summary": aging_summary,
            "bank_balances": bank_balances,
            
            # 数据质量（重要！银行会看）
            "data_quality": data_quality,
            
            # 未匹配项目
            "unreconciled_details": unreconciled_details,
            
            # 元数据
            "report_type": "management_report",
            "report_status": "unaudited"
        }
        
        return report
    
    def _generate_pnl_summary(self, period_start: date, period_end: date) -> Dict:
        """
        生成P&L摘要 - 从真实会计分录汇总
        
        包括：
        - 总收入（Sales Revenue from journal entries）
        - 总费用（Total Expenses from journal entries）
        - 毛利润（Gross Profit）
        - 净利润（Net Profit）
        """
        logger.info(f"汇总P&L数据: company_id={self.company_id}, period={period_start} to {period_end}")
        
        # 查询所有已过账的journal entries（严格小于period_end，排除下月数据）
        query = (
            self.db.query(
                ChartOfAccounts.account_type,
                ChartOfAccounts.account_name,
                func.sum(JournalEntryLine.credit_amount - JournalEntryLine.debit_amount).label('net_amount')
            )
            .join(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccounts.id)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
            .filter(
                ChartOfAccounts.company_id == self.company_id,
                JournalEntry.company_id == self.company_id,
                JournalEntry.entry_date >= period_start,
                JournalEntry.entry_date < period_end,  # 严格小于（不包含period_end）
                JournalEntry.status == 'posted'
            )
            .group_by(ChartOfAccounts.account_type, ChartOfAccounts.account_name)
        )
        
        results = query.all()
        
        # 分类汇总
        income_total = Decimal('0')
        expense_total = Decimal('0')
        income_details = {}
        expense_details = {}
        
        for row in results:
            account_type = row.account_type
            account_name = row.account_name
            net_amount = Decimal(str(row.net_amount or 0))
            
            if account_type == 'income':
                income_total += net_amount
                income_details[account_name] = float(net_amount)
            elif account_type == 'expense':
                # Expense是借方，所以取负值
                expense_amount = abs(net_amount)
                expense_total += expense_amount
                expense_details[account_name] = float(expense_amount)
        
        # 构建收入部分
        revenue = {
            "sales_revenue": float(income_total),
            "other_income": 0.00,  # 可以进一步细分
            "total_revenue": float(income_total),
            "details": income_details
        }
        
        # 构建费用部分
        expenses = {
            "cost_of_goods_sold": 0.00,  # 需要从expense_details中识别COGS
            "operating_expenses": float(expense_total),
            "administrative_expenses": 0.00,
            "finance_costs": 0.00,
            "total_expenses": float(expense_total),
            "details": expense_details
        }
        
        # 计算利润
        gross_profit = float(income_total) - expenses["cost_of_goods_sold"]
        net_profit = float(income_total) - float(expense_total)
        
        return {
            "revenue": revenue,
            "expenses": expenses,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "profit_margin": round((net_profit / float(income_total)) * 100, 2) if income_total > 0 else 0
        }
    
    def _generate_balance_sheet_summary(self, as_of_date: date) -> Dict:
        """
        生成Balance Sheet摘要 - 从真实会计账户余额汇总
        
        包括：
        - 总资产（Total Assets from journal entries）
        - 总负债（Total Liabilities）
        - 总权益（Total Equity）
        """
        logger.info(f"汇总Balance Sheet数据: company_id={self.company_id}, as_of={as_of_date}")
        
        # 查询所有账户的累计余额（严格小于as_of_date，截止到前一天）
        query = (
            self.db.query(
                ChartOfAccounts.account_type,
                ChartOfAccounts.account_name,
                func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount).label('balance')
            )
            .join(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccounts.id)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
            .filter(
                ChartOfAccounts.company_id == self.company_id,
                JournalEntry.company_id == self.company_id,
                JournalEntry.entry_date < as_of_date,  # 严格小于（不包含as_of_date）
                JournalEntry.status == 'posted'
            )
            .group_by(ChartOfAccounts.account_type, ChartOfAccounts.account_name)
        )
        
        results = query.all()
        
        # 分类汇总
        asset_total = Decimal('0')
        liability_total = Decimal('0')
        equity_total = Decimal('0')
        
        asset_details = {}
        liability_details = {}
        equity_details = {}
        
        for row in results:
            account_type = row.account_type
            account_name = row.account_name
            balance = Decimal(str(row.balance or 0))
            
            if account_type == 'asset':
                asset_total += balance
                asset_details[account_name] = float(balance)
            elif account_type == 'liability':
                # Liability是贷方，取负值
                liability_amount = abs(balance)
                liability_total += liability_amount
                liability_details[account_name] = float(liability_amount)
            elif account_type == 'equity':
                # Equity是贷方，取负值
                equity_amount = abs(balance)
                equity_total += equity_amount
                equity_details[account_name] = float(equity_amount)
        
        # 从asset_details中提取AR余额（基于account_name关键词匹配）
        ar_balance = self._extract_ar_balance_from_details(asset_details)
        
        # 从liability_details中提取AP余额（基于account_name关键词匹配）
        ap_balance = self._extract_ap_balance_from_details(liability_details)
        
        # 查询银行余额
        bank_total = self._get_total_bank_balance(as_of_date)
        
        # 构建资产部分
        assets = {
            "current_assets": {
                "cash_and_bank": float(bank_total),
                "accounts_receivable": ar_balance,
                "inventory": 0.00,  # 需要进一步识别
                "total": float(bank_total) + ar_balance
            },
            "non_current_assets": {
                "fixed_assets": 0.00,  # 需要进一步识别
                "total": 0.00
            },
            "total_assets": float(asset_total),
            "details": asset_details
        }
        
        # 构建负债部分
        liabilities = {
            "current_liabilities": {
                "accounts_payable": ap_balance,
                "short_term_loans": 0.00,
                "total": ap_balance
            },
            "non_current_liabilities": {
                "long_term_loans": 0.00,
                "total": 0.00
            },
            "total_liabilities": float(liability_total),
            "details": liability_details
        }
        
        # 构建权益部分
        equity = {
            "share_capital": 0.00,  # 需要进一步识别
            "retained_earnings": float(equity_total),
            "total_equity": float(equity_total),
            "details": equity_details
        }
        
        # 验证平衡
        balance_check = float(asset_total) - (float(liability_total) + float(equity_total))
        
        return {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "as_of_date": as_of_date.isoformat(),
            "balance_check": round(balance_check, 2)
        }
    
    def _generate_aging_summary(self, as_of_date: date) -> Dict:
        """
        生成Aging摘要 - 从真实发票表计算账龄
        
        包括：
        - AR账龄（Accounts Receivable from sales_invoices）
        - AP账龄（Accounts Payable from purchase_invoices）
        """
        logger.info(f"计算Aging数据: company_id={self.company_id}, as_of={as_of_date}")
        
        # 查询AR - 未付清的销售发票（严格小于as_of_date）
        ar_invoices = (
            self.db.query(SalesInvoice)
            .filter(
                SalesInvoice.company_id == self.company_id,
                SalesInvoice.balance_amount > 0,
                SalesInvoice.invoice_date < as_of_date  # 严格小于
            )
            .all()
        )
        
        # 按账龄分类AR
        ar_current = Decimal('0')
        ar_1_30 = Decimal('0')
        ar_31_60 = Decimal('0')
        ar_61_90 = Decimal('0')
        ar_over_90 = Decimal('0')
        
        for invoice in ar_invoices:
            balance = Decimal(str(invoice.balance_amount))
            days_overdue = (as_of_date - invoice.due_date).days
            
            if days_overdue < 0:
                ar_current += balance
            elif days_overdue <= 30:
                ar_1_30 += balance
            elif days_overdue <= 60:
                ar_31_60 += balance
            elif days_overdue <= 90:
                ar_61_90 += balance
            else:
                ar_over_90 += balance
        
        ar_total = ar_current + ar_1_30 + ar_31_60 + ar_61_90 + ar_over_90
        
        # 查询AP - 未付清的采购发票（严格小于as_of_date）
        ap_invoices = (
            self.db.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.company_id == self.company_id,
                PurchaseInvoice.balance_amount > 0,
                PurchaseInvoice.invoice_date < as_of_date  # 严格小于
            )
            .all()
        )
        
        # 按账龄分类AP
        ap_current = Decimal('0')
        ap_1_30 = Decimal('0')
        ap_31_60 = Decimal('0')
        ap_61_90 = Decimal('0')
        ap_over_90 = Decimal('0')
        
        for invoice in ap_invoices:
            balance = Decimal(str(invoice.balance_amount))
            days_overdue = (as_of_date - invoice.due_date).days
            
            if days_overdue < 0:
                ap_current += balance
            elif days_overdue <= 30:
                ap_1_30 += balance
            elif days_overdue <= 60:
                ap_31_60 += balance
            elif days_overdue <= 90:
                ap_61_90 += balance
            else:
                ap_over_90 += balance
        
        ap_total = ap_current + ap_1_30 + ap_31_60 + ap_61_90 + ap_over_90
        
        ar_aging = {
            "ar_current": float(ar_current),
            "ar_1_30": float(ar_1_30),  # 添加1-30天
            "ar_31_60": float(ar_31_60),
            "ar_61_90": float(ar_61_90),
            "ar_over_90": float(ar_over_90),
            "total_ar": float(ar_total)
        }
        
        ap_aging = {
            "ap_current": float(ap_current),
            "ap_1_30": float(ap_1_30),  # 添加1-30天
            "ap_31_60": float(ap_31_60),
            "ap_61_90": float(ap_61_90),
            "ap_over_90": float(ap_over_90),
            "total_ap": float(ap_total)
        }
        
        # 合并返回（兼容PDF生成器）
        return {
            **ar_aging,
            **ap_aging,
            "as_of_date": as_of_date.isoformat()
        }
    
    def _generate_bank_balances(self, as_of_date: date) -> List[Dict]:
        """
        生成银行账户余额列表 - 从bank_statements获取最新余额
        """
        logger.info(f"查询银行余额: company_id={self.company_id}, as_of={as_of_date}")
        
        # 查询所有银行账户（按account_number分组，严格小于as_of_date）
        subquery = (
            self.db.query(
                BankStatement.account_number,
                func.max(BankStatement.transaction_date).label('last_date')
            )
            .filter(
                BankStatement.company_id == self.company_id,
                BankStatement.transaction_date < as_of_date  # 严格小于
            )
            .group_by(BankStatement.account_number)
            .subquery()
        )
        
        # 获取每个账户的最新余额
        bank_accounts = (
            self.db.query(BankStatement)
            .join(
                subquery,
                and_(
                    BankStatement.account_number == subquery.c.account_number,
                    BankStatement.transaction_date == subquery.c.last_date
                )
            )
            .filter(BankStatement.company_id == self.company_id)
            .all()
        )
        
        balances = []
        for stmt in bank_accounts:
            balances.append({
                "bank_name": stmt.bank_name,
                "account_number": stmt.account_number,
                "balance": float(stmt.balance) if stmt.balance is not None else 0.0,
                "last_updated": stmt.transaction_date.isoformat()
            })
        
        return balances
    
    def _generate_data_quality_metrics(
        self, 
        period_start: date, 
        period_end: date
    ) -> Dict:
        """
        生成数据质量指标
        
        这是Management Report的关键部分，银行会关注：
        - 数据新鲜度（Data Freshness）
        - 未匹配项数量（Unreconciled Items）
        - 置信度评分（Confidence Score）
        - 数据来源模块（Source Modules）
        - 可能的收入缺口估算（Estimated Revenue Gap）
        """
        # 1. 获取未匹配项数量
        # TODO: 从pending_documents表中查询
        unreconciled_count = 0  # 模拟数据
        
        # 2. 数据来源模块
        source_modules = {
            "bank": True,   # 银行月结单已导入
            "pos": True,    # POS日报已导入
            "supplier": True,  # 供应商发票已导入
            "manual": False  # 手工记账
        }
        
        # 3. 置信度评分（基于未匹配项比例）
        total_transactions = 500  # 模拟：总交易数
        if total_transactions > 0:
            confidence_score = max(0, 1 - (unreconciled_count / total_transactions))
        else:
            confidence_score = 1.0
        
        # 4. 估算收入缺口（如果有未匹配的POS报告）
        estimated_revenue_gap = 0.00
        if unreconciled_count > 0:
            # 假设平均每笔未匹配交易价值RM 100
            estimated_revenue_gap = unreconciled_count * 100.00
        
        # 5. 数据新鲜度（最后更新日期）
        data_freshness = period_end
        
        return {
            "data_freshness": data_freshness.isoformat(),
            "unreconciled_count": unreconciled_count,
            "confidence_score": round(confidence_score, 4),
            "confidence_percentage": f"{confidence_score * 100:.2f}%",
            "source_modules": source_modules,
            "estimated_revenue_gap": estimated_revenue_gap,
            "total_transactions": total_transactions,
            "reconciled_transactions": total_transactions - unreconciled_count
        }
    
    def _get_unreconciled_details(self) -> List[Dict]:
        """
        获取未匹配项目的详细列表
        
        从pending_documents表中获取
        """
        # TODO: 从pending_documents表中查询
        
        # 模拟数据（示例）
        return [
            {
                "file_name": "pos_report_2025_08_15.pdf",
                "file_type": "pos-report",
                "upload_date": "2025-08-16",
                "failure_stage": "customer_matching_failed",
                "description": "无法自动匹配客户，需要人工确认",
                "estimated_amount": 1200.50
            },
            {
                "file_name": "supplier_invoice_ABC_0815.pdf",
                "file_type": "supplier-invoice",
                "upload_date": "2025-08-17",
                "failure_stage": "ocr_failed",
                "description": "OCR识别失败，需要手动输入",
                "estimated_amount": 850.00
            }
        ]
    
    def save_report_to_database(self, report_data: Dict) -> int:
        """
        保存报表到数据库
        
        Returns:
            report_id
        """
        # TODO: 实现数据库保存逻辑
        # INSERT INTO management_reports (...)
        
        logger.info(f"保存Management Report到数据库: period={report_data['period']}")
        
        # 模拟返回report_id
        return 1
    
    # ========== 辅助方法 ==========
    
    def _extract_ar_balance_from_details(self, asset_details: Dict[str, float]) -> float:
        """
        从asset_details中提取AR余额（基于account_name关键词匹配）
        
        这是正确的做法：从journal_entry_lines汇总的余额已经是time-sliced的，
        而不是使用invoice.balance_amount（它是当前余额，不保留历史）
        """
        ar_keywords = [
            'Receivable', 'receivable', 'AR', 'A/R',
            '应收', '应收账款', 'Accounts Receivable'
        ]
        ar_balance = 0.0
        for account_name, balance in asset_details.items():
            if any(keyword in account_name for keyword in ar_keywords):
                ar_balance += balance
        return ar_balance
    
    def _extract_ap_balance_from_details(self, liability_details: Dict[str, float]) -> float:
        """
        从liability_details中提取AP余额（基于account_name关键词匹配）
        
        这是正确的做法：从journal_entry_lines汇总的余额已经是time-sliced的，
        而不是使用invoice.balance_amount（它是当前余额，不保留历史）
        """
        ap_keywords = [
            'Payable', 'payable', 'AP', 'A/P',
            '应付', '应付账款', 'Accounts Payable'
        ]
        ap_balance = 0.0
        for account_name, balance in liability_details.items():
            if any(keyword in account_name for keyword in ap_keywords):  # 修复：使用ap_keywords
                ap_balance += balance
        return ap_balance
    
    def _get_total_bank_balance(self, as_of_date: date) -> Decimal:
        """获取所有银行账户余额总和"""
        balances = self._generate_bank_balances(as_of_date)
        if not balances:
            return Decimal('0')
        total = sum(Decimal(str(b['balance'])) for b in balances)
        return total


# ========== 便捷函数 ==========

def generate_management_report(
    db: Session, 
    company_id: int, 
    period: str,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：生成Management Report
    
    使用示例:
    report = generate_management_report(db, company_id=1, period='2025-08')
    """
    generator = ManagementReportGenerator(db, company_id)
    report = generator.generate_monthly_report(period)
    
    if save_to_db:
        report_id = generator.save_report_to_database(report)
        report['report_id'] = report_id
    
    return report


# ========== 使用示例 ==========

"""
在路由中使用:

from accounting_app.services.management_report_generator import generate_management_report

@router.get("/reports/management/{period}")
def get_management_report(
    period: str,
    format: str = 'json',
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    # 生成报表
    report = generate_management_report(db, company_id, period)
    
    # 渲染输出
    if format == 'pdf':
        pdf_bytes = render_report(report, 'management', format='pdf')
        return Response(content=pdf_bytes, media_type='application/pdf')
    else:
        return report
"""
