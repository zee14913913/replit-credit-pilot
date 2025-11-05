import os
import time
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from accounting_app.routers import health, files, public
from accounting_app.alerts import record
from accounting_app.backup import start_daily

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

APP_NAME = os.getenv("APP_NAME", "Accounting API")
ENV = os.getenv("ENV", "dev")
CORS_ALLOW = os.getenv("CORS_ALLOW", "*")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp: Response = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        if ENV == "prod":
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return resp

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        t0 = time.time()
        resp = await call_next(request)
        dt = round((time.time() - t0) * 1000)
        logger.info(json.dumps({
            "method": request.method,
            "path": request.url.path,
            "status": resp.status_code,
            "ms": dt
        }))
        record(resp.status_code)
        return resp

app = FastAPI(
    title=APP_NAME,
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

origins = [o.strip() for o in CORS_ALLOW.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AccessLogMiddleware)

app.include_router(health.router)
app.include_router(files.router)
app.include_router(public.router)

@app.get("/")
def root():
    return {"app": APP_NAME, "env": ENV, "docs": (ENV != "prod")}

@app.on_event("startup")
async def startup():
    start_daily()
