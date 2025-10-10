"""
银河主题月度报表生成器
Galaxy-Themed Monthly Report Generator

专业企业级SaaS报表 - 黑白银色系高端设计
Premium Enterprise SaaS Reports - Black/White/Silver Design
"""

from db.database import get_db
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from report.galaxy_design import GalaxyDesign
from report.monthly_report_generator import MonthlyReportGenerator
import os


class GalaxyMonthlyReportGenerator:
    """银河主题月度报表生成器"""
    
    def __init__(self, output_folder='static/reports/monthly'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.design = GalaxyDesign()
        self.base_generator = MonthlyReportGenerator()
    
    def generate_customer_monthly_report_galaxy(self, customer_id, year, month):
        """
        生成客户的银河主题综合月度报表PDF
        Galaxy-themed consolidated monthly report for customer
        """
        # 获取数据（使用基础生成器的数据获取方法）
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取客户信息
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return None
            customer = dict(customer)
            
            # 获取该客户该月所有有confirmed statements的信用卡
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
            
            # 为每张卡获取数据
            cards_data = []
            for card in cards:
                card_data = self.base_generator.get_card_month_data(card['id'], year, month)
                if card_data:
                    cards_data.append(card_data)
            
            if not cards_data:
                return None
        
        # 创建PDF文件
        filename = f"Galaxy_Report_{customer['name']}_{year}_{str(month).zfill(2)}.pdf"
        pdf_path = os.path.join(self.output_folder, filename)
        
        c = canvas.Canvas(pdf_path, pagesize=A4)
        page_width, page_height = A4
        
        # ========== 第1页：封面 ==========
        self.design.draw_galaxy_background(c, page_number=1)
        
        # Logo区域
        self.design.draw_logo_area(c, 50, page_height - 80)
        
        # 主标题
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(page_width/2, page_height - 180, "CONSOLIDATED")
        c.drawCentredString(page_width/2, page_height - 220, "MONTHLY REPORT")
        
        # 中文标题
        c.setFillColor(self.design.COLOR_SILVER_GLOW)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(page_width/2, page_height - 260, f"{year}年{month}月综合月结报告")
        
        # 客户信息框
        info_y = page_height - 350
        info_box_width = 450
        info_box_x = (page_width - info_box_width) / 2
        
        # 深色背景框
        c.setFillColorRGB(0.1, 0.1, 0.1, 0.9)
        c.roundRect(info_box_x, info_y - 120, info_box_width, 120, 15, fill=1, stroke=0)
        
        # 银色边框
        self.design.draw_silver_border(c, info_box_x, info_y - 120, info_box_width, 120, 15)
        
        # 客户信息
        c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 12)
        c.drawString(info_box_x + 30, info_y - 40, f"Customer / 客户:")
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(info_box_x + 160, info_y - 40, customer['name'])
        
        c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 12)
        c.drawString(info_box_x + 30, info_y - 70, f"Report Period / 报表期间:")
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(info_box_x + 210, info_y - 70, f"{year}-{str(month).zfill(2)}")
        
        c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 12)
        c.drawString(info_box_x + 30, info_y - 100, f"Total Cards / 信用卡数量:")
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(info_box_x + 210, info_y - 100, f"{len(cards_data)} cards")
        
        # 月度汇总数据
        total_customer_debit = sum(d['customer']['total_debit'] for d in cards_data)
        total_customer_credit = sum(d['customer']['total_credit'] for d in cards_data)
        total_customer_outstanding = sum(d['customer']['outstanding'] for d in cards_data)
        total_infinite_debit = sum(d['infinite']['total_debit'] for d in cards_data)
        total_infinite_outstanding = sum(d['infinite']['outstanding'] for d in cards_data)
        total_instalment = sum(d['instalment']['total_payment'] for d in cards_data)
        
        # 关键指标展示（3个高亮框）
        metrics_y = 200
        box_width = 160
        box_height = 80
        spacing = 20
        
        start_x = (page_width - (3 * box_width + 2 * spacing)) / 2
        
        # 客户总消费
        self.design.draw_highlight_box(
            c, start_x, metrics_y, box_width, box_height,
            "Customer Spending", f"RM {total_customer_debit:,.0f}"
        )
        
        # 客户未清余额
        self.design.draw_highlight_box(
            c, start_x + box_width + spacing, metrics_y, box_width, box_height,
            "Outstanding", f"RM {total_customer_outstanding:,.0f}"
        )
        
        # 总月供
        self.design.draw_highlight_box(
            c, start_x + 2*(box_width + spacing), metrics_y, box_width, box_height,
            "Total Instalment", f"RM {total_instalment:,.0f}"
        )
        
        # 页脚
        self.design.draw_footer(c, 1, len(cards_data) + 2)
        
        c.showPage()
        
        # ========== 第2-N页：各信用卡详情 ==========
        for idx, card_data in enumerate(cards_data, 1):
            self.design.draw_galaxy_background(c, page_number=idx+1)
            
            card = card_data['card_info']
            current_y = page_height - 80
            
            # 卡片标题
            card_title = f"CARD {idx}: {card['bank_name']} ****{card['card_number_last4']}"
            self.design.draw_premium_section_header(
                c, 50, current_y, page_width - 100,
                card_title, f"信用卡 {idx}"
            )
            
            current_y -= 50
            
            # 交易汇总表
            table_data = [
                ["Metric / 指标", "Amount / 金额"],
                ["Total Transactions / 交易总数", str(len(card_data['transactions']))],
                ["Customer Debit / 客户消费", f"RM {card_data['customer']['total_debit']:,.2f}"],
                ["Customer Credit / 客户付款", f"RM {card_data['customer']['total_credit']:,.2f}"],
                ["Customer Outstanding / 客户未清", f"RM {card_data['customer']['outstanding']:,.2f}"],
                ["INFINITE Debit / INFINITE消费", f"RM {card_data['infinite']['total_debit']:,.2f}"],
                ["INFINITE Outstanding / INFINITE未清", f"RM {card_data['infinite']['outstanding']:,.2f}"]
            ]
            
            self.design.draw_data_table_elegant(
                c, 50, current_y, page_width - 100,
                table_data, [280, 200]
            )
            
            current_y -= 280
            
            # 卡片优化建议
            self.design.draw_premium_section_header(
                c, 50, current_y, page_width - 100,
                "CARD OPTIMIZATION", "优化建议"
            )
            
            current_y -= 40
            
            recommendation = self.base_generator._get_optimization_recommendation(card_data)
            
            # 建议文本框
            c.setFillColorRGB(0.08, 0.08, 0.08, 0.95)
            c.roundRect(50, current_y - 120, page_width - 100, 120, 10, fill=1, stroke=0)
            
            c.setStrokeColor(self.design.COLOR_SILVER)
            c.setLineWidth(1)
            c.roundRect(50, current_y - 120, page_width - 100, 120, 10, fill=0, stroke=1)
            
            c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
            c.setFont("Helvetica", 10)
            
            # 简化建议文本显示
            lines = recommendation.split('\n')[:4]  # 只显示前4行
            line_y = current_y - 30
            for line in lines:
                if line.strip():
                    c.drawString(65, line_y, line[:80])  # 限制每行80字符
                    line_y -= 20
            
            # 页脚
            self.design.draw_footer(c, idx+1, len(cards_data) + 2)
            
            c.showPage()
        
        # ========== 最后页：整体分析 + 50/50服务 ==========
        self.design.draw_galaxy_background(c, page_number=len(cards_data)+2)
        
        current_y = page_height - 80
        
        # 整体财务分析标题
        self.design.draw_premium_section_header(
            c, 50, current_y, page_width - 100,
            "OVERALL FINANCIAL ANALYSIS", "整体财务分析"
        )
        
        current_y -= 60
        
        # DSR分析
        overall_dsr = (total_instalment / customer['monthly_income'] * 100) if customer['monthly_income'] > 0 else 0
        
        dsr_data = [
            ["Financial Metric / 财务指标", "Value / 数值"],
            ["Monthly Income / 月收入", f"RM {customer['monthly_income']:,.2f}"],
            ["Total Monthly Instalment / 总月供", f"RM {total_instalment:,.2f}"],
            ["Overall DSR / 整体债务比率", f"{overall_dsr:.1f}%"]
        ]
        
        self.design.draw_data_table_elegant(
            c, 50, current_y, page_width - 100,
            dsr_data, [280, 200]
        )
        
        current_y -= 180
        
        # 50/50服务说明
        self.design.draw_premium_section_header(
            c, 50, current_y, page_width - 100,
            "50/50 PROFIT-SHARING SERVICE", "利润分成咨询服务"
        )
        
        current_y -= 40
        
        # 服务说明框
        c.setFillColorRGB(0.05, 0.05, 0.05, 0.95)
        c.roundRect(50, 100, page_width - 100, current_y - 100, 15, fill=1, stroke=0)
        
        c.setStrokeColor(self.design.COLOR_SILVER_GLOW)
        c.setLineWidth(2)
        c.roundRect(50, 100, page_width - 100, current_y - 100, 15, fill=0, stroke=1)
        
        # 服务内容
        service_y = current_y - 30
        
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, service_y, "🎯 ZERO-RISK GUARANTEE / 零风险保证")
        
        service_y -= 25
        c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 10)
        c.drawString(70, service_y, "如果我们的优化方案没有为您创造任何收益，我们分毫不取。")
        c.drawString(70, service_y - 15, "If our optimization doesn't create savings/earnings, we charge nothing.")
        
        service_y -= 50
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, service_y, "💰 50/50 PROFIT SPLIT / 利润分成模式")
        
        service_y -= 25
        c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 10)
        c.drawString(70, service_y, "• 从节省或赚取的利润中，您保留50%，我们收取50%作为服务费")
        c.drawString(70, service_y - 15, "• Example: We save you RM 10,000 → You keep RM 5,000, we charge RM 5,000")
        
        service_y -= 50
        c.setFillColor(self.design.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, service_y, "📋 SERVICE WORKFLOW / 服务流程 (7步)")
        
        service_y -= 25
        c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 9)
        steps = [
            "1️⃣ 客户表达意愿 → 2️⃣ 方案准备 → 3️⃣ 商讨细节 → 4️⃣ 拟定合约",
            "5️⃣ 双方签字 → 6️⃣ 执行优化 → 7️⃣ 收取报酬（仅成功后）"
        ]
        for step in steps:
            c.drawString(70, service_y, step)
            service_y -= 15
        
        service_y -= 20
        c.setFillColor(self.design.COLOR_SILVER_GLOW)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(70, service_y, "📞 Contact: infinitegz.reminder@gmail.com")
        c.drawString(70, service_y - 15, "🔗 通过系统'咨询请求'功能了解更多")
        
        # 页脚
        self.design.draw_footer(c, len(cards_data)+2, len(cards_data)+2)
        
        # 保存PDF
        c.save()
        
        # 保存记录到数据库
        self.base_generator._save_consolidated_report_record(customer_id, year, month, pdf_path, cards_data)
        
        return pdf_path


def generate_galaxy_monthly_reports():
    """
    自动生成上个月的所有客户银河主题报表
    Auto-generate galaxy-themed reports for all customers from last month
    """
    today = datetime.now()
    last_month = today.replace(day=1) - timedelta(days=1)
    year = last_month.year
    month = last_month.month
    
    generator = GalaxyMonthlyReportGenerator()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
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
            pdf_path = generator.generate_customer_monthly_report_galaxy(customer_id, year, month)
            
            if pdf_path:
                generated_reports.append({
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'year': year,
                    'month': month,
                    'pdf_path': pdf_path
                })
                print(f"✅ Generated galaxy report for {customer_name} ({year}-{month})")
        
        except Exception as e:
            print(f"❌ Failed to generate galaxy report for customer {customer_id}: {e}")
    
    return generated_reports
