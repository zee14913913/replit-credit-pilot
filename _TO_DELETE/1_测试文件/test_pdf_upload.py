#!/usr/bin/env python3
"""
PDF上传测试脚本 - 生成3种PDF并测试上传
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import requests
import json

BASE_URL = "http://localhost:8000"
COMPANY_ID = 1

def create_pdf_normal():
    """PDF-1：正常版本 - 标准银行月结单"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # 标题
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Maybank Monthly Statement - January 2025</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # 标准表格数据（完整5列）
    data = [
        ['Date', 'Description', 'Debit', 'Credit', 'Balance'],
        ['2025-01-01', 'OPENING BALANCE', '', '', '10000.00'],
        ['2025-01-02', 'SALARY PAYMENT', '', '5000.00', '15000.00'],
        ['2025-01-03', 'ATM WITHDRAWAL', '500.00', '', '14500.00'],
        ['2025-01-04', 'ONLINE TRANSFER', '200.00', '', '14300.00'],
        ['2025-01-05', 'MERCHANT PAYMENT', '150.00', '', '14150.00'],
        ['2025-01-31', 'CLOSING BALANCE', '', '', '14150.00']
    ]
    
    table = Table(data, colWidths=[80, 200, 80, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_pdf_missing_column():
    """PDF-2：缺列版本 - 缺少Credit列"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>CIMB Bank Statement - February 2025</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # 缺少Credit列（只有4列）
    data = [
        ['Date', 'Description', 'Debit', 'Balance'],
        ['2025-02-01', 'OPENING BALANCE', '', '8000.00'],
        ['2025-02-02', 'ATM WITHDRAWAL', '300.00', '7700.00'],
        ['2025-02-03', 'SHOPPING', '150.00', '7550.00']
    ]
    
    table = Table(data, colWidths=[80, 250, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_pdf_scanned():
    """PDF-3：扫描版 - 纯文本无表格结构"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # 模拟扫描件：无结构化文本
    scanned_text = """
    This is a scanned bank statement image.
    
    Account Number: 1122334455
    Statement Period: March 2025
    
    The text is not in table format and cannot be parsed automatically.
    This simulates a scanned PDF document.
    
    Please download CSV format from your online banking portal.
    """
    
    para = Paragraph(scanned_text, styles['Normal'])
    elements.append(para)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def test_pdf_upload(pdf_content, filename, scenario_name):
    """测试PDF上传"""
    print(f"\n{'='*80}")
    print(f"【{scenario_name}】测试 PDF 上传")
    print('='*80)
    
    try:
        # 上传到 FastAPI endpoint
        files = {'file': (filename, pdf_content, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/api/v2/import/bank-statement?company_id={COMPANY_ID}",
            files=files,
            timeout=30
        )
        
        print(f"✓ HTTP Status: {response.status_code}")
        
        result = response.json()
        
        # 提取关键字段
        test_result = {
            "scenario": scenario_name,
            "filename": filename,
            "http_status": response.status_code,
            "success": result.get("success"),
            "status": result.get("status"),
            "raw_document_id": result.get("raw_document_id"),
            "file_id": result.get("file_id"),
            "next_actions": result.get("next_actions", []),
            "error_code": result.get("error_code"),
            "message": result.get("message", "")
        }
        
        print(f"\n结果摘要：")
        print(f"  HTTP = {test_result['http_status']}")
        print(f"  success = {test_result['success']}")
        print(f"  status = {test_result['status']}")
        print(f"  file_id = {test_result['file_id']}")
        print(f"  next_actions = {test_result['next_actions']}")
        if test_result['error_code']:
            print(f"  error_code = {test_result['error_code']}")
        
        return test_result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return {
            "scenario": scenario_name,
            "error": str(e)
        }

if __name__ == "__main__":
    print("🧪 PDF上传功能测试 - 3个场景")
    print("="*80)
    
    results = []
    
    # Scenario 1: 正常PDF
    pdf1 = create_pdf_normal()
    result1 = test_pdf_upload(pdf1, "maybank_jan2025.pdf", "PDF-1 正常版")
    results.append(result1)
    
    # Scenario 2: 缺列PDF
    pdf2 = create_pdf_missing_column()
    result2 = test_pdf_upload(pdf2, "cimb_feb2025_missing_col.pdf", "PDF-2 缺列版")
    results.append(result2)
    
    # Scenario 3: 扫描PDF
    pdf3 = create_pdf_scanned()
    result3 = test_pdf_upload(pdf3, "scanned_mar2025.pdf", "PDF-3 扫描版")
    results.append(result3)
    
    # 总结
    print(f"\n{'='*80}")
    print("📊 测试总结（按您要求的格式）")
    print('='*80)
    
    for r in results:
        if 'error' in r:
            print(f"\n{r['scenario']}: ERROR - {r['error']}")
        else:
            print(f"\n{r['scenario']}: HTTP={r['http_status']}, detail页={'有' if r['file_id'] else '无'}, 按钮={r['next_actions']}")
    
    # 保存完整结果
    with open('/tmp/pdf_upload_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 完整报告已保存: /tmp/pdf_upload_test_results.json")
