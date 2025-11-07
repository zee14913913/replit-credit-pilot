# accounting_app/routers/invoices.py
from fastapi import APIRouter, Query, Response, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
import io

# 只用 reportlab 生成黑白 PDF（正式公文风）
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors

# 数据库相关导入
from sqlalchemy import select, func, extract
from accounting_app.db import get_session
from accounting_app.models import Supplier, Transaction, Invoice, InvoiceSequence

router = APIRouter(prefix="/invoices", tags=["Invoices"])
templates = Jinja2Templates(directory="accounting_app/templates")

# ========= 你的公司信息（全局生效，可改） =========
COMPANY: Dict[str, Any] = {
    "name": "INFINITE GZ SDN BHD",
    "reg_no": "202401019141 (1564990-X)",
    "address": "NO 33-02 JALAN RADIN BAGUS, BANDAR BARU SRI PETALING, 57000 KUALA LUMPUR, MALAYSIA",
    "contact": "Tel: +6016-715 4052  ·  Email: business@infinitegz.com",
    "bank": {
        "name": "HONG LEONG BANK BERHAD",
        "account": "236-0059-4645",
        "beneficiary": "INFINITE GZ SDN BHD",
    },
    # 统一税率（默认 0.00；要切 6% 请改 0.06）
    "tax": {"sst": 0.00},
}

# ========= 默认条款（中英，可改） =========
TERMS_EN: List[str] = [
    "Payment is due within 14 days from the invoice date unless otherwise stated.",
    "Please transfer to the beneficiary account stated above and share the remittance advice.",
    "All services are provided under the agreed service agreement. Late payment may incur a debit note.",
]
TERMS_ZH: List[str] = [
    "除非另有约定，付款期限为开票日起 14 天内。",
    "请汇款至以上收款账户，并提供水单以便对账。",
    "所有服务受《服务协议》约束；逾期付款可能产生借记单。",
]

def money(v: Any) -> str:
    return f"{Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"

def get_terms(lang: str) -> List[str]:
    return TERMS_ZH if lang.lower() == "zh" else TERMS_EN

def _header(c: canvas.Canvas, title: str):
    width, height = A4
    c.setTitle(title)
    c.setAuthor(COMPANY["name"])
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)

    # 公司抬头（黑白）
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, (height - 20*mm), COMPANY["name"])

    c.setFont("Helvetica", 9)
    c.drawString(20*mm, (height - 26*mm), f"Reg. No: {COMPANY['reg_no']}")
    c.drawString(20*mm, (height - 31*mm), COMPANY["address"])
    c.drawString(20*mm, (height - 36*mm), COMPANY["contact"])

    # 右上角标题
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString((width - 20*mm), (height - 22*mm), title)

    # 横线
    c.line(20*mm, (height - 40*mm), (width - 20*mm), (height - 40*mm))

def _footer(c: canvas.Canvas):
    width, _ = A4
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 12*mm, "This is a computer-generated document. No signature is required.")

def _billto_block(c: canvas.Canvas, y: float, lang: str, bill_to: Dict[str, str]):
    label = "Bill To" if lang != "zh" else "收票方"
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, label)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, y - 6*mm, bill_to.get("name", ""))
    if bill_to.get("addr"): 
        c.drawString(20*mm, y - 11*mm, bill_to["addr"])
    if bill_to.get("reg"): 
        c.drawString(20*mm, y - 16*mm, bill_to["reg"])
    return y - 22*mm

def _meta_block(c: canvas.Canvas, y: float, meta: Dict[str, str]):
    width, _ = A4
    c.setFont("Helvetica", 9)
    for k, v in meta.items():
        c.drawRightString(width - 20*mm, y, f"{k}: {v}")
        y -= 6*mm
    return y

