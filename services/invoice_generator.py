"""
供应商付款发票生成器 - Professional Invoice Generator
为Supplier支付生成精美专业的PDF发票
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
from typing import List, Dict
from db.database import get_db


class SupplierInvoiceGenerator:
    """供应商发票生成器 - 专业商务风格"""
    
    def __init__(self, output_dir: str = "static/uploads"):
        """
        初始化发票生成器
        
        Args:
            output_dir: 发票输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_invoice(self, supplier_name: str, transactions: List[Dict], 
                        customer_name: str, customer_code: str, statement_date: str,
                        invoice_number: str) -> str:
        """
        生成供应商发票
        
        Args:
            supplier_name: 供应商名称
            transactions: 交易列表
            customer_name: 客户名称
            customer_code: 客户代码
            statement_date: 账单日期
            invoice_number: 发票编号
            
        Returns:
            生成的PDF文件路径（相对路径）
        """
        # 生成文件路径（按客户分类存储）
        year_month = statement_date[:7]  # YYYY-MM
        customer_dir = os.path.join(self.output_dir, f'customers/{customer_code}/invoices/supplier/{year_month}')
        os.makedirs(customer_dir, exist_ok=True)
        
        safe_supplier = supplier_name.replace(' ', '_').replace('/', '_')
        filename = f"Invoice_{safe_supplier}_{invoice_number}_{statement_date}.pdf"
        filepath = os.path.join(customer_dir, filename)
        
        # 创建PDF
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        story = []
        
        styles = getSampleStyleSheet()
        
        # === 专业商务样式定义 ===
        
        # 公司名称样式（Hot Pink强调）
        company_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#FF007F'),  # Hot Pink
            spaceAfter=4,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=30
        )
        
        # 发票标题样式
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#322446'),  # Dark Purple
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # 小标题样式
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#322446'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # 正文样式
        normal_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            leading=14
        )
        
        # 小字样式
        small_style = ParagraphStyle(
            'SmallText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            leading=12
        )
        
        # === 页面顶部：公司信息 ===
        story.append(Paragraph("INFINITE GZ", company_style))
        story.append(Paragraph("Financial Management Services", small_style))
        story.append(Spacer(1, 15))
        
        # 分隔线
        line_table = Table([['']], colWidths=[7.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#FF007F')),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 20))
        
        # === 发票标题和编号 ===
        invoice_header_data = [
            [Paragraph("<b>SUPPLIER PAYMENT INVOICE</b>", title_style), ''],
            ['', '']
        ]
        
        invoice_info_right = f"""
        <para align=right>
        <b>Invoice No:</b> {invoice_number}<br/>
        <b>Invoice Date:</b> {datetime.now().strftime("%d %B %Y")}<br/>
        <b>Statement Period:</b> {statement_date}
        </para>
        """
        
        invoice_header_data[0][1] = Paragraph(invoice_info_right, normal_style)
        
        header_table = Table(invoice_header_data, colWidths=[4*inch, 3.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 25))
        
        # === 客户和供应商信息 ===
        info_data = [
            [Paragraph('<b>BILL TO:</b>', heading_style), Paragraph('<b>SUPPLIER:</b>', heading_style)],
            [
                Paragraph(f"""
                {customer_name}<br/>
                Customer Code: {customer_code}
                """, normal_style),
                Paragraph(f"""
                {supplier_name}<br/>
                Supplier/Merchant
                """, normal_style)
            ]
        ]
        
        info_table = Table(info_data, colWidths=[3.75*inch, 3.75*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 25))
        
        # === 交易明细表格 ===
        story.append(Paragraph("TRANSACTION DETAILS", heading_style))
        story.append(Spacer(1, 10))
        
        # 表格数据
        table_data = [
            ['Date', 'Description', 'Amount', 'Fee (1%)', 'Total']
        ]
        
        total_amount = 0
        total_fee = 0
        
        for txn in transactions:
            date = txn.get('transaction_date', '')
            desc = txn.get('transaction_details', '')
            # 截断过长的描述
            if len(desc) > 60:
                desc = desc[:57] + '...'
            amount = txn.get('amount', 0)
            fee = txn.get('supplier_fee', 0)
            total = amount + fee
            
            total_amount += amount
            total_fee += fee
            
            table_data.append([
                date,
                desc,
                f"RM {amount:,.2f}",
                f"RM {fee:,.2f}",
                f"RM {total:,.2f}"
            ])
        
        # 小计行
        table_data.append(['', '', '', '', ''])
        
        # 总计行
        grand_total = total_amount + total_fee
        table_data.append([
            '', '', 
            Paragraph('<b>Subtotal:</b>', normal_style),
            f"RM {total_fee:,.2f}",
            ''
        ])
        table_data.append([
            '', '', 
            Paragraph('<b>TOTAL AMOUNT DUE:</b>', ParagraphStyle('Bold', parent=normal_style, fontSize=11, fontName='Helvetica-Bold')),
            '',
            Paragraph(f'<b>RM {grand_total:,.2f}</b>', ParagraphStyle('BoldTotal', parent=normal_style, fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#FF007F')))
        ])
        
        # 创建表格
        txn_table = Table(table_data, colWidths=[0.9*inch, 3*inch, 1.2*inch, 1.1*inch, 1.3*inch])
        
        txn_table.setStyle(TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#322446')),  # Dark Purple
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # 数据行样式
            ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 9),
            ('ALIGN', (0, 1), (0, -4), 'CENTER'),  # 日期居中
            ('ALIGN', (1, 1), (1, -4), 'LEFT'),    # 描述左对齐
            ('ALIGN', (2, 1), (-1, -4), 'RIGHT'),  # 金额右对齐
            ('BOTTOMPADDING', (0, 1), (-1, -4), 8),
            ('TOPPADDING', (0, 1), (-1, -4), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # 分隔行
            ('LINEABOVE', (0, -3), (-1, -3), 1, colors.HexColor('#CCCCCC')),
            
            # 总计行样式
            ('ALIGN', (2, -2), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, -2), (-1, -1), 8),
            ('TOPPADDING', (0, -2), (-1, -1), 8),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#FF007F')),
            
            # 外边框
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('GRID', (0, 0), (-1, -4), 0.5, colors.HexColor('#E0E0E0')),
        ]))
        
        story.append(txn_table)
        story.append(Spacer(1, 30))
        
        # === 付款说明 ===
        story.append(Paragraph("PAYMENT TERMS & NOTES", heading_style))
        payment_terms = f"""
        • Total amount includes 1% processing fee on all transactions<br/>
        • Payment is due within 30 days from invoice date<br/>
        • Please reference invoice number <b>{invoice_number}</b> when making payment<br/>
        • For any inquiries, please contact our billing department
        """
        story.append(Paragraph(payment_terms, normal_style))
        story.append(Spacer(1, 30))
        
        # === 页脚 ===
        footer_text = """
        <para align=center>
        <font size=8 color=#999999>
        Thank you for your business | This is a computer-generated invoice
        </font>
        </para>
        """
        story.append(Paragraph(footer_text, small_style))
        
        # 生成PDF
        doc.build(story)
        
        # 返回相对路径
        relative_path = f"customers/{customer_code}/invoices/supplier/{year_month}/{filename}"
        return relative_path
    
    def generate_all_supplier_invoices(self, customer_id: int, statement_id: int) -> List[Dict]:
        """
        为账单中的所有供应商生成发票
        
        Args:
            customer_id: 客户ID
            statement_id: 账单ID
            
        Returns:
            生成的发票信息列表 [{supplier_name, invoice_number, pdf_path, total_amount, supplier_fee}]
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取客户信息
            cursor.execute('SELECT name, customer_code FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            customer_name = row['name']
            customer_code = row['customer_code']
            
            # 获取账单日期
            cursor.execute('SELECT statement_date FROM statements WHERE id = ?', (statement_id,))
            statement_date = cursor.fetchone()['statement_date']
            
            # 获取所有供应商消费（INFINITE expenses）
            cursor.execute('''
                SELECT t.supplier_name, t.transaction_date, t.description, 
                       t.amount, t.supplier_fee
                FROM transactions t
                WHERE t.statement_id = ?
                  AND t.category = 'infinite_expense'
                  AND t.supplier_name IS NOT NULL
                  AND t.supplier_name != ''
                ORDER BY t.supplier_name, t.transaction_date
            ''', (statement_id,))
            
            all_supplier_txns = cursor.fetchall()
        
        if not all_supplier_txns:
            return []
        
        # 按供应商分组
        suppliers_dict = {}
        for txn in all_supplier_txns:
            supplier = txn['supplier_name']
            if supplier not in suppliers_dict:
                suppliers_dict[supplier] = []
            
            suppliers_dict[supplier].append({
                'transaction_date': txn['transaction_date'],
                'transaction_details': txn['description'],
                'amount': txn['amount'],
                'supplier_fee': txn['supplier_fee']
            })
        
        # 为每个供应商生成发票
        invoice_results = []
        year_month = statement_date[:7]
        
        for idx, (supplier, transactions) in enumerate(suppliers_dict.items(), 1):
            # 生成发票编号
            invoice_number = f"INF-{year_month.replace('-', '')}-{supplier.upper().replace(' ', '')[:10]}-{idx:02d}"
            
            # 生成发票
            pdf_path = self.generate_invoice(
                supplier, transactions, customer_name, customer_code,
                statement_date, invoice_number
            )
            
            # 计算总金额
            total_amount = sum(t['amount'] for t in transactions)
            total_fee = sum(t['supplier_fee'] for t in transactions)
            
            invoice_results.append({
                'supplier_name': supplier,
                'invoice_number': invoice_number,
                'pdf_path': pdf_path,
                'total_amount': total_amount,
                'supplier_fee': total_fee,
                'invoice_date': statement_date
            })
            
            # 保存到数据库
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO supplier_invoices 
                    (customer_id, statement_id, supplier_name, invoice_number, 
                     total_amount, supplier_fee, invoice_date, pdf_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (customer_id, statement_id, supplier, invoice_number,
                      total_amount, total_fee, statement_date, pdf_path))
                conn.commit()
        
        return invoice_results


def generate_supplier_invoices_for_statement(customer_id: int, statement_id: int) -> List[Dict]:
    """
    为账单生成所有供应商发票（便捷函数）
    
    Args:
        customer_id: 客户ID
        statement_id: 账单ID
        
    Returns:
        生成的发票信息列表
    """
    generator = SupplierInvoiceGenerator()
    return generator.generate_all_supplier_invoices(customer_id, statement_id)
