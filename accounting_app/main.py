"""
FastAPI Main Application
银行贷款合规会计系统 - 主入口
"""
import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .db import get_db, init_database, execute_sql_file
from . import models

# 配置模板目录
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# 创建FastAPI应用
app = FastAPI(
    title="Loan-Ready Accounting System",
    description="银行贷款合规会计系统 - 将银行月结单转换为会计分录，生成银行贷款所需的财务报表",
    version="1.0.0"
)

# CORS配置（允许Flask系统调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://0.0.0.0:5000",
        "*"  # 开发环境允许所有，生产环境要改
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由模块
from .routes import (
    bank_import,
    reports,
    invoices,
    companies,
    tasks_routes,
    files,
    smart_import,
    management_reports,
    csv_export,
    supplier_invoices,
    pos_reports,
    pdf_reports
)

# 注册路由
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(bank_import.router, prefix="/api/import", tags=["Bank Import"])
app.include_router(smart_import.router, prefix="/api/smart-import", tags=["Smart Import"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(tasks_routes.router, prefix="/api/tasks", tags=["Scheduled Tasks"])
app.include_router(files.router, prefix="/api/files", tags=["File Management"])
app.include_router(management_reports.router, prefix="/api", tags=["Management Reports"])
app.include_router(csv_export.router, prefix="/api", tags=["CSV Export"])
app.include_router(supplier_invoices.router, prefix="/api", tags=["Supplier Invoices"])
app.include_router(pos_reports.router, tags=["POS Reports"])
app.include_router(pdf_reports.router, tags=["PDF Reports"])


# 启动事件：初始化数据库
@app.on_event("startup")
async def startup_event():
    print("🚀 正在启动财务会计系统...")
    
    # 初始化数据库表
    init_database()
    
    # 执行初始化SQL（创建会计科目等）
    sql_file_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
    if os.path.exists(sql_file_path):
        try:
            execute_sql_file(sql_file_path)
            print("✅ 数据库初始化SQL已执行")
        except Exception as e:
            print(f"⚠️ SQL初始化失败: {e}")
    
    print("✅ 财务会计系统启动成功！")
    print("📊 API文档: http://localhost:8000/docs")


# 根路由
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>银行贷款合规会计系统</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 3rem;
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 1rem;
            }
            p {
                color: #666;
                line-height: 1.8;
            }
            .btn {
                display: inline-block;
                margin: 1rem 0.5rem;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .btn:hover {
                background: #764ba2;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .status {
                background: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                display: inline-block;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status">✅ System Online</div>
            <h1>🏦 银行贷款合规会计系统</h1>
            <p>
                <strong>核心功能：</strong>将客户的真实银行月结单自动转换为会计分录，
                生成符合银行审核标准的财务报表包。
            </p>
            <p>
                <strong>支持报表：</strong>
                Suppliers Aging | Customer Ledger | P&L | Balance Sheet | 
                Payroll | Tax Adjustments | 自动发票
            </p>
            <a href="/docs" class="btn">📚 API文档</a>
            <a href="/accounting" class="btn">💼 管理后台</a>
        </div>
    </body>
    </html>
    """


# 健康检查
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # 测试数据库连接
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Accounting system is running"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# 前端管理界面
@app.get("/accounting", response_class=HTMLResponse)
async def accounting_dashboard(request: Request):
    """
    财务管理后台界面
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})
