"""
供应商付款发票生成器 - Payment Invoice Generator
为Supplier Debit交易生成精美的PDF发票
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
from typing import List, Dict
from db.database import get_db


class SupplierInvoiceGenerator:
    """供应商发票生成器"""
    
    def __init__(self, output_dir: str = "static/invoices"):
        """
        初始化发票生成器
        
        Args:
            output_dir: 发票输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_invoice(self, supplier_name: str, transactions: List[Dict], 
                        customer_name: str, statement_date: str) -> str:
        """
        生成供应商发票
        
        Args:
            supplier_name: 供应商名称
            transactions: 交易列表
            customer_name: 客户名称
            statement_date: 账单日期
            
        Returns:
            生成的PDF文件路径
        """
        # 生成文件名
        safe_supplier = supplier_name.replace(' ', '_').replace('/', '_')
        filename = f"Invoice_{safe_supplier}_{statement_date}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # 创建PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        
        # 自定义样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF6B35'),  # Orange
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495E')
        )
        
        # 标题
        story.append(Paragraph("PAYMENT INVOICE", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 发票信息
        invoice_info = [
            ["Invoice Date:", datetime.now().strftime("%d %B %Y")],
            ["Statement Period:", statement_date],
            ["Supplier:", supplier_name],
            ["Client:", customer_name],
        ]
        
        info_table = Table(invoice_info, colWidths=[2*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.4*inch))
        
        # 交易明细标题
        story.append(Paragraph("Transaction Details", heading_style))
        story.append(Spacer(1, 0.2*inch))
        
        # 交易表格
        table_data = [
            ['Date', 'Description', 'Amount (RM)', 'Fee (1%)', 'Total (RM)']
        ]
        
        total_amount = 0
        total_fee = 0
        
        for txn in transactions:
            date = txn.get('transaction_date', '')
            desc = txn.get('transaction_details', '')[:50]  # 截断长描述
            amount = txn.get('amount', 0)
            fee = txn.get('supplier_fee', 0)
            total = amount + fee
            
            total_amount += amount
            total_fee += fee
            
            table_data.append([
                date,
                desc,
                f"{amount:.2f}",
                f"{fee:.2f}",
                f"{total:.2f}"
            ])
        
        # 总计行
        grand_total = total_amount + total_fee
        table_data.append([
            '', 'TOTAL', 
            f"RM {total_amount:.2f}", 
            f"RM {total_fee:.2f}", 
            f"RM {grand_total:.2f}"
        ])
        
        # 创建表格
        txn_table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 0.9*inch, 1*inch])
        
        txn_table.setStyle(TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # 数据行样式
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 8),
            ('TOPPADDING', (0, 1), (-1, -2), 8),
            
            # 总计行样式
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#FF6B35')),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
            
            # 网格线
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#FF6B35')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#FF6B35')),
        ]))
        
        story.append(txn_table)
        story.append(Spacer(1, 0.4*inch))
        
        # 付款说明
        story.append(Paragraph("Payment Terms", heading_style))
        payment_terms = f"""
        <b>Total Amount Due: RM {grand_total:.2f}</b><br/>
        <br/>
        Please process payment to <b>{supplier_name}</b> for the above amount.<br/>
        This invoice includes a 1% processing fee on all transactions.
        """
        story.append(Paragraph(payment_terms, normal_style))
        
        # 生成PDF
        doc.build(story)
        
        return filepath
    
    def generate_all_supplier_invoices(self, customer_id: int, 
                                      statement_id: int) -> List[str]:
        """
        为账单中的所有供应商生成发票
        
        Args:
            customer_id: 客户ID
            statement_id: 账单ID
            
        Returns:
            生成的发票文件路径列表
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取客户名称
            cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
            customer_name = cursor.fetchone()[0]
            
            # 获取账单日期
            cursor.execute('SELECT statement_date FROM statements WHERE id = ?', (statement_id,))
            statement_date = cursor.fetchone()[0]
            
            # 获取所有供应商消费（使用新的 OWNER vs INFINITE 分类）
            cursor.execute('''
                SELECT t.supplier_name, t.transaction_date, t.description, 
                       t.amount, t.supplier_fee
                FROM transactions t
                WHERE t.statement_id = ?
                  AND t.category = 'infinite_expense'
                  AND t.supplier_name IS NOT NULL
                ORDER BY t.supplier_name, t.transaction_date
            ''', (statement_id,))
            
            all_supplier_txns = cursor.fetchall()
        
        # 按供应商分组
        suppliers_dict = {}
        for txn in all_supplier_txns:
            supplier, date, details, amount, fee = txn
            if supplier not in suppliers_dict:
                suppliers_dict[supplier] = []
            
            suppliers_dict[supplier].append({
                'transaction_date': date,
                'transaction_details': details,
                'amount': amount,
                'supplier_fee': fee
            })
        
        # 为每个供应商生成发票
        invoice_paths = []
        for supplier, transactions in suppliers_dict.items():
            invoice_path = self.generate_invoice(
                supplier, transactions, customer_name, statement_date
            )
            invoice_paths.append(invoice_path)
        
        return invoice_paths


def generate_supplier_invoices_for_statement(customer_id: int, statement_id: int) -> List[str]:
    """
    为账单生成所有供应商发票（便捷函数）
    
    Args:
        customer_id: 客户ID
        statement_id: 账单ID
        
    Returns:
        生成的发票文件路径列表
    """
    generator = SupplierInvoiceGenerator()
    return generator.generate_all_supplier_invoices(customer_id, statement_id)
