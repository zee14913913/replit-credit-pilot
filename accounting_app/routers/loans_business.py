# accounting_app/routers/loans_business.py
from typing import Dict, Any, Optional
from uuid import uuid4
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
import math
import os
import json
import http.client

router = APIRouter(prefix="/loans", tags=["Loans Business"])

BASKETS: Dict[str, Dict[str, Any]] = {}

def get_basket_id(req: Request) -> str:
    bid = req.cookies.get("basket_id")
    if not bid:
        bid = str(uuid4())
    return bid

def annuity_monthly(amount: float, annual_rate_pct: float, years: int) -> float:
    r = (annual_rate_pct/100.0)/12.0
    n = years*12
    if r == 0:
        return amount/n
    return amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

@router.post("/dsr/calc")
async def dsr_calc(payload: Dict[str, Any]):
    amount = float(payload.get("amount", 0))
    rate = float(payload.get("rate", 0))
    tenure = int(payload.get("tenure_years", 30))
    income = float(payload.get("income", 0))
    commitments = float(payload.get("commitments", 0))
    monthly = annuity_monthly(amount, rate, tenure)
    dsr = (monthly + commitments) / income if income > 0 else 1.0
    verdict = "PASS" if dsr < 0.6 else ("BORDERLINE" if dsr < 0.7 else "HIGH")
    return {"monthly": monthly, "dsr_pct": dsr, "verdict": verdict}

@router.post("/compare/add")
async def compare_add(req: Request, payload: Dict[str, Any]):
    bid = get_basket_id(req)
    item = payload.get("item", {})
    BASKETS.setdefault(bid, {"items": []})
    BASKETS[bid]["items"].append(item)
    resp = JSONResponse({"ok": True, "count": len(BASKETS[bid]["items"]), "basket_id": bid})
    resp.set_cookie("basket_id", bid, max_age=86400*7)
    return resp

@router.post("/compare/remove")
async def compare_remove(req: Request, payload: Dict[str, Any]):
    bid = get_basket_id(req)
    idx = int(payload.get("index", -1))
    if bid in BASKETS and 0 <= idx < len(BASKETS[bid]["items"]):
        BASKETS[bid]["items"].pop(idx)
    return {"ok": True, "count": len(BASKETS.get(bid, {}).get("items", []))}

@router.get("/compare/list/{basket_id}")
async def compare_list(basket_id: str):
    return BASKETS.get(basket_id, {"items": []})

