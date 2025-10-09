"""
供应商发票生成器
Generate professional PDF invoices for supplier transactions with 1% fee
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from db.database import get_db
from datetime import datetime
import os

class SupplierInvoiceGenerator:
    
    def __init__(self, output_folder='static/uploads/invoices'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def generate_supplier_invoice(self, statement_id, supplier_name):
        """
        为特定供应商生成发票
        """
        # 获取该供应商的所有交易
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    t.*,
                    s.statement_date,
                    s.card_full_number,
                    cc.bank_name,
                    cc.card_type,
                    c.name as customer_name,
                    c.ic_number
                FROM transactions t
                JOIN statements s ON t.statement_id = s.id
                JOIN credit_cards cc ON s.card_id = cc.id
                JOIN customers c ON cc.customer_id = c.id
                WHERE t.statement_id = ? 
                AND t.transaction_subtype = 'supplier_debit'
                AND t.description LIKE ?
                ORDER BY t.transaction_date
            ''', (statement_id, f'%{supplier_name}%'))
            
            transactions = [dict(row) for row in cursor.fetchall()]
            
            if not transactions:
                return None
            
            # 生成发票
            invoice_number = f"INV-{statement_id}-{supplier_name.replace(' ', '')}-{datetime.now().strftime('%Y%m%d')}"
            pdf_filename = f"{invoice_number}.pdf"
            pdf_path = os.path.join(self.output_folder, pdf_filename)
            
            # 计算总计
            subtotal = sum(abs(t['amount']) for t in transactions)
            total_fee = sum(t['supplier_fee'] for t in transactions)
            grand_total = subtotal + total_fee
            
            # 创建PDF
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # 添加标题
            title = Paragraph(f"<b>SUPPLIER INVOICE</b>", title_style)
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # 发票信息
            invoice_info = f"""
            <para alignment='right'>
            <b>Invoice Number:</b> {invoice_number}<br/>
            <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>
            <b>Statement Period:</b> {transactions[0]['statement_date']}<br/>
            </para>
            """
            story.append(Paragraph(invoice_info, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # 客户和供应商信息
            client_info = [
                ['<b>Bill To:</b>', '<b>Supplier:</b>'],
                [transactions[0]['customer_name'], supplier_name],
                [f"IC: {transactions[0]['ic_number']}", ''],
                [f"{transactions[0]['bank_name']} - {transactions[0]['card_type']}", ''],
                [f"Card: {transactions[0]['card_full_number']}", '']
            ]
            
            client_table = Table(client_info, colWidths=[3*inch, 3*inch])
            client_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(client_table)
            story.append(Spacer(1, 0.4*inch))
            
            # 交易明细表
            data = [['Date', 'Description', 'Amount (RM)', 'Fee 1% (RM)']]
            
            for t in transactions:
                data.append([
                    t['transaction_date'],
                    t['description'][:50],  # 限制长度
                    f"{abs(t['amount']):.2f}",
                    f"{t['supplier_fee']:.2f}"
                ])
            
            # 添加小计行
            data.append(['', '<b>Subtotal</b>', f"<b>{subtotal:.2f}</b>", f"<b>{total_fee:.2f}</b>"])
            data.append(['', '<b>Total Fee (1%)</b>', '', f"<b>{total_fee:.2f}</b>"])
            data.append(['', '<b>Grand Total</b>', '', f"<b>{grand_total:.2f}</b>"])
            
            # 创建表格
            detail_table = Table(data, colWidths=[1.2*inch, 3.5*inch, 1.2*inch, 1.2*inch])
            detail_table.setStyle(TableStyle([
                # 表头
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # 数据行
                ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -4), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.white, colors.HexColor('#f5f5f5')]),
                # 总计行
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                # 边框
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(detail_table)
            story.append(Spacer(1, 0.5*inch))
            
            # 付款说明
            payment_notes = f"""
            <para>
            <b>Payment Terms:</b> Due upon receipt<br/>
            <b>Note:</b> This invoice includes a 1% processing fee on all {supplier_name} transactions.<br/>
            </para>
            """
            story.append(Paragraph(payment_notes, styles['Normal']))
            
            # 生成PDF
            doc.build(story)
            
            # 保存到数据库
            cursor.execute('''
                INSERT INTO supplier_invoices 
                (customer_id, statement_id, supplier_name, invoice_number, total_amount, supplier_fee, invoice_date, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transactions[0]['customer_id'] if 'customer_id' in transactions[0] else None,
                statement_id,
                supplier_name,
                invoice_number,
                grand_total,
                total_fee,
                datetime.now().strftime('%Y-%m-%d'),
                pdf_path
            ))
            
            conn.commit()
            
            return {
                'invoice_number': invoice_number,
                'pdf_path': pdf_path,
                'total_amount': grand_total,
                'supplier_fee': total_fee,
                'transaction_count': len(transactions)
            }
    
    def generate_all_supplier_invoices(self, statement_id):
        """
        为账单生成所有供应商的发票
        """
        # 7个特定供应商
        suppliers = [
            '7sl', 'Dinas', 'Raub Syc Hainan', 
            'Ai Smart Tech', 'Huawei', 'Pasar Raya', 'Puchong Herbs'
        ]
        
        invoices = []
        for supplier in suppliers:
            invoice = self.generate_supplier_invoice(statement_id, supplier)
            if invoice:
                invoices.append(invoice)
        
        return invoices


def generate_invoice(statement_id, supplier_name):
    """便捷函数：生成单个供应商发票"""
    generator = SupplierInvoiceGenerator()
    return generator.generate_supplier_invoice(statement_id, supplier_name)

def generate_all_invoices(statement_id):
    """便捷函数：生成所有供应商发票"""
    generator = SupplierInvoiceGenerator()
    return generator.generate_all_supplier_invoices(statement_id)
