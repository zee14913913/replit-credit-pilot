"""
Enhanced Monthly Report Generator with Financial Advisory
Includes: Credit card recommendations, optimization suggestions, income requirements, fee policy
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Dict, List
from advisory.card_recommendation_engine import CardRecommendationEngine
from advisory.financial_optimizer import FinancialOptimizer
from db.database import get_db

def generate_enhanced_monthly_report(customer: Dict, output_path: str):
    """生成包含财务建议的增强月结报告"""
    
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1FAA59'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#F5E6C8'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#1FAA59'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    # Report title
    elements.append(Paragraph(f"📊 财务优化月结报告", title_style))
    elements.append(Paragraph(f"Smart Credit & Loan Manager", styles['Normal']))
    elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Customer information
    elements.append(Paragraph(f"客户姓名: {customer['name']}", heading_style))
    elements.append(Paragraph(f"月收入: RM {customer['monthly_income']:,.2f}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Section 1: Credit Card Recommendations
    elements.append(Paragraph("🎯 为您推荐：最适合的信用卡", heading_style))
    elements.append(Paragraph(
        "根据您的消费习惯，我们为您推荐以下信用卡，助您获取更多积分和福利：",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Get recommendations
    card_engine = CardRecommendationEngine()
    recommendations = card_engine.analyze_and_recommend(customer['id'])
    
    if recommendations:
        for i, rec in enumerate(recommendations[:3], 1):
            elements.append(Paragraph(
                f"推荐 #{i}: {rec['bank_name']} {rec['card_name']} (匹配度: {rec['match_score']:.0f}%)",
                subheading_style
            ))
            elements.append(Paragraph(f"• 预计每月收益: <b>RM {rec['estimated_monthly_benefit']:.2f}</b>", styles['Normal']))
            elements.append(Paragraph(f"• 预计年度净收益: <b>RM {rec['annual_benefit']:.2f}</b>", styles['Normal']))
            elements.append(Paragraph(f"• 推荐理由: {rec['reasoning']}", styles['Normal']))
            elements.append(Paragraph(f"• 特别优惠: {rec['special_promotions']}", styles['Normal']))
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph("您目前使用的信用卡已经很适合您的消费习惯。", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # Section 2: Financial Optimization Suggestions
    elements.append(Paragraph("💡 财务优化建议", heading_style))
    elements.append(Paragraph(
        "基于马来西亚国家银行(BNM)最新政策和各大银行最新利率，我们为您提供以下优化方案：",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    
    # Get optimization suggestions
    optimizer = FinancialOptimizer()
    optimizations = optimizer.generate_optimization_suggestions(customer['id'])
    
    if optimizations:
        for i, opt in enumerate(optimizations, 1):
            opt_type_cn = {
                'debt_consolidation': '债务整合',
                'balance_transfer': '余额转移',
                'refinancing': '贷款再融资'
            }.get(opt['optimization_type'], opt['optimization_type'])
            
            elements.append(Paragraph(f"优化方案 #{i}: {opt_type_cn}", subheading_style))
            
            # Comparison table: Before vs After
            comparison_data = [
                ['项目', '优化前', '优化后', '节省'],
                ['月供', f"RM {opt['current_monthly_payment']:.2f}", 
                 f"RM {opt['optimized_monthly_payment']:.2f}",
                 f"RM {opt['monthly_savings']:.2f}"],
                ['利率', f"{opt['current_interest_rate']:.2f}%", 
                 f"{opt['optimized_interest_rate']:.2f}%",
                 f"{opt['current_interest_rate'] - opt['optimized_interest_rate']:.2f}%"],
                ['总成本 (3年)', f"RM {opt['current_total_cost']:.2f}", 
                 f"RM {opt['optimized_total_cost']:.2f}",
                 f"RM {opt['total_savings']:.2f}"]
            ]
            
            comparison_table = Table(comparison_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            comparison_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1FAA59')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(comparison_table)
            elements.append(Spacer(1, 10))
            
            elements.append(Paragraph(f"<b>额外收益:</b> {opt['additional_benefits']}", styles['Normal']))
            elements.append(Paragraph(f"<b>推荐银行:</b> {opt['recommended_bank']}", styles['Normal']))
            elements.append(Paragraph(f"<b>推荐产品:</b> {opt['recommended_product']}", styles['Normal']))
            elements.append(Spacer(1, 10))
            
            # Highlight total benefit
            elements.append(Paragraph(
                f"⭐ <b>采用此方案，您将每月节省 RM {opt['monthly_savings']:.2f}，3年总共节省 RM {opt['total_savings']:.2f}！</b>",
                ParagraphStyle('Highlight', parent=styles['Normal'], textColor=colors.HexColor('#1FAA59'), fontSize=11)
            ))
            elements.append(Spacer(1, 15))
    else:
        elements.append(Paragraph("您目前的财务状况良好，暂无需优化。", styles['Normal']))
    
    elements.append(PageBreak())
    
    # Section 3: Income Documentation Requirements
    elements.append(Paragraph("📋 收入证明要求说明", heading_style))
    
    # Get customer employment type if exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT employment_type FROM customer_employment_types 
            WHERE customer_id = ?
        ''', (customer['id'],))
        emp_row = cursor.fetchone()
        emp_type = emp_row['employment_type'] if emp_row else 'employee'
        
        # Get relevant service terms
        term_type = f'income_requirements_{emp_type}'
        cursor.execute('''
            SELECT title_cn, content_cn FROM service_terms 
            WHERE term_type = ?
        ''', (term_type,))
        term_row = cursor.fetchone()
        
        if term_row:
            elements.append(Paragraph(term_row['title_cn'], subheading_style))
            for paragraph in term_row['content_cn'].split('\n\n'):
                elements.append(Paragraph(paragraph.replace('\n', '<br/>'), styles['Normal']))
                elements.append(Spacer(1, 8))
    
    elements.append(Spacer(1, 20))
    
    # Section 4: Fee Policy Declaration
    elements.append(Paragraph("💎 我们的承诺：成功收费政策", heading_style))
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content_cn FROM service_terms 
            WHERE term_type = 'fee_policy'
        ''')
        fee_policy_row = cursor.fetchone()
        
        if fee_policy_row:
            for paragraph in fee_policy_row['content_cn'].split('\n\n'):
                elements.append(Paragraph(paragraph.replace('\n', '<br/>'), styles['Normal']))
                elements.append(Spacer(1, 10))
    
    elements.append(Spacer(1, 20))
    
    # Call to action
    elements.append(Paragraph("💬 想了解完整的优化方案？", heading_style))
    elements.append(Paragraph(
        "如果您对以上任何优化建议感兴趣，希望深入了解详情并获得专业咨询，"
        "请通过系统通知我们。我们的财务顾问团队将为您提供一对一的专业服务。",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "🎯 <b>记住：只有当我们为您节省或赚取收益后，我们才收取费用（50%收益分成）。"
        "如果没有为您创造任何价值，我们不收取任何费用！</b>",
        ParagraphStyle('CallOut', parent=styles['Normal'], 
                      textColor=colors.HexColor('#1FAA59'), 
                      fontSize=12, 
                      alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(elements)
    return output_path
