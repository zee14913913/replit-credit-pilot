from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory="accounting_app/templates")

def _key_ok(request: Request):
    need = os.getenv("PORTAL_KEY")
    if not need:
        return True
    key = request.query_params.get("key")
    if key != need:
        raise HTTPException(404, "Not Found")
    return True

@router.get("/portal", response_class=HTMLResponse)
def portal_page(request: Request):
    key=os.getenv("PORTAL_KEY")
    return templates.TemplateResponse("portal.html", {
        "request": request, 
        "env": os.getenv("ENV","prod"), 
        "key": key,
        "portal_key": key,
        "admin_key": os.getenv("ADMIN_KEY")
    })

@router.get("/portal/history", response_class=HTMLResponse)
def history_page(request: Request):
    key=os.getenv("PORTAL_KEY")
    # Sample history data
    rows = [
        {"ts": "2025-11-07 14:00:00", "event": "Auto Harvest", "detail": "Successfully collected 12 products from banking websites"},
        {"ts": "2025-11-07 11:00:00", "event": "Rate Update", "detail": "Bank A: -0.05% | Bank B: +0.10%"},
        {"ts": "2025-11-06 11:00:00", "event": "Auto Harvest", "detail": "Successfully collected 12 products"}
    ]
    return templates.TemplateResponse("history.html", {"request": request, "env": os.getenv("ENV","prod"), "key": key, "rows": rows, "portal_key": key, "admin_key": os.getenv("ADMIN_KEY")})
