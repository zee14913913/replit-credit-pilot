#!/usr/bin/env python3
"""
基于真实Hong Leong Bank月结单生成3个测试PDF
- PDF-1: 正常版（原始文件）
- PDF-2: 缺失版（缺少Credit列）
- PDF-3: 扫描版（无结构化表格）
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import shutil
import os

# 创建测试文件夹
os.makedirs('test_pdfs', exist_ok=True)

def create_pdf_missing_column():
    """PDF-2：缺失Credit列版本 - 模拟银行系统导出错误"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           topMargin=15*mm, bottomMargin=15*mm,
                           leftMargin=15*mm, rightMargin=15*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # 银行抬头
    title = Paragraph("<b>CURRENT ACCOUNT STATEMENT</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 10))
    
    # 客户信息
    info = Paragraph("""
    <b>INFINITE GZ SDN. BHD.</b><br/>
    NO 33-02 JALAN RADIN BAGUS BANDAR BARU<br/>
    SRI PETALING<br/>
    57000 KUALA LUMPUR<br/><br/>
    <b>A/C No:</b> 23600594645 MYR<br/>
    <b>Statement Period:</b> 06/05/25 - 05/06/25<br/>
    <b>Date:</b> 05-06-2025
    """, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 20))
    
    # ⚠️ 缺失Credit列的表格（只有4列）
    data = [
        ['Date', 'Description', 'Withdrawal', 'Balance'],  # 缺少Credit/Deposit
        ['08-05-2025', 'SALARY PAYMENT AHMAD DZAFRI', '2,207.85', '18,207.11'],
        ['08-05-2025', 'SALARY PAYMENT MUHAMMAD AMIR', '2,372.65', '15,834.46'],
        ['08-05-2025', 'SALARY PAYMENT NUR ALIFAH', '3,908.95', '11,925.51'],
        ['08-05-2025', 'SALARY PAYMENT MUHAMMAD ZIKRI', '4,209.50', '7,716.01'],
        ['11-05-2025', 'INSTANT TRANSFER AI SMART TECH', '', '37,716.01'],
        ['11-05-2025', 'CIB TRANSFER CHEONG REN JOW', '1,000.00', '36,716.01'],
        ['11-05-2025', 'CIB TRANSFER CHIA VUI LEONG', '17,150.00', '19,566.01'],
        ['12-05-2025', 'CREDIT CARD PAYMENT', '20,056.00', '-490.00'],
    ]
    
    table = Table(data, colWidths=[70, 200, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # 底部说明
    footer = Paragraph(
        "<i>⚠️ This statement is missing the Credit/Deposit column. "
        "The validation system should detect this as incomplete data.</i>",
        styles['Normal']
    )
    elements.append(footer)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_pdf_scanned():
    """PDF-3：扫描版 - 模拟手机拍照或扫描仪输出"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           topMargin=20*mm, bottomMargin=20*mm,
                           leftMargin=20*mm, rightMargin=20*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # 模拟扫描件的特征：文本不规整，无结构化表格
    scanned_content = """
    
    
              CURRENT ACCOUNT STATEMENT
    
    
    INFINITE GZ SDN. BHD.
    NO 33-02 JALAN RADIN BAGUS BANDAR BARU
    SRI PETALING
    57000 KUALA LUMPUR
    
    
    Account Number: 23600594645    Currency: MYR
    Statement Date: 05-06-2025
    Statement Period: 06/05/25 - 05/06/25
    
    
    ---------------------------------------------------
    
    This is a scanned bank statement image.
    
    The original document was photographed or scanned,
    resulting in image-based PDF content.
    
    Text recognition (OCR) would be required to extract
    transaction details from this type of document.
    
    Transactions visible in the scanned image:
    - 08-05-2025: Salary payments to various employees
    - 11-05-2025: Transfers and commission payments
    - 12-05-2025: Credit card payments
    
    The system should detect that this PDF does not
    contain structured table data and prompt the user
    to download a CSV format from online banking instead.
    
    ---------------------------------------------------
    
    For digital processing, please download the
    statement in CSV or Excel format from your
    online banking portal.
    
    
    Hong Leong Bank Berhad (97141-X)
    
    """
    
    para = Paragraph(scanned_content, styles['Normal'])
    elements.append(para)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# 生成3个测试PDF
print("📄 生成测试PDF文件...")
print("="*80)

# PDF-1: 复制原始真实文件
print("\n1️⃣ PDF-1（正常版）: 复制真实月结单...")
shutil.copy(
    'attached_assets/05-06-2025_1762144711337.pdf',
    'test_pdfs/PDF-1-Normal-HongLeong-May2025.pdf'
)
print("   ✅ 已保存: test_pdfs/PDF-1-Normal-HongLeong-May2025.pdf")

# PDF-2: 缺失列版本
print("\n2️⃣ PDF-2（缺列版）: 生成缺少Credit列的月结单...")
pdf2_content = create_pdf_missing_column()
with open('test_pdfs/PDF-2-Missing-Column-May2025.pdf', 'wb') as f:
    f.write(pdf2_content)
print("   ✅ 已保存: test_pdfs/PDF-2-Missing-Column-May2025.pdf")
print("   ⚠️  特征：缺少Credit/Deposit列，应该触发验证失败")

# PDF-3: 扫描版
print("\n3️⃣ PDF-3（扫描版）: 生成模拟扫描件...")
pdf3_content = create_pdf_scanned()
with open('test_pdfs/PDF-3-Scanned-May2025.pdf', 'wb') as f:
    f.write(pdf3_content)
print("   ✅ 已保存: test_pdfs/PDF-3-Scanned-May2025.pdf")
print("   ⚠️  特征：无结构化表格，纯文本内容")

print("\n" + "="*80)
print("✅ 3个测试PDF已生成！")
print("\n📋 测试文件清单：")
print("   1. test_pdfs/PDF-1-Normal-HongLeong-May2025.pdf (真实月结单)")
print("   2. test_pdfs/PDF-2-Missing-Column-May2025.pdf (缺失Credit列)")
print("   3. test_pdfs/PDF-3-Scanned-May2025.pdf (扫描版)")
print("\n🚀 现在可以开始上传测试了！")