def _table(c: canvas.Canvas, top_y: float, cols: List[Dict[str, Any]], rows: List[List[str]]):
    width, _ = A4
    x0 = 20*mm
    x1 = width - 20*mm
    c.setFont("Helvetica-Bold", 9)
    # 表头
    col_x = x0
    for col in cols:
        c.drawString(col_x + 2*mm, top_y, col["label"])
        col_x += col["w"]
    c.line(x0, top_y - 2*mm, x1, top_y - 2*mm)

    # 内容
    y = top_y - 8*mm
    c.setFont("Helvetica", 9)
    for r in rows:
        col_x = x0
        for i, col in enumerate(cols):
            text = r[i]
            if col.get("align") == "right":
                c.drawRightString(col_x + col["w"] - 2*mm, y, text)
            else:
                c.drawString(col_x + 2*mm, y, text)
            col_x += col["w"]
        y -= 6*mm
    c.line(x0, y + 2*mm, x1, y + 2*mm)
    return y

def _totals_block(c: canvas.Canvas, y: float, sub: Decimal, tax_rate: float, lang: str):
    width, _ = A4
    labels_en = ["Subtotal", "SST", "Total"]
    labels_zh = ["小计", "销售服务税（SST）", "合计"]
    labels = labels_zh if lang == "zh" else labels_en

    tax_amt = (sub * Decimal(str(tax_rate))).quantize(Decimal('0.01'))
    total = sub + tax_amt

    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50*mm, y, labels[0] + ":")
    c.drawRightString(width - 20*mm, y, f"RM {money(sub)}")
    y -= 6*mm
    c.drawRightString(width - 50*mm, y, labels[1] + f" ({int(tax_rate*100)}%):")
    c.drawRightString(width - 20*mm, y, f"RM {money(tax_amt)}")
    y -= 6*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 50*mm, y, labels[2] + ":")
    c.drawRightString(width - 20*mm, y, f"RM {money(total)}")
    return y - 10*mm, total

def _bank_block(c: canvas.Canvas, y: float, lang: str):
    c.setFont("Helvetica", 9)
    bank_label = "Bank Details" if lang != "zh" else "收款账户"
    c.drawString(20*mm, y, bank_label)
    y -= 6*mm
    c.drawString(20*mm, y, f"Bank: {COMPANY['bank']['name']}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Account: {COMPANY['bank']['account']}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Beneficiary: {COMPANY['bank']['beneficiary']}")
    return y - 6*mm

def _terms_block(c: canvas.Canvas, y: float, lang: str):
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, "Terms & Notes" if lang != "zh" else "条款与说明")
    y -= 6*mm
    c.setFont("Helvetica", 9)
    for t in get_terms(lang):
        c.drawString(20*mm, y, f"• {t}")
        y -= 5*mm
    return y

# ------------------- 三种版式渲染 -------------------

