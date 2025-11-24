"""
银河主题报表设计系统
Galaxy-Themed Professional Report Design System

高端企业级SaaS报表视觉设计
Premium Enterprise SaaS Report Visual Design
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import random
import math


class GalaxyDesign:
    """银河主题设计系统"""
    
    # 色彩定义 - Color Palette
    COLOR_BLACK = colors.HexColor('#000000')           # 纯黑背景
    COLOR_WHITE = colors.HexColor('#FFFFFF')           # 纯白文字
    COLOR_ELEPHANT_GRAY = colors.HexColor('#2C3E50')   # 大象深灰
    COLOR_DARK_GRAY = colors.HexColor('#1a1a1a')       # 深灰
    COLOR_SILVER = colors.HexColor('#C0C0C0')          # 银色
    COLOR_BRIGHT_SILVER = colors.HexColor('#E8E8E8')   # 亮银色
    COLOR_SILVER_GLOW = colors.HexColor('#F0F0F0')     # 银色发光
    
    # 渐变色定义
    GRADIENT_DARK = colors.HexColor('#0a0a0a')
    GRADIENT_MID = colors.HexColor('#1a1a1a')
    GRADIENT_LIGHT = colors.HexColor('#2a2a2a')
    
    def __init__(self):
        self.page_width, self.page_height = A4
    
    def draw_galaxy_background(self, c, page_number=1):
        """
        绘制银河背景
        Draw galaxy background with scattered silver particles
        """
        # 1. 纯黑色基础背景
        c.setFillColor(self.COLOR_BLACK)
        c.rect(0, 0, self.page_width, self.page_height, fill=1, stroke=0)
        
        # 2. 添加银河星点效果（亮银色细粉）
        self._draw_galaxy_stars(c)
        
        # 3. 添加若隐若现的银色光晕
        self._draw_subtle_glow(c, page_number)
    
    def _draw_galaxy_stars(self, c):
        """绘制银河星点（随机分布的亮银色粒子）"""
        random.seed(42)  # 固定种子以保持一致性
        
        # 生成不同大小的星点
        for _ in range(150):  # 大星点
            x = random.uniform(0, self.page_width)
            y = random.uniform(0, self.page_height)
            size = random.uniform(0.5, 1.5)
            opacity = random.uniform(0.3, 0.8)
            
            # 银色星点
            c.setFillColorRGB(0.94, 0.94, 0.94, opacity)
            c.circle(x, y, size, fill=1, stroke=0)
        
        # 添加更多微小星点（银河粉末效果）
        for _ in range(300):
            x = random.uniform(0, self.page_width)
            y = random.uniform(0, self.page_height)
            size = random.uniform(0.2, 0.6)
            opacity = random.uniform(0.2, 0.5)
            
            c.setFillColorRGB(0.88, 0.88, 0.88, opacity)
            c.circle(x, y, size, fill=1, stroke=0)
    
    def _draw_subtle_glow(self, c, page_number):
        """绘制若隐若现的银色光晕"""
        # 页面顶部银色渐变光晕
        glow_height = 100
        for i in range(50):
            opacity = (50 - i) / 100 * 0.15
            y = self.page_height - (i * 2)
            
            c.setStrokeColorRGB(0.9, 0.9, 0.9, opacity)
            c.setLineWidth(2)
            c.line(0, y, self.page_width, y)
    
    def draw_silver_border(self, c, x, y, width, height, corner_radius=5):
        """
        绘制银色发光边框
        Draw silver glowing border
        """
        # 外层银色发光
        c.setStrokeColor(self.COLOR_BRIGHT_SILVER)
        c.setLineWidth(2)
        c.roundRect(x-2, y-2, width+4, height+4, corner_radius, fill=0, stroke=1)
        
        # 内层亮银边框
        c.setStrokeColor(self.COLOR_SILVER_GLOW)
        c.setLineWidth(1)
        c.roundRect(x, y, width, height, corner_radius, fill=0, stroke=1)
    
    def draw_gradient_title_box(self, c, x, y, width, height, title_text):
        """
        绘制黑白渐变标题框
        Draw gradient title box with silver accents
        """
        # 深色渐变背景
        c.setFillColor(self.COLOR_ELEPHANT_GRAY)
        c.roundRect(x, y, width, height, 8, fill=1, stroke=0)
        
        # 银色顶边装饰
        c.setStrokeColor(self.COLOR_SILVER_GLOW)
        c.setLineWidth(3)
        c.line(x, y + height, x + width, y + height)
        
        # 银色底边装饰
        c.setStrokeColor(self.COLOR_SILVER)
        c.setLineWidth(1)
        c.line(x, y, x + width, y)
        
        # 标题文字（白色）
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 15, y + height/2 - 5, title_text)
    
    def draw_premium_section_header(self, c, x, y, width, title_en, title_cn):
        """
        绘制高级章节标题（银色渐变效果）
        Draw premium section header with silver gradient
        """
        # 银色渐变线
        c.setStrokeColor(self.COLOR_SILVER_GLOW)
        c.setLineWidth(2)
        c.line(x, y, x + width * 0.3, y)
        
        # 英文标题（白色粗体）
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y + 5, title_en)
        
        # 中文副标题（银色）
        c.setFillColor(self.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 10)
        c.drawString(x, y - 10, title_cn)
        
        # 装饰性银点
        for i in range(5):
            dot_x = x + width * 0.32 + (i * 8)
            c.setFillColorRGB(0.9, 0.9, 0.9, 0.6 - i*0.1)
            c.circle(dot_x, y + 2, 2, fill=1, stroke=0)
    
    def draw_data_table_elegant(self, c, x, y, width, data_rows, col_widths):
        """
        绘制优雅的数据表格（黑白灰银配色）
        Draw elegant data table with black/white/gray/silver theme
        """
        row_height = 30
        current_y = y
        
        for idx, row in enumerate(data_rows):
            if idx == 0:
                # 表头 - 深灰背景+银色边框
                c.setFillColor(self.COLOR_ELEPHANT_GRAY)
                c.rect(x, current_y, width, row_height, fill=1, stroke=0)
                
                # 银色顶边
                c.setStrokeColor(self.COLOR_SILVER_GLOW)
                c.setLineWidth(2)
                c.line(x, current_y + row_height, x + width, current_y + row_height)
                
                # 白色文字
                c.setFillColor(self.COLOR_WHITE)
                c.setFont("Helvetica-Bold", 11)
            else:
                # 数据行 - 深黑背景+微弱银边
                if idx % 2 == 0:
                    c.setFillColorRGB(0.05, 0.05, 0.05)  # 极深灰
                else:
                    c.setFillColorRGB(0.08, 0.08, 0.08)  # 稍亮深灰
                
                c.rect(x, current_y, width, row_height, fill=1, stroke=0)
                
                # 亮银色文字
                c.setFillColor(self.COLOR_BRIGHT_SILVER)
                c.setFont("Helvetica", 10)
            
            # 绘制单元格内容
            current_x = x + 10
            for col_idx, cell_value in enumerate(row):
                if col_idx < len(col_widths):
                    c.drawString(current_x, current_y + 10, str(cell_value))
                    current_x += col_widths[col_idx]
            
            current_y -= row_height
        
        # 整体银色边框
        table_height = len(data_rows) * row_height
        self.draw_silver_border(c, x, y - table_height + row_height, width, table_height)
    
    def draw_highlight_box(self, c, x, y, width, height, label, value):
        """
        绘制高亮信息框（用于关键指标）
        Draw highlight box for key metrics
        """
        # 深色背景
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.roundRect(x, y, width, height, 10, fill=1, stroke=0)
        
        # 银色发光边框
        c.setStrokeColor(self.COLOR_SILVER_GLOW)
        c.setLineWidth(2)
        c.roundRect(x, y, width, height, 10, fill=0, stroke=1)
        
        # 标签（银色小字）
        c.setFillColor(self.COLOR_SILVER)
        c.setFont("Helvetica", 9)
        c.drawString(x + 15, y + height - 20, label)
        
        # 数值（白色大字）
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x + 15, y + 15, value)
    
    def draw_logo_area(self, c, x, y):
        """
        绘制品牌标识区域
        Draw brand logo area with silver accents
        """
        # INFINITE GZ 标识
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(x, y, "INFINITE")
        
        # GZ 银色高亮
        c.setFillColor(self.COLOR_SILVER_GLOW)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(x + 90, y, "GZ")
        
        # 副标题
        c.setFillColor(self.COLOR_BRIGHT_SILVER)
        c.setFont("Helvetica", 10)
        c.drawString(x, y - 15, "Premium Financial Advisory Services")
    
    def draw_footer(self, c, page_num, total_pages):
        """
        绘制页脚
        Draw elegant footer
        """
        footer_y = 30
        
        # 银色分隔线
        c.setStrokeColor(self.COLOR_SILVER)
        c.setLineWidth(0.5)
        c.line(50, footer_y + 15, self.page_width - 50, footer_y + 15)
        
        # 页码（白色）
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica", 9)
        c.drawCentredString(self.page_width / 2, footer_y, f"Page {page_num} / {total_pages}")
        
        # 左侧版权信息（银色）
        c.setFillColor(self.COLOR_SILVER)
        c.drawString(50, footer_y, "© 2025 INFINITE GZ")
        
        # 右侧联系方式（银色）
        c.drawRightString(self.page_width - 50, footer_y, "infinitegz.reminder@gmail.com")


# 工具函数
def create_galaxy_canvas(file_path):
    """创建带银河背景的画布"""
    c = canvas.Canvas(file_path, pagesize=A4)
    design = GalaxyDesign()
    design.draw_galaxy_background(c, page_number=1)
    return c, design
