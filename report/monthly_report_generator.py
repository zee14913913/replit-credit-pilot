"""
月度报表自动生成系统
Monthly Report Auto-Generator

功能：
1. 每月5号自动生成上月报表
2. 按statement月份分组统计
3. Debit汇总（Supplier + AIA + 未分类）
4. Credit汇总（Owner Payment + 其他付款）
5. Instalment汇总
6. 净额计算（Debit - Credit）
7. DSR分析和贷款建议
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
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import os


class MonthlyReportGenerator:
    """月度报表生成器"""
    
    def __init__(self, output_folder='static/reports/monthly'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def get_month_data(self, customer_id, year, month):
        """
        获取指定月份的所有数据
        按statement_date的月份分组
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. 获取该月所有statements
            cursor.execute('''
                SELECT s.*, cc.bank_name, cc.card_number_last4
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ?
                  AND strftime('%Y', s.statement_date) = ?
                  AND strftime('%m', s.statement_date) = ?
                  AND s.is_confirmed = 1
                ORDER BY s.statement_date
            ''', (customer_id, str(year), str(month).zfill(2)))
            
            statements = [dict(row) for row in cursor.fetchall()]
            
            if not statements:
                return None
            
            statement_ids = [s['id'] for s in statements]
            
            # 2. 获取所有交易
            placeholders = ','.join('?' * len(statement_ids))
            cursor.execute(f'''
                SELECT *
                FROM transactions
                WHERE statement_id IN ({placeholders})
            ''', statement_ids)
            
            transactions = [dict(row) for row in cursor.fetchall()]
            
            # 3. 分类统计
            debit_supplier = 0
            debit_aia = 0
            debit_other = 0
            credit_owner = 0
            credit_other = 0
            supplier_fees = 0
            
            for t in transactions:
                amount = t['amount']
                
                if t['transaction_type'] == 'debit':
                    # 消费类交易
                    if t.get('transaction_subtype') == 'supplier_debit':
                        # Supplier商家消费
                        debit_supplier += abs(amount)
                        supplier_fees += t.get('supplier_fee', 0)
                    elif 'aia' in t['description'].lower():
                        # AIA保险
                        debit_aia += abs(amount)
                    else:
                        # 其他消费
                        debit_other += abs(amount)
                
                elif t['transaction_type'] == 'credit':
                    # 付款类交易
                    if t.get('payment_user') == 'owner':
                        # Owner付款
                        credit_owner += abs(amount)
                    else:
                        # 其他付款
                        credit_other += abs(amount)
            
            # 4. 获取该月分期付款
            cursor.execute('''
                SELECT ip.*
                FROM instalment_plans ip
                WHERE ip.customer_id = ?
                  AND ip.status = 'active'
                  AND strftime('%Y-%m', ip.start_date) <= ?
                  AND strftime('%Y-%m', ip.end_date) >= ?
            ''', (customer_id, f"{year}-{str(month).zfill(2)}", f"{year}-{str(month).zfill(2)}"))
            
            instalments = [dict(row) for row in cursor.fetchall()]
            total_instalment = sum(p['monthly_payment'] for p in instalments)
            
            # 5. 获取客户信息
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            customer = dict(cursor.fetchone())
            
            # 6. 计算净额和DSR
            total_debit = debit_supplier + debit_aia + debit_other
            total_credit = credit_owner + credit_other
            net_amount = total_debit - total_credit
            
            # DSR = (总月供 + 总分期) / 月收入
            total_monthly_repayment = total_instalment
            dsr = (total_monthly_repayment / customer['monthly_income'] * 100) if customer['monthly_income'] > 0 else 0
            
            return {
                'customer': customer,
                'year': year,
                'month': month,
                'statements': statements,
                'transactions': transactions,
                'debit': {
                    'supplier': debit_supplier,
                    'aia': debit_aia,
                    'other': debit_other,
                    'total': total_debit
                },
                'credit': {
                    'owner': credit_owner,
                    'other': credit_other,
                    'total': total_credit
                },
                'instalment': {
                    'plans': instalments,
                    'total': total_instalment
                },
                'net_amount': net_amount,
                'dsr': dsr,
                'supplier_fees': supplier_fees
            }
    
    def generate_monthly_report_pdf(self, customer_id, year, month):
        """
        生成月度PDF报表
        """
        data = self.get_month_data(customer_id, year, month)
        
        if not data:
            return None
        
        customer = data['customer']
        
        # 创建PDF文件
        filename = f"Monthly_Report_{customer['name']}_{year}_{str(month).zfill(2)}.pdf"
        pdf_path = os.path.join(self.output_folder, filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph(f"MONTHLY STATEMENT REPORT", title_style))
        story.append(Paragraph(f"{year}年{month}月账单月结报告", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 客户信息
        info_data = [
            ['Customer Name / 客户姓名', customer['name']],
            ['Report Period / 报表期间', f"{year}-{str(month).zfill(2)}"],
            ['Monthly Income / 月收入', f"RM {customer['monthly_income']:,.2f}"],
            ['Total Statements / 账单数量', str(len(data['statements']))]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))
        
        # A. DEBIT汇总（消费）
        story.append(Paragraph("<b>A. DEBIT SUMMARY / 消费汇总</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        debit_data = [
            ['Category / 类别', 'Amount / 金额'],
            ['Supplier Merchants / 指定商家', f"RM {data['debit']['supplier']:,.2f}"],
            ['AIA Insurance / AIA保险', f"RM {data['debit']['aia']:,.2f}"],
            ['Other Expenses / 其他消费', f"RM {data['debit']['other']:,.2f}"],
            ['<b>Total Debit / 消费总计</b>', f"<b>RM {data['debit']['total']:,.2f}</b>"]
        ]
        
        debit_table = Table(debit_data, colWidths=[3*inch, 2*inch])
        debit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(debit_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Supplier费用
        if data['supplier_fees'] > 0:
            supplier_fee_text = f"<b>💰 Supplier Merchant Fee (1%): RM {data['supplier_fees']:,.2f}</b>"
            story.append(Paragraph(supplier_fee_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # B. CREDIT汇总（付款）
        story.append(Paragraph("<b>B. CREDIT SUMMARY / 付款汇总</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        credit_data = [
            ['Category / 类别', 'Amount / 金额'],
            ['Owner Payment / Owner付款', f"RM {data['credit']['owner']:,.2f}"],
            ['Other Payments / 其他付款', f"RM {data['credit']['other']:,.2f}"],
            ['<b>Total Credit / 付款总计</b>', f"<b>RM {data['credit']['total']:,.2f}</b>"]
        ]
        
        credit_table = Table(credit_data, colWidths=[3*inch, 2*inch])
        credit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f8f5')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(credit_table)
        story.append(Spacer(1, 0.3*inch))
        
        # C. INSTALMENT汇总（分期）
        story.append(Paragraph("<b>C. INSTALMENT SUMMARY / 分期付款汇总</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        if data['instalment']['plans']:
            instalment_data = [['Product / 商品', 'Monthly Payment / 月供', 'Tenure / 期限']]
            
            for plan in data['instalment']['plans']:
                instalment_data.append([
                    plan['product_name'],
                    f"RM {plan['monthly_payment']:,.2f}",
                    f"{plan['tenure_months']} months"
                ])
            
            instalment_data.append([
                '<b>Total Instalment / 分期总计</b>',
                f"<b>RM {data['instalment']['total']:,.2f}</b>",
                ''
            ])
            
            instalment_table = Table(instalment_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            instalment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f4ecf7')),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(instalment_table)
        else:
            story.append(Paragraph("No active instalment plans / 无活跃分期计划", styles['Normal']))
        
        story.append(Spacer(1, 0.5*inch))
        
        # D. 净额计算
        story.append(Paragraph("<b>D. NET AMOUNT CALCULATION / 净额计算</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        net_data = [
            ['Item / 项目', 'Amount / 金额'],
            ['Total Debit / 总消费', f"RM {data['debit']['total']:,.2f}"],
            ['Total Credit / 总付款', f"RM -{data['credit']['total']:,.2f}"],
            ['<b>Net Amount / 净额</b>', f"<b>RM {data['net_amount']:,.2f}</b>"]
        ]
        
        net_table = Table(net_data, colWidths=[3*inch, 2*inch])
        net_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(net_table)
        story.append(Spacer(1, 0.5*inch))
        
        # E. DSR分析
        story.append(Paragraph("<b>E. DSR ANALYSIS / 债务负担率分析</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        dsr_data = [
            ['Monthly Income / 月收入', f"RM {customer['monthly_income']:,.2f}"],
            ['Total Monthly Repayment / 总月供', f"RM {data['instalment']['total']:,.2f}"],
            ['<b>DSR Ratio / 债务负担率</b>', f"<b>{data['dsr']:.1f}%</b>"]
        ]
        
        dsr_table = Table(dsr_data, colWidths=[3*inch, 2*inch])
        dsr_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(dsr_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 贷款建议
        dsr_status = "✅ Healthy" if data['dsr'] < 70 else "⚠️ High Risk"
        recommendation = self._get_loan_recommendation(data['dsr'], customer['monthly_income'], data['instalment']['total'])
        
        story.append(Paragraph(f"<b>DSR Status / 状态:</b> {dsr_status}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Recommendation / 建议:</b>", styles['Normal']))
        story.append(Paragraph(recommendation, styles['Normal']))
        
        # 生成PDF
        doc.build(story)
        
        # 保存到数据库
        self._save_report_record(customer_id, year, month, pdf_path, data)
        
        return pdf_path
    
    def _get_loan_recommendation(self, dsr, monthly_income, current_repayment):
        """根据DSR给出贷款建议"""
        if dsr < 50:
            max_loan = monthly_income * 0.7 - current_repayment
            return f"Your DSR is healthy. You can apply for additional loans with max monthly repayment of RM {max_loan:,.2f}"
        elif dsr < 70:
            return "Your DSR is moderate. Consider debt consolidation to reduce interest rates before taking new loans."
        else:
            return "⚠️ Your DSR is high. We recommend debt refinancing or balance transfer to lower your monthly burden before any new loans."
    
    def _save_report_record(self, customer_id, year, month, pdf_path, data):
        """保存报表记录到数据库"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO monthly_reports (
                    customer_id, report_year, report_month,
                    total_debit, total_credit, total_instalment,
                    net_amount, dsr, supplier_fees,
                    pdf_path, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                customer_id, year, month,
                data['debit']['total'],
                data['credit']['total'],
                data['instalment']['total'],
                data['net_amount'],
                data['dsr'],
                data['supplier_fees'],
                pdf_path
            ))
            
            conn.commit()
    
    def auto_generate_last_month_reports(self):
        """
        自动生成上个月的所有客户报表
        （每月5号运行）
        """
        # 计算上个月
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM customers')
            customers = cursor.fetchall()
        
        generated_reports = []
        
        for customer in customers:
            customer_id = customer['id']
            
            try:
                pdf_path = self.generate_monthly_report_pdf(customer_id, year, month)
                
                if pdf_path:
                    generated_reports.append({
                        'customer_id': customer_id,
                        'customer_name': customer['name'],
                        'year': year,
                        'month': month,
                        'pdf_path': pdf_path
                    })
                    print(f"✅ Generated report for {customer['name']} ({year}-{month})")
            
            except Exception as e:
                print(f"❌ Failed to generate report for {customer['name']}: {e}")
        
        return generated_reports


# 工具函数
def generate_monthly_report(customer_id, year, month):
    """生成指定月份的月度报表"""
    generator = MonthlyReportGenerator()
    return generator.generate_monthly_report_pdf(customer_id, year, month)


def auto_generate_monthly_reports():
    """自动生成上月所有客户的月度报表"""
    generator = MonthlyReportGenerator()
    return generator.auto_generate_last_month_reports()
