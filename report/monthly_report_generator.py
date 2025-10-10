"""
月度报表自动生成系统 (Consolidated Customer Version)
Monthly Report Auto-Generator (Consolidated Per Customer)

核心改进：
1. 一个月一份综合报表（包含所有信用卡）
2. 客户交易 vs INFINITE交易分离
3. 客户未清余额 vs INFINITE未清余额
4. Instalment capital余额追踪
5. 每张卡的完整交易明细 + 优化建议
6. 整体财务健康分析和50/50服务流程集成
"""

from db.database import get_db
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os


# 7家指定Supplier商家（INFINITE交易）
INFINITE_SUPPLIERS = [
    '7sl', 'dinas', 'raub syc hainan', 
    'ai smart tech', 'huawei', 'pasar raya', 'puchong herbs'
]


class MonthlyReportGenerator:
    """月度报表生成器 - 按信用卡分别生成"""
    
    def __init__(self, output_folder='static/reports/monthly'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def get_card_month_data(self, card_id, year, month):
        """
        获取指定信用卡在指定月份的数据
        按statement_date的月份分组
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. 获取信用卡信息
            cursor.execute('''
                SELECT cc.*, c.name as customer_name, c.monthly_income
                FROM credit_cards cc
                JOIN customers c ON cc.customer_id = c.id
                WHERE cc.id = ?
            ''', (card_id,))
            
            card_info = cursor.fetchone()
            if not card_info:
                return None
            
            card_info = dict(card_info)
            customer_id = card_info['customer_id']
            
            # 2. 获取该月该卡的所有statements
            cursor.execute('''
                SELECT *
                FROM statements
                WHERE card_id = ?
                  AND strftime('%Y', statement_date) = ?
                  AND strftime('%m', statement_date) = ?
                  AND is_confirmed = 1
                ORDER BY statement_date
            ''', (card_id, str(year), str(month).zfill(2)))
            
            statements = [dict(row) for row in cursor.fetchall()]
            
            if not statements:
                return None
            
            statement_ids = [s['id'] for s in statements]
            
            # 3. 获取该卡该月的所有交易
            placeholders = ','.join('?' * len(statement_ids))
            cursor.execute(f'''
                SELECT *
                FROM transactions
                WHERE statement_id IN ({placeholders})
            ''', statement_ids)
            
            transactions = [dict(row) for row in cursor.fetchall()]
            
            # 4. 分类统计 - 客户 vs INFINITE
            customer_debit_supplier = 0  # 客户在Supplier的消费（非INFINITE商家）
            customer_debit_other = 0     # 客户其他消费
            customer_credit_owner = 0    # Owner付款（客户的付款）
            customer_credit_other = 0    # 其他付款
            
            infinite_debit_suppliers = 0  # INFINITE在7家商家的消费
            infinite_debit_3rdparty = 0   # INFINITE的3rd party payment
            infinite_credit = 0           # INFINITE的付款
            infinite_supplier_fees = 0    # INFINITE的1% merchant fee
            
            for t in transactions:
                amount = abs(t['amount'])
                desc_lower = t['description'].lower()
                
                if t['transaction_type'] == 'debit':
                    # Debit交易（消费）
                    is_infinite_supplier = any(supplier in desc_lower for supplier in INFINITE_SUPPLIERS)
                    
                    if t.get('transaction_subtype') == 'supplier_debit':
                        # Supplier商家消费
                        if is_infinite_supplier:
                            # 7家指定商家 → INFINITE
                            infinite_debit_suppliers += amount
                            infinite_supplier_fees += t.get('supplier_fee', 0)
                        else:
                            # 其他Supplier → 客户
                            customer_debit_supplier += amount
                    elif t.get('transaction_subtype') == '3rd_party_payment':
                        # 3rd party payment → INFINITE
                        infinite_debit_3rdparty += amount
                    else:
                        # 其他消费 → 客户
                        customer_debit_other += amount
                
                elif t['transaction_type'] == 'credit':
                    # Credit交易（付款）
                    if t.get('payment_user') == 'infinite' or t.get('transaction_subtype') == 'infinite_payment':
                        # INFINITE付款
                        infinite_credit += amount
                    elif t.get('payment_user') == 'owner':
                        # Owner付款 → 客户付款
                        customer_credit_owner += amount
                    else:
                        # 其他付款 → 客户付款
                        customer_credit_other += amount
            
            # 5. 获取该客户该月的分期付款
            cursor.execute('''
                SELECT ip.*, 
                       (SELECT SUM(remaining_balance) 
                        FROM instalment_payment_records 
                        WHERE plan_id = ip.id AND status = 'pending' 
                        LIMIT 1) as capital_balance
                FROM instalment_plans ip
                WHERE ip.customer_id = ?
                  AND ip.status = 'active'
                  AND strftime('%Y-%m', ip.start_date) <= ?
                  AND strftime('%Y-%m', ip.end_date) >= ?
            ''', (customer_id, f"{year}-{str(month).zfill(2)}", f"{year}-{str(month).zfill(2)}"))
            
            instalments = [dict(row) for row in cursor.fetchall()]
            total_instalment_payment = sum(p['monthly_payment'] for p in instalments)
            total_instalment_capital = sum(p['capital_balance'] or p['principal_amount'] for p in instalments)
            
            # 6. 计算客户未清余额和INFINITE未清余额
            customer_total_debit = customer_debit_supplier + customer_debit_other
            customer_total_credit = customer_credit_owner + customer_credit_other
            customer_outstanding = customer_total_debit - customer_total_credit
            
            infinite_total_debit = infinite_debit_suppliers + infinite_debit_3rdparty
            infinite_total_credit = infinite_credit
            infinite_outstanding = infinite_total_debit - infinite_total_credit
            
            # 7. DSR计算
            monthly_income = card_info['monthly_income']
            dsr = (total_instalment_payment / monthly_income * 100) if monthly_income > 0 else 0
            
            return {
                'card_info': card_info,
                'customer_id': customer_id,
                'year': year,
                'month': month,
                'statements': statements,
                'transactions': transactions,
                
                # 客户数据
                'customer': {
                    'debit_supplier': customer_debit_supplier,
                    'debit_other': customer_debit_other,
                    'total_debit': customer_total_debit,
                    'credit_owner': customer_credit_owner,
                    'credit_other': customer_credit_other,
                    'total_credit': customer_total_credit,
                    'outstanding': customer_outstanding
                },
                
                # INFINITE数据
                'infinite': {
                    'debit_suppliers': infinite_debit_suppliers,
                    'debit_3rdparty': infinite_debit_3rdparty,
                    'total_debit': infinite_total_debit,
                    'total_credit': infinite_total_credit,
                    'outstanding': infinite_outstanding,
                    'supplier_fees': infinite_supplier_fees
                },
                
                # 分期付款
                'instalment': {
                    'plans': instalments,
                    'total_payment': total_instalment_payment,
                    'capital_balance': total_instalment_capital
                },
                
                # DSR
                'dsr': dsr,
                'monthly_income': monthly_income
            }
    
    def generate_card_monthly_report_pdf(self, card_id, year, month):
        """
        为指定信用卡生成月度PDF报表
        """
        data = self.get_card_month_data(card_id, year, month)
        
        if not data:
            return None
        
        card = data['card_info']
        
        # 创建PDF文件
        filename = f"Monthly_Report_{card['customer_name']}_{card['bank_name']}_{card['card_number_last4']}_{year}_{str(month).zfill(2)}.pdf"
        pdf_path = os.path.join(self.output_folder, filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                               leftMargin=0.75*inch, rightMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # === 标题 ===
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"MONTHLY STATEMENT REPORT", title_style))
        story.append(Paragraph(f"{year}年{month}月信用卡月结报告", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # === 信用卡信息 ===
        info_data = [
            ['Customer / 客户', card['customer_name']],
            ['Credit Card / 信用卡', f"{card['bank_name']} ****{card['card_number_last4']}"],
            ['Report Period / 报表期间', f"{year}-{str(month).zfill(2)}"],
            ['Monthly Income / 月收入', f"RM {data['monthly_income']:,.2f}"]
        ]
        
        info_table = Table(info_data, colWidths=[2.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.4*inch))
        
        # === 交易记录明细表 (TRANSACTION DETAILS) ===
        story.append(Paragraph("<b>TRANSACTION DETAILS / 交易记录明细</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # 对交易进行分类
        customer_debit_txns = []
        customer_credit_txns = []
        infinite_debit_txns = []
        infinite_credit_txns = []
        
        for t in data['transactions']:
            desc_lower = t['description'].lower()
            is_infinite_supplier = any(supplier in desc_lower for supplier in INFINITE_SUPPLIERS)
            
            if t['transaction_type'] == 'debit':
                # Debit交易（消费）
                if t.get('transaction_subtype') == 'supplier_debit' and is_infinite_supplier:
                    infinite_debit_txns.append(t)
                elif t.get('transaction_subtype') == '3rd_party_payment':
                    infinite_debit_txns.append(t)
                else:
                    customer_debit_txns.append(t)
            elif t['transaction_type'] == 'credit':
                # Credit交易（付款）
                # 检查是否为INFINITE付款（如果payment_user标记为'infinite'或相关标识）
                if t.get('payment_user') == 'infinite' or t.get('transaction_subtype') == 'infinite_payment':
                    infinite_credit_txns.append(t)
                elif t.get('payment_user') == 'owner':
                    customer_credit_txns.append(t)
                else:
                    # 默认归类为客户付款
                    customer_credit_txns.append(t)
        
        # 1. 客户消费明细
        if customer_debit_txns:
            story.append(Paragraph("<b>1. CUSTOMER DEBIT / 客户消费明细</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            debit_data = [['Date/日期', 'Description/描述', 'Amount/金额']]
            for t in customer_debit_txns:
                debit_data.append([
                    t['transaction_date'][:10] if t['transaction_date'] else 'N/A',
                    t['description'][:50],  # 限制长度
                    f"RM {abs(t['amount']):,.2f}"
                ])
            
            debit_table = Table(debit_data, colWidths=[1.2*inch, 3.5*inch, 1.3*inch])
            debit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(debit_table)
            story.append(Spacer(1, 0.3*inch))
        
        # 2. 客户付款明细
        if customer_credit_txns:
            story.append(Paragraph("<b>2. CUSTOMER CREDIT / 客户付款明细</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            credit_data = [['Date/日期', 'Description/描述', 'Amount/金额']]
            for t in customer_credit_txns:
                credit_data.append([
                    t['transaction_date'][:10] if t['transaction_date'] else 'N/A',
                    t['description'][:50],
                    f"RM {abs(t['amount']):,.2f}"
                ])
            
            credit_table = Table(credit_data, colWidths=[1.2*inch, 3.5*inch, 1.3*inch])
            credit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(credit_table)
            story.append(Spacer(1, 0.3*inch))
        
        # 3. INFINITE消费明细
        if infinite_debit_txns:
            story.append(Paragraph("<b>3. INFINITE GZ DEBIT / INFINITE消费明细</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            inf_debit_data = [['Date/日期', 'Description/描述', 'Amount/金额']]
            for t in infinite_debit_txns:
                inf_debit_data.append([
                    t['transaction_date'][:10] if t['transaction_date'] else 'N/A',
                    t['description'][:50],
                    f"RM {abs(t['amount']):,.2f}"
                ])
            
            inf_debit_table = Table(inf_debit_data, colWidths=[1.2*inch, 3.5*inch, 1.3*inch])
            inf_debit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(inf_debit_table)
            story.append(Spacer(1, 0.3*inch))
        
        # 4. INFINITE付款明细（如果有）
        if infinite_credit_txns:
            story.append(Paragraph("<b>4. INFINITE GZ CREDIT / INFINITE付款明细</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            inf_credit_data = [['Date/日期', 'Description/描述', 'Amount/金额']]
            for t in infinite_credit_txns:
                inf_credit_data.append([
                    t['transaction_date'][:10] if t['transaction_date'] else 'N/A',
                    t['description'][:50],
                    f"RM {abs(t['amount']):,.2f}"
                ])
            
            inf_credit_table = Table(inf_credit_data, colWidths=[1.2*inch, 3.5*inch, 1.3*inch])
            inf_credit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(inf_credit_table)
            story.append(Spacer(1, 0.3*inch))
        
        # 分页 - 明细和汇总分开
        story.append(PageBreak())
        
        # === A. 客户交易汇总 ===
        story.append(Paragraph("<b>A. CUSTOMER TRANSACTIONS SUMMARY / 客户交易汇总</b>", styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        customer_debit_data = [
            ['<b>CUSTOMER DEBIT / 客户消费</b>', '<b>Amount / 金额</b>'],
            ['Supplier Expenses / Supplier消费', f"RM {data['customer']['debit_supplier']:,.2f}"],
            ['Other Expenses / 其他消费', f"RM {data['customer']['debit_other']:,.2f}"],
            ['<b>Total Debit / 消费总计</b>', f"<b>RM {data['customer']['total_debit']:,.2f}</b>"]
        ]
        
        customer_debit_table = Table(customer_debit_data, colWidths=[3.5*inch, 2.5*inch])
        customer_debit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fadbd8')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(customer_debit_table)
        story.append(Spacer(1, 0.2*inch))
        
        customer_credit_data = [
            ['<b>CUSTOMER CREDIT / 客户付款</b>', '<b>Amount / 金额</b>'],
            ['Owner Payment / Owner付款', f"RM {data['customer']['credit_owner']:,.2f}"],
            ['Other Payments / 其他付款', f"RM {data['customer']['credit_other']:,.2f}"],
            ['<b>Total Credit / 付款总计</b>', f"<b>RM {data['customer']['total_credit']:,.2f}</b>"]
        ]
        
        customer_credit_table = Table(customer_credit_data, colWidths=[3.5*inch, 2.5*inch])
        customer_credit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d5f4e6')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(customer_credit_table)
        story.append(Spacer(1, 0.2*inch))
        
        # 客户未清余额
        customer_outstanding_data = [
            ['<b>CUSTOMER OUTSTANDING / 客户未清余额</b>', 
             f"<b>RM {data['customer']['outstanding']:,.2f}</b>"]
        ]
        
        customer_outstanding_table = Table(customer_outstanding_data, colWidths=[3.5*inch, 2.5*inch])
        customer_outstanding_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(customer_outstanding_table)
        story.append(Spacer(1, 0.4*inch))
        
        # === B. INFINITE GZ交易汇总 ===
        story.append(Paragraph("<b>B. INFINITE GZ TRANSACTIONS / INFINITE GZ交易汇总</b>", styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        infinite_debit_data = [
            ['<b>INFINITE DEBIT / INFINITE消费</b>', '<b>Amount / 金额</b>'],
            ['7 Suppliers Merchants / 7家指定商家', f"RM {data['infinite']['debit_suppliers']:,.2f}"],
            ['3rd Party Payments / 第三方付款', f"RM {data['infinite']['debit_3rdparty']:,.2f}"],
            ['<b>Total INFINITE Debit / INFINITE总消费</b>', f"<b>RM {data['infinite']['total_debit']:,.2f}</b>"]
        ]
        
        infinite_debit_table = Table(infinite_debit_data, colWidths=[3.5*inch, 2.5*inch])
        infinite_debit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ebdef0')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(infinite_debit_table)
        story.append(Spacer(1, 0.2*inch))
        
        # INFINITE Credit（如果有）
        if data['infinite']['total_credit'] > 0:
            infinite_credit_data = [
                ['<b>INFINITE CREDIT / INFINITE付款</b>', '<b>Amount / 金额</b>'],
                ['<b>Total INFINITE Credit / INFINITE总付款</b>', f"<b>RM {data['infinite']['total_credit']:,.2f}</b>"]
            ]
            
            infinite_credit_table = Table(infinite_credit_data, colWidths=[3.5*inch, 2.5*inch])
            infinite_credit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fdebd0')),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(infinite_credit_table)
            story.append(Spacer(1, 0.2*inch))
        
        # INFINITE Supplier Fee (1%)
        if data['infinite']['supplier_fees'] > 0:
            fee_text = f"💰 <b>INFINITE Merchant Fee (1%):</b> RM {data['infinite']['supplier_fees']:,.2f}"
            story.append(Paragraph(fee_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # INFINITE未清余额
        infinite_outstanding_data = [
            ['<b>INFINITE OUTSTANDING / INFINITE未清余额</b>', 
             f"<b>RM {data['infinite']['outstanding']:,.2f}</b>"]
        ]
        
        infinite_outstanding_table = Table(infinite_outstanding_data, colWidths=[3.5*inch, 2.5*inch])
        infinite_outstanding_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(infinite_outstanding_table)
        story.append(Spacer(1, 0.4*inch))
        
        # === C. 分期付款汇总 ===
        story.append(Paragraph("<b>C. INSTALMENT SUMMARY / 分期付款汇总</b>", styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        if data['instalment']['plans']:
            instalment_data = [
                ['Product / 商品', 'Monthly Payment / 月供', 'Capital Balance / 本金余额']
            ]
            
            for plan in data['instalment']['plans']:
                capital_balance = plan.get('capital_balance') or plan['principal_amount']
                instalment_data.append([
                    plan['product_name'],
                    f"RM {plan['monthly_payment']:,.2f}",
                    f"RM {capital_balance:,.2f}"
                ])
            
            instalment_data.append([
                '<b>Total / 总计</b>',
                f"<b>RM {data['instalment']['total_payment']:,.2f}</b>",
                f"<b>RM {data['instalment']['capital_balance']:,.2f}</b>"
            ])
            
            instalment_table = Table(instalment_data, colWidths=[2.5*inch, 1.75*inch, 1.75*inch])
            instalment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1f2eb')),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(instalment_table)
        else:
            story.append(Paragraph("No active instalment plans / 无活跃分期计划", styles['Normal']))
        
        story.append(Spacer(1, 0.4*inch))
        
        # === D. DSR分析和优化建议 ===
        story.append(Paragraph("<b>D. DSR ANALYSIS & OPTIMIZATION / DSR分析和优化建议</b>", styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        dsr_data = [
            ['Monthly Income / 月收入', f"RM {data['monthly_income']:,.2f}"],
            ['Total Monthly Repayment / 总月供', f"RM {data['instalment']['total_payment']:,.2f}"],
            ['<b>DSR Ratio / 债务负担率</b>', f"<b>{data['dsr']:.1f}%</b>"]
        ]
        
        dsr_table = Table(dsr_data, colWidths=[3.5*inch, 2.5*inch])
        dsr_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1'))
        ]))
        
        story.append(dsr_table)
        story.append(Spacer(1, 0.2*inch))
        
        # DSR状态和建议
        dsr_status = "✅ Healthy / 健康" if data['dsr'] < 70 else "⚠️ High Risk / 高风险"
        recommendation = self._get_optimization_recommendation(data)
        
        story.append(Paragraph(f"<b>DSR Status / 状态:</b> {dsr_status}", styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph(f"<b>Optimization Recommendation / 优化建议:</b>", styles['Heading3']))
        story.append(Paragraph(recommendation, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # === E. 50/50服务流程 ===
        service_info = """
        <b>💡 INFINITE GZ Advisory Service / 咨询服务</b><br/>
        <br/>
        如果您想了解完整的优化方案（债务整合、余额转移、贷款再融资等），我们的顾问团队随时为您服务：<br/>
        <br/>
        <b>服务流程 / Service Process:</b><br/>
        1️⃣ 系统将通知我们的顾问为您准备详细优化方案<br/>
        2️⃣ 顾问与您讨论方案细节和预期节省金额<br/>
        3️⃣ 双方同意后，生成授权合约（中英双语）供双方签署<br/>
        4️⃣ 我们帮您执行优化方案<br/>
        <br/>
        <b>💰 收费模式 / Fee Structure:</b><br/>
        • <b>零风险保证</b>：如果没有帮您省钱或赚到额外利润，我们不收取任何费用<br/>
        • <b>50/50利润分成</b>：只从我们帮您节省或赚取的金额中收取50%作为服务报酬<br/>
        • 例如：我们帮您节省RM 10,000，我们收取RM 5,000，您净赚RM 5,000<br/>
        <br/>
        <i>联系方式: infinitegz.reminder@gmail.com</i>
        """
        
        service_style = ParagraphStyle(
            'ServiceInfo',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            leftIndent=10,
            rightIndent=10
        )
        
        story.append(Paragraph(service_info, service_style))
        
        # 生成PDF
        doc.build(story)
        
        # 保存到数据库
        self._save_report_record(card_id, year, month, pdf_path, data)
        
        return pdf_path
    
    def _get_optimization_recommendation(self, data):
        """根据该信用卡的数据生成个性化优化建议"""
        card = data['card_info']
        dsr = data['dsr']
        customer_outstanding = data['customer']['outstanding']
        infinite_outstanding = data['infinite']['outstanding']
        customer_debit = data['customer']['total_debit']
        infinite_debit = data['infinite']['total_debit']
        
        recommendations = []
        
        # 1. 整体DSR评估
        if dsr > 70:
            recommendations.append(f"<b>⚠️ 高风险警告：</b>您的DSR为 {dsr:.1f}%，已超过70%健康标准。强烈建议考虑债务整合以降低月供压力。")
        elif dsr > 50:
            recommendations.append(f"<b>💡 优化建议：</b>您的DSR为 {dsr:.1f}%，建议通过余额转移或再融资降低利率，减轻债务负担。")
        else:
            recommendations.append(f"<b>✅ 财务健康：</b>您的DSR为 {dsr:.1f}%，属于健康范围，继续保持良好的理财习惯。")
        
        # 2. 客户未清余额分析
        if customer_outstanding > 10000:
            recommendations.append(f"<b>📊 客户未清余额：</b>RM {customer_outstanding:,.2f}（较高）- 建议优先还款或申请低利率余额转移，可节省利息支出。")
        elif customer_outstanding > 5000:
            recommendations.append(f"<b>📊 客户未清余额：</b>RM {customer_outstanding:,.2f}（中等）- 建议制定还款计划，逐步降低欠款。")
        elif customer_outstanding > 0:
            recommendations.append(f"<b>📊 客户未清余额：</b>RM {customer_outstanding:,.2f}（较低）- 维持良好的还款习惯。")
        else:
            recommendations.append(f"<b>✅ 客户账户：</b>无未清余额，财务管理优秀！")
        
        # 3. INFINITE未清余额分析
        if infinite_outstanding > 0:
            recommendations.append(f"<b>🏢 INFINITE未清余额：</b>RM {infinite_outstanding:,.2f} - 公司业务欠款，需要公司财务部门结算。")
        
        # 4. 信用卡使用模式分析
        if customer_debit > 0 and infinite_debit > 0:
            recommendations.append(f"<b>💳 用卡模式：</b>此卡混合使用（客户消费 RM {customer_debit:,.2f} + INFINITE业务 RM {infinite_debit:,.2f}）。建议分开使用不同卡片以便更清晰管理。")
        elif customer_debit > 0:
            recommendations.append(f"<b>💳 用卡模式：</b>此卡主要用于个人消费（RM {customer_debit:,.2f}），使用模式清晰。")
        elif infinite_debit > 0:
            recommendations.append(f"<b>💳 用卡模式：</b>此卡主要用于公司业务（RM {infinite_debit:,.2f}），使用模式清晰。")
        
        # 5. 分期付款优化
        if data['instalment']['capital_balance'] > 0:
            recommendations.append(f"<b>📅 分期付款：</b>剩余本金 RM {data['instalment']['capital_balance']:,.2f}。如果找到更低利率贷款，可考虑提前还清再融资，能节省利息成本。")
        
        # 6. 信用卡推荐
        if customer_debit > 3000:
            recommendations.append(f"<b>💡 信用卡优化：</b>您本月消费 RM {customer_debit:,.2f}，可考虑申请高回赠率信用卡（如现金回赠2-5%），每月可省RM {customer_debit * 0.03:,.2f}左右。")
        
        return "<br/><br/>".join(recommendations) if recommendations else "✅ 您的财务管理良好，继续保持！"
    
    def _save_report_record(self, card_id, year, month, pdf_path, data):
        """保存报表记录到数据库"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 计算总额（为兼容旧字段）
            total_debit = data['customer']['total_debit'] + data['infinite']['total_debit']
            total_credit = data['customer']['total_credit']
            net_amount = total_debit - total_credit
            
            # 删除该客户该月的旧记录（如果存在）
            # 注意：旧系统按customer_id生成，新系统按card_id生成，需要删除旧记录以避免UNIQUE冲突
            cursor.execute('''
                DELETE FROM monthly_reports
                WHERE customer_id = ? AND report_year = ? AND report_month = ?
            ''', (data['customer_id'], year, month))
            
            # 插入新记录
            cursor.execute('''
                INSERT INTO monthly_reports (
                    customer_id, card_id, report_year, report_month,
                    total_debit, total_credit, net_amount,
                    customer_total_debit, customer_total_credit, customer_outstanding,
                    infinite_total_debit, infinite_outstanding,
                    total_instalment, instalment_capital_balance,
                    dsr, supplier_fees, infinite_supplier_fees,
                    pdf_path, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                data['customer_id'], card_id, year, month,
                total_debit, total_credit, net_amount,
                data['customer']['total_debit'],
                data['customer']['total_credit'],
                data['customer']['outstanding'],
                data['infinite']['total_debit'],
                data['infinite']['outstanding'],
                data['instalment']['total_payment'],
                data['instalment']['capital_balance'],
                data['dsr'],
                data['infinite']['supplier_fees'],
                data['infinite']['supplier_fees'],
                pdf_path
            ))
            
            conn.commit()
    
    def generate_customer_monthly_report_pdf(self, customer_id, year, month):
        """
        生成客户的综合月度报表PDF（包含所有信用卡）
        一个月一份PDF，包含该客户所有信用卡的完整交易明细和分析
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. 获取客户信息
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return None
            customer = dict(customer)
            
            # 2. 获取该客户该月所有有confirmed statements的信用卡
            cursor.execute('''
                SELECT DISTINCT cc.*
                FROM credit_cards cc
                JOIN statements s ON cc.id = s.card_id
                WHERE cc.customer_id = ?
                  AND strftime('%Y', s.statement_date) = ?
                  AND strftime('%m', s.statement_date) = ?
                  AND s.is_confirmed = 1
                ORDER BY cc.id
            ''', (customer_id, str(year), str(month).zfill(2)))
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            if not cards:
                return None
            
            # 3. 为每张卡获取数据
            cards_data = []
            for card in cards:
                card_data = self.get_card_month_data(card['id'], year, month)
                if card_data:
                    cards_data.append(card_data)
            
            if not cards_data:
                return None
        
        # 4. 创建综合PDF文件
        filename = f"Monthly_Report_{customer['name']}_{year}_{str(month).zfill(2)}.pdf"
        pdf_path = os.path.join(self.output_folder, filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                               leftMargin=0.75*inch, rightMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # ===  标题页 ===
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"CONSOLIDATED MONTHLY REPORT", title_style))
        story.append(Paragraph(f"{year}年{month}月综合月结报告", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 客户信息
        customer_info_data = [
            ['Customer / 客户', customer['name']],
            ['Report Period / 报表期间', f"{year}-{str(month).zfill(2)}"],
            ['Total Cards / 信用卡数量', f"{len(cards_data)} cards"],
            ['Monthly Income / 月收入', f"RM {customer['monthly_income']:,.2f}"]
        ]
        
        customer_info_table = Table(customer_info_data, colWidths=[2.5*inch, 4*inch])
        customer_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(customer_info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 月度总览汇总
        total_customer_debit = sum(d['customer']['total_debit'] for d in cards_data)
        total_customer_credit = sum(d['customer']['total_credit'] for d in cards_data)
        total_customer_outstanding = sum(d['customer']['outstanding'] for d in cards_data)
        total_infinite_debit = sum(d['infinite']['total_debit'] for d in cards_data)
        total_infinite_credit = sum(d['infinite']['total_credit'] for d in cards_data)
        total_infinite_outstanding = sum(d['infinite']['outstanding'] for d in cards_data)
        total_instalment = sum(d['instalment']['total_payment'] for d in cards_data)
        
        overview_data = [
            ['<b>MONTHLY OVERVIEW / 月度总览</b>', '<b>Amount / 金额</b>'],
            ['Total Customer Debit / 客户总消费', f"RM {total_customer_debit:,.2f}"],
            ['Total Customer Credit / 客户总付款', f"RM {total_customer_credit:,.2f}"],
            ['Total Customer Outstanding / 客户总未清', f"RM {total_customer_outstanding:,.2f}"],
            ['Total INFINITE Debit / INFINITE总消费', f"RM {total_infinite_debit:,.2f}"],
            ['Total INFINITE Credit / INFINITE总付款', f"RM {total_infinite_credit:,.2f}"],
            ['Total INFINITE Outstanding / INFINITE总未清', f"RM {total_infinite_outstanding:,.2f}"],
            ['Total Monthly Instalment / 总月供', f"RM {total_instalment:,.2f}"]
        ]
        
        overview_table = Table(overview_data, colWidths=[3.5*inch, 2.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')])
        ]))
        
        story.append(overview_table)
        story.append(PageBreak())
        
        # === 为每张信用卡生成独立章节 ===
        for idx, card_data in enumerate(cards_data, 1):
            card = card_data['card_info']
            
            # 卡片章节标题
            card_title = f"CARD {idx}: {card['bank_name']} ****{card['card_number_last4']}"
            story.append(Paragraph(f"<b>{card_title}</b>", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            # 调用现有的卡片详情生成逻辑
            self._add_card_details_to_story(story, card_data, styles)
            
            # 每张卡后分页（除了最后一张）
            if idx < len(cards_data):
                story.append(PageBreak())
        
        # === 整体财务分析和50/50服务 ===
        self._add_overall_analysis_to_story(story, cards_data, customer, styles)
        
        # 生成PDF
        doc.build(story)
        
        # 保存记录到数据库
        self._save_consolidated_report_record(customer_id, year, month, pdf_path, cards_data)
        
        return pdf_path
    
    def _add_card_details_to_story(self, story, data, styles):
        """添加单张卡的详细内容到story中"""
        # 交易明细（简化版 - 仅列出交易数量）
        story.append(Paragraph(f"<b>Transaction Summary / 交易汇总</b>", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        
        txn_summary = [
            ['Total Transactions / 交易总数', str(len(data['transactions']))],
            ['Customer Debit / 客户消费', f"RM {data['customer']['total_debit']:,.2f}"],
            ['Customer Credit / 客户付款', f"RM {data['customer']['total_credit']:,.2f}"],
            ['Customer Outstanding / 客户未清', f"RM {data['customer']['outstanding']:,.2f}"],
            ['INFINITE Debit / INFINITE消费', f"RM {data['infinite']['total_debit']:,.2f}"],
            ['INFINITE Outstanding / INFINITE未清', f"RM {data['infinite']['outstanding']:,.2f}"]
        ]
        
        txn_table = Table(txn_summary, colWidths=[3*inch, 2.5*inch])
        txn_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        story.append(txn_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 卡片优化建议
        recommendation = self._get_optimization_recommendation(data)
        story.append(Paragraph(f"<b>Card Optimization / 优化建议</b>", styles['Heading3']))
        story.append(Paragraph(recommendation, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    def _add_overall_analysis_to_story(self, story, cards_data, customer, styles):
        """添加整体分析和50/50服务说明"""
        story.append(PageBreak())
        story.append(Paragraph("<b>OVERALL FINANCIAL ANALYSIS / 整体财务分析</b>", styles['Heading1']))
        story.append(Spacer(1, 0.3*inch))
        
        # 计算整体DSR
        total_instalment = sum(d['instalment']['total_payment'] for d in cards_data)
        overall_dsr = (total_instalment / customer['monthly_income'] * 100) if customer['monthly_income'] > 0 else 0
        
        dsr_data = [
            ['Monthly Income / 月收入', f"RM {customer['monthly_income']:,.2f}"],
            ['Total Monthly Instalment / 总月供', f"RM {total_instalment:,.2f}"],
            ['<b>Overall DSR / 整体DSR</b>', f"<b>{overall_dsr:.1f}%</b>"]
        ]
        
        dsr_table = Table(dsr_data, colWidths=[3.5*inch, 2.5*inch])
        dsr_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1'))
        ]))
        story.append(dsr_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 50/50服务说明
        service_info = """
        <b>💡 INFINITE GZ 50/50 PROFIT-SHARING ADVISORY SERVICE / 咨询优化服务</b><br/>
        <br/>
        <b>🎯 零风险保证 / Zero-Risk Guarantee:</b><br/>
        如果我们的优化方案没有为您创造任何收益，我们<b>分毫不取</b>。<br/>
        If our optimization doesn't create any savings or earnings for you, we charge <b>absolutely nothing</b>.<br/>
        <br/>
        <b>💰 50/50 利润分成模式 / 50/50 Profit Split:</b><br/>
        • 我们倾尽所有资源和服务，为您争取最高利益<br/>
        • 从节省或赚取的利润中，您保留50%，我们收取50%作为服务费<br/>
        • 例如：我们帮您省/赚RM 10,000 → 您净得RM 5,000，我们收取RM 5,000<br/>
        <br/>
        <b>📋 服务流程 / Service Process:</b><br/>
        1️⃣ <b>客户表达意愿</b>：通过系统告知您想了解优化方案<br/>
        2️⃣ <b>方案准备</b>：我们的顾问为您准备详细的优化方案和收益分析<br/>
        3️⃣ <b>商讨细节</b>：与您讨论方案具体内容、预期收益和执行计划<br/>
        4️⃣ <b>拟定合约</b>：双方达成共识后，生成中英双语授权合约<br/>
        5️⃣ <b>双方签字</b>：客户与INFINITE GZ双方签署合约<br/>
        6️⃣ <b>执行优化</b>：我们全力执行优化方案<br/>
        7️⃣ <b>收取报酬</b>：<b>仅在成功为您省/赚钱后</b>，我们才收取50%服务费<br/>
        <br/>
        <b>✨ 为什么选择我们？</b><br/>
        • <b>资源共享、利益结合</b>：我们的成功建立在您的成功之上<br/>
        • <b>专业分析</b>：利用AI和金融专家团队进行深度分析<br/>
        • <b>透明对比</b>：清晰展示优化前后的收益对比，让您做出明智选择<br/>
        • <b>全程跟进</b>：从咨询到执行，一站式服务<br/>
        <br/>
        <i>📞 联系我们: infinitegz.reminder@gmail.com</i><br/>
        <i>🔗 通过系统"咨询请求"功能联系我们了解更多</i>
        """
        
        service_style = ParagraphStyle(
            'ServiceInfo',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            leftIndent=10,
            rightIndent=10
        )
        
        story.append(Paragraph(service_info, service_style))
    
    def _save_consolidated_report_record(self, customer_id, year, month, pdf_path, cards_data):
        """保存综合报表记录到数据库"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 删除该客户该月的所有旧记录
            cursor.execute('''
                DELETE FROM monthly_reports
                WHERE customer_id = ? AND report_year = ? AND report_month = ?
            ''', (customer_id, year, month))
            
            # 为每张卡插入记录（保持数据库兼容性）
            for data in cards_data:
                card_id = data['card_info']['id']
                
                total_debit = data['customer']['total_debit'] + data['infinite']['total_debit']
                total_credit = data['customer']['total_credit']
                net_amount = total_debit - total_credit
                
                cursor.execute('''
                    INSERT INTO monthly_reports (
                        customer_id, card_id, report_year, report_month,
                        total_debit, total_credit, net_amount,
                        customer_total_debit, customer_total_credit, customer_outstanding,
                        infinite_total_debit, infinite_outstanding,
                        total_instalment, instalment_capital_balance,
                        dsr, supplier_fees, infinite_supplier_fees,
                        pdf_path, generated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    customer_id, card_id, year, month,
                    total_debit, total_credit, net_amount,
                    data['customer']['total_debit'],
                    data['customer']['total_credit'],
                    data['customer']['outstanding'],
                    data['infinite']['total_debit'],
                    data['infinite']['outstanding'],
                    data['instalment']['total_payment'],
                    data['instalment']['capital_balance'],
                    data['dsr'],
                    data['infinite']['supplier_fees'],
                    data['infinite']['supplier_fees'],
                    pdf_path  # 所有卡共享同一个PDF路径
                ))
            
            conn.commit()
    
    def auto_generate_last_month_reports(self):
        """
        自动生成上个月的所有客户综合报表（每个客户一份PDF）
        （每月5号运行）
        """
        # 计算上个月
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取所有有confirmed statements的客户
            cursor.execute('''
                SELECT DISTINCT c.id, c.name
                FROM customers c
                JOIN credit_cards cc ON c.id = cc.customer_id
                JOIN statements s ON cc.id = s.card_id
                WHERE strftime('%Y', s.statement_date) = ?
                  AND strftime('%m', s.statement_date) = ?
                  AND s.is_confirmed = 1
                ORDER BY c.id
            ''', (str(year), str(month).zfill(2)))
            
            customers = cursor.fetchall()
        
        generated_reports = []
        
        for customer in customers:
            customer_id = customer['id']
            customer_name = customer['name']
            
            try:
                pdf_path = self.generate_customer_monthly_report_pdf(customer_id, year, month)
                
                if pdf_path:
                    generated_reports.append({
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'year': year,
                        'month': month,
                        'pdf_path': pdf_path
                    })
                    print(f"✅ Generated consolidated report for {customer_name} ({year}-{month})")
            
            except Exception as e:
                print(f"❌ Failed to generate report for customer {customer_id}: {e}")
        
        return generated_reports


# 工具函数
def generate_card_monthly_report(card_id, year, month):
    """生成指定信用卡的月度报表"""
    generator = MonthlyReportGenerator()
    return generator.generate_card_monthly_report_pdf(card_id, year, month)


def auto_generate_monthly_reports():
    """自动生成上月所有信用卡的月度报表"""
    generator = MonthlyReportGenerator()
    return generator.auto_generate_last_month_reports()
