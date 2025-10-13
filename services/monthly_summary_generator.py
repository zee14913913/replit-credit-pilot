"""
月度汇总报告生成器 - Monthly Summary Report Generator
生成客户所有信用卡的月度消费/付款总结，包含优化建议和积分兑换策略
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, 
                                Spacer, PageBreak, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
from typing import List, Dict, Tuple
from db.database import get_db


class MonthlySummaryGenerator:
    """月度汇总报告生成器"""
    
    def __init__(self, output_dir: str = "static/monthly_reports"):
        """初始化生成器"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_monthly_summary(self, customer_id: int, month: str) -> str:
        """
        生成月度汇总报告
        
        Args:
            customer_id: 客户ID
            month: 月份 (YYYY-MM)
            
        Returns:
            PDF文件路径
        """
        # 获取数据
        data = self._collect_monthly_data(customer_id, month)
        
        if not data:
            return None
        
        # 生成PDF
        filename = f"Monthly_Summary_{customer_id}_{month}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.75*inch)
        story = []
        
        # 添加封面
        story.extend(self._create_cover_page(data['customer_name'], month))
        story.append(PageBreak())
        
        # 添加总览
        story.extend(self._create_overview_section(data))
        story.append(Spacer(1, 0.3*inch))
        
        # 添加每张卡的详细报告
        for card_data in data['cards']:
            story.extend(self._create_card_section(card_data))
            story.append(Spacer(1, 0.3*inch))
        
        # 添加积分总结
        story.extend(self._create_points_section(data))
        story.append(Spacer(1, 0.3*inch))
        
        # 添加优化建议
        story.extend(self._create_optimization_section(data))
        
        # 生成PDF
        doc.build(story)
        
        return filepath
    
    def _collect_monthly_data(self, customer_id: int, month: str) -> Dict:
        """收集月度数据"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取客户信息
            cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
            result = cursor.fetchone()
            if not result:
                return None
            customer_name = result[0]
            
            # 获取该月的所有账单
            cursor.execute('''
                SELECT DISTINCT s.id, s.card_id, c.bank_name, c.card_number_last4,
                       s.card_full_number, s.statement_date
                FROM statements s
                JOIN credit_cards c ON s.card_id = c.id
                WHERE c.customer_id = ?
                  AND strftime('%Y-%m', s.statement_date) = ?
                ORDER BY c.bank_name, c.card_number_last4
            ''', (customer_id, month))
            
            statements = cursor.fetchall()
            
            if not statements:
                return None
            
            cards_data = []
            total_consumption = 0
            total_payment = 0
            total_supplier_fees = 0
            total_points = 0
            
            for stmt_id, card_id, bank, last4, full_num, stmt_date in statements:
                # 获取消费数据
                cursor.execute('''
                    SELECT category, suppliers_usage,
                           COUNT(*) as count,
                           SUM(amount) as total,
                           SUM(supplier_fee) as fees
                    FROM consumption_records
                    WHERE statement_id = ? AND customer_id = ?
                    GROUP BY category, suppliers_usage
                ''', (stmt_id, customer_id))
                consumption = cursor.fetchall()
                
                # 获取付款数据
                cursor.execute('''
                    SELECT category, payment_user,
                           COUNT(*) as count,
                           SUM(payment_amount) as total
                    FROM payment_records
                    WHERE statement_id = ? AND customer_id = ?
                    GROUP BY category, payment_user
                ''', (stmt_id, customer_id))
                payments = cursor.fetchall()
                
                # 获取积分
                cursor.execute('''
                    SELECT points_this_month, points_cumulative
                    FROM points_tracking
                    WHERE card_id = ? AND statement_date = ?
                ''', (card_id, stmt_date))
                points_result = cursor.fetchone()
                points_month = points_result[0] if points_result else 0
                points_cum = points_result[1] if points_result else 0
                
                # 计算总计
                card_consumption_total = sum(row[3] for row in consumption)
                card_payment_total = sum(row[3] for row in payments)
                card_fees_total = sum(row[4] for row in consumption if row[4])
                
                total_consumption += card_consumption_total
                total_payment += card_payment_total
                total_supplier_fees += card_fees_total
                total_points += points_cum
                
                cards_data.append({
                    'bank': bank,
                    'card_last4': last4,
                    'card_full': full_num or f"****{last4}",
                    'statement_date': stmt_date,
                    'consumption': consumption,
                    'payments': payments,
                    'consumption_total': card_consumption_total,
                    'payment_total': card_payment_total,
                    'fees_total': card_fees_total,
                    'points_month': points_month,
                    'points_cumulative': points_cum
                })
            
            return {
                'customer_name': customer_name,
                'month': month,
                'cards': cards_data,
                'total_consumption': total_consumption,
                'total_payment': total_payment,
                'total_supplier_fees': total_supplier_fees,
                'total_points': total_points
            }
    
    def _create_cover_page(self, customer_name: str, month: str) -> List:
        """创建封面"""
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=32,
            textColor=colors.HexColor('#FF6B35'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        elements = []
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("月度财务报告", title_style))
        elements.append(Paragraph("MONTHLY FINANCIAL SUMMARY", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        month_obj = datetime.strptime(month, '%Y-%m')
        month_display = month_obj.strftime('%B %Y')
        elements.append(Paragraph(f"报告期间: {month_display}", subtitle_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"客户: {customer_name}", subtitle_style))
        elements.append(Spacer(1, 0.5*inch))
        
        date_style = ParagraphStyle(
            'Date',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"生成日期: {datetime.now().strftime('%Y年%m月%d日')}", date_style))
        
        return elements
    
    def _create_overview_section(self, data: Dict) -> List:
        """创建总览部分"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF6B35'),
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        elements = []
        elements.append(Paragraph("📊 月度总览 | Monthly Overview", heading_style))
        
        # 创建总览表格
        overview_data = [
            ['项目', '金额 (RM)'],
            ['总消费金额', f"{data['total_consumption']:.2f}"],
            ['总付款金额', f"{data['total_payment']:.2f}"],
            ['供应商手续费', f"{data['total_supplier_fees']:.2f}"],
            ['净支出', f"{data['total_consumption'] - data['total_payment']:.2f}"],
            ['累计积分', f"{data['total_points']:.0f}"],
        ]
        
        overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))
        
        elements.append(overview_table)
        
        return elements
    
    def _create_card_section(self, card_data: Dict) -> List:
        """创建每张卡的详细报告"""
        styles = getSampleStyleSheet()
        
        card_heading = ParagraphStyle(
            'CardHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elements = []
        
        # 卡片标题
        card_title = f"💳 {card_data['bank']} {card_data['card_full']}"
        elements.append(Paragraph(card_title, card_heading))
        
        # 消费总结
        consumption_data = [['分类', '供应商', '笔数', '金额 (RM)', '手续费 (RM)']]
        for cat, supplier, count, total, fee in card_data['consumption']:
            consumption_data.append([
                cat or 'N/A',
                supplier or 'N/A',
                str(count),
                f"{total:.2f}",
                f"{fee:.2f}" if fee else "0.00"
            ])
        
        if len(consumption_data) > 1:
            consumption_data.append([
                'TOTAL', '',
                str(sum(int(row[2]) for row in consumption_data[1:])),
                f"{card_data['consumption_total']:.2f}",
                f"{card_data['fees_total']:.2f}"
            ])
            
            consumption_table = Table(consumption_data, colWidths=[1.5*inch, 1.5*inch, 0.8*inch, 1*inch, 1*inch])
            consumption_table.setStyle(self._get_table_style())
            elements.append(Paragraph("消费明细:", styles['Normal']))
            elements.append(consumption_table)
            elements.append(Spacer(1, 0.15*inch))
        
        # 付款总结
        payment_data = [['分类', '付款人', '笔数', '金额 (RM)']]
        for cat, user, count, total in card_data['payments']:
            payment_data.append([
                cat or 'N/A',
                user or 'N/A',
                str(count),
                f"{total:.2f}"
            ])
        
        if len(payment_data) > 1:
            payment_data.append([
                'TOTAL', '',
                str(sum(int(row[2]) for row in payment_data[1:])),
                f"{card_data['payment_total']:.2f}"
            ])
            
            payment_table = Table(payment_data, colWidths=[1.8*inch, 1.5*inch, 0.8*inch, 1.2*inch])
            payment_table.setStyle(self._get_table_style())
            elements.append(Paragraph("付款明细:", styles['Normal']))
            elements.append(payment_table)
            elements.append(Spacer(1, 0.15*inch))
        
        # 优化建议
        tips = self._generate_card_tips(card_data)
        if tips:
            elements.append(Paragraph(f"💡 <b>优化建议:</b> {tips}", styles['Normal']))
        
        return elements
    
    def _create_points_section(self, data: Dict) -> List:
        """创建积分总结部分"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF6B35'),
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        elements = []
        elements.append(Paragraph("⭐ 积分总结 | Points Summary", heading_style))
        
        # 积分明细表
        points_data = [['信用卡', '本月获得', '累计积分']]
        for card in data['cards']:
            points_data.append([
                f"{card['bank']} {card['card_full']}",
                f"{card['points_month']:.0f}",
                f"{card['points_cumulative']:.0f}"
            ])
        
        points_data.append([
            'TOTAL',
            f"{sum(c['points_month'] for c in data['cards']):.0f}",
            f"{data['total_points']:.0f}"
        ])
        
        points_table = Table(points_data, colWidths=[3*inch, 1.2*inch, 1.2*inch])
        points_table.setStyle(self._get_table_style())
        elements.append(points_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # 积分兑换建议
        redemption_tips = self._generate_redemption_strategy(data['total_points'])
        elements.append(Paragraph(f"<b>💰 最佳兑换策略:</b><br/>{redemption_tips}", styles['Normal']))
        
        return elements
    
    def _create_optimization_section(self, data: Dict) -> List:
        """创建优化建议部分"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF6B35'),
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        elements = []
        elements.append(Paragraph("🎯 优化建议与省钱技巧", heading_style))
        
        # 生成优化建议
        tips = self._generate_overall_optimization_tips(data)
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            spaceAfter=8
        )
        
        for i, tip in enumerate(tips, 1):
            elements.append(Paragraph(f"{i}. {tip}", normal_style))
        
        return elements
    
    def _get_table_style(self) -> TableStyle:
        """获取标准表格样式"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
    
    def _generate_card_tips(self, card_data: Dict) -> str:
        """为单张卡生成优化建议"""
        tips = []
        
        # 检查消费vs付款比例
        if card_data['payment_total'] < card_data['consumption_total']:
            shortage = card_data['consumption_total'] - card_data['payment_total']
            tips.append(f"本月还需还款 RM {shortage:.2f}")
        
        # 检查供应商手续费
        if card_data['fees_total'] > 0:
            tips.append(f"本月供应商手续费 RM {card_data['fees_total']:.2f}")
        
        return '; '.join(tips) if tips else "消费记录良好"
    
    def _generate_redemption_strategy(self, total_points: float) -> str:
        """生成积分兑换策略"""
        strategies = []
        
        if total_points >= 10000:
            strategies.append("建议兑换航空里程或酒店积分，价值最大化")
        elif total_points >= 5000:
            strategies.append("可兑换现金回扣或购物券")
        elif total_points >= 1000:
            strategies.append("积累更多积分后再兑换，以获得更好的兑换率")
        else:
            strategies.append("继续累积积分")
        
        return '<br/>'.join(strategies)
    
    def _generate_overall_optimization_tips(self, data: Dict) -> List[str]:
        """生成整体优化建议"""
        tips = []
        
        # 建议1: 按时还款
        tips.append("<b>按时还款</b>: 避免利息和滞纳金，维持良好信用记录")
        
        # 建议2: 积分最大化
        if data['total_points'] > 0:
            tips.append(f"<b>积分策略</b>: 您本月累积了 {data['total_points']:.0f} 积分，建议用于兑换航空里程或现金回扣")
        
        # 建议3: 供应商费用
        if data['total_supplier_fees'] > 0:
            tips.append(f"<b>手续费优化</b>: 本月供应商手续费为 RM {data['total_supplier_fees']:.2f}，考虑使用无手续费的支付方式")
        
        # 建议4: 多卡管理
        if len(data['cards']) > 1:
            tips.append("<b>多卡优化</b>: 根据不同商户类别选择最优惠的信用卡消费，最大化回扣和积分")
        
        # 建议5: 预算管理
        tips.append("<b>预算控制</b>: 建议设置月度消费预算，避免过度消费")
        
        return tips


def generate_monthly_summary_for_customer(customer_id: int, month: str) -> str:
    """
    为客户生成月度汇总报告（便捷函数）
    
    Args:
        customer_id: 客户ID
        month: 月份 (YYYY-MM)
        
    Returns:
        PDF文件路径
    """
    generator = MonthlySummaryGenerator()
    return generator.generate_monthly_summary(customer_id, month)
