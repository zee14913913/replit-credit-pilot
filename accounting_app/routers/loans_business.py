from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import math

router = APIRouter(prefix="/loans", tags=["loans"])
templates = Jinja2Templates(directory="accounting_app/templates")

class DsrReq(BaseModel):
    income: float
    commitments: float
    amount: float
    rate: float
    tenure_years: int

@router.post("/dsr/calc")
def dsr_calc(payload: DsrReq):
    n = payload.tenure_years*12
    r = (payload.rate/100)/12
    if r<=0:
        monthly = payload.amount / max(n,1)
    else:
        monthly = payload.amount * (r*(1+r)**n) / ((1+r)**n - 1)
    dsr = (payload.commitments + monthly) / max(payload.income,1) * 100
    status = "PASS" if dsr<60 else ("BORDERLINE" if dsr<70 else "HIGH")
    return {"monthly_payment": round(monthly,2), "dsr_percent": round(dsr,2), "status": status}

_compare: list[dict] = []

@router.post("/compare/add")
def compare_add(item: dict):
    if item and item not in _compare:
        _compare.append({"source": item.get("source",""), "product": item.get("product","")})
    return {"len": len(_compare)}

@router.get("/compare/json")
def compare_json():
    return {"items": _compare}

@router.get("/compare/list")
def compare_list():
    return _compare

@router.post("/compare/remove")
def compare_remove(item: dict):
    global _compare
    before = len(_compare)
    _compare = [x for x in _compare if not (x.get("source")==item.get("source") and x.get("product")==item.get("product"))]
    return {"removed": before - len(_compare), "len": len(_compare)}

@router.post("/compare/clear")
def compare_clear():
    _compare.clear()
    return {"len": 0}

@router.get("/compare/page", response_class=HTMLResponse)
def compare_page(request: Request):
    return templates.TemplateResponse("compare.html", {"request": request, "env": "prod"})

@router.get("/page", response_class=HTMLResponse)
def loans_page(request: Request):
    return templates.TemplateResponse("loans_page.html", {"request": request, "env": "prod"})
