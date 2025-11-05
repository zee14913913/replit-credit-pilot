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
        monthly = payload.amount / n
    else:
        monthly = payload.amount * (r*(1+r)**n) / ((1+r)**n - 1)
    dsr = (payload.commitments + monthly) / max(payload.income,1) * 100
    status = "PASS" if dsr<60 else ("BORDERLINE" if dsr<70 else "HIGH")
    return {"monthly_payment": round(monthly,2), "dsr_percent": round(dsr,2), "status": status}

_compare = []

@router.post("/compare/add")
def compare_add(item: dict):
    if item and item not in _compare:
        _compare.append(item)
    return {"len": len(_compare)}

@router.get("/compare/page", response_class=HTMLResponse)
def compare_page(request: Request):
    return templates.TemplateResponse("base.html", {
        "request": request,
        "title": "Compare Basket",
        "env": "prod",
        "key": None,
        "content": ""
    }, media_type="text/html", status_code=200)

@router.get("/page", response_class=HTMLResponse)
def loans_page(request: Request):
    return templates.TemplateResponse("loans_page.html", {"request": request, "env": "prod"})
