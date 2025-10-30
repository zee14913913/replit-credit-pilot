"""
月度汇总报告服务
Monthly Summary Report Service

功能：
1. 按月份汇总同一客户所有信用卡的Supplier消费
2. 追踪该月为客户支付的所有款项
3. 生成月度对账报告，避免误会
4. 导出PDF格式的月度和年度汇总报告
"""

import sqlite3
import os
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from services.file_storage_manager import FileStorageManager

def get_bank_abbreviation(bank_name):
    """Convert bank full name to abbreviation"""
    if not bank_name:
        return ''
    
    bank_name_upper = bank_name.upper()
    bank_abbr_map = {
        'MAYBANK': 'MBB',
        'CIMB': 'CIMB',
        'PUBLIC BANK': 'PBB',
        'RHB': 'RHB',
        'HONG LEONG': 'HLB',
        'AMBANK': 'AMB',
        'ALLIANCE': 'ALL',
        'AFFIN': 'AFF',
        'HSBC': 'HSBC',
        'STANDARD CHARTERED': 'SCB',
        'CITIBANK': 'CITI',
        'UOB': 'UOB',
        'OCBC': 'OCBC',
        'BANK ISLAM': 'BIM',
        'BANK RAKYAT': 'BRK',
        'BANK MUAMALAT': 'BMM',
        'GX BANK': 'GX',
    }
    
    return bank_abbr_map.get(bank_name_upper, bank_name[:4].upper())

