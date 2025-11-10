"""
FastAPI Main Application
银行贷款合规会计系统 - 主入口
"""
import os
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from sqlalchemy.orm import Session

from .db import get_db, init_database, execute_sql_file
from . import models

# 配置模板目录
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# 创建FastAPI应用（🔒 禁用默认公开文档，改为需要登录）
app = FastAPI(
    title="Loan-Ready Accounting System",
    description="银行贷款合规会计系统 - 将银行月结单转换为会计分录，生成银行贷款所需的财务报表",
    version="1.0.0",
    docs_url=None,  # 禁用默认 /docs
    redoc_url=None  # 禁用默认 /redoc
)

# CORS配置（允许Flask系统调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://0.0.0.0:5000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由模块
from .routes import (
    bank_import,
    bank_import_v2,  # Phase 1-5: 新版上传接口
    bank_statements,  # 银行月结单操作：验证、入账、设为主对账单
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
    pdf_reports,
    exceptions,
    posting_rules,
    export_templates,
    file_index,
    audit_logs,
    auth,  # Phase 2-1: 认证与RBAC系统
    api_key_management,  # Phase 2-2 Task 5: API密钥管理
    notifications,  # 通知系统
    unified_files,  # 统一文件管理API
    self_test,  # 自测接口
    parsers,  # Phase 1-10: 解析器注册表
    metrics  # Phase 1-10: 分银行指标监控
)

# 注册路由
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(bank_import.router, prefix="/api/import", tags=["Bank Import"])
app.include_router(bank_import_v2.router, tags=["Bank Import V2"])  # Phase 1-5: 集成raw_documents保护
app.include_router(bank_statements.router, tags=["Bank Statements"])  # 银行月结单操作
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
app.include_router(exceptions.router, prefix="/api", tags=["Exception Center"])
app.include_router(posting_rules.router, prefix="/api", tags=["Auto Posting Rules"])
app.include_router(export_templates.router, prefix="/api", tags=["Export Templates"])
app.include_router(file_index.router, tags=["File Index"])  # Phase 1-3: 统一文件索引
app.include_router(audit_logs.router, tags=["Audit Logs"])  # Phase 1-4: 审计日志系统
app.include_router(auth.router, tags=["Authentication"])  # Phase 2-1: 认证与RBAC系统
app.include_router(api_key_management.router, tags=["API Key Management"])  # Phase 2-2 Task 5: API密钥管理
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])  # 通知系统
app.include_router(unified_files.router, tags=["Unified File Management"])  # 统一文件管理（Flask+FastAPI双引擎）
app.include_router(self_test.router, tags=["Self Test"])  # 自测接口（验收标准）
app.include_router(parsers.router, tags=["Parser Registry"])  # Phase 1-10: 解析器注册表（支持的银行列表）
app.include_router(metrics.router, tags=["Metrics"])  # Phase 1-10: 分银行指标监控


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
    
    # 执行规则引擎种子数据（仅在首次启动时）
    seed_file_path = os.path.join(os.path.dirname(__file__), 'seed_posting_rules.sql')
    if os.path.exists(seed_file_path):
        try:
            execute_sql_file(seed_file_path)
            print("✅ 规则引擎种子数据已加载")
        except Exception as e:
            print(f"⚠️ 规则种子数据加载失败: {e}")
    
    # 执行导出模板种子数据
    template_seed_path = os.path.join(os.path.dirname(__file__), 'seed_export_templates.sql')
    if os.path.exists(template_seed_path):
        try:
            execute_sql_file(template_seed_path)
            print("✅ 导出模板种子数据已加载")
        except Exception as e:
            print(f"⚠️ 导出模板种子数据加载失败: {e}")
    
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

# 🔒 需要登录的API文档（Swagger UI）
@app.get("/docs", include_in_schema=False)
async def get_documentation(request: Request, db: Session = Depends(get_db)):
    """
    Swagger UI 文档（需要登录且验证有效）
    调用/api/auth/me验证token的有效性
    """
    import requests as http_requests
    
    # 1. 检查认证凭据是否存在
    auth_header = request.headers.get("Authorization")
    session_cookie = request.cookies.get("session_token")
    
    if not auth_header and not session_cookie:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>需要登录</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                    }
                    .card {
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }
                    h1 { color: #333; }
                    p { color: #666; }
                    a {
                        display: inline-block;
                        margin-top: 1rem;
                        padding: 10px 20px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }
                    a:hover { background: #764ba2; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>🔒 需要登录</h1>
                    <p>API文档仅限登录用户访问</p>
                    <p>请先登录后再访问此页面</p>
                    <a href="/api/auth/login">前往登录</a>
                </div>
            </body>
            </html>
            """,
            status_code=401
        )
    
    # 2. 验证token的有效性（调用/api/auth/me）
    try:
        token = auth_header.replace("Bearer ", "") if auth_header else session_cookie
        
        # 调用自己的/api/auth/me端点验证
        verify_response = http_requests.get(
            "http://localhost:8000/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if verify_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # 验证成功，显示Swagger UI
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Swagger UI"
        )
    
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>认证失败</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                    }}
                    .card {{
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }}
                    h1 {{ color: #333; }}
                    p {{ color: #666; }}
                    a {{
                        display: inline-block;
                        margin-top: 1rem;
                        padding: 10px 20px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }}
                    a:hover {{ background: #764ba2; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>❌ 认证失败</h1>
                    <p>您的登录凭据无效或已过期</p>
                    <p>请重新登录后再访问</p>
                    <a href="/api/auth/login">重新登录</a>
                </div>
            </body>
            </html>
            """,
            status_code=401
        )


# 🔒 需要登录的API文档（ReDoc）
@app.get("/redoc", include_in_schema=False)
async def get_redoc(request: Request, db: Session = Depends(get_db)):
    """
    ReDoc 文档（需要登录且验证有效）
    """
    import requests as http_requests
    
    # 1. 检查认证凭据是否存在
    auth_header = request.headers.get("Authorization")
    session_cookie = request.cookies.get("session_token")
    
    if not auth_header and not session_cookie:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>需要登录</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                    }
                    .card {
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }
                    h1 { color: #333; }
                    p { color: #666; }
                    a {
                        display: inline-block;
                        margin-top: 1rem;
                        padding: 10px 20px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }
                    a:hover { background: #764ba2; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>🔒 需要登录</h1>
                    <p>API文档仅限登录用户访问</p>
                    <p>请先登录后再访问此页面</p>
                    <a href="/api/auth/login">前往登录</a>
                </div>
            </body>
            </html>
            """,
            status_code=401
        )
    
    # 2. 验证token的有效性
    try:
        token = auth_header.replace("Bearer ", "") if auth_header else session_cookie
        
        # 调用自己的/api/auth/me端点验证
        verify_response = http_requests.get(
            "http://localhost:8000/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if verify_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # 验证成功，显示ReDoc
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - ReDoc"
        )
    
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>认证失败</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                    }}
                    .card {{
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }}
                    h1 {{ color: #333; }}
                    p {{ color: #666; }}
                    a {{
                        display: inline-block;
                        margin-top: 1rem;
                        padding: 10px 20px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }}
                    a:hover {{ background: #764ba2; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>❌ 认证失败</h1>
                    <p>您的登录凭据无效或已过期</p>
                    <p>请重新登录后再访问</p>
                    <a href="/api/auth/login">重新登录</a>
                </div>
            </body>
            </html>
            """,
            status_code=401
        )


# 前端管理界面
@app.get("/accounting", response_class=HTMLResponse)
async def accounting_dashboard(request: Request):
    """
    财务管理后台界面
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})
