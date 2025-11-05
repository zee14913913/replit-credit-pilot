"""
Loans Ranking + PDF Export
Adds /loans/ranking (Top-3)  and  /loans/ranking/pdf (PDF export)
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import math, sqlite3, os

router = APIRouter(prefix="/loans/ranking", tags=["Ranking"])

DB = "loans.db"

def calc_score(p):
    """评分权重：DSR/情绪/偏好"""
    dsr_score = {"PASS":100,"BORDERLINE":70,"HIGH":30}.get(p.get("dsr_status","PASS"),70)
    sentiment = float(p.get("sentiment_score",0))*100
    pref = 100 if "受薪" in (p.get("preferred_customer","")) else 60
    return round(0.6*dsr_score + 0.25*sentiment + 0.15*pref,2)

@router.get("")
async def top3():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    u = con.execute("select * from loan_updates").fetchall()
    i = con.execute("select * from loan_intel").fetchall()
    con.close()
    intel_map = {x["product"]: dict(x) for x in i}
    combined=[]
    for r in u:
        rec = dict(r)
        intel = intel_map.get(rec["product"],{})
        rec.update(intel)
        rec["score"] = calc_score(rec)
        combined.append(rec)
    top = sorted(combined,key=lambda x:x["score"],reverse=True)[:3]
    return JSONResponse(top)

@router.get("/pdf")
async def pdf_export():
    """生成 Top-3 PDF 报告"""
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    u = con.execute("select * from loan_updates").fetchall()
    i = con.execute("select * from loan_intel").fetchall()
    con.close()
    intel_map = {x["product"]: dict(x) for x in i}
    combined=[]
    for r in u:
        rec=dict(r); rec.update(intel_map.get(rec["product"],{}))
        rec["score"]=calc_score(rec); combined.append(rec)
    top=sorted(combined,key=lambda x:x["score"],reverse=True)[:3]

    buf=BytesIO()
    c=canvas.Canvas(buf,pagesize=A4)
    w,h=A4; y=h-80
    c.setTitle("CreditPilot Loan Top-3 Report")
    c.setFont("Helvetica-Bold",18)
    c.setFillColorRGB(1,0,0.5)
    c.drawString(50,y,"CreditPilot Loan Top-3 Report")
    y-=40
    c.setFont("Helvetica",10)
    c.setFillColorRGB(1,1,1)
    for idx,p in enumerate(top,1):
        c.setFillColorRGB(1,0,0.5)
        c.rect(45,y-10,500,70,fill=0,stroke=1)
        c.setFillColorRGB(1,1,1)
        c.drawString(55,y+45,f"{idx}. {p.get('bank','?')} · {p.get('product','')}")
        c.drawString(55,y+30,f"利率: {p.get('apr','?')}%   分数: {p['score']}")
        c.drawString(55,y+15,f"DSR 状态: {p.get('dsr_status','')}  情绪: {p.get('sentiment_score','')}")
        c.drawString(55,y,f"偏好客户: {p.get('preferred_customer','')[:60]}")
        y-=90
    c.setFillColorRGB(1,0,0.5)
    c.drawString(50,40,f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · CreditPilot")
    c.showPage(); c.save()
    buf.seek(0)
    
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Loan_Top3_Report.pdf"}
    )
