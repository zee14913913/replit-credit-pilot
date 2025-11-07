from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from io import BytesIO

# 可从 main.py 里的 templates 取同一个实例；独立使用也行
templates = Jinja2Templates(directory="accounting_app/templates")
router = APIRouter(prefix="/credit-cards", tags=["credit-cards"])

# ===== 占位数据（可替换为数据库查询）=====
DEMO_TX = [
    {"date":"2025-11-05","desc":"DINAS RESTAURANT","amount":85.00,"tag":"INFINITE","receipt":"matched"},
    {"date":"2025-11-04","desc":"GRAB RIDE","amount":12.50,"tag":"OWNER","receipt":"pending"},
    {"date":"2025-11-03","desc":"SHOPEE ONLINE","amount":156.00,"tag":"OWNER","receipt":"missing"},
]

DEMO_SUPPLIERS = [
    {"name":"Dinas","sum":850.00,"fee":8.50,"tx":6},
    {"name":"Huawei","sum":1200.00,"fee":12.00,"tx":3},
    {"name":"7SL","sum":650.00,"fee":6.50,"tx":5},
    {"name":"Pasar Raya","sum":500.00,"fee":5.00,"tx":4},
]

# ========== Tab 1: 交易明细 ==========
@router.get("/transactions", response_class=HTMLResponse)
async def page_transactions(request: Request):
    stats = {
        "matched": sum(1 for x in DEMO_TX if x["receipt"]=="matched"),
        "pending": sum(1 for x in DEMO_TX if x["receipt"]=="pending"),
        "missing": sum(1 for x in DEMO_TX if x["receipt"]=="missing"),
    }
    return templates.TemplateResponse("credit_cards_transactions.html",
        {"request": request, "items": DEMO_TX, "stats": stats})

# ========== Tab 2: 收据匹配 ==========
@router.get("/receipts", response_class=HTMLResponse)
async def page_receipts(request: Request):
    coverage_percent = 75
    matched_count = sum(1 for x in DEMO_TX if x["receipt"]=="matched")
    total_count = len(DEMO_TX)
    pending_items = [
        {
            "tx_id": i,
            "tx_date": x["date"],
            "tx_desc": x["desc"],
            "tx_amount": x["amount"],
            "candidate_brief": "N/A",
            "similarity": "Pending",
            "receipt_id": None
        }
        for i, x in enumerate(DEMO_TX) if x["receipt"]!="matched"
    ]
    return templates.TemplateResponse("credit_cards_receipts.html",
        {"request": request, "coverage_percent": coverage_percent, 
         "matched_count": matched_count, "total_count": total_count,
         "pending": pending_items, "ocr_results": []})

@router.post("/receipts/ocr")
async def api_receipts_ocr(file: UploadFile = File(...)):
    # TODO: 调用 services/ocr_client.py
    extracted = {
        "merchant_name": "KFC RESTAURANT",
        "amount": 23.40,
        "date": "2025-11-05",
        "confidence_score": 0.88
    }
    return JSONResponse({"ok": True, "extracted": extracted})

@router.post("/receipts/match")
async def api_receipts_match(
    tx_date: str = Form(...),
    tx_amount: float = Form(...),
    ocr_date: str = Form(...),
    ocr_amount: float = Form(...),
    merchant: str = Form(...)
):
    # TODO: 实现金额/日期/商户相似度；现在给示例分数
    score = 0.4*min(1.0, ocr_amount/tx_amount if tx_amount else 0) \
          + 0.3*(1.0 if tx_date==ocr_date else 0.7) \
          + 0.2*(0.85 if merchant.lower() in "kfc restaurant" else 0.5) \
          + 0.1*0.9
    level = "优秀" if score>=0.9 else ("良好" if score>=0.8 else ("一般" if score>=0.6 else "差"))
    return JSONResponse({"ok": True, "score": round(score,3), "level": level})

# ========== Tab 3: 供应商发票（1% 服务费） ==========
@router.get("/supplier-invoices", response_class=HTMLResponse)
async def page_supplier_invoices(request: Request):
    total = sum(x["sum"] for x in DEMO_SUPPLIERS)
    total_fee = round(total*0.01, 2)
    return templates.TemplateResponse("credit_cards_supplier_invoices.html",
        {"request": request, "suppliers": DEMO_SUPPLIERS, "total": total, "total_fee": total_fee})

@router.get("/supplier-invoices/export.pdf")
async def export_invoices_pdf():
    # TODO: 调用 services/invoice_service.py 生成真实 PDF
    # 先返回一个示例 PDF 二进制
    bio = BytesIO()
    bio.write(b"%PDF-1.4\n% Demo PDF\n")
    bio.seek(0)
    return StreamingResponse(bio, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=supplier_invoices_demo.pdf"})

# ========== Tab 4: 月结报告 ==========
@router.get("/monthly-report", response_class=HTMLResponse)
async def page_monthly_report(request: Request):
    coverage = 0 if not DEMO_TX else round(100*sum(1 for x in DEMO_TX if x["receipt"]=="matched")/len(DEMO_TX),2)
    grade = "A" if coverage>=90 else ("B" if coverage>=70 else ("C" if coverage>=50 else "D"))
    owner = {"expenses": 8500.00, "payments": 6000.00, "credits": 0.0}
    gz    = {"expenses": 3200.00, "payments": 2800.00, "credits": 0.0, "fee": round(3200*0.01,2)}
    return templates.TemplateResponse("credit_cards_monthly_report.html",
        {"request": request, "coverage": coverage, "grade": grade, "owner": owner, "gz": gz})
