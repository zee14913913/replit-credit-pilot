import os
import time
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from accounting_app.routers import health, files, public, history, stats
from accounting_app.core.middleware import SecurityAndLogMiddleware, SimpleRateLimitMiddleware
from accounting_app.core.logger import info
from accounting_app.core.maintenance import start_local_cleanup_thread

APP_NAME = os.getenv("APP_NAME", "Accounting API")
ENV = os.getenv("ENV", "dev")  # dev / prod
CORS_ALLOW = os.getenv("CORS_ALLOW", "*")

app = FastAPI(
    title=APP_NAME,
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

# 启动本地原件清理线程
start_local_cleanup_thread()

# ====== 安全与跨域 ======
origins = [o.strip() for o in CORS_ALLOW.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 新中间件：安全头 + 日志 + 限流
app.add_middleware(SecurityAndLogMiddleware, env=ENV)
app.add_middleware(SimpleRateLimitMiddleware)

# ====== 路由注册 ======
app.include_router(health.router)
app.include_router(files.router)
app.include_router(public.router)
app.include_router(history.router)
app.include_router(stats.router)

# ====== Sentry 错误追踪（可选）======
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.05)

# ====== 根路由 ======
@app.get("/")
def root():
    return {"app": APP_NAME, "env": ENV, "docs": (ENV != "prod")}
