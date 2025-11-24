from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

def generate_monthly_report(customer_data, spending_summary, dsr_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    title = Paragraph("Monthly Financial Summary Report", title_style)
    elements.append(title)
    
    report_date = Paragraph(f"Report Generated: {datetime.now().strftime('%d %B %Y')}", styles['Normal'])
    elements.append(report_date)
    elements.append(Spacer(1, 0.3*inch))
    
    customer_heading = Paragraph("Customer Information", heading_style)
    elements.append(customer_heading)
    
    customer_table_data = [
        ['Name:', customer_data.get('name', 'N/A')],
        ['Email:', customer_data.get('email', 'N/A')],
        ['Monthly Income:', f"RM {customer_data.get('monthly_income', 0):,.2f}"]
    ]
    
    customer_table = Table(customer_table_data, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 0.3*inch))
    
    spending_heading = Paragraph("Spending Summary by Category", heading_style)
    elements.append(spending_heading)
    
    spending_table_data = [['Category', 'Amount (RM)', 'Transactions', 'Percentage']]
    total_spending = sum(cat['total'] for cat in spending_summary.values())
    
    for category, data in spending_summary.items():
        percentage = (data['total'] / total_spending * 100) if total_spending > 0 else 0
        spending_table_data.append([
            category,
            f"{data['total']:,.2f}",
            str(data['count']),
            f"{percentage:.1f}%"
        ])
    
    spending_table_data.append([
        'TOTAL',
        f"{total_spending:,.2f}",
        str(sum(cat['count'] for cat in spending_summary.values())),
        '100%'
    ])
    
    spending_table = Table(spending_table_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1*inch])
    spending_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6f2ff')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(spending_table)
    elements.append(Spacer(1, 0.3*inch))
    
    if dsr_data:
        dsr_heading = Paragraph("Debt Service Ratio (DSR) Analysis", heading_style)
        elements.append(dsr_heading)
        
        dsr_table_data = [
            ['Current DSR:', f"{dsr_data.get('dsr', 0):.2%}"],
            ['Total Monthly Repayments:', f"RM {dsr_data.get('total_repayments', 0):,.2f}"],
            ['Max Loan Capacity:', f"RM {dsr_data.get('max_loan', 0):,.2f}"],
            ['Status:', 'Healthy' if dsr_data.get('dsr', 0) < 0.45 else 'Caution']
        ]
        
        dsr_table = Table(dsr_table_data, colWidths=[2.5*inch, 3.5*inch])
        dsr_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(dsr_table)
    
    elements.append(Spacer(1, 0.5*inch))
    footer = Paragraph(
        "This report is generated by Smart Credit & Loan Manager<br/>Confidential - For personal use only", 
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(footer)
    
    doc.build(elements)
    return output_path
