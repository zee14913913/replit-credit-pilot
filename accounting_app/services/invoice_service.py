# -*- coding: utf-8 -*-
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# —— 字体（尽量用系统自带。若你有 NotoSansCJK，可换同名字体以更美观）——
# pdfmetrics.registerFont(TTFont("NotoSans", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"))
# pdfmetrics.registerFont(TTFont("NotoSans-Bold", "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"))
BASE_FONT = "Helvetica"
BASE_FONT_B = "Helvetica-Bold"

LINE_GREY = colors.HexColor("#444444")
TEXT_GREY = colors.HexColor("#111111")
MUTED_GREY = colors.HexColor("#666666")
HAIRLINE = 0.4

def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="H1", fontName=BASE_FONT_B, fontSize=16, leading=20, textColor=TEXT_GREY))
    ss.add(ParagraphStyle(name="H2", fontName=BASE_FONT_B, fontSize=12, leading=16, textColor=TEXT_GREY))
    ss.add(ParagraphStyle(name="Body", fontName=BASE_FONT, fontSize=10.5, leading=14, textColor=TEXT_GREY))
    ss.add(ParagraphStyle(name="Muted", fontName=BASE_FONT, fontSize=9, leading=12, textColor=MUTED_GREY))
    ss.add(ParagraphStyle(name="Right", parent=ss["Body"], alignment=2))
    return ss

# —— 通用页眉（黑白）——
def _header(c: canvas.Canvas, company):
    c.setLineWidth(HAIRLINE)
    c.setStrokeColor(LINE_GREY)
    top_y = 287 * mm
    # 公司名
    c.setFont(BASE_FONT_B, 14)
    c.setFillColor(TEXT_GREY)
    c.drawString(20*mm, top_y, company.get("name", "INFINITE GZ SDN. BHD."))
    c.setFont(BASE_FONT, 9.5)
    c.setFillColor(MUTED_GREY)
    c.drawString(20*mm, top_y-6*mm, company.get("address", "No. 28, Jalan Ipoh, 51200 Kuala Lumpur, Malaysia"))
    c.drawString(20*mm, top_y-11*mm, company.get("contact", "Tel: +60-12-345-6789  •  finance@infinitegz.com"))
    # 细线
    c.line(20*mm, top_y-14*mm, 190*mm, top_y-14*mm)
    return top_y-18*mm

def _draw_kv(c, x, y, kvs, col_gap=42*mm, row_gap=6*mm):
    c.setFont(BASE_FONT, 10.5)
    c.setFillColor(TEXT_GREY)
    cx, cy = x, y
    for k, v in kvs:
        c.setFont(BASE_FONT_B, 10.5); c.drawString(cx, cy, f"{k}:")
        c.setFont(BASE_FONT, 10.5);   c.drawString(cx+22*mm, cy, str(v))
        cy -= row_gap
        if cy < 40*mm:
            cy = y; cx += col_gap
    return cy

def _money(x):  # 金额显示
    if x is None: return "-"
    val = Decimal(str(x)).quantize(Decimal("0.01"))
    return f"RM {val:,.2f}"

