"""
生成完整的CreditPilot中文版企业报告PDF
包含：封面 + 系统概述 + 核心模块 + 算法说明 + 客户流程
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_full_report():
    c = canvas.Canvas("CREDITPILOT_完整报告_中文版.pdf", pagesize=A4)
    w, h = A4
    
    pink = HexColor("#FF007F")
    purple = HexColor("#322446")
    white = HexColor("#FFFFFF")
    
    # ===== 封面页 =====
    c.setFillColor(purple)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    
    c.setFillColor(pink)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(80, h-150, "INFINITE GZ SDN. BHD.")
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(80, h-200, "CREDITPILOT")
    c.drawString(80, h-225, "智能贷款与 CTOS 情报系统")
    
    c.setFont("Helvetica", 14)
    c.drawString(80, h-260, "自动分析 · DSR评估 · 智能匹配报告")
    
    c.setFillColor(white)
    c.setFont("Helvetica", 10)
    c.drawString(80, 80, "© INFINITE GZ SDN. BHD.  版权所有")
    
    # ===== 第2页：系统概述 =====
    c.showPage()
    c.setFillColor(purple)
    c.rect(0, h-60, w, 60, stroke=0, fill=1)
    
    c.setFillColor(pink)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h-40, "系统概述")
    
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica", 12)
    y = h - 100
    
    intro_lines = [
        "CreditPilot 是由 INFINITE GZ SDN. BHD. 开发的智能信贷与贷款管理系统，",
        "通过人工智能算法、CTOS 授权接口与实时数据分析，为客户提供：",
        "",
        "  • 精准的贷款匹配推荐",
        "  • 自动化 DSR 债务收入比计算",
        "  • 一键导出报告（PDF / Excel）",
        "  • 银行偏好与市场口碑分析",
        "  • 企业级数据安全与隐私保护",
        "",
        "该系统旨在为个人与中小企业客户提供更透明、更高效的贷款决策体验。"
    ]
    
    for line in intro_lines:
        c.drawString(40, y, line)
        y -= 20
    
    # ===== 第3页：核心模块 =====
    c.showPage()
    c.setFillColor(purple)
    c.rect(0, h-60, w, 60, stroke=0, fill=1)
    
    c.setFillColor(pink)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h-40, "核心模块")
    
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 12)
    y = h - 100
    
    modules = [
        ("Loans", "智能贷款情报中心，显示实时产品与银行偏好"),
        ("Compare", "贷款对比系统，自动排序 + 一键生成报告"),
        ("CTOS", "在线授权与报告回传"),
        ("Reports", "自动生成财务与贷款分析报告（PDF）"),
        ("Dashboard", "综合客户资产负债与评分总览")
    ]
    
    for module, desc in modules:
        c.setFillColor(pink)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, module)
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica", 11)
        c.drawString(40, y-15, "  " + desc)
        y -= 40
    
    # ===== 第4页：算法逻辑 =====
    c.showPage()
    c.setFillColor(purple)
    c.rect(0, h-60, w, 60, stroke=0, fill=1)
    
    c.setFillColor(pink)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h-40, "算法逻辑 (Top-3 排名评分)")
    
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 14)
    y = h - 100
    c.drawString(40, y, "综合评分公式")
    
    c.setFont("Helvetica", 12)
    y -= 30
    c.drawString(40, y, "总分 = (DSR权重 60%) + (情绪权重 25%) + (偏好匹配度 15%)")
    
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "示例：")
    
    y -= 30
    table_data = [
        ("项目", "权重", "分值", "贡献"),
        ("DSR", "60%", "100", "60.0"),
        ("情绪分数", "25%", "85", "21.25"),
        ("偏好匹配", "15%", "100", "15.0"),
        ("总分", "100%", "-", "96.25")
    ]
    
    c.setFont("Helvetica", 10)
    for row in table_data:
        c.drawString(60, y, row[0])
        c.drawString(180, y, row[1])
        c.drawString(260, y, row[2])
        c.drawString(340, y, row[3])
        y -= 20
    
    # ===== 第5页：客户体验流程 =====
    c.showPage()
    c.setFillColor(purple)
    c.rect(0, h-60, w, 60, stroke=0, fill=1)
    
    c.setFillColor(pink)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h-40, "客户体验流程")
    
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica", 12)
    y = h - 100
    
    steps = [
        "1. 打开网址 https://portal.creditpilot.digital",
        "2. 浏览「Top-3 热门贷款推荐」",
        "3. 点击「加入比价篮」进入对比页",
        "4. 调整贷款金额与期限 → 「一键重算」",
        "5. 点击「保存快照 / 分享链接 / 导出PDF」",
        "6. 客户即可下载带企业封面的专业报告"
    ]
    
    for step in steps:
        c.drawString(40, y, step)
        y -= 30
    
    # ===== 第6页：品牌规范 & 联系方式 =====
    c.showPage()
    c.setFillColor(purple)
    c.rect(0, h-60, w, 60, stroke=0, fill=1)
    
    c.setFillColor(pink)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h-40, "品牌规范 & 联系方式")
    
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 14)
    y = h - 100
    c.drawString(40, y, "配色方案")
    
    c.setFont("Helvetica", 11)
    y -= 25
    c.drawString(40, y, "• 主色调：Hot Pink #FF007F")
    y -= 20
    c.drawString(40, y, "• 辅助色：Dark Purple #322446")
    y -= 20
    c.drawString(40, y, "• 背景色：Deep Black #1A1323")
    
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "安全与合规")
    
    c.setFont("Helvetica", 11)
    y -= 25
    c.drawString(40, y, "• 所有个人与公司资料经 AES-Fernet 加密存储")
    y -= 20
    c.drawString(40, y, "• 系统使用 HTTPS + 双重访问密钥")
    y -= 20
    c.drawString(40, y, "• 满足马来西亚个人数据保护法（PDPA）标准")
    
    y -= 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "联系方式")
    
    c.setFont("Helvetica", 11)
    y -= 25
    c.drawString(40, y, "INFINITE GZ SDN. BHD.")
    y -= 18
    c.drawString(40, y, "总部：Kuala Lumpur, Malaysia")
    y -= 18
    c.drawString(40, y, "客服邮箱：support@infinitegz.com")
    y -= 18
    c.drawString(40, y, "官方网站：https://portal.creditpilot.digital")
    
    # 页脚版权
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#666666"))
    c.drawString(40, 40, "© INFINITE GZ SDN. BHD. 版权所有")
    
    c.save()
    print("✅ 完整中文版企业报告已生成：CREDITPILOT_完整报告_中文版.pdf")

if __name__ == "__main__":
    create_full_report()
