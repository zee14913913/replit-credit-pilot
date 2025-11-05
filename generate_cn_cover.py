"""
生成CreditPilot中文版企业封面PDF
INFINITE GZ SDN. BHD. 品牌标准
"""
import sys
sys.path.insert(0, '/home/runner/CreditPilot-Smart-Credit-Loan-Manager')

from accounting_app.services.pdf_maker import make_brand_cover

# 生成中文版封面
make_brand_cover(
    path="CREDITPILOT_企业封面_中文版.pdf",
    title="CREDITPILOT 智能贷款与 CTOS 情报系统",
    subtitle="自动分析 · DSR评估 · 智能匹配报告"
)

print("✅ 中文版企业封面PDF已生成：CREDITPILOT_企业封面_中文版.pdf")
