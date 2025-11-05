# accounting_app/routers/loans_updates.py
import os
import csv
import io
import datetime as dt
from typing import Optional, List

from fastapi import APIRouter, Request, Response, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, select, desc
from sqlalchemy.orm import declarative_base, sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from accounting_app.services.loans_harvester import harvest_loans

router = APIRouter(prefix="/loans", tags=["Loans Updates"])

DB_PATH = os.getenv("LOANS_DB_PATH", "/home/runner/loans.db")
engine = create_engine(f"sqlite:///{DB_PATH}", future=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class LoanUpdate(Base):
    __tablename__ = "loan_updates"
    id = Column(Integer, primary_key=True)
    source = Column(String(120))
    product = Column(String(200))
    type = Column(String(80))
    rate = Column(Float)
    link = Column(String(500))
    snapshot = Column(Text)
    pulled_at = Column(DateTime, index=True)

class LoanMeta(Base):
    __tablename__ = "loan_meta_kv"
    id = Column(Integer, primary_key=True)
    k = Column(String(64), unique=True, index=True)
    v = Column(String(255))

Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

MIN_HOURS = float(os.getenv("MIN_REFRESH_HOURS", "20"))
REFRESH_KEY = os.getenv("LOANS_REFRESH_KEY", "")

def _get_last_time(db) -> Optional[dt.datetime]:
    row = db.execute(select(LoanMeta).where(LoanMeta.k == "last_harvest_at")).scalar_one_or_none()
    if row and row.v:
        try:
            return dt.datetime.fromisoformat(row.v)
        except Exception:
            return None
    return None

def _set_last_time(db, ts: dt.datetime):
    row = db.execute(select(LoanMeta).where(LoanMeta.k == "last_harvest_at")).scalar_one_or_none()
    iso = ts.isoformat()
    if row:
        row.v = iso
    else:
        row = LoanMeta(k="last_harvest_at", v=iso)
        db.add(row)
    db.commit()

async def _do_harvest(db):
    items = harvest_loans()
    saved = 0
    now = dt.datetime.utcnow()
    for it in items:
        rec = LoanUpdate(
            source=it.get("source"),
            product=it.get("product"),
            type=it.get("type"),
            rate=float(it.get("rate") or 0.0),
            link=it.get("link"),
            snapshot=it.get("snapshot"),
            pulled_at=now,
        )
        db.add(rec)
        saved += 1
    db.commit()
    _set_last_time(db, now)
    return saved, now

@router.get("/updates/last")
def last_status(db=Depends(get_db)):
    last = _get_last_time(db)
    return {
        "last_harvest_at": last.isoformat() if last else None,
        "min_hours": MIN_HOURS
    }

@router.post("/updates/refresh")
async def manual_refresh(
    request: Request,
    x_refresh_key: Optional[str] = Header(None),
    db=Depends(get_db),
):
    if not REFRESH_KEY or x_refresh_key != REFRESH_KEY:
        raise HTTPException(403, "forbidden")
    last = _get_last_time(db)
    now = dt.datetime.utcnow()
    if last:
        hours = (now - last).total_seconds() / 3600.0
        if hours < MIN_HOURS:
            return {"status": "skipped", "skipped_reason": f"cooldown {MIN_HOURS}h", "last_harvest_at": last.isoformat()}
    if _loans_harvest_once_fn is None:
        raise HTTPException(500, "Scheduler not initialized")
    saved, ts = await _loans_harvest_once_fn(db=db)
    return {"status": "done", "saved": saved, "last_harvest_at": ts.isoformat()}

@router.get("/updates")
def list_updates(q: Optional[str] = None, limit: int = 50, db=Depends(get_db)):
    stmt = select(LoanUpdate).order_by(desc(LoanUpdate.pulled_at), desc(LoanUpdate.id)).limit(limit)
    rows: List[LoanUpdate] = db.execute(stmt).scalars().all()
    out = []
    for r in rows:
        if q:
            s = f"{r.source} {r.product} {r.type} {r.snapshot}".lower()
            if q.lower() not in s:
                continue
        out.append({
            "id": r.id,
            "source": r.source,
            "product": r.product,
            "type": r.type,
            "rate": r.rate,
            "link": r.link,
            "snapshot": r.snapshot,
            "pulled_at": (r.pulled_at or dt.datetime.utcnow()).isoformat(),
        })
    return {"items": out, "count": len(out)}

@router.get("/updates/export.csv")
def export_csv(db=Depends(get_db)):
    stmt = select(LoanUpdate).order_by(desc(LoanUpdate.pulled_at), desc(LoanUpdate.id)).limit(2000)
    rows: List[LoanUpdate] = db.execute(stmt).scalars().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["source", "product", "type", "rate", "link", "snapshot", "pulled_at"])
    for r in rows:
        w.writerow([r.source, r.product, r.type, r.rate, r.link, r.snapshot, r.pulled_at.isoformat() if r.pulled_at else ""])
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=loans_updates.csv", "Cache-Control": "private, max-age=600"},
    )

