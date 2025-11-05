from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from starlette.templating import _TemplateResponse
import os

router = APIRouter(tags=["preview"])

def _env(k: str, default: str = "") -> str:
    return os.getenv(k, default)

@router.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/preview", status_code=302)

@router.get("/preview", include_in_schema=False)
def preview_hub(request: Request) -> _TemplateResponse:
    """
    预览总览页：集中入口 + 同源 iframe 预览（若被拦截则显示跳转按钮）
    """
    data = {
        "company": _env("COMPANY_NAME", "INFINITE GZ SDN. BHD."),
        "portal_key": _env("PORTAL_KEY", ""),
        "admin_key": _env("ADMIN_KEY", ""),
        "env": _env("ENV", "prod"),
        "pages": [
            {"name": "Portal", "url": "/portal"},
            {"name": "Loans Intelligence", "url": "/loans/page"},
            {"name": "Compare", "url": "/loans/compare/page"},
            {"name": "Top-3 Cards", "url": "/loans/top3/cards"},
            {"name": "CTOS Form (Gated)", "url": f"/ctos/page?key={_env('PORTAL_KEY','')}"},
            {"name": "Docs · EN PDF", "url": "/docs/official/CREDITPILOT_企业报告_EN.pdf"},
            {"name": "Docs · CN PDF", "url": "/docs/official/CREDITPILOT_企业报告_CN.pdf"},
        ],
    }
    return request.app.state.templates.TemplateResponse(
        "preview_hub.html",
        {"request": request, **data}
    )
