from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

HOT_PINK = (1, 0, 0.5)   # #FF007F
DARK_PURPLE = (0.196, 0.141, 0.275)  # #322446

def draw_header(c, title):
    w, h = A4
    c.setFillColorRGB(*HOT_PINK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20*mm, h-20*mm, title)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(1,1,1)
    c.drawString(20*mm, h-26*mm, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · CreditPilot")

def line(c, y):
    w,_=A4
    c.setStrokeColorRGB(*DARK_PURPLE); c.setLineWidth(0.7)
    c.line(20*mm, y, w-20*mm, y)

def build_top3_pdf(top3: list[dict]) -> BytesIO:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    draw_header(c, "Loan Top-3 Ranking")
    y = A4[1] - 35*mm
    for idx, p in enumerate(top3, 1):
        c.setFillColorRGB(*HOT_PINK)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20*mm, y, f"{idx}. {p.get('bank','?')} · {p.get('product','')}")
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica", 10)
        y -= 7*mm; c.drawString(20*mm, y, f"APR: {p.get('apr','?')}%   Score: {p.get('score','?')}   DSR: {p.get('dsr_status','')}")
        y -= 6*mm; c.drawString(20*mm, y, f"Preferred: {p.get('preferred_customer','')[:80]}")
        y -= 6*mm; c.drawString(20*mm, y, f"Feedback: {p.get('feedback_summary','')[:90]} (sentiment {p.get('sentiment_score','')})")
        y -= 8*mm; line(c, y); y -= 6*mm
        if y < 30*mm: c.showPage(); draw_header(c, "Loan Top-3 Ranking (cont.)"); y = A4[1]-30*mm
    c.showPage(); c.save(); buf.seek(0)
    return buf

def build_compare_pdf(snapshot: dict) -> BytesIO:
    """snapshot = {params:{income,commitments,rate,tenure_years}, items:[{bank,product,apr,monthly,dsr_percent,status}]}"""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    draw_header(c, "Loan Compare Report")
    y = A4[1] - 35*mm
    p = snapshot.get("params", {})
    c.setFont("Helvetica-Bold", 12); c.setFillColorRGB(*HOT_PINK)
    c.drawString(20*mm, y, "Input Parameters")
    c.setFont("Helvetica", 10); c.setFillColorRGB(1,1,1)
    y -= 7*mm; c.drawString(20*mm, y, f"Amount: RM {p.get('amount','-')}   Tenure: {p.get('tenure_years','-')} yrs   Rate: {p.get('rate','-')}%")
    y -= 6*mm; c.drawString(20*mm, y, f"Income: RM {p.get('income','-')}   Commitments: RM {p.get('commitments','-')}")
    y -= 7*mm; line(c,y); y -= 5*mm

    items = snapshot.get("items", [])
    c.setFont("Helvetica-Bold", 12); c.setFillColorRGB(*HOT_PINK)
    c.drawString(20*mm, y, "Results")
    y -= 6*mm; c.setFont("Helvetica", 10); c.setFillColorRGB(1,1,1)

    for idx, it in enumerate(items,1):
        row = f"{idx}. {it.get('bank','?')} · {it.get('product','')} | APR {it.get('apr','?')}% | Monthly RM {it.get('monthly','?')} | DSR {it.get('dsr_percent','?')}% | {it.get('status','')}"
        if y < 25*mm: c.showPage(); draw_header(c, "Loan Compare Report (cont.)"); y = A4[1]-30*mm
        c.drawString(20*mm, y, row); y -= 6*mm
    c.showPage(); c.save(); buf.seek(0)
    return buf