# ========== 布局1：Service Invoice（专业服务） ==========
def _layout_service_invoice(c, data):
    ss = _styles()
    y = _header(c, data.get("company", {}))
    # 抬头
    c.setFont(BASE_FONT_B, 18); c.setFillColor(TEXT_GREY)
    c.drawRightString(190*mm, y+6*mm, data.get("title", "INVOICE"))
    y -= 6*mm

    # 左右信息区
    bill_to = data.get("bill_to", {})
    meta = data.get("meta", {})
    _draw_kv(c, 20*mm, y, [
        ("Bill To", bill_to.get("name","")),
        ("Address", bill_to.get("address","")),
        ("Email", bill_to.get("email","")),
    ])
    _draw_kv(c, 110*mm, y, [
        ("Invoice No", meta.get("number","INV-0001")),
        ("Date", meta.get("date", datetime.today().strftime("%Y-%m-%d"))),
        ("Terms", meta.get("terms", "14 days")),
    ])

    # 明细表
    items = data.get("items", [])
    table_data = [["Description", "Qty", "Unit Price", "Amount"]]
    for it in items:
        amt = Decimal(str(it.get("qty",1))) * Decimal(str(it.get("unit_price",0)))
        table_data.append([
            it.get("desc",""),
            str(it.get("qty",1)),
            _money(it.get("unit_price",0)),
            _money(amt)
        ])
    # 小计/税/合计
    subtotal = sum(Decimal(str(i.get("qty",1)))*Decimal(str(i.get("unit_price",0))) for i in items)
    tax_rate = Decimal(str(data.get("tax_rate", 0)))  # e.g. 0.06
    tax = (subtotal * tax_rate) if tax_rate>0 else Decimal("0.00")
    total = subtotal + tax

    table_data += [
        ["", "", "Subtotal", _money(subtotal)],
    ]
    if tax_rate>0:
        table_data += [["", "", f"Tax ({int(tax_rate*100)}%)", _money(tax)]]
    table_data += [["", "", "Total", _money(total)]]

    t = Table(table_data, colWidths=[100*mm, 18*mm, 28*mm, 24*mm])
    t.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), BASE_FONT_B, 10),
        ("LINEABOVE", (0,0), (-1,0), HAIRLINE, LINE_GREY),
        ("LINEBELOW", (0,0), (-1,0), HAIRLINE, LINE_GREY),
        ("FONT", (0,1), (-1,-1), BASE_FONT, 10),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("ALIGN", (0,1), (0,-1), "LEFT"),
        ("LINEBELOW", (-2,-3), (-1,-3), HAIRLINE, LINE_GREY),
        ("LINEABOVE", (-2,-1), (-1,-1), HAIRLINE, LINE_GREY),
        ("TEXTCOLOR", (0,0), (-1,-1), TEXT_GREY),
    ]))
    w, h = t.wrapOn(c, 170*mm, 120*mm)
    t.drawOn(c, 20*mm, 140*mm)

    # 备注/付款信息
    c.setFont(BASE_FONT_B, 10.5); c.drawString(20*mm, 130*mm, "Payment Details")
    c.setFont(BASE_FONT, 10.5)
    c.drawString(20*mm, 124*mm, data.get("payment","Bank: HLB 160-0000-9191 • Payable to INFINITE GZ SDN BHD"))

    c.setFont(BASE_FONT_B, 10.5); c.drawString(20*mm, 114*mm, "Notes")
    c.setFont(BASE_FONT, 10); c.setFillColor(MUTED_GREY)
    notes = data.get("notes", [
        "Kindly transfer within 14 days from invoice date.",
        "Late payment fee may apply as per agreement."
    ])
    y0 = 108*mm
    for n in notes:
        c.drawString(20*mm, y0, f"• {n}"); y0 -= 6*mm

    # 签名区
    c.setFillColor(TEXT_GREY)
    c.line(20*mm, 58*mm, 70*mm, 58*mm)
    c.setFont(BASE_FONT, 10); c.drawString(20*mm, 54*mm, "Authorised Signatory")

