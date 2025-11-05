# accounting_app/routers/ctos.py
import os
import uuid
import datetime as dt
from typing import Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from sqlalchemy import create_engine, Column, String, Integer, DateTime, LargeBinary, Text, select
from sqlalchemy.orm import declarative_base, sessionmaker

from accounting_app.services.crypto_box import encrypt, decrypt
from accounting_app.services.ctos_client import is_enabled, submit_consent, fetch_metrics_from_report

router = APIRouter(prefix="/ctos", tags=["CTOS"])

DB_PATH = os.getenv("CTOS_DB_PATH", "/home/runner/ctos.db")
engine = create_engine(f"sqlite:///{DB_PATH}", future=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

UPLOAD_DIR = os.getenv("CTOS_UPLOAD_DIR", "/home/runner/ctos_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Consent(Base):
    __tablename__ = "ctos_consent"
    id = Column(String(64), primary_key=True)
    created_at = Column(DateTime, index=True)
    name = Column(String(120))
    email_enc = Column(Text)
    phone_enc = Column(Text)
    ic_enc = Column(Text)
    company_ssm_enc = Column(Text)
    status = Column(String(32))
    report_path = Column(Text)
    dsr = Column(String(32))
    dsrc = Column(String(32))
    commitments = Column(String(32))
    monthly_income = Column(String(32))

Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _require_key(key: Optional[str]):
    portal_key = os.getenv("PORTAL_KEY", "")
    if not portal_key or key != portal_key:
        raise HTTPException(404, "Not Found")

@router.get("/page", response_class=HTMLResponse)
def ctos_page(key: Optional[str] = None):
    _require_key(key)
    return HTMLResponse(f"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>CTOS Consent</title>
<style>
:root {{ --primary:#FF007F; --bg:#1a1323; --card:#322446; --text:#fff; --muted:#999; --line:#888; }}
body {{ margin:0; font-family:ui-sans-serif,system-ui; background:linear-gradient(180deg,#1a1323,#0f0a14); color:var(--text); }}
.container {{ max-width:760px; margin:40px auto; padding:0 16px; }}
.card {{ background:linear-gradient(180deg,#322446,#281a3a); border-radius:14px; padding:16px; border:1px solid #3a2a4f; box-shadow:0 8px 24px #0003; }}
input {{ background:#1a1323; color:#fff; border:1px solid #403150; padding:8px 10px; border-radius:10px; width:100%; }}
.btn {{ background:var(--primary); border:none; color:#fff; padding:10px 14px; border-radius:12px; cursor:pointer; }}
label {{ display:block; margin:10px 0 6px; color:#ddd; }}
</style></head>
<body>
<div class="container">
  <h2>CTOS 授权与资料上传</h2>
  <div class="card">
    <form action="/ctos/submit" method="post" enctype="multipart/form-data">
      <input type="hidden" name="key" value="{key}"/>
      <label>姓名 Name</label>
      <input name="name" required/>
      <div style="display:flex; gap:10px;">
        <div style="flex:1">
          <label>Email</label>
          <input name="email" required/>
        </div>
        <div style="flex:1">
          <label>Phone</label>
          <input name="phone" required/>
        </div>
      </div>
      <label>IC（NRIC）</label>
      <input name="ic" required/>
      <label>公司 SSM No.（可选）</label>
      <input name="ssm"/>
      <label>上传 IC/公司文件（PDF/JPG/PNG）</label>
      <input type="file" name="doc" accept=".pdf,.jpg,.jpeg,.png" required/>
      <div style="margin-top:12px; display:flex; gap:10px; justify-content:flex-end;">
        <button class="btn" type="submit">提交并跳转 Loans 比价</button>
      </div>
    </form>
  </div>
</div>
</body></html>
""")

@router.post("/submit")
async def ctos_submit(
    key: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    ic: str = Form(...),
    ssm: Optional[str] = Form(None),
    doc: UploadFile = File(...)
):
    _require_key(key)
    if doc.content_type not in ("application/pdf", "image/jpeg", "image/png"):
        raise HTTPException(400, "Unsupported file type")

    cid = str(uuid.uuid4())
    now = dt.datetime.utcnow()
    db = SessionLocal()
    try:
        consent = Consent(
            id=cid,
            created_at=now,
            name=name,
            email_enc=encrypt(email),
            phone_enc=encrypt(phone),
            ic_enc=encrypt(ic),
            company_ssm_enc=encrypt(ssm or ""),
            status="queued",
            report_path="",
            dsr="",
            dsrc="",
            commitments="",
            monthly_income=""
        )
        db.add(consent)
        db.commit()

        ext = ".pdf" if doc.content_type == "application/pdf" else (".jpg" if doc.content_type=="image/jpeg" else ".png")
        save_path = os.path.join(UPLOAD_DIR, f"{cid}{ext}")
        with open(save_path, "wb") as f:
            f.write(await doc.read())

        meta = submit_consent({
            "id": cid, "name": name, "email": email, "phone": phone, "ic": ic, "ssm": ssm, "doc_path": save_path
        })

        consent.status = "submitted" if meta.get("status") in ("submitted","queued") else "queued"
        db.commit()

        url = f"/loans/compare/page?use_ctos=1&consent_id={cid}&key={key}"
        return RedirectResponse(url, status_code=302)
    finally:
        db.close()

@router.get("/admin", response_class=HTMLResponse)
def admin_page(key: Optional[str] = None, ak: Optional[str] = None):
    _require_key(key)
    admin_key = os.getenv("ADMIN_KEY", "")
    if not admin_key or ak != admin_key:
        raise HTTPException(404, "Not Found")

    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>CTOS Admin</title>
<style>
:root {{ --primary:#FF007F; --bg:#1a1323; --card:#322446; --text:#fff; --muted:#999; --line:#888; }}
body {{ margin:0; font-family:ui-sans-serif,system-ui; background:linear-gradient(180deg,#1a1323,#0f0a14); color:var(--text); }}
.container {{ max-width:900px; margin:40px auto; padding:0 16px; }}
.card {{ background:linear-gradient(180deg,#322446,#281a3a); border-radius:14px; padding:16px; border:1px solid #3a2a4f; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ border-bottom:1px dashed #403150; padding:10px; text-align:left; }}
.btn {{ background:var(--primary); border:none; color:#fff; padding:6px 10px; border-radius:10px; cursor:pointer; }}
</style></head>
<body>
<div class="container">
  <h2>CTOS 队列（管理员）</h2>
  <div class="card">
    <table id="tb"><thead>
      <tr><th>ID</th><th>Name</th><th>Status</th><th>DSR</th><th>Action</th></tr>
    </thead><tbody></tbody></table>
  </div>
</div>
<script>
async function load(){{
  const res = await fetch('/ctos/list?key={key}&ak={ak}');
  const js = await res.json();
  const tb = document.querySelector('#tb tbody'); tb.innerHTML='';
  js.items.forEach(it=>{{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{it.id}}</td><td>${{it.name}}</td><td>${{it.status}}</td><td>${{it.dsr||'-'}}</td>
    <td><button class="btn" onclick="upload('${{it.id}}')">Attach Report</button></td>`;
    tb.appendChild(tr);
  }});
}}
function upload(id){{
  const form = document.createElement('form');
  form.method='post'; form.enctype='multipart/form-data'; form.action='/ctos/attach-report';
  form.innerHTML = `<input name="consent_id" value="${{id}}"/><input name="ak" value="{ak}"/><input type="file" name="pdf" accept=".pdf"/><button>Upload</button>`;
  document.body.appendChild(form); form.querySelector('input[type=file]').click();
}}
load();
</script>
</body></html>
""")

@router.get("/list")
def list_items(key: Optional[str] = None, ak: Optional[str] = None):
    _require_key(key)
    if os.getenv("ADMIN_KEY", "") != (ak or ""):
        raise HTTPException(404, "Not Found")
    db = SessionLocal()
    try:
        rows = db.execute(select(Consent).order_by(Consent.created_at.desc())).scalars().all()
        out = []
        for c in rows:
            out.append({
                "id": c.id, "name": c.name, "status": c.status,
                "dsr": c.dsr, "dsrc": c.dsrc, "created_at": (c.created_at or dt.datetime.utcnow()).isoformat()
            })
        return {"items": out}
    finally:
        db.close()

@router.post("/attach-report")
async def attach_report(consent_id: str = Form(...), ak: str = Form(...), pdf: UploadFile = File(...)):
    if os.getenv("ADMIN_KEY", "") != ak:
        raise HTTPException(404, "Not Found")
    if pdf.content_type != "application/pdf":
        raise HTTPException(400, "PDF only")

    db = SessionLocal()
    try:
        c = db.get(Consent, consent_id)
        if not c:
            raise HTTPException(404, "not found")
        save_path = os.path.join(UPLOAD_DIR, f"{consent_id}-report.pdf")
        with open(save_path, "wb") as f:
            f.write(await pdf.read())

        c.report_path = save_path
        c.status = "ready"

        with open(save_path, "rb") as f:
            meta = fetch_metrics_from_report(f.read())
        c.dsr = str(meta.get("dsr", ""))
        c.dsrc = str(meta.get("dsrc", ""))
        c.commitments = str(meta.get("commitments", ""))
        c.monthly_income = str(meta.get("monthly_income", ""))
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@router.get("/metrics/{consent_id}")
def metrics(consent_id: str):
    db = SessionLocal()
    try:
        c = db.get(Consent, consent_id)
        if not c:
            raise HTTPException(404, "not found")
        def _f(v: str) -> Optional[float]:
            try:
                return float(v)
            except Exception:
                return None
        return {
            "consent_id": consent_id,
            "dsr": _f(c.dsr),
            "dsrc": _f(c.dsrc),
            "commitments": _f(c.commitments),
            "monthly_income": _f(c.monthly_income)
        }
    finally:
        db.close()

@router.get("/download/{consent_id}")
def download_report(consent_id: str):
    db = SessionLocal()
    try:
        c = db.get(Consent, consent_id)
        if not c or not c.report_path or not os.path.exists(c.report_path):
            raise HTTPException(404, "not found")
        return StreamingResponse(
            open(c.report_path, "rb"),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{consent_id}-report.pdf"'}
        )
    finally:
        db.close()