class MonthlySummaryReport:
    """月度汇总报告生成器"""
    
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self.file_manager = FileStorageManager()
    
    def get_customer_monthly_summary(self, customer_id: int, year: int, month: int) -> Dict:
        """
        获取客户指定月份的汇总报告
        
        参数:
            customer_id: 客户ID
            year: 年份（如2025）
            month: 月份（1-12）
        
        返回:
            {
                'period': '2025-01',
                'customer_name': 'YEO CHEE WANG',
                'cards': [...],  # 该月所有有交易的信用卡
                'total_supplier_spending': 12500.00,  # 总Supplier消费
                'total_supplier_fee': 125.00,  # 总手续费(1%)
                'total_payments': 10000.00,  # 总付款额
                'net_balance': 2625.00,  # 净余额（消费+费用-付款）
                'card_details': [...],  # 每张卡的详细信息
                'payment_details': [...]  # 付款详情
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. 获取客户信息
        cursor.execute("SELECT name, customer_code FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return None
        
        # 2. 构建月份起始日期（用于匹配）
        month_start = f"{year}-{month:02d}-01"
        period_str = f"{year}-{month:02d}"
        
        # 3. 获取该月所有信用卡的INFINITE账本数据
        cursor.execute('''
            SELECT 
                iml.card_id,
                cc.bank_name,
                cc.card_number_last4,
                cc.card_type,
                iml.month_start,
                iml.statement_id,
                iml.infinite_spend,
                iml.supplier_fee,
                iml.infinite_payments,
                iml.rolling_balance,
                iml.transfer_count,
                s.statement_date
            FROM infinite_monthly_ledger iml
            JOIN credit_cards cc ON iml.card_id = cc.id
            LEFT JOIN statements s ON iml.statement_id = s.id
            WHERE iml.customer_id = ?
              AND substr(iml.month_start, 1, 7) = ?
            ORDER BY cc.bank_name, s.statement_date
        ''', (customer_id, period_str))
        
        card_ledgers = cursor.fetchall()
        
        # 4. 汇总数据
        total_supplier_spending = 0
        total_supplier_fee = 0
        total_infinite_payments = 0
        card_details = []
        
        for ledger in card_ledgers:
            card_info = {
                'card_id': ledger['card_id'],
                'bank_name': get_bank_abbreviation(ledger['bank_name']),
                'card_number': ledger['card_number_last4'],
                'card_type': ledger['card_type'],
                'statement_date': ledger['statement_date'],
                'infinite_spend': ledger['infinite_spend'],
                'supplier_fee': ledger['supplier_fee'],
                'infinite_payments': ledger['infinite_payments'],
                'rolling_balance': ledger['rolling_balance'],
                'transfer_count': ledger['transfer_count']
            }
            card_details.append(card_info)
            
            total_supplier_spending += ledger['infinite_spend']
            total_supplier_fee += ledger['supplier_fee']
            total_infinite_payments += ledger['infinite_payments']
        
        # 5. 获取该月的INFINITE转账详情
        cursor.execute('''
            SELECT 
                it.card_id,
                cc.bank_name,
                cc.card_number_last4,
                it.transfer_date,
                it.payer_name,
                it.payee_name,
                it.amount,
                it.description
            FROM infinite_transfers it
            JOIN credit_cards cc ON it.card_id = cc.id
            WHERE it.customer_id = ?
              AND substr(it.month_start, 1, 7) = ?
            ORDER BY it.transfer_date
        ''', (customer_id, period_str))
        
        payment_details = []
        for transfer in cursor.fetchall():
            payment_details.append({
                'card_id': transfer['card_id'],
                'bank_name': get_bank_abbreviation(transfer['bank_name']),
                'card_number': transfer['card_number_last4'],
                'transfer_date': transfer['transfer_date'],
                'payer_name': transfer['payer_name'],
                'payee_name': transfer['payee_name'],
                'amount': transfer['amount'],
                'description': transfer['description']
            })
        
        # 6. 计算净余额
        # 正确逻辑：净余额 = 我们垫付 - 客户应还
        # 如果 > 0：客户欠我们钱（客户需补款）
        # 如果 < 0：我们欠客户钱（我们需退款）
        total_spending_with_fee = total_supplier_spending + total_supplier_fee
        net_balance = total_infinite_payments - total_spending_with_fee
        
        conn.close()
        
        # 7. 返回汇总报告
        return {
            'period': period_str,
            'year': year,
            'month': month,
            'customer_id': customer_id,
            'customer_name': customer['name'],
            'customer_code': customer['customer_code'],
            'total_cards': len(card_details),
            'total_supplier_spending': total_supplier_spending,
            'total_supplier_fee': total_supplier_fee,
            'total_spending_with_fee': total_spending_with_fee,
            'total_payments': total_infinite_payments,
            'net_balance': net_balance,
            'card_details': card_details,
            'payment_details': payment_details
        }
    
    def get_customer_yearly_summary(self, customer_id: int, year: int) -> List[Dict]:
        """获取客户全年的月度汇总（1-12月）"""
        yearly_data = []
        
        for month in range(1, 13):
            summary = self.get_customer_monthly_summary(customer_id, year, month)
            if summary and summary['total_cards'] > 0:
                yearly_data.append(summary)
        
        return yearly_data
    
    def get_all_customers_monthly_summary(self, year: int, month: int) -> List[Dict]:
        """获取所有客户指定月份的汇总"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有有INFINITE账本记录的客户
        period_str = f"{year}-{month:02d}"
        cursor.execute('''
            SELECT DISTINCT customer_id
            FROM infinite_monthly_ledger
            WHERE substr(month_start, 1, 7) = ?
        ''', (period_str,))
        
        customer_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # 获取每个客户的月度汇总
        all_summaries = []
        for customer_id in customer_ids:
            summary = self.get_customer_monthly_summary(customer_id, year, month)
            if summary:
                all_summaries.append(summary)
        
        return all_summaries
    
    def generate_text_report(self, summary: Dict) -> str:
        """生成文本格式的月度汇总报告"""
        if not summary:
            return "无数据"
        
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append(f"月度汇总报告 - {summary['period']}")
        report_lines.append("=" * 100)
        report_lines.append(f"客户: {summary['customer_name']} ({summary['customer_code']})")
        report_lines.append(f"月份: {summary['year']}年{summary['month']}月")
        report_lines.append(f"信用卡数量: {summary['total_cards']}张")
        report_lines.append("=" * 100)
        
        # 信用卡详情
        report_lines.append("\n📊 信用卡详情：")
        report_lines.append("-" * 100)
        
        for i, card in enumerate(summary['card_details'], 1):
            report_lines.append(f"\n第{i}张卡：{card['bank_name']} - {card['card_number']}")
            report_lines.append(f"  账单日期: {card['statement_date']}")
            report_lines.append(f"  Supplier消费: RM {card['infinite_spend']:,.2f}")
            report_lines.append(f"  手续费(1%):  RM {card['supplier_fee']:,.2f}")
            report_lines.append(f"  付款金额:    RM {card['infinite_payments']:,.2f}")
            report_lines.append(f"  滚动余额:    RM {card['rolling_balance']:,.2f}")
            report_lines.append(f"  转账次数:    {card['transfer_count']}次")
        
        # 付款详情
        if summary['payment_details']:
            report_lines.append("\n\n💰 付款详情：")
            report_lines.append("-" * 100)
            
            for i, payment in enumerate(summary['payment_details'], 1):
                report_lines.append(f"\n第{i}笔付款：")
                report_lines.append(f"  日期: {payment['transfer_date']}")
                report_lines.append(f"  付款人: {payment['payer_name']}")
                report_lines.append(f"  收款人: {payment['payee_name']}")
                report_lines.append(f"  金额: RM {payment['amount']:,.2f}")
                report_lines.append(f"  信用卡: {payment['bank_name']} - {payment['card_number']}")
                if payment['description']:
                    report_lines.append(f"  说明: {payment['description']}")
        
        # 月度汇总
        report_lines.append("\n\n" + "=" * 100)
        report_lines.append("📈 月度汇总")
        report_lines.append("=" * 100)
        report_lines.append(f"Supplier消费总额:    RM {summary['total_supplier_spending']:,.2f}")
        report_lines.append(f"手续费总额(1%):      RM {summary['total_supplier_fee']:,.2f}")
        report_lines.append(f"消费合计(含费用):    RM {summary['total_spending_with_fee']:,.2f}")
        report_lines.append(f"付款总额:            RM {summary['total_payments']:,.2f}")
        report_lines.append("-" * 100)
        
        if summary['net_balance'] > 0:
            report_lines.append(f"应收余额:            RM {summary['net_balance']:,.2f}  ⚠️  客户需补款")
        elif summary['net_balance'] < 0:
            report_lines.append(f"应付余额:            RM {abs(summary['net_balance']):,.2f}  💰 我们需退款")
        else:
            report_lines.append(f"余额:                RM 0.00  ✅ 已结清")
        
        report_lines.append("=" * 100)
        
        return "\n".join(report_lines)
    
    def generate_monthly_pdf(self, customer_id: int, year: int, month: int) -> str:
        """
        生成月度汇总PDF报告
        
        返回: PDF文件路径
        """
        # 1. 获取月度汇总数据
        summary = self.get_customer_monthly_summary(customer_id, year, month)
        
        if not summary or summary['total_cards'] == 0:
            raise ValueError(f"{year}年{month}月暂无Supplier消费数据")
        
        # 2. 确定文件路径
        customer_code = summary['customer_code']
        filename = f"{customer_code}_Monthly_Summary_{year}_{month:02d}.pdf"
        
        # 构建reports/monthly_summary目录
        monthly_summary_dir = os.path.join(
            self.file_manager.BASE_DIR,
            customer_code,
            'reports',
            'monthly_summary'
        )
        os.makedirs(monthly_summary_dir, exist_ok=True)
        
        pdf_path = os.path.join(monthly_summary_dir, filename)
        
        # 3. 创建PDF文档
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4),
                                rightMargin=1*cm, leftMargin=1*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # 自定义样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF007F'),
            spaceAfter=12,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#FF007F'),
            spaceAfter=10
        )
        
        # 标题
        title = Paragraph(f"月度汇总报告 - {summary['period']}", title_style)
        elements.append(title)
        
        subtitle = Paragraph(
            f"{summary['customer_name']} ({summary['customer_code']})", 
            styles['Normal']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.5*cm))
        
        # 汇总数据卡片
        summary_data = [
            ['项目', '金额'],
            ['Supplier消费', f"RM {summary['total_supplier_spending']:,.2f}"],
            ['手续费 (1%)', f"RM {summary['total_supplier_fee']:,.2f}"],
            ['消费合计', f"RM {summary['total_spending_with_fee']:,.2f}"],
            ['已付款', f"RM {summary['total_payments']:,.2f}"],
            ['净余额', f"RM {summary['net_balance']:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[6*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#322446')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#1a1a1a'), colors.HexColor('#0d0d0d')])
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 信用卡详情
        elements.append(Paragraph(f"信用卡详情 ({summary['total_cards']}张)", heading_style))
        
        card_data = [['银行', '卡号', '账单日期', 'Supplier消费', '手续费', '付款金额', '滚动余额', '转账次数']]
        
        for card in summary['card_details']:
            card_data.append([
                card['bank_name'],
                card['card_number'],
                card['statement_date'] or '-',
                f"RM {card['infinite_spend']:,.2f}",
                f"RM {card['supplier_fee']:,.2f}",
                f"RM {card['infinite_payments']:,.2f}",
                f"RM {card['rolling_balance']:,.2f}",
                str(card['transfer_count'])
            ])
        
        card_table = Table(card_data, colWidths=[3.5*cm, 3.5*cm, 2.5*cm, 3*cm, 2.5*cm, 3*cm, 3*cm, 2*cm])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#322446')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#1a1a1a'), colors.HexColor('#0d0d0d')])
        ]))
        elements.append(card_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 付款详情
        if summary['payment_details']:
            elements.append(Paragraph(f"付款详情 ({len(summary['payment_details'])}笔)", heading_style))
            
            payment_data = [['日期', '付款人', '收款人', '信用卡', '金额', '说明']]
            
            for payment in summary['payment_details']:
                payment_data.append([
                    payment['transfer_date'],
                    payment['payer_name'],
                    payment['payee_name'],
                    f"{payment['bank_name']}-{payment['card_number']}",
                    f"RM {payment['amount']:,.2f}",
                    payment['description'] or '-'
                ])
            
            payment_table = Table(payment_data, colWidths=[2.5*cm, 4*cm, 4*cm, 5*cm, 3*cm, 5*cm])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#1a1a1a')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#322446')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#1a1a1a'), colors.HexColor('#0d0d0d')])
            ]))
            elements.append(payment_table)
        
        # 生成PDF
        doc.build(elements)
        
        return pdf_path
    
    def generate_yearly_pdf(self, customer_id: int, year: int) -> str:
        """
        生成年度汇总PDF报告
        
        返回: PDF文件路径
        """
        # 1. 获取年度汇总数据
        yearly_data = self.get_customer_yearly_summary(customer_id, year)
        
        if not yearly_data:
            raise ValueError(f"{year}年暂无Supplier消费数据")
        
        # 2. 获取客户信息
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, customer_code FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        
        customer_name = customer[0]
        customer_code = customer[1]
        
        # 3. 确定文件路径
        filename = f"{customer_code}_Yearly_Summary_{year}.pdf"
        
        # 构建reports/monthly_summary目录
        monthly_summary_dir = os.path.join(
            self.file_manager.BASE_DIR,
            customer_code,
            'reports',
            'monthly_summary'
        )
        os.makedirs(monthly_summary_dir, exist_ok=True)
        
        pdf_path = os.path.join(monthly_summary_dir, filename)
        
        # 4. 计算年度总计
        year_total = {
            'total_supplier_spending': sum(m['total_supplier_spending'] for m in yearly_data),
            'total_supplier_fee': sum(m['total_supplier_fee'] for m in yearly_data),
            'total_payments': sum(m['total_payments'] for m in yearly_data),
            'net_balance': sum(m['net_balance'] for m in yearly_data)
        }
        
        # 5. 创建PDF文档
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4),
                                rightMargin=1*cm, leftMargin=1*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # 自定义样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF007F'),
            spaceAfter=12,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#FF007F'),
            spaceAfter=10
        )
        
        # 标题
        title = Paragraph(f"{year}年度汇总报告", title_style)
        elements.append(title)
        
        subtitle = Paragraph(f"{customer_name} ({customer_code})", styles['Normal'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.5*cm))
        
        # 年度总计
        total_data = [
            ['项目', '金额'],
            ['年度Supplier消费', f"RM {year_total['total_supplier_spending']:,.2f}"],
            ['年度手续费 (1%)', f"RM {year_total['total_supplier_fee']:,.2f}"],
            ['年度消费合计', f"RM {year_total['total_supplier_spending'] + year_total['total_supplier_fee']:,.2f}"],
            ['年度已付款', f"RM {year_total['total_payments']:,.2f}"],
            ['年度净余额', f"RM {year_total['net_balance']:,.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[6*cm, 6*cm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#322446')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#1a1a1a'), colors.HexColor('#0d0d0d')])
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 逐月明细
        elements.append(Paragraph(f"逐月明细 ({len(yearly_data)}个月)", heading_style))
        
        monthly_data = [['月份', '信用卡数', 'Supplier消费', '手续费', '付款金额', '净余额']]
        
        for month_summary in yearly_data:
            monthly_data.append([
                month_summary['period'],
                str(month_summary['total_cards']),
                f"RM {month_summary['total_supplier_spending']:,.2f}",
                f"RM {month_summary['total_supplier_fee']:,.2f}",
                f"RM {month_summary['total_payments']:,.2f}",
                f"RM {month_summary['net_balance']:,.2f}"
            ])
        
        # 添加总计行
        monthly_data.append([
            f'{year}年总计',
            '-',
            f"RM {year_total['total_supplier_spending']:,.2f}",
            f"RM {year_total['total_supplier_fee']:,.2f}",
            f"RM {year_total['total_payments']:,.2f}",
            f"RM {year_total['net_balance']:,.2f}"
        ])
        
        monthly_table = Table(monthly_data, colWidths=[3*cm, 3*cm, 4.5*cm, 4*cm, 4.5*cm, 4.5*cm])
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF007F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#322446')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor('#1a1a1a'), colors.HexColor('#0d0d0d')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FF007F')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        elements.append(monthly_table)
        
        # 生成PDF
        doc.build(elements)
        
        return pdf_path


# 测试代码
if __name__ == '__main__':
    reporter = MonthlySummaryReport()
    
    # 示例：获取YEO CHEE WANG 2025年1月的汇总
    print("测试月度汇总报告...\n")
    
    # 首先获取YEO CHEE WANG的customer_id
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM customers WHERE name = 'YEO CHEE WANG'")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        customer_id = result[0]
        print(f"客户ID: {customer_id}\n")
        
        # 获取2025年1月的汇总
        summary = reporter.get_customer_monthly_summary(customer_id, 2025, 1)
        
        if summary:
            print(reporter.generate_text_report(summary))
        else:
            print("该月份暂无数据")
    else:
        print("客户不存在")