# ========== 布局2：Debit Note（借记单） ==========
def _layout_debit_note(c, data):
    y = _header(c, data.get("company", {}))
    c.setFont(BASE_FONT_B, 16); c.drawCentredString(105*mm, y+8*mm, "DEBIT NOTE")
    # 受票方 + 元信息
    bill_to = data.get("bill_to", {})
    meta = data.get("meta", {})
    _draw_kv(c, 20*mm, y, [
        ("TO", bill_to.get("name","")),
        ("Address", bill_to.get("address","")),
        ("Tel", bill_to.get("tel","")),
        ("Email", bill_to.get("email","")),
    ])
    _draw_kv(c, 120*mm, y, [
        ("Invoice No", meta.get("number","DN-0001")),
        ("Date", meta.get("date", datetime.today().strftime("%Y-%m-%d"))),
        ("Terms", meta.get("terms","CASH")),
        ("Page", "1 of 1")
    ])
    # 单行或多行描述
    items = data.get("items", [])
    table = [["NO.", "DESCRIPTIONS", "AMOUNT (RM)"]]
    for idx, it in enumerate(items, start=1):
        amt = Decimal(str(it.get("amount", 0)))
        table.append([str(idx), it.get("desc",""), f"{amt:.2f}"])
    total = sum(Decimal(str(it.get("amount",0))) for it in items)
    table.append(["", "TOTAL", f"{total:.2f}"])
    t = Table(table, colWidths=[15*mm, 120*mm, 35*mm])
    t.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), BASE_FONT_B, 10),
        ("LINEABOVE", (0,0), (-1,0), HAIRLINE, LINE_GREY),
        ("LINEBELOW", (0,0), (-1,0), HAIRLINE, LINE_GREY),
        ("FONT", (0,1), (-1,-2), BASE_FONT, 10),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),
        ("LINEABOVE", (0,-1), (-1,-1), HAIRLINE, LINE_GREY),
        ("FONT", (1,-1), (1,-1), BASE_FONT_B, 10),
    ]))
    t.wrapOn(c, 170*mm, 160*mm)
    t.drawOn(c, 20*mm, 120*mm)
    # 页脚提示
    c.setFont(BASE_FONT, 9); c.setFillColor(MUTED_GREY)
    c.drawString(20*mm, 52*mm, "NO SIGNATURE REQUIRED – COMPUTER GENERATED BILLING")

# ========== 布局3：Itemised Tax Invoice（航司/费用清单） ==========
def _layout_itemised(c, data):
    y = _header(c, data.get("company", {}))
    c.setFont(BASE_FONT_B, 16); c.drawString(20*mm, y+6*mm, data.get("title", "TAX INVOICE"))
    meta = data.get("meta", {})
    _draw_kv(c, 120*mm, y, [
        ("Invoice No", meta.get("number","TI-0001")),
        ("Date", meta.get("date", datetime.today().strftime("%Y-%m-%d"))),
        ("ST @", f"{int(Decimal(str(data.get('st_rate',0))) * 100)}%"),
    ])
    sections = data.get("sections", [])  # 每个 section 含小表
    y_table = 230*mm
    for sec in sections:
        # Section title bar
        c.setFont(BASE_FONT_B, 10); c.setFillColor(TEXT_GREY)
        c.drawString(20*mm, y_table, sec.get("title",""))
        y_table -= 5*mm
        table_data = sec.get("rows", [])
        t = Table(table_data, colWidths=[12*mm, 120*mm, 25*mm, 25*mm])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), HAIRLINE, LINE_GREY),
            ("FONT", (0,0), (-1,0), BASE_FONT_B, 9),
            ("FONT", (0,1), (-1,-1), BASE_FONT, 9),
            ("ALIGN", (-2,1), (-1,-1), "RIGHT"),
        ]))
        w, h = t.wrapOn(c, 170*mm, 999)
        t.drawOn(c, 20*mm, y_table - h)
        y_table -= (h + 6*mm)

    # 总计
    c.setFont(BASE_FONT_B, 11)
    c.drawRightString(185*mm, 70*mm, f"Grand Total: {_money(data.get('grand_total',0))}")

# —— 对外主函数 ——    
def build_invoice_pdf(layout: str, payload: dict) -> bytes:
    """
    layout: 'service' | 'debit' | 'itemised'
    payload: 数据字典，见各布局示例
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    if layout == "service":
        _layout_service_invoice(c, payload)
    elif layout == "debit":
        _layout_debit_note(c, payload)
    else:
        _layout_itemised(c, payload)
    c.showPage(); c.save()
    buf.seek(0)
    return buf.read()
