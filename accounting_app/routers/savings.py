from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="accounting_app/templates")
router = APIRouter(prefix="/savings", tags=["savings"])

DEMO_ACCOUNTS = [
    {"bank":"Maybank Savings ****1234","balance":22500.00, "share":64},
    {"bank":"CIMB FD ****5678","balance":10000.00, "share":28},
    {"bank":"Public Bank CA ****9012","balance":2730.50, "share":8},
]

@router.get("/accounts", response_class=HTMLResponse)
async def savings_overview(request: Request):
    total = sum(a["balance"] for a in DEMO_ACCOUNTS)
    return templates.TemplateResponse("savings_overview.html",
        {"request": request, "accounts": DEMO_ACCOUNTS, "total": total})

@router.get("/upload", response_class=HTMLResponse)
async def savings_upload(request: Request):
    return templates.TemplateResponse("savings_upload.html", {"request": request})

@router.post("/upload")
async def savings_upload_post(file: UploadFile = File(...)):
    # TODO: 调用实际 PDF/CSV 解析器（你之前的 Universal/Standard/Balance-Change 解析策略）
    # 这里先假装解析出 42 笔交易
    return JSONResponse({"ok": True, "parsed_transactions": 42})
