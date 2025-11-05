import os, pathlib
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from accounting_app.services import ctos_client as C

router = APIRouter(prefix="/ctos", tags=["ctos"])
templates = Jinja2Templates(directory="accounting_app/templates")

def _gate(request: Request):
    need = os.getenv("PORTAL_KEY")
    if not need:
        return
    if request.query_params.get("key") != need:
        raise HTTPException(404, "Not Found")

def _ak(request: Request):
    need = os.getenv("ADMIN_KEY")
    if not need:
        raise HTTPException(401,"ADMIN_KEY missing")
    if request.query_params.get("ak") != need:
        raise HTTPException(401,"unauthorized")

@router.get("/page", response_class=HTMLResponse)
def ctos_page(request: Request):
    _gate(request)
    return templates.TemplateResponse("ctos_form.html", {"request": request, "env": os.getenv("ENV","prod"), "key": os.getenv("PORTAL_KEY"), "ak": os.getenv("ADMIN_KEY")})

@router.post("/submit")
async def ctos_submit(request: Request,
                      name: str = Form(...),
                      idnum: str = Form(...),
                      email: str = Form(...),
                      phone: str = Form(...),
                      ctype: str = Form(...),
                      doc: UploadFile = File(...)):
    _gate(request)
    base = pathlib.Path(os.getenv("LOCAL_FILES_DIR","/home/runner/files"))
    base.mkdir(parents=True, exist_ok=True)
    ext = pathlib.Path(doc.filename).suffix.lower()
    if ext not in [".pdf",".jpg",".jpeg",".png"]:
        raise HTTPException(415,"Only PDF/JPG/PNG")
    dest = base / f"ctos_{idnum.replace('/','_')}{ext}"
    with open(dest,"wb") as f:
        f.write(await doc.read())
    jid = C.enqueue(ctype, name, idnum, email, phone, str(dest))
    return {"ok": True, "job_id": jid, "next": "/loans/page"}

@router.get("/admin", response_class=HTMLResponse)
def admin_list(request: Request):
    _gate(request); _ak(request)
    rows = C.list_jobs()
    html = ["<div class='card'><h3>CTOS 队列</h3><table class='table'><thead><tr><th>ID</th><th>Type</th><th>Doc</th><th>Status</th><th>Time</th></tr></thead><tbody>"]
    for r in rows:
        html.append(f"<tr><td>{r['id']}</td><td>{r['ctype']}</td><td>{r['doc_path']}</td><td>{r['status']}</td><td>{r['created_at']}</td></tr>")
    html.append("</tbody></table></div>")
    return HTMLResponse(content=f"""<!doctype html><html><head><link rel="stylesheet" href="/static/css/brand.css"/></head>
<body><div class="container">{''.join(html)}</div></body></html>""")