def render_service_invoice(data: Dict[str, Any], lang: str) -> bytes:
    """专业服务发票"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _header(c, "SERVICE INVOICE" if lang != "zh" else "服务发票")

    # 对方信息 + 元数据
    y = _billto_block(c, (A4[1] - 48*mm), lang, {
        "name": data.get("bill_to_name", ""),
        "addr": data.get("bill_to_addr", ""),
        "reg": data.get("bill_to_reg", ""),
    })
    y_meta = _meta_block(c, (A4[1] - 48*mm), {
        ("Invoice No" if lang != "zh" else "发票编号"): data.get("number", ""),
        ("Date" if lang != "zh" else "开票日期"): data.get("date", datetime.now().strftime("%Y-%m-%d")),
        ("Due" if lang != "zh" else "到期日"): data.get("due", ""),
    })
    y = min(y, y_meta) - 6*mm

    # 表格
    items = data.get("items") or [{
        "desc": data.get("desc", "Professional Services"),
        "qty": 1, "unit_price": data.get("amount", 0)
    }]
    rows, sub = [], Decimal("0.00")
    for it in items:
        qty = Decimal(str(it.get("qty", 1)))
        unit = Decimal(str(it.get("unit_price", 0)))
        line = (qty * unit).quantize(Decimal('0.01'))
        rows.append([str(it.get("desc","")), str(qty), money(unit), money(line)])
        sub += line

    cols = [
        {"label": "Description" if lang != "zh" else "项目", "w": 100*mm},
        {"label": "Qty" if lang != "zh" else "数量", "w": 20*mm, "align": "right"},
        {"label": "Unit (RM)" if lang != "zh" else "单价 (RM)", "w": 30*mm, "align": "right"},
        {"label": "Amount (RM)" if lang != "zh" else "金额 (RM)", "w": 30*mm, "align": "right"},
    ]
    y = _table(c, y, cols, rows)

    # 合计 + 银行 + 备注 + 条款
    y, _ = _totals_block(c, y - 4*mm, sub, COMPANY["tax"]["sst"], lang)
    y = _bank_block(c, y, lang)
    if data.get("notes"):
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(20*mm, y, ("Notes: " if lang != "zh" else "备注：") + data["notes"])
        y -= 6*mm
    _terms_block(c, y, lang)
    _footer(c)
    c.showPage(); c.save()
    return buf.getvalue()

def render_debit_note(data: Dict[str, Any], lang: str) -> bytes:
    """借记单（逾期利息/调整）"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _header(c, "DEBIT NOTE" if lang != "zh" else "借记单")

    y = _billto_block(c, (A4[1] - 48*mm), lang, {
        "name": data.get("bill_to_name", ""),
        "addr": data.get("bill_to_addr", ""),
        "reg": data.get("bill_to_reg", ""),
    })
    y_meta = _meta_block(c, (A4[1] - 48*mm), {
        ("Debit No" if lang != "zh" else "借记编号"): data.get("number", ""),
        ("Date" if lang != "zh" else "日期"): data.get("date", datetime.now().strftime("%Y-%m-%d")),
    })
    y = min(y, y_meta) - 6*mm

    reason = data.get("reason") or ("Late payment surcharge" if lang != "zh" else "逾期支付附加款")
    amount = Decimal(str(data.get("amount", "0")))

    cols = [
        {"label": "Reason" if lang != "zh" else "原因", "w": 150*mm},
        {"label": "Amount (RM)" if lang != "zh" else "金额 (RM)", "w": 30*mm, "align": "right"},
    ]
    y = _table(c, y, cols, [[reason, money(amount)]])

    # 借记单常规不计税（如要计税，自行调 _totals_block 第四参）
    y, _ = _totals_block(c, y - 4*mm, amount, 0.00, lang)
    y = _bank_block(c, y, lang)
    _terms_block(c, y, lang)
    _footer(c)
    c.showPage(); c.save()
    return buf.getvalue()

