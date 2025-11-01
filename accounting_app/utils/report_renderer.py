"""
统一报表渲染工具
支持JSON和PDF双输出
"""
from typing import Dict, Any, Literal
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
import json
import logging

logger = logging.getLogger(__name__)


class ReportRenderer:
    """
    统一报表渲染器
    支持JSON和PDF两种输出格式
    """
    
    def __init__(self, company_name: str = "Your Company Ltd"):
        self.company_name = company_name
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # 副标题样式
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#FF007F'),  # 粉红色
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        # 普通文本样式
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#000000')
        )
    
    def render(self, 
               data: Dict[str, Any], 
               report_type: str,
               format: Literal['json', 'pdf'] = 'json') -> Any:
        """
        统一渲染入口
        
        Args:
            data: 报表数据
            report_type: 报表类型 ('balance_sheet', 'pnl', 'management', 'aging')
            format: 输出格式 ('json' or 'pdf')
        
        Returns:
            JSON格式: Dict
            PDF格式: bytes
        """
        if format == 'json':
            return self._render_json(data, report_type)
        elif format == 'pdf':
            return self._render_pdf(data, report_type)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _render_json(self, data: Dict[str, Any], report_type: str) -> Dict:
        """
        渲染为JSON格式
        """
        return {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "company_name": self.company_name,
            "data": data,
            "format": "json"
        }
    
    def _render_pdf(self, data: Dict[str, Any], report_type: str) -> bytes:
        """
        渲染为PDF格式
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # 添加标题
        title = self._get_report_title(report_type)
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 12))
        
        # 添加公司信息
        story.append(Paragraph(f"<b>{self.company_name}</b>", self.normal_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.normal_style))
        story.append(Spacer(1, 20))
        
        # 根据报表类型添加内容
        if report_type == 'balance_sheet':
            story.extend(self._render_balance_sheet_pdf(data))
        elif report_type == 'pnl':
            story.extend(self._render_pnl_pdf(data))
        elif report_type == 'management':
            story.extend(self._render_management_report_pdf(data))
        elif report_type == 'aging':
            story.extend(self._render_aging_pdf(data))
        else:
            story.append(Paragraph(f"报表类型 {report_type} 暂不支持", self.normal_style))
        
        # 生成PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _get_report_title(self, report_type: str) -> str:
        """获取报表标题"""
        titles = {
            'balance_sheet': 'Balance Sheet',
            'pnl': 'Profit & Loss Statement',
            'management': 'Management Report',
            'aging': 'Aging Report',
            'ar_aging': 'Accounts Receivable Aging',
            'ap_aging': 'Accounts Payable Aging'
        }
        return titles.get(report_type, 'Financial Report')
    
    def _render_balance_sheet_pdf(self, data: Dict) -> list:
        """渲染资产负债表PDF"""
        story = []
        
        # 期间
        if 'period' in data:
            story.append(Paragraph(f"<b>As at: {data['period']}</b>", self.subtitle_style))
            story.append(Spacer(1, 12))
        
        # 资产部分
        story.append(Paragraph("<b>ASSETS</b>", self.subtitle_style))
        if 'assets' in data:
            story.append(self._create_table(data['assets']))
            story.append(Spacer(1, 12))
        
        # 负债部分
        story.append(Paragraph("<b>LIABILITIES</b>", self.subtitle_style))
        if 'liabilities' in data:
            story.append(self._create_table(data['liabilities']))
            story.append(Spacer(1, 12))
        
        # 权益部分
        story.append(Paragraph("<b>EQUITY</b>", self.subtitle_style))
        if 'equity' in data:
            story.append(self._create_table(data['equity']))
        
        return story
    
    def _render_pnl_pdf(self, data: Dict) -> list:
        """渲染损益表PDF"""
        story = []
        
        # 期间
        if 'period' in data:
            story.append(Paragraph(f"<b>Period: {data['period']}</b>", self.subtitle_style))
            story.append(Spacer(1, 12))
        
        # 收入
        story.append(Paragraph("<b>REVENUE</b>", self.subtitle_style))
        if 'revenue' in data:
            story.append(self._create_table(data['revenue']))
            story.append(Spacer(1, 12))
        
        # 费用
        story.append(Paragraph("<b>EXPENSES</b>", self.subtitle_style))
        if 'expenses' in data:
            story.append(self._create_table(data['expenses']))
            story.append(Spacer(1, 12))
        
        # 净利润
        if 'net_profit' in data:
            story.append(Paragraph(f"<b>Net Profit: RM {data['net_profit']:,.2f}</b>", self.subtitle_style))
        
        return story
    
    def _render_management_report_pdf(self, data: Dict) -> list:
        """渲染Management Report PDF"""
        story = []
        
        # 报表说明
        story.append(Paragraph("<b>MANAGEMENT USE ONLY - UNAUDITED</b>", self.subtitle_style))
        story.append(Spacer(1, 12))
        
        # 数据质量部分（重要！）
        story.append(Paragraph("<b>Data Quality & Reconciliation Status</b>", self.subtitle_style))
        
        quality_data = []
        quality_data.append(['Metric', 'Value'])
        quality_data.append(['Data Freshness', data.get('data_freshness', 'N/A')])
        quality_data.append(['Unreconciled Items', str(data.get('unreconciled_count', 0))])
        quality_data.append(['Confidence Score', f"{data.get('confidence_score', 0):.0%}"])
        
        if 'source_modules' in data:
            modules = data['source_modules']
            quality_data.append(['Data Sources', ', '.join([k for k, v in modules.items() if v])])
        
        story.append(self._create_table(quality_data))
        story.append(Spacer(1, 20))
        
        # P&L Summary
        if 'pnl_summary' in data:
            story.append(Paragraph("<b>Profit & Loss Summary</b>", self.subtitle_style))
            story.append(self._create_table(data['pnl_summary']))
            story.append(Spacer(1, 12))
        
        # Balance Sheet Summary
        if 'bs_summary' in data:
            story.append(Paragraph("<b>Balance Sheet Summary</b>", self.subtitle_style))
            story.append(self._create_table(data['bs_summary']))
            story.append(Spacer(1, 12))
        
        # Aging Summary
        if 'aging_summary' in data:
            story.append(Paragraph("<b>Aging Summary</b>", self.subtitle_style))
            story.append(self._create_table(data['aging_summary']))
            story.append(Spacer(1, 12))
        
        # 未匹配项目（如果有）
        if data.get('unreconciled_count', 0) > 0:
            story.append(PageBreak())
            story.append(Paragraph("<b>Unreconciled / Pending Items</b>", self.subtitle_style))
            story.append(Paragraph(
                f"There are {data['unreconciled_count']} items pending manual review.",
                self.normal_style
            ))
            
            if 'unreconciled_details' in data:
                story.append(self._create_table(data['unreconciled_details']))
        
        return story
    
    def _render_aging_pdf(self, data: Dict) -> list:
        """渲染账龄报表PDF"""
        story = []
        
        if 'aging_data' in data:
            story.append(self._create_table(data['aging_data']))
        
        return story
    
    def _create_table(self, data: Any) -> Table:
        """
        创建表格
        data可以是:
        - List of lists
        - List of dicts
        - Dict
        """
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                # Convert list of dicts to list of lists
                headers = list(data[0].keys())
                table_data = [headers]
                for row in data:
                    table_data.append([str(row.get(h, '')) for h in headers])
            else:
                table_data = data
        elif isinstance(data, dict):
            # Convert dict to list of lists
            table_data = [['Item', 'Amount']]
            for key, value in data.items():
                table_data.append([str(key), f"RM {value:,.2f}" if isinstance(value, (int, float)) else str(value)])
        else:
            table_data = [['No data']]
        
        table = Table(table_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        return table


# ========== 便捷函数 ==========

def render_report(data: Dict, report_type: str, format: str = 'json', company_name: str = "Your Company Ltd") -> Any:
    """
    便捷函数：渲染报表
    
    使用示例:
    # JSON输出
    json_data = render_report(data, 'balance_sheet', format='json')
    
    # PDF输出
    pdf_bytes = render_report(data, 'balance_sheet', format='pdf')
    """
    renderer = ReportRenderer(company_name=company_name)
    return renderer.render(data, report_type, format)


# ========== 使用示例 ==========

"""
在路由中使用:

from accounting_app.utils.report_renderer import render_report

@router.get("/reports/balance-sheet")
def get_balance_sheet(
    format: str = 'json',
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    # 获取数据
    data = generate_balance_sheet_data(db, company_id)
    
    # 渲染报表
    result = render_report(data, 'balance_sheet', format=format)
    
    if format == 'pdf':
        return Response(content=result, media_type='application/pdf')
    else:
        return result
"""
