import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 路由
from accounting_app.routers import health, files
from accounting_app.routers import public  # /portal

APP_NAME = os.getenv("APP_NAME", "Accounting API")
ENV = os.getenv("ENV", "dev")  # dev / prod
CORS_ALLOW = os.getenv("CORS_ALLOW", "*")  # 多域逗号分隔

app = FastAPI(
    title=APP_NAME,
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

# CORS
origins = [o.strip() for o in CORS_ALLOW.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由挂载
app.include_router(health.router)
app.include_router(files.router)
app.include_router(public.router)  # /portal

@app.get("/")
def root():
    return {"app": APP_NAME, "env": ENV, "docs": (ENV != "prod")}
