"""
专业PDF财务报表生成器
使用ReportLab生成银行贷款所需的财务报表

支持报表：
1. Balance Sheet (资产负债表)
2. Profit & Loss Statement (损益表)
3. Bank Package (完整银行贷款包)
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
import io
import logging

# 导入统一配色系统
from config.colors import COLORS

logger = logging.getLogger(__name__)

# 严格3色调色板 - 从统一配置加载
COLOR_BLACK = colors.HexColor(COLORS.core.black)
COLOR_HOT_PINK = colors.HexColor(COLORS.core.hot_pink)
COLOR_DARK_PURPLE = colors.HexColor(COLORS.core.dark_purple)


class PDFReportGenerator:
    """
    专业PDF财务报表生成器
    
    设计理念：
    - 严格遵循3色调色板（黑色、热粉、深紫）
    - 符合银行贷款审批标准
    - 清晰的数据呈现
    - 专业的排版
    """
    
    def __init__(self, company_name: str, company_code: str):
        self.company_name = company_name
        self.company_code = company_code
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式（黑色）
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=COLOR_BLACK,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # 副标题样式（热粉）
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=COLOR_HOT_PINK,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        # 小标题样式（深紫）
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=COLOR_DARK_PURPLE,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        # 正文样式
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=COLOR_BLACK
        )
    
    def generate_balance_sheet(
        self,
        bs_data: Dict[str, Any],
        period: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        生成资产负债表PDF
        
        Args:
            bs_data: Balance Sheet数据（来自management_report_generator）
            period: 期间（例如：2025-11-30）
            output_path: 输出文件路径（可选，默认返回字节流）
        
        Returns:
            PDF字节流
        """
        logger.info(f"生成Balance Sheet PDF: {self.company_name}, period={period}")
        
        # 创建PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # 构建内容
        story = []
        
        # 标题
        story.append(Paragraph(self.company_name, self.title_style))
        story.append(Paragraph("BALANCE SHEET", self.subtitle_style))
        story.append(Paragraph(f"As of {period}", self.normal_style))
        story.append(Spacer(1, 20))
        
        # 资产部分
        story.append(Paragraph("ASSETS", self.heading_style))
        story.append(Spacer(1, 10))
        
        # 流动资产表格
        current_assets = bs_data.get('assets', {}).get('current_assets', {})
        assets_data = [
            ['Current Assets', '', ''],
            ['  Cash and Bank', '', self._format_money(current_assets.get('cash_and_bank', 0))],
            ['  Accounts Receivable', '', self._format_money(current_assets.get('accounts_receivable', 0))],
            ['  Inventory', '', self._format_money(current_assets.get('inventory', 0))],
            ['  Total Current Assets', '', self._format_money(current_assets.get('total', 0))],
        ]
        
        # 非流动资产
        non_current_assets = bs_data.get('assets', {}).get('non_current_assets', {})
        assets_data.extend([
            ['', '', ''],
            ['Non-Current Assets', '', ''],
            ['  Fixed Assets', '', self._format_money(non_current_assets.get('fixed_assets', 0))],
            ['  Total Non-Current Assets', '', self._format_money(non_current_assets.get('total', 0))],
        ])
        
        # 总资产
        total_assets = bs_data.get('assets', {}).get('total_assets', 0)
        assets_data.append(['TOTAL ASSETS', '', self._format_money(total_assets)])
        
        assets_table = Table(assets_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
        assets_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_DARK_PURPLE),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLOR_HOT_PINK),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, COLOR_BLACK),
            ('LINEBELOW', (0, -1), (-1, -1), 2, COLOR_BLACK),
        ]))
        
        story.append(assets_table)
        story.append(Spacer(1, 30))
        
        # 负债与权益部分
        story.append(Paragraph("LIABILITIES & EQUITY", self.heading_style))
        story.append(Spacer(1, 10))
        
        # 流动负债
        current_liabilities = bs_data.get('liabilities', {}).get('current_liabilities', {})
        liabilities_data = [
            ['Current Liabilities', '', ''],
            ['  Accounts Payable', '', self._format_money(current_liabilities.get('accounts_payable', 0))],
            ['  Short-term Loans', '', self._format_money(current_liabilities.get('short_term_loans', 0))],
            ['  Total Current Liabilities', '', self._format_money(current_liabilities.get('total', 0))],
        ]
        
        # 非流动负债
        non_current_liabilities = bs_data.get('liabilities', {}).get('non_current_liabilities', {})
        liabilities_data.extend([
            ['', '', ''],
            ['Non-Current Liabilities', '', ''],
            ['  Long-term Loans', '', self._format_money(non_current_liabilities.get('long_term_loans', 0))],
            ['  Total Non-Current Liabilities', '', self._format_money(non_current_liabilities.get('total', 0))],
        ])
        
        # 总负债
        total_liabilities = bs_data.get('liabilities', {}).get('total_liabilities', 0)
        liabilities_data.append(['TOTAL LIABILITIES', '', self._format_money(total_liabilities)])
        
        # 权益
        equity = bs_data.get('equity', {})
        liabilities_data.extend([
            ['', '', ''],
            ['Equity', '', ''],
            ['  Share Capital', '', self._format_money(equity.get('share_capital', 0))],
            ['  Retained Earnings', '', self._format_money(equity.get('retained_earnings', 0))],
            ['  Total Equity', '', self._format_money(equity.get('total_equity', 0))],
        ])
        
        # 总负债与权益
        total_liabilities_equity = total_liabilities + equity.get('total_equity', 0)
        liabilities_data.append(['TOTAL LIABILITIES & EQUITY', '', self._format_money(total_liabilities_equity)])
        
        liabilities_table = Table(liabilities_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
        liabilities_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_DARK_PURPLE),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLOR_HOT_PINK),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, COLOR_BLACK),
            ('LINEBELOW', (0, -1), (-1, -1), 2, COLOR_BLACK),
        ]))
        
        story.append(liabilities_table)
        story.append(Spacer(1, 20))
        
        # 页脚
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Company Code: {self.company_code}"
        story.append(Paragraph(footer_text, self.normal_style))
        
        # 构建PDF
        doc.build(story)
        
        # 保存到文件（如果指定）
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_profit_loss(
        self,
        pnl_data: Dict[str, Any],
        period: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        生成损益表PDF
        
        Args:
            pnl_data: P&L数据（来自management_report_generator）
            period: 期间（例如：2025-11）
            output_path: 输出文件路径（可选）
        
        Returns:
            PDF字节流
        """
        logger.info(f"生成P&L PDF: {self.company_name}, period={period}")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # 标题
        story.append(Paragraph(self.company_name, self.title_style))
        story.append(Paragraph("PROFIT & LOSS STATEMENT", self.subtitle_style))
        story.append(Paragraph(f"For the Period: {period}", self.normal_style))
        story.append(Spacer(1, 20))
        
        # 收入部分
        story.append(Paragraph("REVENUE", self.heading_style))
        story.append(Spacer(1, 10))
        
        revenue = pnl_data.get('revenue', {})
        revenue_data = [
            ['Sales Revenue', '', self._format_money(revenue.get('sales_revenue', 0))],
            ['Other Income', '', self._format_money(revenue.get('other_income', 0))],
            ['Total Revenue', '', self._format_money(revenue.get('total_revenue', 0))],
        ]
        
        revenue_table = Table(revenue_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
        revenue_table.setStyle(TableStyle([
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLOR_HOT_PINK),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, COLOR_BLACK),
        ]))
        
        story.append(revenue_table)
        story.append(Spacer(1, 20))
        
        # 费用部分
        story.append(Paragraph("EXPENSES", self.heading_style))
        story.append(Spacer(1, 10))
        
        expenses = pnl_data.get('expenses', {})
        expenses_data = [
            ['Cost of Goods Sold', '', self._format_money(expenses.get('cost_of_goods_sold', 0))],
            ['Operating Expenses', '', self._format_money(expenses.get('operating_expenses', 0))],
            ['Administrative Expenses', '', self._format_money(expenses.get('administrative_expenses', 0))],
            ['Finance Costs', '', self._format_money(expenses.get('finance_costs', 0))],
            ['Total Expenses', '', self._format_money(expenses.get('total_expenses', 0))],
        ]
        
        expenses_table = Table(expenses_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
        expenses_table.setStyle(TableStyle([
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLOR_DARK_PURPLE),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, COLOR_BLACK),
        ]))
        
        story.append(expenses_table)
        story.append(Spacer(1, 20))
        
        # 利润汇总
        story.append(Paragraph("PROFITABILITY", self.heading_style))
        story.append(Spacer(1, 10))
        
        gross_profit = pnl_data.get('gross_profit', 0)
        net_profit = pnl_data.get('net_profit', 0)
        profit_margin = pnl_data.get('profit_margin', 0)
        
        profit_data = [
            ['Gross Profit', '', self._format_money(gross_profit)],
            ['Net Profit', '', self._format_money(net_profit)],
            ['Profit Margin', '', f"{profit_margin}%"],
        ]
        
        profit_table = Table(profit_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
        profit_table.setStyle(TableStyle([
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 1), (-1, 1), COLOR_HOT_PINK),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (0, 1), (-1, 1), 2, COLOR_BLACK),
            ('LINEBELOW', (0, 1), (-1, 1), 2, COLOR_BLACK),
        ]))
        
        story.append(profit_table)
        story.append(Spacer(1, 20))
        
        # 页脚
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Company Code: {self.company_code}"
        story.append(Paragraph(footer_text, self.normal_style))
        
        doc.build(story)
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_bank_package(
        self,
        report_data: Dict[str, Any],
        period: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        生成完整银行贷款包PDF
        
        包含：
        1. 封面
        2. Balance Sheet
        3. P&L Statement
        4. Aging Report Summary
        5. Bank Balances
        6. Data Quality Metrics
        
        Args:
            report_data: 完整Management Report数据
            period: 期间
            output_path: 输出文件路径（可选）
        
        Returns:
            PDF字节流
        """
        logger.info(f"生成Bank Package PDF: {self.company_name}, period={period}")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # ===== 封面 =====
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(self.company_name, self.title_style))
        story.append(Spacer(1, 0.5*inch))
        
        cover_subtitle = ParagraphStyle(
            'CoverSubtitle',
            parent=self.subtitle_style,
            fontSize=20,
            textColor=COLOR_HOT_PINK
        )
        story.append(Paragraph("BANK LOAN APPLICATION PACKAGE", cover_subtitle))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"Period: {period}", self.normal_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d')}", self.normal_style))
        story.append(PageBreak())
        
        # ===== Balance Sheet =====
        story.append(Paragraph("1. BALANCE SHEET", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        bs_summary = report_data.get('balance_sheet_summary', {})
        
        # 简化的资产负债表（用于汇总）
        assets = bs_summary.get('assets', {})
        liabilities = bs_summary.get('liabilities', {})
        equity = bs_summary.get('equity', {})
        
        bs_summary_data = [
            ['ASSETS', self._format_money(assets.get('total_assets', 0))],
            ['  Current Assets', self._format_money(assets.get('current_assets', {}).get('total', 0))],
            ['  Non-Current Assets', self._format_money(assets.get('non_current_assets', {}).get('total', 0))],
            ['', ''],
            ['LIABILITIES', self._format_money(liabilities.get('total_liabilities', 0))],
            ['  Current Liabilities', self._format_money(liabilities.get('current_liabilities', {}).get('total', 0))],
            ['  Non-Current Liabilities', self._format_money(liabilities.get('non_current_liabilities', {}).get('total', 0))],
            ['', ''],
            ['EQUITY', self._format_money(equity.get('total_equity', 0))],
        ]
        
        bs_table = Table(bs_summary_data, colWidths=[4*inch, 2*inch])
        bs_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
            ('FONTNAME', (0, 8), (0, 8), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, 0), COLOR_DARK_PURPLE),
            ('TEXTCOLOR', (0, 4), (0, 4), COLOR_DARK_PURPLE),
            ('TEXTCOLOR', (0, 8), (0, 8), COLOR_HOT_PINK),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        
        story.append(bs_table)
        story.append(Spacer(1, 30))
        
        # ===== P&L Statement =====
        story.append(Paragraph("2. PROFIT & LOSS STATEMENT", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        pnl_summary = report_data.get('pnl_summary', {})
        revenue = pnl_summary.get('revenue', {})
        expenses = pnl_summary.get('expenses', {})
        
        pnl_summary_data = [
            ['REVENUE', self._format_money(revenue.get('total_revenue', 0))],
            ['  Sales Revenue', self._format_money(revenue.get('sales_revenue', 0))],
            ['  Other Income', self._format_money(revenue.get('other_income', 0))],
            ['', ''],
            ['EXPENSES', self._format_money(expenses.get('total_expenses', 0))],
            ['  COGS', self._format_money(expenses.get('cost_of_goods_sold', 0))],
            ['  Operating', self._format_money(expenses.get('operating_expenses', 0))],
            ['', ''],
            ['NET PROFIT', self._format_money(pnl_summary.get('net_profit', 0))],
            ['Profit Margin', f"{pnl_summary.get('profit_margin', 0)}%"],
        ]
        
        pnl_table = Table(pnl_summary_data, colWidths=[4*inch, 2*inch])
        pnl_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
            ('FONTNAME', (0, 8), (-1, 9), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 8), (-1, 9), COLOR_HOT_PINK),
            ('FONTSIZE', (0, 8), (-1, 9), 12),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 8), (-1, 8), 2, COLOR_BLACK),
        ]))
        
        story.append(pnl_table)
        story.append(PageBreak())
        
        # ===== Aging Summary =====
        story.append(Paragraph("3. AGING REPORT SUMMARY", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        aging_summary = report_data.get('aging_summary', {})
        
        aging_data = [
            ['Accounts Receivable (AR)', ''],
            ['  Current (0-30 days)', self._format_money(aging_summary.get('ar_current', 0))],
            ['  31-60 days', self._format_money(aging_summary.get('ar_31_60', 0))],
            ['  61-90 days', self._format_money(aging_summary.get('ar_61_90', 0))],
            ['  Over 90 days', self._format_money(aging_summary.get('ar_over_90', 0))],
            ['  Total AR', self._format_money(aging_summary.get('total_ar', 0))],
            ['', ''],
            ['Accounts Payable (AP)', ''],
            ['  Total AP', self._format_money(aging_summary.get('total_ap', 0))],
        ]
        
        aging_table = Table(aging_data, colWidths=[4*inch, 2*inch])
        aging_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 5), (0, 5), 'Helvetica-Bold'),
            ('FONTNAME', (0, 7), (0, 7), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, 0), COLOR_DARK_PURPLE),
            ('TEXTCOLOR', (0, 5), (0, 5), COLOR_HOT_PINK),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 5), (-1, 5), 1, COLOR_BLACK),
        ]))
        
        story.append(aging_table)
        story.append(Spacer(1, 30))
        
        # ===== Bank Balances =====
        story.append(Paragraph("4. BANK ACCOUNT BALANCES", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        bank_balances = report_data.get('bank_balances', [])
        
        if bank_balances:
            bank_data = [['Bank Name', 'Account Number', 'Balance']]
            for bank in bank_balances:
                bank_data.append([
                    bank.get('bank_name', ''),
                    bank.get('account_number', ''),
                    self._format_money(bank.get('balance', 0))
                ])
        else:
            bank_data = [['No bank accounts on record', '', '']]
        
        bank_table = Table(bank_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        bank_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_PURPLE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(bank_table)
        story.append(Spacer(1, 30))
        
        # ===== Data Quality =====
        story.append(Paragraph("5. DATA QUALITY METRICS", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        data_quality = report_data.get('data_quality', {})
        
        quality_text = f"""
        <b>Unreconciled Items:</b> {data_quality.get('unreconciled_count', 0)}<br/>
        <b>Data Completeness:</b> {data_quality.get('completeness_score', 0)}%<br/>
        <b>Confidence Level:</b> {data_quality.get('confidence_level', 'Medium')}<br/>
        """
        
        story.append(Paragraph(quality_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # 页脚
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Company Code: {self.company_code} | Confidential"
        story.append(Paragraph(footer_text, self.normal_style))
        
        doc.build(story)
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _format_money(self, amount: float) -> str:
        """格式化金额：RM 12,345.67"""
        if isinstance(amount, Decimal):
            amount = float(amount)
        return f"RM {amount:,.2f}"


# ========== 便捷函数 ==========

def create_pdf_generator(company_name: str, company_code: str) -> PDFReportGenerator:
    """创建PDF生成器实例"""
    return PDFReportGenerator(company_name, company_code)
