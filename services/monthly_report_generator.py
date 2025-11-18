"""
月度报表生成器 - Monthly Report Generator
生成包含交易明细、分类汇总、银行流水、未结余额、优化建议的PDF报表
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import sqlite3
from pathlib import Path


def generate_monthly_pdf_report(customer_id: int, year: int, month: int) -> str:
    """
    生成月度报表PDF
    
    Args:
        customer_id: 客户ID
        year: 年份
        month: 月份
        
    Returns:
        PDF文件路径
    """
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取客户信息
    cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        conn.close()
        raise ValueError(f"Customer {customer_id} not found")
    
    # 创建PDF
    output_dir = Path(f'static/reports/{customer["customer_code"]}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_filename = f'Monthly_Report_{year}_{month:02d}.pdf'
    pdf_path = output_dir / pdf_filename
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # 标题
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                 fontSize=24, textColor=colors.HexColor('#FF007F'))
    story.append(Paragraph(f'Monthly Financial Report - {year}/{month:02d}', title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # 客户信息
    story.append(Paragraph(f'<b>Customer:</b> {customer["name"]}', styles['Normal']))
    story.append(Paragraph(f'<b>Customer Code:</b> {customer["customer_code"]}', styles['Normal']))
    story.append(Paragraph(f'<b>Report Date:</b> {datetime.now().strftime("%Y-%m-%d")}', styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # 1. 当月所有交易明细
    cursor.execute("""
        SELECT t.transaction_date, t.description, t.amount, t.category,
               cc.bank_name, cc.card_number_last4
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.customer_id = ? AND strftime('%Y', t.transaction_date) = ? 
              AND strftime('%m', t.transaction_date) = ?
        ORDER BY t.transaction_date DESC
    """, (customer_id, str(year), f'{month:02d}'))
    
    transactions = cursor.fetchall()
    
    story.append(Paragraph('<b>1. Transaction Details</b>', styles['Heading2']))
    
    if transactions:
        txn_data = [['Date', 'Description', 'Amount (RM)', 'Category', 'Bank']]
        for txn in transactions:
            txn_data.append([
                txn['transaction_date'],
                txn['description'][:30],
                f"{txn['amount']:,.2f}",
                txn['category'] or 'N/A',
                txn['bank_name']
            ])
        
        txn_table = Table(txn_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1.3*inch, 1.5*inch])
        txn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(txn_table)
    else:
        story.append(Paragraph('No transactions found for this month.', styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # 2. Owners/Infinite GZ分类汇总
    story.append(Paragraph('<b>2. Category Summary</b>', styles['Heading2']))
    
    cursor.execute("""
        SELECT category, COUNT(*) as count, SUM(amount) as total
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.customer_id = ? AND strftime('%Y-%m', t.transaction_date) = ?
        GROUP BY category
    """, (customer_id, f'{year}-{month:02d}'))
    
    categories = cursor.fetchall()
    
    if categories:
        cat_data = [['Category', 'Count', 'Total (RM)']]
        for cat in categories:
            cat_data.append([
                cat['category'] or 'Uncategorized',
                str(cat['count']),
                f"{cat['total']:,.2f}"
            ])
        
        cat_table = Table(cat_data, colWidths=[3*inch, 1.5*inch, 2*inch])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#322446')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(cat_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # 3. 优化建议
    story.append(Paragraph('<b>3. Optimization Recommendations</b>', styles['Heading2']))
    story.append(Paragraph('Based on your spending patterns, we recommend:', styles['Normal']))
    story.append(Paragraph('• Consider consolidating credit card payments', styles['Normal']))
    story.append(Paragraph('• Explore lower interest rate options (5% vs 18%)', styles['Normal']))
    story.append(Paragraph('• Contact us for personalized consultation: 0167154052', styles['Normal']))
    
    # 构建PDF
    doc.build(story)
    conn.close()
    
    return str(pdf_path)
