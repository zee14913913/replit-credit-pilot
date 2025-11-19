"""
Miscellaneous Fee System - 手续费系统
=====================================
完全独立的手续费计算与Invoice生成系统

计算规则：
- Miscellaneous Fee = GZ's Expenses × 1%
- 完全独立，不参与DR/CR平衡
- 生成单独Invoice PDF
- 存储路径：/CreditPilot/Invoices/YYYY-MM/MF_*.pdf
"""

from typing import Dict, Optional
from decimal import Decimal
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors as reportlab_colors
from db.database import get_db


class MiscellaneousFeeSystem:
    """手续费系统 - 独立Invoice生成"""
    
    FEE_RATE = Decimal('0.01')  # 1%手续费率
    
    def __init__(self, base_dir: str = 'CreditPilot/Invoices'):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_fee(self, gz_expenses: Decimal) -> Decimal:
        """
        计算手续费
        
        Args:
            gz_expenses: GZ's Expenses金额
            
        Returns:
            手续费金额（1%）
        """
        return gz_expenses * self.FEE_RATE
    
    def generate_invoice(
        self, 
        customer_id: int, 
        year_month: str, 
        gz_expenses: Decimal,
        statement_ids: Optional[list] = None
    ) -> str:
        """
        生成手续费Invoice PDF
        
        Args:
            customer_id: 客户ID
            year_month: 年月 (YYYY-MM)
            gz_expenses: GZ's Expenses总额
            statement_ids: 相关账单ID列表（可选）
            
        Returns:
            PDF文件路径
        """
        # 计算手续费
        fee = self.calculate_fee(gz_expenses)
        
        # 获取客户信息
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, customer_code, email, phone
                FROM customers
                WHERE id = ?
            """, (customer_id,))
            customer_row = cursor.fetchone()
            
            if not customer_row:
                raise ValueError(f"Customer {customer_id} not found")
            
            customer = {
                'name': customer_row[0],
                'code': customer_row[1],
                'email': customer_row[2],
                'phone': customer_row[3]
            }
        
        # 创建月份目录
        year, month = year_month.split('-')
        month_dir = self.base_dir / year_month
        month_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        invoice_number = f"MF-{customer['code']}-{year_month}"
        pdf_filename = f"{invoice_number}.pdf"
        pdf_path = month_dir / pdf_filename
        
        # 生成PDF
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 标题样式（使用批准的颜色）
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=reportlab_colors.HexColor('#FF007F'),  # Hot Pink
            alignment=1  # Center
        )
        
        # 标题
        story.append(Paragraph('MISCELLANEOUS FEE INVOICE', title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Invoice信息
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=reportlab_colors.HexColor('#000000')
        )
        
        story.append(Paragraph(f'<b>Invoice Number:</b> {invoice_number}', info_style))
        story.append(Paragraph(f'<b>Date:</b> {datetime.now().strftime("%Y-%m-%d")}', info_style))
        story.append(Paragraph(f'<b>Statement Period:</b> {year_month}', info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 客户信息
        story.append(Paragraph('<b>Bill To:</b>', styles['Heading3']))
        story.append(Paragraph(f'{customer["name"]}', info_style))
        story.append(Paragraph(f'Customer Code: {customer["code"]}', info_style))
        if customer['email']:
            story.append(Paragraph(f'Email: {customer["email"]}', info_style))
        if customer['phone']:
            story.append(Paragraph(f'Phone: {customer["phone"]}', info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 费用明细表
        data = [
            ['Description', 'Base Amount (RM)', 'Rate', 'Fee Amount (RM)'],
            [
                'Miscellaneous Fee (1% of GZ\'s Expenses)',
                f'{gz_expenses:,.2f}',
                '1%',
                f'{fee:,.2f}'
            ]
        ]
        
        table = Table(data, colWidths=[3*inch, 1.5*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            # 表头样式（使用批准的颜色）
            ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # 数据行样式
            ('BACKGROUND', (0, 1), (-1, -1), reportlab_colors.HexColor('#FFFFFF')),
            ('TEXTCOLOR', (0, 1), (-1, -1), reportlab_colors.HexColor('#000000')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, reportlab_colors.HexColor('#322446')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        # 总计
        total_style = ParagraphStyle(
            'TotalStyle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=reportlab_colors.HexColor('#FF007F'),
            alignment=2  # Right
        )
        story.append(Paragraph(f'<b>Total Fee: RM {fee:,.2f}</b>', total_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 备注
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=reportlab_colors.HexColor('#322446')
        )
        story.append(Paragraph('<b>Note:</b>', note_style))
        story.append(Paragraph(
            'This miscellaneous fee is calculated independently and does not participate in DR/CR balance.',
            note_style
        ))
        story.append(Paragraph(
            'Fee Rate: 1% of GZ\'s Expenses as per agreement.',
            note_style
        ))
        
        # 构建PDF
        doc.build(story)
        
        # 保存记录到数据库
        self._save_invoice_record(
            customer_id=customer_id,
            year_month=year_month,
            invoice_number=invoice_number,
            gz_expenses=gz_expenses,
            fee=fee,
            pdf_path=str(pdf_path)
        )
        
        return str(pdf_path)
    
    def _save_invoice_record(
        self,
        customer_id: int,
        year_month: str,
        invoice_number: str,
        gz_expenses: Decimal,
        fee: Decimal,
        pdf_path: str
    ):
        """保存Invoice记录到数据库"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 创建表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS miscellaneous_fee_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    year_month TEXT NOT NULL,
                    invoice_number TEXT NOT NULL UNIQUE,
                    gz_expenses DECIMAL(10, 2) NOT NULL,
                    fee_amount DECIMAL(10, 2) NOT NULL,
                    fee_rate DECIMAL(5, 4) DEFAULT 0.01,
                    pdf_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            
            # 插入记录
            cursor.execute("""
                INSERT OR REPLACE INTO miscellaneous_fee_invoices
                (customer_id, year_month, invoice_number, gz_expenses, fee_amount, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (customer_id, year_month, invoice_number, float(gz_expenses), float(fee), pdf_path))
            
            conn.commit()
    
    def get_monthly_invoice(self, customer_id: int, year_month: str) -> Optional[Dict]:
        """
        获取某月的手续费Invoice记录
        
        Args:
            customer_id: 客户ID
            year_month: 年月 (YYYY-MM)
            
        Returns:
            Invoice记录字典，如果不存在返回None
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, invoice_number, gz_expenses, fee_amount, pdf_path, created_at
                FROM miscellaneous_fee_invoices
                WHERE customer_id = ? AND year_month = ?
            """, (customer_id, year_month))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row[0],
                'invoice_number': row[1],
                'gz_expenses': Decimal(str(row[2])),
                'fee_amount': Decimal(str(row[3])),
                'pdf_path': row[4],
                'created_at': row[5]
            }
