"""
供应商付款发票生成器 - Professional Invoice Generator
为Supplier支付生成精美专业的PDF发票
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os
from typing import List, Dict
from db.database import get_db


class SupplierInvoiceGenerator:
    """供应商发票生成器 - 真实商业风格"""
    
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
        生成供应商发票 - 参考真实商业发票样式
        
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
        # 生成文件路径
        year_month = statement_date[:7]
        customer_dir = os.path.join(self.output_dir, f'customers/{customer_code}/invoices/supplier/{year_month}')
        os.makedirs(customer_dir, exist_ok=True)
        
        safe_supplier = supplier_name.replace(' ', '_').replace('/', '_')
        filename = f"Invoice_{safe_supplier}_{invoice_number}_{statement_date}.pdf"
        filepath = os.path.join(customer_dir, filename)
        
        # 创建PDF
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=A4,
            rightMargin=25*mm,
            leftMargin=25*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        story = []
        
        styles = getSampleStyleSheet()
        
        # === 简洁商业样式定义 ===
        
        # 公司名称
        company_style = ParagraphStyle(
            'Company',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=4
        )
        
        # 副标题
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=2
        )
        
        # INVOICE标题
        invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Normal'],
            fontSize=28,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
            spaceAfter=10
        )
        
        # 小标签
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # 正文
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black
        )
        
        # === 页面顶部 ===
        
        # 公司信息 + INVOICE标题
        header_data = [
            [
                Paragraph("INFINITE GZ SDN BHD", company_style),
                Paragraph("INVOICE", invoice_title_style)
            ],
            [
                Paragraph("Financial Management Services", subtitle_style),
                ''
            ],
            [
                Paragraph("Kuala Lumpur, Malaysia", subtitle_style),
                ''
            ]
        ]
        
        header_table = Table(header_data, colWidths=[3.5*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))
        
        # 顶部分隔线
        line = Table([['']], colWidths=[6.5*inch])
        line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ]))
        story.append(line)
        story.append(Spacer(1, 20))
        
        # === 发票信息 ===
        
        invoice_date = datetime.now().strftime("%d %B %Y")
        
        info_data = [
            [
                Paragraph("<b>BILLED TO:</b>", label_style),
                '',
                Paragraph("<b>Invoice No:</b>", label_style),
                Paragraph(invoice_number, normal_style)
            ],
            [
                Paragraph(customer_name, normal_style),
                '',
                Paragraph("<b>Invoice Date:</b>", label_style),
                Paragraph(invoice_date, normal_style)
            ],
            [
                Paragraph(f"Customer Code: {customer_code}", normal_style),
                '',
                Paragraph("<b>Statement Period:</b>", label_style),
                Paragraph(statement_date, normal_style)
            ],
            ['', '', '', ''],
            [
                Paragraph("<b>SUPPLIER:</b>", label_style),
                '',
                '',
                ''
            ],
            [
                Paragraph(supplier_name, normal_style),
                '',
                '',
                ''
            ]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 25))
        
        # === 交易明细表格 ===
        
        # 表头
        table_data = [
            ['No.', 'Date', 'Description', 'Qty', 'Unit Price', 'Fee (1%)', 'Subtotal']
        ]
        
        total_amount = 0
        total_fee = 0
        
        for idx, txn in enumerate(transactions, 1):
            date = txn.get('transaction_date', '')
            desc = txn.get('transaction_details', '')
            if len(desc) > 45:
                desc = desc[:42] + '...'
            amount = txn.get('amount', 0)
            fee = txn.get('supplier_fee', 0)
            subtotal = amount + fee
            
            total_amount += amount
            total_fee += fee
            
            table_data.append([
                str(idx),
                date,
                desc,
                '1',
                f"RM {amount:,.2f}",
                f"RM {fee:,.2f}",
                f"RM {subtotal:,.2f}"
            ])
        
        # 空白分隔行
        table_data.append(['', '', '', '', '', '', ''])
        
        # 总计
        grand_total = total_amount + total_fee
        table_data.append(['', '', '', '', '', 'Subtotal:', f"RM {total_amount:,.2f}"])
        table_data.append(['', '', '', '', '', 'Processing Fee (1%):', f"RM {total_fee:,.2f}"])
        table_data.append(['', '', '', '', '', 'Total:', f"RM {grand_total:,.2f}"])
        
        # 创建表格
        txn_table = Table(
            table_data,
            colWidths=[0.4*inch, 0.8*inch, 2.5*inch, 0.4*inch, 1*inch, 1.1*inch, 1.1*inch]
        )
        
        txn_table.setStyle(TableStyle([
            # 表头
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, 0), 1, colors.black),
            
            # 数据行
            ('FONTNAME', (0, 1), (-1, -5), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -5), 9),
            ('ALIGN', (0, 1), (0, -5), 'CENTER'),
            ('ALIGN', (1, 1), (1, -5), 'CENTER'),
            ('ALIGN', (2, 1), (2, -5), 'LEFT'),
            ('ALIGN', (3, 1), (3, -5), 'CENTER'),
            ('ALIGN', (4, 1), (-1, -5), 'RIGHT'),
            ('BOTTOMPADDING', (0, 1), (-1, -5), 6),
            ('TOPPADDING', (0, 1), (-1, -5), 6),
            ('GRID', (0, 1), (-1, -5), 0.5, colors.black),
            
            # 总计区域
            ('FONTNAME', (5, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (5, -3), (-1, -1), 9),
            ('ALIGN', (5, -3), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, -3), (-1, -1), 5),
            ('TOPPADDING', (0, -3), (-1, -1), 5),
            ('LINEABOVE', (5, -3), (-1, -3), 1, colors.black),
            ('LINEABOVE', (5, -1), (-1, -1), 1.5, colors.black),
            
            # 外边框
            ('BOX', (0, 0), (-1, -5), 1, colors.black),
        ]))
        
        story.append(txn_table)
        story.append(Spacer(1, 30))
        
        # === 付款条款 ===
        
        terms_style = ParagraphStyle(
            'Terms',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            leading=11
        )
        
        payment_terms = f"""
        <b>PAYMENT TERMS:</b><br/>
        • Payment is due within 30 days from invoice date<br/>
        • Total amount includes 1% processing fee on all transactions<br/>
        • Please reference invoice number <b>{invoice_number}</b> when making payment<br/>
        • For inquiries, please contact our billing department
        """
        story.append(Paragraph(payment_terms, terms_style))
        story.append(Spacer(1, 20))
        
        # === 页脚 ===
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        footer_text = "Thank you for your business | This is a computer-generated invoice"
        story.append(Paragraph(footer_text, footer_style))
        
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
            生成的发票信息列表
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
            
            # 获取所有供应商消费
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
    """
    generator = SupplierInvoiceGenerator()
    return generator.generate_all_supplier_invoices(customer_id, statement_id)
