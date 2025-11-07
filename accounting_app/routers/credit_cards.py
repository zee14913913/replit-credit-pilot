from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, date
from decimal import Decimal
from io import BytesIO

from sqlalchemy import select, func, extract
from accounting_app.db import get_session
from accounting_app.models import Supplier, Transaction

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
async def page_supplier_invoices(request: Request, y: int = None, m: int = None):
    """供应商发票页面：读取数据库真实数据"""
    today = date.today()
    y = y or today.year
    m = m or today.month
    
    with get_session() as db:
        rows = db.execute(
            select(
                Supplier.id,
                Supplier.supplier_name,
                Supplier.address,
                func.coalesce(func.sum(Transaction.amount), 0).label('total')
            )
            .join(
                Transaction,
                (Transaction.supplier_id == Supplier.id) &
                (extract('year', Transaction.txn_date) == y) &
                (extract('month', Transaction.txn_date) == m),
                isouter=True
            )
            .group_by(Supplier.id, Supplier.supplier_name, Supplier.address)
            .order_by(Supplier.supplier_name.asc())
        ).all()
        
        suppliers = []
        total_infinite = Decimal("0.00")
        for sid, name, addr, total in rows:
            total = Decimal(str(total or 0)).quantize(Decimal("0.01"))
            suppliers.append({
                "id": sid,
                "name": name,
                "address": addr or "",
                "total": float(total),
                "fee": float((total * Decimal("0.01")).quantize(Decimal("0.01"))),
            })
            total_infinite += total
    
    service_fee = (total_infinite * Decimal("0.01")).quantize(Decimal("0.01"))
    
    return templates.TemplateResponse("credit_cards_supplier_invoices.html", {
        "request": request,
        "y": y,
        "m": m,
        "suppliers": suppliers,
        "total_infinite": float(total_infinite),
        "service_fee": float(service_fee),
    })

@router.get("/supplier-invoices/batch.zip")
async def batch_zip_invoices(y: int = None, m: int = None, lang: str = "en"):
    """批量生成供应商发票ZIP包"""
    import zipfile
    import re
    import hashlib
    from accounting_app.routers.invoices import render_service_invoice
    
    def sanitize_filename(name: str) -> str:
        """安全化文件名，防止Zip Slip漏洞"""
        # 移除路径分隔符和危险字符
        safe = re.sub(r'[^\w\s-]', '', name)
        # 替换空格为下划线
        safe = re.sub(r'\s+', '_', safe)
        # 截断过长文件名
        return safe[:50] if safe else "UNNAMED"
    
    def file_hash(data: bytes) -> str:
        """生成文件SHA256哈希摘要（前10位）"""
        return hashlib.sha256(data).hexdigest()[:10]
    
    today = date.today()
    y = y or today.year
    m = m or today.month
    
    with get_session() as db:
        rows = db.execute(
            select(
                Supplier.id,
                Supplier.supplier_name,
                Supplier.address,
                func.coalesce(func.sum(Transaction.amount), 0).label('total')
            )
            .join(
                Transaction,
                (Transaction.supplier_id == Supplier.id) &
                (extract('year', Transaction.txn_date) == y) &
                (extract('month', Transaction.txn_date) == m),
                isouter=True
            )
            .group_by(Supplier.id, Supplier.supplier_name, Supplier.address)
            .order_by(Supplier.supplier_name.asc())
        ).all()
        
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, (sid, name, addr, total) in enumerate(rows, start=1):
                total = Decimal(str(total or 0)).quantize(Decimal("0.01"))
                if total == 0:
                    continue
                    
                fee = (total * Decimal("0.01")).quantize(Decimal("0.01"))
                number = f"INV-{y}-{idx:04d}"
                
                # 调用现有的发票渲染函数
                pdf = render_service_invoice({
                    "number": number,
                    "date": str(today),
                    "bill_to_name": name,
                    "bill_to_addr": addr or "",
                    "amount": float(fee)
                }, "zh" if lang.lower() == "zh" else "en")
                
                # 安全化文件名 + 添加哈希校验
                safe_name = sanitize_filename(name)
                pdf_hash = file_hash(pdf)
                zf.writestr(f"{number}_{safe_name}_{pdf_hash}.pdf", pdf)
        
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="invoices_{y}-{m:02d}.zip"'}
        )

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
async def page_monthly_report(request: Request, y: int = None, m: int = None):
    today = date.today()
    y = y or today.year
    m = m or today.month
    
    coverage = 0 if not DEMO_TX else round(100*sum(1 for x in DEMO_TX if x["receipt"]=="matched")/len(DEMO_TX),2)
    grade = "A" if coverage>=90 else ("B" if coverage>=70 else ("C" if coverage>=50 else "D"))
    matched = sum(1 for x in DEMO_TX if x["receipt"]=="matched")
    total = len(DEMO_TX)
    need_for_A = max(0, int(total * 0.9) - matched)
    
    owner = {"expenses": 8500.00, "payments": 6000.00, "balance": 2500.00}
    gz = {"expenses": 3200.00, "payments": 2800.00, "service_fee": 32.00, "balance": 400.00}
    
    return templates.TemplateResponse("credit_cards_monthly_report.html", {
        "request": request,
        "y": y,
        "m": m,
        "coverage": coverage,
        "grade": grade,
        "matched": matched,
        "total": total,
        "need_for_A": need_for_A,
        "owner": owner,
        "gz": gz
    })