@router.get("/compare/page", response_class=HTMLResponse)
async def compare_page(req: Request, use_ctos: Optional[int] = 0, consent_id: Optional[str] = None, key: Optional[str] = None):
    bid = get_basket_id(req)
    items = BASKETS.setdefault(bid, {"items":[]})["items"]

    ctos_hint = ""
    if use_ctos and consent_id:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", int(os.getenv("PORT", "5000")), timeout=2)
            path = f"/ctos/metrics/{consent_id}"
            conn.request("GET", path)
            r = conn.getresponse()
            if r.status == 200:
                meta = json.loads(r.read().decode())
                ctos_hint = f"CTOS 最新 DSR: {(meta.get('dsr',0)*100):.1f}% · DSRC: {(meta.get('dsrc',0)*100):.1f}% · Commitments: RM {meta.get('commitments',0):,.2f}"
        except Exception:
            pass

    return HTMLResponse(f"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>Compare Basket</title>
<style>
:root {{ --primary:#FF007F; --bg:#1a1323; --card:#322446; --text:#fff; --muted:#999; --line:#888; }}
body {{ margin:0; font-family:ui-sans-serif,system-ui; background:linear-gradient(180deg,#1a1323,#0f0a14); color:var(--text); }}
.container {{ max-width:1000px; margin:40px auto; padding:0 16px; }}
.card {{ background:linear-gradient(180deg,#322446,#281a3a); border-radius:14px; padding:16px; border:1px solid #3a2a4f; box-shadow:0 8px 24px #0003; }}
.btn {{ background:var(--primary); border:none; color:#fff; padding:8px 12px; border-radius:12px; cursor:pointer; }}
input,select {{ background:#1a1323; color:#fff; border:1px solid #403150; padding:8px 10px; border-radius:10px; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ border-bottom:1px dashed #403150; padding:10px; text-align:left; }}
.hint {{ font-size:12px; opacity:.85; }}
</style></head>
<body>
<div class="container">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <h2>Compare Basket</h2>
    <a href="/loans/page" class="btn" style="text-decoration:none">← Back to Loans</a>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
      <div class="hint">{ctos_hint}</div>
      <div style="margin-left:auto"></div>
      <label>Income RM <input id="income" type="number" value="8000" style="width:120px"/></label>
      <label>Commitments RM <input id="commit" type="number" value="1500" style="width:120px"/></label>
      <label>Tenure <select id="tenure"><option>30</option><option>25</option><option>20</option></select> years</label>
      <button class="btn" onclick="recalc()">Recalculate</button>
    </div>
  </div>

  <div class="card">
    <table id="tb"><thead>
      <tr><th>#</th><th>Product</th><th>Bank</th><th>Type</th><th>Rate</th><th>Monthly (RM)</th><th>DSR</th><th></th></tr>
    </thead><tbody></tbody></table>
  </div>
</div>
<script>
const basketId = "{bid}";
const fmt = n=> Number(n||0).toFixed(2);
async function load(){{
  const res = await fetch('/loans/compare/list/{bid}');
  const js = await res.json();
  window._items = js.items||[];
  render();
}}
async function recalc(){{
  const income = Number(document.getElementById('income').value||0);
  const commit = Number(document.getElementById('commit').value||0);
  const tenure = Number(document.getElementById('tenure').value||30);
  const tbody = document.querySelector('#tb tbody');
  tbody.querySelectorAll('tr').forEach(tr=>{{
    const rate = Number(tr.getAttribute('data-rate')||0);
    const amt = Number(tr.getAttribute('data-amount')||400000);
    fetch('/loans/dsr/calc', {{
      method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{ amount: amt, rate: rate, tenure_years: tenure, income: income, commitments: commit }})
    }}).then(r=>r.json()).then(js=>{{
      tr.querySelector('[data-monthly]').innerText = fmt(js.monthly);
      tr.querySelector('[data-dsr]').innerText = (js.dsr_pct*100).toFixed(1)+'% '+js.verdict;
    }});
  }});
}}
function render(){{
  const tbody = document.querySelector('#tb tbody');
  tbody.innerHTML = '';
  (window._items||[]).forEach((it,idx)=>{{
    const tr = document.createElement('tr');
    tr.setAttribute('data-rate', it.rate||0);
    tr.setAttribute('data-amount', 400000);
    tr.innerHTML = `
      <td>${{idx+1}}</td>
      <td>${{it.product||''}}</td>
      <td>${{it.source||''}}</td>
      <td>${{it.type||''}}</td>
      <td>${{it.rate??''}}%</td>
      <td data-monthly>-</td>
      <td data-dsr>-</td>
      <td><button class="btn" onclick="rm(${{idx}})">Remove</button></td>`;
    tbody.appendChild(tr);
  }});
  recalc();
}}
async function rm(i){{
  await fetch('/loans/compare/remove', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{index:i}})}});
  load();
}}
load();
</script>
</body></html>
""")

@router.get("/dsr/from-ctos")
async def dsr_from_ctos(consent_id: str):
    import http.client, json, os
    try:
        conn = http.client.HTTPConnection("127.0.0.1", int(os.getenv("PORT","5000")), timeout=2)
        conn.request("GET", f"/ctos/metrics/{consent_id}")
        r = conn.getresponse()
        if r.status == 200:
            meta = json.loads(r.read().decode())
            return meta
    except Exception:
        pass
    return {"dsr": None, "dsrc": None, "commitments": None, "monthly_income": None}
