"""
Extras: Top-3 visual cards, Save/Share snapshot, PDF export
"""
from fastapi import APIRouter, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
import sqlite3, os
from io import BytesIO

from accounting_app.services.share_store import save_snapshot, load_snapshot
from accounting_app.services.pdf_maker import build_top3_pdf, build_compare_pdf

router = APIRouter(tags=["Loans Extras"])

DB = "loans.db"

def _fetch_updates_intel():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    u = [dict(r) for r in con.execute("select * from loan_updates").fetchall()]
    i = [dict(r) for r in con.execute("select * from loan_intel").fetchall()]
    con.close()
    imap = {x["product"]: x for x in i}
    return u, imap

def _calc_score(p):
    dsr_score = {"PASS":100,"BORDERLINE":70,"HIGH":30}.get(p.get("dsr_status","PASS"),70)
    sentiment = float(p.get("sentiment_score",0))*100
    pref = 100 if ("受薪" in (p.get("preferred_customer","")) or "salar" in (p.get("preferred_customer","").lower())) else 60
    return round(0.6*dsr_score + 0.25*sentiment + 0.15*pref,2)

@router.get("/loans/top3/cards", response_class=HTMLResponse)
async def top3_cards():
    updates, imap = _fetch_updates_intel()
    items=[]
    for r in updates:
        rec = dict(r)
        rec.update(imap.get(rec["product"], {}))
        rec["score"] = _calc_score(rec)
        items.append(rec)
    top = sorted(items, key=lambda x: x["score"], reverse=True)[:3]

    # 纯 HTML 片段（内置样式 + JS）→ 可放 iframe
    html = """
    <style>
      :root{--pink:#FF007F;--card:#322446;--bg:#1a1323;--white:#fff}
      .tp-wrap{background:transparent;color:var(--white);font-family:ui-sans-serif,system-ui;display:grid;gap:12px;grid-template-columns:repeat(3,minmax(0,1fr));padding:8px}
      .tp-card{background:linear-gradient(180deg,#322446,#281a3a);border:1px solid #3b2b4e;border-radius:14px;padding:14px;box-shadow:0 6px 18px #0006;position:relative}
      .tp-rank{position:absolute;top:10px;right:12px;background:var(--pink);color:#fff;font-weight:700;border-radius:999px;padding:2px 8px}
      .tp-title{font-weight:700;margin-bottom:4px}
      .tp-meta{opacity:.9;font-size:13px;margin-bottom:8px}
      .tp-badges span{display:inline-block;background:#ff007f26;border:1px solid #FF007F55;border-radius:999px;padding:2px 8px;margin-right:6px;font-size:12px}
      .tp-actions{display:flex;gap:8px;margin-top:10px}
      .btn{background:var(--pink);color:#fff;border:none;border-radius:10px;padding:8px 10px;cursor:pointer}
      .btn.ghost{background:#0000;border:1px solid #FF007F66}
      @media (max-width:900px){.tp-wrap{grid-template-columns:1fr}}
    </style>
    <div class="tp-wrap">
    """
    crown = " 👑"
    for idx,p in enumerate(top,1):
        html += f"""
        <div class="tp-card">
          <div class="tp-rank">#{idx}{crown if idx==1 else ""}</div>
          <div class="tp-title">{p.get('bank','?')} · {p.get('product','')}</div>
          <div class="tp-meta">APR {p.get('apr','?')}% · Score {p.get('score','?')} · DSR {p.get('dsr_status','')}</div>
          <div class="tp-badges">
            <span>Preferred: {(p.get('preferred_customer','')[:22]+'…') if len(p.get('preferred_customer',''))>22 else p.get('preferred_customer','')}</span>
            <span>Sentiment {p.get('sentiment_score','')}</span>
          </div>
          <div class="tp-actions">
            <button class="btn add-compare" data-source="{p.get('source','')}" data-product="{p.get('product','')}">加入比价</button>
            <a class="btn ghost" href="/loans/ranking/pdf" target="_blank">下载Top3 PDF</a>
          </div>
        </div>
        """
    html += """
    </div>
    <script>
      async function addCompare(payload){
        await fetch('/loans/compare/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
        // 触发父页徽标刷新（如果存在）
        if(window.parent && window.parent.syncBadge){ try{ window.parent.syncBadge(); }catch(e){} }
        alert('已加入比价篮');
      }
      document.querySelectorAll('.add-compare').forEach(btn=>{
        btn.addEventListener('click',()=>{
          const payload={
            source: btn.dataset.source,
            product: btn.dataset.product
          };
          addCompare(payload);
        });
      });
    </script>
    """
    return HTMLResponse(html)

@router.get("/loans/ranking/pdf")
async def ranking_pdf():
    updates, imap = _fetch_updates_intel()
    items=[]
    for r in updates:
        rec=dict(r); rec.update(imap.get(rec["product"],{}))
        rec["score"]=_calc_score(rec); items.append(rec)
    top = sorted(items, key=lambda x: x["score"], reverse=True)[:3]
    buf = build_top3_pdf(top)
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Loan_Top3_Report.pdf"}
    )

@router.post("/loans/compare/snapshot")
async def save_share(snapshot: dict = Body(...)):
    """保存当前对比篮与参数，返回短码"""
    code = save_snapshot(snapshot)
    return JSONResponse({"code": code, "url": f"/loans/compare/share/{code}"})

@router.get("/loans/compare/share/{code}", response_class=HTMLResponse)
async def view_share(code: str):
    """只读预览页（用于分享链接）"""
    snap = load_snapshot(code)
    if not snap: raise HTTPException(404, "Not found")
    # 极简只读表，品牌配色
    rows=""
    for i, it in enumerate(snap.get("items", []), 1):
        rows += f"<tr><td>{i}</td><td>{it.get('bank','')}</td><td>{it.get('product','')}</td><td>{it.get('apr','')}%</td><td>RM {it.get('monthly','')}</td><td>{it.get('dsr_percent','')}%</td><td>{it.get('status','')}</td></tr>"
    html = f"""
    <html><head><meta charset="utf-8"><title>Compare Snapshot</title>
    <style>
      body{{background:#1a1323;color:#fff;font-family:ui-sans-serif}}
      .wrap{{max-width:980px;margin:24px auto;padding:18px}}
      h2{{color:#FF007F}}
      table{{width:100%;border-collapse:collapse}}
      th,td{{border:1px solid #322446;padding:8px;font-size:14px}}
      .bar{{margin-bottom:10px;opacity:.9}}
      .btn{{background:#FF007F;color:#fff;border-radius:10px;padding:8px 12px;text-decoration:none}}
    </style></head>
    <body><div class="wrap">
      <h2>📄 比价快照（只读）</h2>
      <div class="bar">参数：金额 RM {snap.get('params',{}).get('amount','-')} · 年期 {snap.get('params',{}).get('tenure_years','-')} · 利率 {snap.get('params',{}).get('rate','-')}% · 收入 RM {snap.get('params',{}).get('income','-')} · 月供 RM {snap.get('params',{}).get('commitments','-')}</div>
      <table><thead><tr><th>#</th><th>Bank</th><th>Product</th><th>APR</th><th>Monthly</th><th>DSR%</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>
      <div style="margin-top:12px"><a class="btn" href="/loans/compare/pdf/{code}">下载 PDF</a></div>
    </div></body></html>
    """
    return HTMLResponse(html)

@router.get("/loans/compare/pdf/{code}")
async def share_pdf(code: str):
    snap = load_snapshot(code)
    if not snap: raise HTTPException(404, "Not found")
    buf = build_compare_pdf(snap)
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Compare_{code}.pdf"}
    )