@router.get("/page", response_class=HTMLResponse)
def loans_page():
    show_refresh = os.getenv("SHOW_REFRESH_BUTTON", "0") == "1"
    return HTMLResponse(f"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>Loans Updates</title>
<style>
:root {{
  --primary:#FF007F; --bg:#1a1323; --card:#322446; --text:#fff; --muted:#999; --line:#888;
}}
body {{ margin:0; font-family: ui-sans-serif, system-ui; background: linear-gradient(180deg,#1a1323,#0f0a14); color:var(--text); }}
.container {{ max-width:1000px; margin:40px auto; padding:0 16px; }}
.card {{ background: linear-gradient(180deg,#322446,#281a3a); border-radius:14px; padding:16px; box-shadow:0 8px 24px #00000066; border:1px solid #3a2a4f; margin-bottom:16px; }}
.btn {{ background:var(--primary); border:none; color:#fff; padding:8px 12px; border-radius:12px; cursor:pointer; }}
.btn.ghost {{ background:transparent; border:1px solid var(--line); color:#fff; }}
a {{ color:#ff9bc6; text-decoration:none; }}
.tools {{ display:flex; gap:8px; align-items:center; justify-content:space-between; margin-bottom:12px; }}
input[type=search]{{ background:#1a1323; color:#fff; border:1px solid #403150; padding:8px 10px; border-radius:10px; width:280px; }}
.list .item {{ display:flex; gap:12px; align-items:flex-start; border-top:1px dashed #403150; padding:12px 0; }}
.rate {{ color:#ff9bc6; font-weight:600; }}
.badge {{ font-size:12px; border:1px solid #554067; padding:2px 6px; border-radius:10px; color:#ddd; }}
.footer {{ opacity:.7; font-size:12px; margin-top:12px; }}
</style>
</head>
<body>
  <div class="container">
    <div class="tools">
      <div style="display:flex;gap:8px;align-items:center;">
        <input id="q" type="search" placeholder="Search product/bank/type..."/>
        <button class="btn ghost" onclick="loadList()">Search</button>
      </div>
      <div style="display:flex;gap:8px;">
        <a class="btn ghost" href="/loans/updates/export.csv">Export CSV</a>
        <a class="btn" href="/loans/compare/page">Compare Basket</a>
        {"<button class='btn ghost' onclick='refresh()'>Refresh</button>" if show_refresh else ""}
      </div>
    </div>
    <div class="card" id="listCard">
      <div id="list" class="list"></div>
      <div class="footer" id="last"></div>
    </div>
  </div>
<script>
async function loadList(){{
  const q = document.getElementById('q').value.trim();
  const res = await fetch('/loans/updates'+(q?('?q='+encodeURIComponent(q)):''));
  const js = await res.json();
  const el = document.getElementById('list');
  el.innerHTML = '';
  js.items.forEach(it => {{
    const row = document.createElement('div');
    row.className='item';
    row.innerHTML = `
      <div style="flex:1">
        <div><span class="badge">${{it.type||'N/A'}}</span> <strong>${{it.product||''}}</strong></div>
        <div style="opacity:.9;margin:6px 0">${{it.snapshot||''}}</div>
        <div style="font-size:12px;opacity:.8">${{it.source||''}} · <a href="${{it.link||'#'}}" target="_blank">Open</a> · <span class="rate">${{(it.rate??'')}}%</span> · <span>${{new Date(it.pulled_at).toLocaleString()}}</span></div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn ghost" onclick="add('${{encodeURIComponent(JSON.stringify(it))}}')">Add to Compare</button>
        <button class="btn" onclick="tryDSR(${{it.rate||0}})">Try DSR</button>
      </div>`;
    el.appendChild(row);
  }});
  const last = await fetch('/loans/updates/last').then(r=>r.json());
  document.getElementById('last').innerText = 'Last update: '+(last.last_harvest_at||'N/A')+' · Cooldown: '+last.min_hours+'h';
}}
async function add(payload){{
  const it = JSON.parse(decodeURIComponent(payload));
  const res = await fetch('/loans/compare/add', {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{ item: it }})
  }});
  const js = await res.json();
  alert('Added to basket: '+js.count+' items');
}}
function tryDSR(rate){{
  const amount = prompt('Loan Amount (RM)', '400000');
  const income = prompt('Monthly Income (RM)', '8000');
  const commit = prompt('Other Commitments (RM)', '1500');
  fetch('/loans/dsr/calc', {{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{ amount: Number(amount||0), income:Number(income||0), commitments:Number(commit||0), rate:Number(rate||0), tenure_years:30 }})
  }}).then(r=>r.json()).then(js=>alert('Monthly: RM '+js.monthly.toFixed(2)+' · DSR: '+(js.dsr_pct*100).toFixed(1)+'% · '+js.verdict));
}}
async function refresh(){{
  const key = prompt('Refresh Key');
  if(!key) return;
  const res = await fetch('/loans/updates/refresh', {{method:'POST', headers:{{'X-Refresh-Key':key}}}});
  const js = await res.json();
  alert(JSON.stringify(js));
  loadList();
}}
loadList();
</script>
</body></html>
""")

_scheduler = None
_loans_harvest_once_fn = None

@router.on_event("startup")
async def _start_scheduler():
    global _scheduler, _loans_harvest_once_fn
    tz = ZoneInfo(os.getenv("TZ", "Asia/Kuala_Lumpur"))
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=tz)
        _scheduler.start()

    async def job():
        db = SessionLocal()
        try:
            last = _get_last_time(db)
            now = dt.datetime.utcnow()
            if last:
                hours = (now - last).total_seconds()/3600.0
                if hours < MIN_HOURS:
                    return
            if _loans_harvest_once_fn:
                await _loans_harvest_once_fn(db=db)
        finally:
            db.close()

    async def harvest_once(db=None):
        owned = False
        if db is None:
            db = SessionLocal(); owned=True
        try:
            saved, ts = await _maybe_async(_do_harvest, db)
            return saved, ts
        finally:
            if owned: db.close()

    _loans_harvest_once_fn = harvest_once
    trigger = CronTrigger(hour=11, minute=0)
    _scheduler.add_job(job, trigger, id="loans_harvest_daily", replace_existing=True)

async def _maybe_async(fn, *a, **kw):
    ret = fn(*a, **kw)
    if hasattr(ret, "__await__"):
        return await ret
    return ret
