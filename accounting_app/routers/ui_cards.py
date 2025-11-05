# accounting_app/routers/ui_cards.py
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ui", tags=["UI Demo"])

@router.get("/cards", response_class=HTMLResponse)
def cards(step: int = Query(1, ge=1, le=3), lang: str = "zh"):
    label = {
        "zh": ["上传账单", "收据匹配", "月结报告"],
        "en": ["Upload Statements", "Receipt Matching", "Monthly Report"]
    }.get(lang, ["Step1","Step2","Step3"])
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>Cards Funnel</title>
<style>
:root {{ --primary:#FF007F; --bg:#1a1323; --card:#322446; --text:#fff; --muted:#999; --line:#888; }}
body {{ margin:0; font-family:ui-sans-serif; background:linear-gradient(180deg,#1a1323,#0f0a14); color:var(--text); }}
.container {{ max-width:1000px; margin:40px auto; padding:0 16px; display:grid; grid-template-columns:220px 1fr 240px; gap:12px; }}
.panel {{ background:linear-gradient(180deg,#322446,#281a3a); border-radius:14px; padding:16px; border:1px solid #3a2a4f; }}
.btn {{ background:var(--primary); border:none; color:#fff; padding:8px 12px; border-radius:12px; cursor:pointer; text-decoration:none; display:inline-block; }}
.step {{ padding:10px 12px; border-radius:10px; margin-bottom:8px; border:1px solid #403150; }}
.step.active {{ border-color:#FF007F; box-shadow:0 0 0 2px #ff007f44 inset; }}
</style></head>
<body>
<div class="container">
  <div class="panel">
    <div class="step {'active' if step==1 else ''}">1. {label[0]}</div>
    <div class="step {'active' if step==2 else ''}">2. {label[1]}</div>
    <div class="step {'active' if step==3 else ''}">3. {label[2]}</div>
    <div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">
      <a class="btn" href="/ui/cards?step={max(1,step-1)}&lang={lang}">上一步</a>
      <a class="btn" href="/ui/cards?step={min(3,step+1)}&lang={lang}">下一步</a>
    </div>
  </div>
  <div class="panel">
    <h3>Work Area · Step {step}</h3>
    <p style="opacity:.85">这里展示与该步骤相关的主要操作入口（上传、匹配、导出）。</p>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
      <a class="btn" href="/portal">上传账单</a>
      <a class="btn" href="/portal/history">收据/记录</a>
      <a class="btn" href="/files/result/txt/DEMO">导出 TXT</a>
    </div>
  </div>
  <div class="panel">
    <h3>收益 · Value</h3>
    <ul>
      <li>节省时间 67%</li>
      <li>数据准确 100%</li>
      <li>一键导出（PDF/Excel/CSV）</li>
    </ul>
  </div>
</div>
</body></html>
""")
