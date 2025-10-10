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
            
            # ========== 完整交易明细表 ==========
            self.design.draw_premium_section_header(
                c, 50, current_y, page_width - 100,
                "TRANSACTION DETAILS", "交易明细记录"
            )
            
            current_y -= 40
            
            # 交易明细表头
            detail_headers = [
                "Date/日期", "Description/描述", "Type/类型", "Amount/金额"
            ]
            
            # 准备交易数据
            transactions = card_data['transactions']
            detail_rows = [detail_headers]
            
            for txn in transactions[:20]:  # 最多显示20笔交易
                txn_date = txn['transaction_date'][:10] if txn['transaction_date'] else 'N/A'
                desc = txn['description'][:30] if len(txn['description']) > 30 else txn['description']
                
                # 判断交易类型（基于belongs_to字段和amount正负）
                belongs_to = txn.get('belongs_to', 'customer')
                if belongs_to == 'INFINITE':
                    if txn['amount'] > 0:
                        txn_type = "INFINITE消费"
                    else:
                        txn_type = "INFINITE付款"
                else:
                    if txn['amount'] > 0:
                        txn_type = "客户消费"
                    else:
                        txn_type = "客户付款"
                
                amount_str = f"RM {abs(txn['amount']):,.2f}"
                detail_rows.append([txn_date, desc, txn_type, amount_str])
            
            # 如果交易太多，添加提示
            if len(transactions) > 20:
                detail_rows.append(['...', f'还有{len(transactions)-20}笔交易', '...', '...'])
            
            # 绘制交易明细表
            self.design.draw_data_table_elegant(
                c, 50, current_y, page_width - 100,
                detail_rows, [70, 180, 100, 100]
            )
            
            table_height = len(detail_rows) * 30
            current_y -= (table_height + 30)
            
            # ========== 交易分类汇总表 ==========
            self.design.draw_premium_section_header(
                c, 50, current_y, page_width - 100,
                "CATEGORY SUMMARY", "分类汇总"
            )
            
            current_y -= 40
            
            summary_data = [
                ["Category / 类别", "Amount / 金额"],
                ["客户总消费 Customer Debit", f"RM {card_data['customer']['total_debit']:,.2f}"],
                ["客户总付款 Customer Credit", f"RM {card_data['customer']['total_credit']:,.2f}"],
                ["客户未结余额 Customer Outstanding", f"RM {card_data['customer']['outstanding']:,.2f}"],
                ["INFINITE总消费 INFINITE Debit", f"RM {card_data['infinite']['total_debit']:,.2f}"],
                ["INFINITE总付款 INFINITE Credit", f"RM {card_data['infinite']['total_credit']:,.2f}"],
                ["INFINITE未结余额 INFINITE Outstanding", f"RM {card_data['infinite']['outstanding']:,.2f}"]
            ]
            
            self.design.draw_data_table_elegant(
                c, 50, current_y, page_width - 100,
                summary_data, [280, 200]
            )
            
            current_y -= 250
            
            # ========== 优化方案对比 ==========
            self.design.draw_premium_section_header(
                c, 50, current_y, page_width - 100,
                "OPTIMIZATION PROPOSAL", "优化方案对比"
            )
            
            current_y -= 50
            
            # 计算当前状况和优化后的对比
            current_outstanding = card_data['customer']['outstanding']
            current_dsr = card_data['dsr']
            
            # 模拟优化后的情况（示例）
            optimized_outstanding = current_outstanding * 0.7  # 假设减少30%
            optimized_dsr = current_dsr * 0.8  # 假设降低20%
            savings_potential = current_outstanding - optimized_outstanding
            
            # 对比表格
            comparison_data = [
                ["指标 / Metric", "当前状况 / Current", "优化后 / Optimized", "改善 / Improvement"],
                ["未结余额 Outstanding", 
                 f"RM {current_outstanding:,.2f}", 
                 f"RM {optimized_outstanding:,.2f}", 
                 f"↓ RM {savings_potential:,.2f}"],
                ["债务比率 DSR", 
                 f"{current_dsr:.1f}%", 
                 f"{optimized_dsr:.1f}%", 
                 f"↓ {(current_dsr - optimized_dsr):.1f}%"],
            ]
            
            self.design.draw_data_table_elegant(
                c, 50, current_y, page_width - 100,
                comparison_data, [140, 120, 120, 120]
            )
            
            current_y -= 150
            
            # 优化说明框
            c.setFillColorRGB(0.05, 0.05, 0.05, 0.95)
            c.roundRect(50, current_y - 100, page_width - 100, 100, 10, fill=1, stroke=0)
            
            c.setStrokeColor(self.design.COLOR_SILVER_GLOW)
            c.setLineWidth(2)
            c.roundRect(50, current_y - 100, page_width - 100, 100, 10, fill=0, stroke=1)
            
            c.setFillColor(self.design.COLOR_WHITE)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(65, current_y - 25, "💡 优化方案价值 / Optimization Value")
            
            c.setFillColor(self.design.COLOR_BRIGHT_SILVER)
            c.setFont("Helvetica", 9)
            c.drawString(65, current_y - 45, f"• 通过我们的优化，您可能节省约 RM {savings_potential:,.0f}")
            c.drawString(65, current_y - 60, f"• 我们只在成功为您省/赚钱后，收取50%作为服务费")
            c.drawString(65, current_y - 75, f"• 您净得约 RM {savings_potential * 0.5:,.0f}，零风险保证！")
            c.drawString(65, current_y - 90, f"• 通过系统'咨询请求'了解完整方案详情")
            
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
