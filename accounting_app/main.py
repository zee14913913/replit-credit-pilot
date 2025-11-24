"""
FastAPI Main Application
银行贷款合规会计系统 - 主入口
"""
import os
from fastapi import FastAPI, Depends, Request, HTTPException, status, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    # bank_import_v2,  # Phase 1-5: 新版上传接口 - 文件不存在，已注释
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
    metrics,  # Phase 1-10: 分银行指标监控
    sftp_sync,  # SFTP ERP自动同步系统
    ai_assistant,  # AI智能助手（Savings页面集成）
    ai_predict,  # AI预测分析模块（AI V3 扩展）
    income_documents,  # 收入证明文件管理系统
    loans,  # Phase B: 贷款资格评估模块（DSR/DSRC Integration）
    loan_products,  # Phase C: 多贷款产品模拟（等额本息/等额本金）
    business_loans,  # Phase D: 企业贷款评估（基于DSCR + Modern Risk Engine）
    loan_reports,  # PHASE 5: 贷款报告生成系统（HTML/PDF）
    loans_quick,  # PHASE 8.1: Quick Estimate API（Income Only / Income+Commitments）
    loans_ai,  # PHASE 8.2: AI & Product Matching（Product Recommendations + AI Advisor）
    loans_full_auto,  # PHASE 8.3: Full Automated Mode（File Upload + Auto Enrichment）
    loan_products_catalog,  # PHASE 9: Loan Products Catalog（产品目录统一API）
    pending_files  # Phase 1-11: 文件上传确认系统
)

# 注册路由
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(bank_import.router, prefix="/api/import", tags=["Bank Import"])
# app.include_router(bank_import_v2.router, tags=["Bank Import V2"])  # Phase 1-5: 文件不存在，已注释
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
app.include_router(sftp_sync.router, tags=["SFTP Sync"])  # SFTP ERP自动同步系统
app.include_router(ai_assistant.router, tags=["AI Assistant"])  # AI智能助手（Savings页面集成）
app.include_router(ai_predict.router, tags=["AI Predict"])  # AI预测分析（AI V3 扩展 - 不修改现有ai_assistant）
app.include_router(income_documents.router, tags=["Income Documents"])  # 收入证明文件管理系统
app.include_router(loans.router, tags=["Loans"])  # Phase B: 贷款资格评估（DSR/DSRC Integration）
app.include_router(loan_products.router, tags=["Loan Products"])  # Phase C: 多贷款产品模拟（等额本息/等额本金）
app.include_router(business_loans.router, tags=["Business Loans"])  # Phase D: Modern/SME引擎（基于DTI/FOIR/CCRIS/BRR/DSCR）
app.include_router(loan_reports.router, tags=["Loan Reports"])  # PHASE 5: 贷款报告生成系统（HTML/PDF）
app.include_router(loans_quick.router, tags=["Loans Quick Estimate"])  # PHASE 8.1: Quick Estimate API
app.include_router(loans_ai.router, tags=["Loans AI"])  # PHASE 8.2: AI & Product Matching（Product Recommendations + AI Advisor）
app.include_router(loans_full_auto.router, tags=["Loans Full Auto"])  # PHASE 8.3: Full Automated Mode（File Upload + Auto Enrichment）
app.include_router(loan_products_catalog.router, tags=["Loan Products Catalog"])  # PHASE 9: Loan Products Catalog（产品目录统一API）
app.include_router(pending_files.router, tags=["Pending Files"])  # Phase 1-11: 文件上传确认系统


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
    
    # 启动SFTP后台调度器（每10分钟自动同步）
    try:
        from .services.sftp.scheduler import start_global_scheduler
        start_global_scheduler(company_id=1, sync_interval_minutes=10)
        print("✅ SFTP自动同步调度器已启动（每10分钟同步一次）")
    except Exception as e:
        print(f"⚠️ SFTP调度器启动失败: {e}")
    
    print("✅ 财务会计系统启动成功！")
    print("📊 API文档: http://localhost:8000/docs")


# 关闭事件：停止SFTP调度器
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 正在关闭财务会计系统...")
    
    # 停止SFTP后台调度器
    try:
        from .services.sftp.scheduler import stop_global_scheduler
        stop_global_scheduler()
        print("✅ SFTP自动同步调度器已停止")
    except Exception as e:
        print(f"⚠️ SFTP调度器停止失败: {e}")
    
    print("✅ 系统已安全关闭")


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
        db.execute(text("SELECT 1"))
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


# ========================================
# 🆕 新增API端点（用于MiniMax前端集成）
# ========================================

# SQLite数据库连接辅助函数（用于访问Flask的客户数据）
def get_sqlite_connection():
    """获取SQLite数据库连接"""
    import sqlite3
    db_path = "db/smart_loan_manager.db"
    return sqlite3.connect(db_path)