@router.get("/monthly-report/export.csv")
async def export_monthly_report_csv(y: int = None, m: int = None):
    """导出月度报告CSV"""
    from io import StringIO
    import csv
    
    today = date.today()
    y = y or today.year
    m = m or today.month
    
    # TODO: 使用真实数据库查询
    owner = {"expenses": 8500.00, "payments": 6000.00, "balance": 2500.00}
    gz = {"expenses": 3200.00, "payments": 2800.00, "service_fee": 32.00, "balance": 400.00}
    
    # 计算评级
    coverage = 33.33  # TODO: 从数据库计算
    grade = "A" if coverage >= 90 else ("B" if coverage >= 70 else ("C" if coverage >= 50 else "D"))
    
    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(["Category", "Expenses", "Payments", "Service Fee", "Balance"])
    w.writerow(["OWNER", owner["expenses"], owner["payments"], 0, owner["balance"]])
    w.writerow(["INFINITE", gz["expenses"], gz["payments"], gz["service_fee"], gz["balance"]])
    
    sio.seek(0)
    # 文件名包含年月和评级
    filename = f"monthly_{y}-{m:02d}_{grade}.csv"
    return StreamingResponse(
        iter([sio.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/month-summary")
async def api_month_summary(y: int = None, m: int = None):
    """月末统计数据API（Portal页面调用）"""
    pending = sum(1 for x in DEMO_TX if x["receipt"] != "matched")
    
    today = date.today()
    y = y or today.year
    m = m or today.month
    
    with get_session() as db:
        # 统计当月有交易的供应商数量
        suppliers_count = db.execute(
            select(func.count(func.distinct(Transaction.supplier_id)))
            .where(
                extract('year', Transaction.txn_date) == y,
                extract('month', Transaction.txn_date) == m
            )
        ).scalar() or 0
        
        # 当月交易总额
        total_amount = db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                extract('year', Transaction.txn_date) == y,
                extract('month', Transaction.txn_date) == m
            )
        ).scalar() or 0
        
    service_fee = float(Decimal(str(total_amount)) * Decimal("0.01"))
    
    return JSONResponse({
        "ok": True,
        "pending": pending,
        "suppliers": suppliers_count,
        "service_fee": round(service_fee, 2)
    })

@router.post("/receipts/upload")
async def upload_receipts(file: UploadFile = File(...)):
    """上传收据并OCR识别"""
    # TODO: 调用真实OCR服务（需配置OCR_API_KEY）
    extracted = {
        "merchant_name": "DEMO MERCHANT",
        "amount": 12.34,
        "date": str(date.today()),
        "confidence_score": 0.76
    }
    # 成功上传后，前端应自动跳转到 ?filter=pending
    return JSONResponse({
        "ok": True, 
        "extracted": extracted,
        "redirect": "/credit-cards/receipts?filter=pending"
    })

@router.post("/receipts/confirm")
async def confirm_receipt_match(tx_id: int = Form(...), receipt_id: int = Form(...)):
    """确认收据匹配"""
    # TODO: 更新数据库匹配关系
    return JSONResponse({"ok": True})

@router.post("/receipts/match_all")
async def match_all_receipts(threshold: float = 0.90):
    """批量自动匹配（相似度>=阈值）"""
    # TODO: 批量匹配逻辑
    auto_confirmed = 1
    return JSONResponse({"ok": True, "auto_confirmed": auto_confirmed})
