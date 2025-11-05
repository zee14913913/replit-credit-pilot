import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from accounting_app.routers import health, files

APP_NAME = os.getenv("APP_NAME", "Accounting API")
ENV = os.getenv("ENV", "dev")
CORS_ALLOW = os.getenv("CORS_ALLOW", "*")

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

app.include_router(health.router)
app.include_router(files.router)

@app.get("/")
def root():
    return {"app": APP_NAME, "env": ENV, "docs": (ENV != "prod")}