@app.get("/api/companies")
async def get_companies_list(
    skip: int = 0,
    limit: int = 100
):
    """
    GET /api/companies - 返回公司客户列表
    
    查询参数:
    - skip: 分页偏移量（默认0）
    - limit: 每页数量（默认100）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "客户姓名",
                "email": "email@example.com",
                "phone": "0123456789",
                "customer_code": "Be_rich_CJY",
                "monthly_income": 15000.0,
                "created_at": "2025-11-01T00:00:00"
            }
        ],
        "total": 8,
        "skip": 0,
        "limit": 100
    }
    """
    try:
        # 使用SQLite数据库（Flask应用的数据库）
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # 查询总数
        cursor.execute("SELECT COUNT(*) FROM customers")
        total = cursor.fetchone()[0]
        
        # 查询客户列表
        query = """
            SELECT 
                id,
                name,
                email,
                phone,
                customer_code,
                monthly_income,
                created_at,
                personal_account_name,
                personal_account_number,
                company_account_name,
                company_account_number,
                tag_desc
            FROM customers
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (limit, skip))
        customers = []
        
        for row in cursor.fetchall():
            customers.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "customer_code": row[4],
                "monthly_income": row[5],
                "created_at": row[6],
                "personal_account_name": row[7],
                "personal_account_number": row[8],
                "company_account_name": row[9],
                "company_account_number": row[10],
                "tag_desc": row[11]
            })
        
        conn.close()
        
        return {
            "success": True,
            "data": customers,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch companies: {str(e)}"
        )


@app.get("/api/bank-statements")
async def get_bank_statements(
    customer_id: int = None,
    bank_name: str = None,
    statement_month: str = None,
    skip: int = 0,
    limit: int = 100
):
    """
    GET /api/bank-statements - 返回银行对账单列表
    
    查询参数:
    - customer_id: 客户ID（可选）
    - bank_name: 银行名称（可选）
    - statement_month: 账单月份，格式 YYYY-MM（可选）
    - skip: 分页偏移量（默认0）
    - limit: 每页数量（默认100）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "customer_id": 1,
                "bank_name": "AMBANK",
                "statement_month": "2025-05",
                "period_start_date": "2025-05-01",
                "period_end_date": "2025-05-31",
                "previous_balance_total": 15000.50,
                "closing_balance_total": 18500.75,
                "owner_balance": 12000.00,
                "gz_balance": 6500.75,
                "card_count": 3,
                "transaction_count": 45,
                "validation_score": 0.98,
                "is_confirmed": 1,
                "created_at": "2025-11-01T00:00:00"
            }
        ],
        "total": 281,
        "filters": {
            "customer_id": 1,
            "bank_name": "AMBANK",
            "statement_month": "2025-05"
        }
    }
    """
    try:
        # 使用SQLite数据库（Flask应用的数据库）
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if customer_id is not None:
            where_clauses.append("customer_id = ?")
            params.append(customer_id)
        
        if bank_name:
            where_clauses.append("bank_name = ?")
            params.append(bank_name)
        
        if statement_month:
            where_clauses.append("statement_month = ?")
            params.append(statement_month)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_query = f"SELECT COUNT(*) FROM monthly_statements WHERE {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 查询账单列表
        query = f"""
            SELECT 
                id,
                customer_id,
                bank_name,
                statement_month,
                period_start_date,
                period_end_date,
                previous_balance_total,
                closing_balance_total,
                owner_balance,
                gz_balance,
                owner_expenses,
                owner_payments,
                gz_expenses,
                gz_payments,
                file_paths,
                card_count,
                transaction_count,
                validation_score,
                is_confirmed,
                inconsistencies,
                created_at,
                updated_at
            FROM monthly_statements
            WHERE {where_sql}
            ORDER BY statement_month DESC, bank_name ASC
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, skip])
        cursor.execute(query, params)
        statements = []
        
        for row in cursor.fetchall():
            statements.append({
                "id": row[0],
                "customer_id": row[1],
                "bank_name": row[2],
                "statement_month": row[3],
                "period_start_date": row[4],
                "period_end_date": row[5],
                "previous_balance_total": row[6],
                "closing_balance_total": row[7],
                "owner_balance": row[8],
                "gz_balance": row[9],
                "owner_expenses": row[10],
                "owner_payments": row[11],
                "gz_expenses": row[12],
                "gz_payments": row[13],
                "file_paths": row[14],
                "card_count": row[15],
                "transaction_count": row[16],
                "validation_score": row[17],
                "is_confirmed": bool(row[18]),
                "inconsistencies": row[19],
                "created_at": row[20],
                "updated_at": row[21]
            })
        
        conn.close()
        
        return {
            "success": True,
            "data": statements,
            "total": total,
            "filters": {
                "customer_id": customer_id,
                "bank_name": bank_name,
                "statement_month": statement_month
            },
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bank statements: {str(e)}"
        )