def render_itemised_tax_invoice(data: Dict[str, Any], lang: str) -> bytes:
    """明细税务发票（类似航空/电商）"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _header(c, "TAX INVOICE" if lang != "zh" else "税务发票")

    y = _billto_block(c, (A4[1] - 48*mm), lang, {
        "name": data.get("bill_to_name", ""),
        "addr": data.get("bill_to_addr", ""),
        "reg": data.get("bill_to_reg", ""),
    })
    y_meta = _meta_block(c, (A4[1] - 48*mm), {
        ("Invoice No" if lang != "zh" else "发票编号"): data.get("number", ""),
        ("Date" if lang != "zh" else "开票日期"): data.get("date", datetime.now().strftime("%Y-%m-%d")),
    })
    y = min(y, y_meta) - 6*mm

    items = data.get("items") or [
        {"desc": "Passenger Service Charge", "tax_code": "SST-0%", "amount": 50.00},
        {"desc": "Airport Tax", "tax_code": "SST-0%", "amount": 30.00},
        {"desc": "Service Fee", "tax_code": f"SST-{int(COMPANY['tax']['sst']*100)}%", "amount": data.get("amount", 0)},
    ]
    rows, sub = [], Decimal("0.00")
    for it in items:
        amt = Decimal(str(it.get("amount", 0))).quantize(Decimal('0.01'))
        rows.append([str(it.get("desc","")), str(it.get("tax_code","")), money(amt)])
        sub += amt

    cols = [
        {"label": "Item" if lang != "zh" else "项目", "w": 100*mm},
        {"label": "Tax Code" if lang != "zh" else "税码", "w": 30*mm},
        {"label": "Amount (RM)" if lang != "zh" else "金额 (RM)", "w": 50*mm, "align": "right"},
    ]
    y = _table(c, y, cols, rows)
    y, _ = _totals_block(c, y - 4*mm, sub, COMPANY["tax"]["sst"], lang)
    y = _bank_block(c, y, lang)
    _terms_block(c, y, lang)
    _footer(c)
    c.showPage(); c.save()
    return buf.getvalue()

# 渲染映射
RENDERERS = {
    "service": render_service_invoice,
    "debit": render_debit_note,
    "itemised": render_itemised_tax_invoice,
    "itemised_tax": render_itemised_tax_invoice,
    "itemised_invoice": render_itemised_tax_invoice,
}
def _pick_renderer(layout: str):
    key = (layout or "").strip().lower()
    if key not in RENDERERS:
        raise HTTPException(status_code=400, detail="Unknown layout. Use one of: service | debit | itemised")
    return RENDERERS[key]

def next_number(prefix: str = "INV") -> str:
    """
    按年自动递增发票编号：INV-YYYY-0001、0002……
    线程安全：使用数据库事务保证唯一性
    """
    y = date.today().year
    with get_session() as db:
        seq = db.execute(
            select(InvoiceSequence).where(
                InvoiceSequence.prefix == prefix,
                InvoiceSequence.year == y
            )
        ).scalar_one_or_none()
        
        if not seq:
            seq = InvoiceSequence(prefix=prefix, year=y, next_seq=1)
            db.add(seq)
            db.flush()
        
        num = f"{prefix}-{y}-{seq.next_seq:04d}"
        seq.next_seq += 1
    
    return num

# ------------------- 路由 -------------------

@router.get("/credit-cards/supplier-invoices", response_class=HTMLResponse)
def page_supplier_invoices(request: Request, y: int = None, m: int = None):
    """
    供应商发票页面：读取数据库真实数据，按月汇总供应商交易并计算1%服务费
    """
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
            .join(Transaction, Transaction.supplier_id == Supplier.id, isouter=True)
            .where(
                extract('year', Transaction.txn_date) == y,
                extract('month', Transaction.txn_date) == m
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
        "suppliers": suppliers,
        "total_infinite": float(total_infinite),
        "service_fee": float(service_fee),
    })

@router.get("/preview.pdf")
def preview_pdf(
    layout: str = Query("service"),
    lang: str = Query("en"),
) -> Response:
    """浏览器预览三种发票（演示数据）"""
    render = _pick_renderer(layout)
    demo = {
        "number": "DEMO-0001",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "due": (datetime.now().strftime("%Y-%m-%d")),
        "bill_to_name": "Demo Client Sdn Bhd",
        "bill_to_addr": "Kuala Lumpur, Malaysia",
        "amount": 280.00,
        "items": [
            {"desc": "Professional Service (Consulting)", "qty": 1, "unit_price": 280.00}
        ],
        "notes": "Thank you for your business.",
    }
    pdf = render(demo, "zh" if lang.lower()=="zh" else "en")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="preview.pdf"'})

@router.get("/make")
def make_invoice(
    layout: str = Query(...),
    bill_to_name: str = Query(...),
    amount: float = Query(...),
    number: str = Query(None),
    bill_to_addr: str = Query(""),
    bill_to_reg: str = Query(""),
    lang: str = Query("en"),
) -> Response:
    """
    生成并下载 PDF 发票
    - number参数可选，若未提供则自动生成 INV-YYYY-0001 格式编号
    - 自动保存发票记录到数据库
    """
    render = _pick_renderer(layout)
    
    inv_no = number or next_number("INV")
    
    tax_rate = Decimal(str(COMPANY["tax"]["sst"]))
    base_amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    total = base_amount * (Decimal("1.00") + tax_rate)
    
    with get_session() as db:
        db.add(Invoice(
            number=inv_no,
            lang=lang,
            layout=layout,
            bill_to_name=bill_to_name,
            bill_to_addr=bill_to_addr,
            bill_to_reg=bill_to_reg,
            amount=base_amount,
            tax_rate=tax_rate,
            total=total,
        ))
    
    data = {
        "number": inv_no,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "bill_to_name": bill_to_name,
        "bill_to_addr": bill_to_addr,
        "bill_to_reg": bill_to_reg,
        "amount": amount,
    }
    pdf = render(data, "zh" if lang.lower()=="zh" else "en")
    filename = f"{inv_no}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
