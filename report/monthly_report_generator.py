"""
月度报表自动生成系统 (Per-Card Version)
Monthly Report Auto-Generator (Per Credit Card)

核心改进：
1. 每张信用卡独立生成一份报表（不混合）
2. 客户交易 vs INFINITE交易分离
3. 客户未清余额 vs INFINITE未清余额
4. Instalment capital余额追踪
5. 优化建议和50/50服务流程集成
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
                    if t.get('payment_user') == 'owner':
                        # Owner付款 → 客户付款
                        customer_credit_owner += amount
                    else:
                        # 其他付款
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
            infinite_outstanding = infinite_total_debit  # INFINITE无Credit付款
            
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
        
        # === A. 客户交易汇总 ===
        story.append(Paragraph("<b>A. CUSTOMER TRANSACTIONS / 客户交易汇总</b>", styles['Heading2']))
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
        
        infinite_data = [
            ['<b>INFINITE DEBIT / INFINITE消费</b>', '<b>Amount / 金额</b>'],
            ['7 Suppliers Merchants / 7家指定商家', f"RM {data['infinite']['debit_suppliers']:,.2f}"],
            ['3rd Party Payments / 第三方付款', f"RM {data['infinite']['debit_3rdparty']:,.2f}"],
            ['<b>Total INFINITE Debit / INFINITE总消费</b>', f"<b>RM {data['infinite']['total_debit']:,.2f}</b>"]
        ]
        
        infinite_table = Table(infinite_data, colWidths=[3.5*inch, 2.5*inch])
        infinite_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ebdef0')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(infinite_table)
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
        """根据数据生成优化建议"""
        dsr = data['dsr']
        customer_outstanding = data['customer']['outstanding']
        infinite_outstanding = data['infinite']['outstanding']
        
        recommendations = []
        
        if dsr > 70:
            recommendations.append("⚠️ 您的DSR超过70%，建议考虑债务整合降低月供")
        elif dsr > 50:
            recommendations.append("建议通过余额转移降低信用卡利率")
        else:
            recommendations.append("✅ 您的财务状况健康")
        
        if customer_outstanding > 5000:
            recommendations.append(f"客户未清余额较高(RM {customer_outstanding:,.2f})，建议优先还款")
        
        if data['instalment']['capital_balance'] > 0:
            recommendations.append(f"分期付款剩余本金 RM {data['instalment']['capital_balance']:,.2f}，可考虑再融资降低利率")
        
        return "<br/>".join(recommendations) if recommendations else "保持良好的财务习惯"
    
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
    
    def auto_generate_last_month_reports(self):
        """
        自动生成上个月的所有信用卡报表
        （每月5号运行）
        """
        # 计算上个月
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取所有有confirmed statements的信用卡
            cursor.execute('''
                SELECT DISTINCT cc.id, cc.bank_name, cc.card_number_last4, c.name as customer_name
                FROM credit_cards cc
                JOIN customers c ON cc.customer_id = c.id
                JOIN statements s ON cc.id = s.card_id
                WHERE strftime('%Y', s.statement_date) = ?
                  AND strftime('%m', s.statement_date) = ?
                  AND s.is_confirmed = 1
            ''', (str(year), str(month).zfill(2)))
            
            cards = cursor.fetchall()
        
        generated_reports = []
        
        for card in cards:
            card_id = card['id']
            
            try:
                pdf_path = self.generate_card_monthly_report_pdf(card_id, year, month)
                
                if pdf_path:
                    generated_reports.append({
                        'card_id': card_id,
                        'customer_name': card['customer_name'],
                        'card': f"{card['bank_name']} ****{card['card_number_last4']}",
                        'year': year,
                        'month': month,
                        'pdf_path': pdf_path
                    })
                    print(f"✅ Generated report for {card['customer_name']} - {card['bank_name']} ****{card['card_number_last4']} ({year}-{month})")
            
            except Exception as e:
                print(f"❌ Failed to generate report for card {card_id}: {e}")
        
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