@app.post("/api/bill/upload")
async def upload_bill(
    file: UploadFile = File(...),
    customer_id: int = Form(...)
):
    """
    POST /api/bill/upload - 上传账单文件
    
    请求参数（Form Data）:
    - file: 账单文件（PDF、Excel、CSV）
    - customer_id: 客户ID
    
    返回格式:
    {
        "success": true,
        "message": "Bill uploaded successfully",
        "file_path": "/uploads/20251123_123456_statement.pdf",
        "filename": "20251123_123456_statement.pdf",
        "customer_id": 1,
        "file_size": 245678
    }
    """
    from datetime import datetime
    import os
    
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail="No file provided"
            )
        
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="Customer ID is required"
            )
        
        # 验证客户是否存在（使用SQLite）
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
        customer_check = cursor.fetchone()
        conn.close()
        
        if not customer_check:
            raise HTTPException(
                status_code=404,
                detail=f"Customer with ID {customer_id} not found"
            )
        
        # 生成文件名和保存路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{file.filename}"
        
        # 创建上传目录
        upload_dir = os.path.join("static", "uploads", f"customer_{customer_id}")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, safe_filename)
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_size = len(content)
        
        return {
            "success": True,
            "message": "Bill uploaded successfully",
            "file_path": f"/{file_path}",
            "filename": safe_filename,
            "customer_id": customer_id,
            "file_size": file_size,
            "upload_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload bill: {str(e)}"
        )


@app.get("/api/bill/ocr-status")
async def get_bill_ocr_status(
    file_id: str = None
):
    """
    GET /api/bill/ocr-status - 获取账单OCR处理状态
    
    查询参数:
    - file_id: 文件ID（可选）
    
    返回格式（无file_id时）:
    {
        "success": true,
        "message": "OCR status endpoint ready",
        "status": "ready",
        "supported_formats": ["PDF", "JPG", "PNG", "Excel", "CSV"],
        "ocr_engines": ["Google Document AI", "Tesseract OCR"]
    }
    
    返回格式（有file_id时）:
    {
        "success": true,
        "file_id": "20251123_123456_statement.pdf",
        "status": "completed",
        "progress": 100,
        "extracted_fields": {
            "bank_name": "AMBANK",
            "statement_date": "2025-05-31",
            "total_amount": 15000.50,
            "transaction_count": 45
        },
        "processing_time": "2.5s",
        "ocr_engine": "Google Document AI",
        "accuracy_score": 0.98
    }
    """
    try:
        if not file_id:
            # 返回OCR系统状态信息
            return {
                "success": True,
                "message": "OCR status endpoint ready",
                "status": "ready",
                "supported_formats": ["PDF", "JPG", "PNG", "Excel", "CSV"],
                "ocr_engines": [
                    "Google Document AI (Primary)",
                    "Tesseract OCR (Fallback)",
                    "pdfplumber (Bank-Specific)"
                ],
                "supported_banks": [
                    "AMBANK", "AMBANK_ISLAMIC", "UOB", "HONG_LEONG",
                    "OCBC", "HSBC", "STANDARD_CHARTERED", "MAYBANK",
                    "AFFIN_BANK", "CIMB", "ALLIANCE_BANK", "PUBLIC_BANK",
                    "RHB_BANK"
                ],
                "extracted_fields": [
                    "bank_name", "customer_name", "ic_no", "card_type",
                    "card_no", "credit_limit", "statement_date",
                    "payment_due_date", "full_due_amount", "minimum_payment",
                    "previous_balance", "transaction_date", "description",
                    "amount_CR", "amount_DR", "earned_point"
                ]
            }
        
        # 如果提供了file_id，查询具体文件的OCR状态（使用SQLite）
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id,
                file_path,
                upload_status,
                validation_score,
                created_at
            FROM statements
            WHERE file_path LIKE ?
            LIMIT 1
        """
        
        cursor.execute(query, (f"%{file_id}%",))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {
                "success": False,
                "message": f"File '{file_id}' not found in processing queue",
                "file_id": file_id,
                "status": "not_found"
            }
        
        # 解析处理状态
        upload_status = result[2] or "pending"
        validation_score = result[3] or 0.0
        
        status_mapping = {
            "pending": ("processing", 25),
            "processing": ("processing", 50),
            "completed": ("completed", 100),
            "error": ("failed", 0)
        }
        
        status, progress = status_mapping.get(upload_status, ("unknown", 0))
        
        return {
            "success": True,
            "file_id": file_id,
            "status": status,
            "progress": progress,
            "accuracy_score": validation_score,
            "ocr_engine": "Google Document AI",
            "created_at": result[4],
            "message": f"OCR processing {status}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OCR status: {str(e)}"
        )
