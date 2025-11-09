import os
import time
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.templating import Jinja2Templates

from accounting_app.routers import health, files, public, history, stats, loans_updates, loans_business, ctos, ui_cards, loans_ranking, loans_extras, preview, credit_cards, savings, statements, invoices, admin_seed, loans_detailed
from accounting_app.core.middleware import SecurityAndLogMiddleware, SimpleRateLimitMiddleware
from accounting_app.core.logger import info
from accounting_app.core.maintenance import start_local_cleanup_thread

from accounting_app.db import Base, engine

APP_NAME = os.getenv("APP_NAME", "Accounting API")
ENV = os.getenv("ENV", "dev")  # dev / prod
CORS_ALLOW = os.getenv("CORS_ALLOW", "*")

app = FastAPI(
    title=APP_NAME,
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

# 数据库表初始化（启动时自动创建新表）
Base.metadata.create_all(bind=engine)

# Jinja2 Templates for preview hub
app.state.templates = Jinja2Templates(directory="accounting_app/templates")

# 启动本地原件清理线程
start_local_cleanup_thread()

# 启动还款提醒调度器
from accounting_app.services.reminders import start_scheduler
scheduler = start_scheduler()
info("Reminders scheduler started")

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

# ====== 静态文件 ======
app.mount("/static", StaticFiles(directory="accounting_app/static"), name="static")
app.mount("/docs", StaticFiles(directory="docs"), name="docs")

# ====== 路由注册 ======
app.include_router(preview.router)
app.include_router(health.router)
app.include_router(files.router)
app.include_router(public.router)
app.include_router(history.router)
app.include_router(stats.router)
app.include_router(loans_updates.router)
app.include_router(loans_detailed.router)
app.include_router(loans_business.router)
app.include_router(loans_ranking.router)
app.include_router(loans_extras.router)
app.include_router(ctos.router)
app.include_router(ui_cards.router)
app.include_router(credit_cards.router)
app.include_router(savings.router)
app.include_router(statements.router)
app.include_router(invoices.router)
app.include_router(admin_seed.router)

# ====== Sentry 错误追踪（可选）======
# 注释掉直到安装 sentry_sdk 或配置 SENTRY_DSN
# if os.getenv("SENTRY_DSN"):
#     import sentry_sdk
#     sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.05)

