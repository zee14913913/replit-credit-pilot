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
        生成P&L摘要
        
        包括：
        - 总收入（Sales Revenue）
        - 总费用（Total Expenses）
        - 毛利润（Gross Profit）
        - 净利润（Net Profit）
        """
        # TODO: 从实际会计分录表中汇总
        # 这里使用模拟数据，后续需要连接真实数据库
        
        # 模拟数据（示例）
        revenue = {
            "sales_revenue": 150000.00,
            "other_income": 5000.00,
            "total_revenue": 155000.00
        }
        
        expenses = {
            "cost_of_goods_sold": 80000.00,
            "operating_expenses": 35000.00,
            "administrative_expenses": 12000.00,
            "finance_costs": 3000.00,
            "total_expenses": 130000.00
        }
        
        gross_profit = revenue["sales_revenue"] - expenses["cost_of_goods_sold"]
        net_profit = revenue["total_revenue"] - expenses["total_expenses"]
        
        return {
            "revenue": revenue,
            "expenses": expenses,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "profit_margin": round((net_profit / revenue["total_revenue"]) * 100, 2) if revenue["total_revenue"] > 0 else 0
        }
    
    def _generate_balance_sheet_summary(self, as_of_date: date) -> Dict:
        """
        生成Balance Sheet摘要
        
        包括：
        - 总资产（Total Assets）
        - 总负债（Total Liabilities）
        - 总权益（Total Equity）
        """
        # TODO: 从实际会计账户余额表中汇总
        
        # 模拟数据（示例）
        assets = {
            "current_assets": {
                "cash_and_bank": 85000.00,
                "accounts_receivable": 45000.00,
                "inventory": 30000.00,
                "total": 160000.00
            },
            "non_current_assets": {
                "fixed_assets": 120000.00,
                "total": 120000.00
            },
            "total_assets": 280000.00
        }
        
        liabilities = {
            "current_liabilities": {
                "accounts_payable": 35000.00,
                "short_term_loans": 20000.00,
                "total": 55000.00
            },
            "non_current_liabilities": {
                "long_term_loans": 75000.00,
                "total": 75000.00
            },
            "total_liabilities": 130000.00
        }
        
        equity = {
            "share_capital": 100000.00,
            "retained_earnings": 50000.00,
            "total_equity": 150000.00
        }
        
        # 验证平衡
        balance_check = assets["total_assets"] - (liabilities["total_liabilities"] + equity["total_equity"])
        
        return {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "as_of_date": as_of_date.isoformat(),
            "balance_check": balance_check  # 应该为0
        }
    
    def _generate_aging_summary(self, as_of_date: date) -> Dict:
        """
        生成Aging摘要
        
        包括：
        - AR账龄（Accounts Receivable）
        - AP账龄（Accounts Payable）
        """
        # TODO: 从sales_invoices和purchase_invoices表中计算
        
        # 模拟数据（示例）
        ar_aging = {
            "current": 25000.00,
            "1_30_days": 12000.00,
            "31_60_days": 5000.00,
            "61_90_days": 2000.00,
            "over_90_days": 1000.00,
            "total": 45000.00
        }
        
        ap_aging = {
            "current": 18000.00,
            "1_30_days": 10000.00,
            "31_60_days": 5000.00,
            "61_90_days": 2000.00,
            "over_90_days": 0.00,
            "total": 35000.00
        }
        
        return {
            "accounts_receivable": ar_aging,
            "accounts_payable": ap_aging,
            "as_of_date": as_of_date.isoformat()
        }
    
    def _generate_bank_balances(self, as_of_date: date) -> List[Dict]:
        """
        生成银行账户余额列表
        
        从bank_statements表中获取最新余额
        """
        # TODO: 从bank_statements表中查询
        
        # 模拟数据（示例）
        return [
            {
                "bank_name": "Maybank",
                "account_number": "1234567890",
                "account_type": "Current Account",
                "balance": 45000.00,
                "currency": "MYR",
                "last_updated": as_of_date.isoformat()
            },
            {
                "bank_name": "CIMB",
                "account_number": "9876543210",
                "account_type": "Savings Account",
                "balance": 40000.00,
                "currency": "MYR",
                "last_updated": as_of_date.isoformat()
            }
        ]
    
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
