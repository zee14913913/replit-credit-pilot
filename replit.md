# Smart Credit & Loan Manager

## Recent Changes
- **Phase CLEAN: SME 360 Removal** (Nov 14, 2025) - 删除非核心Dashboard模块（❌ 已删除）：
  - **删除理由**: SME 360° Dashboard中看不中用，对核心贷款业务无实际价值
  - **删除文件**: templates/sme_360.html, static/css/sme_360.css, static/js/sme_360.js, accounting_app/routes/sme_360.py
  - **移除路由**: FastAPI router注册、Flask /sme-360/<company_id>路由
  - **保留核心**: Modern Loan Evaluate、Loan Products Catalog、CTOS Consent、Auto Enrichment、风控引擎全部保留
- **Phase 10: Customer 360° Loan Dashboard** (Nov 14, 2025) - 个人贷款画像总览系统（✅ 已完成）：
  - **创建customer_360.html**: Galaxy Theme 4面板布局（Credit Profile / Cashflow Insights / Loan Capabilities / Product Matches）
  - **创建customer_360.css（520行）**: 响应式Grid Layout、风险等级颜色映射（A/B/C/D/E）、Approval Odds SVG圆形进度条
  - **创建customer_360.js（365行）**: 完整前端引擎，包含4个render函数、Chart.js双图表、Loan Simulator、产品选择联动
  - **创建customer_360.py FastAPI router**: GET /api/customers/{customer_id}/loan-profile端点，整合Income/Spending/Risk/Products数据
  - **数据整合**: (1) file_index表JSON查询获取Income Documents，(2) transactions表聚合查询获取月度消费，(3) personal_loan_products表查询推荐产品
  - **风险算法**: calculate_risk_grade()基于DTI/FOIR/CCRIS，calculate_approval_odds()基于Risk Grade + Income
  - **贷款能力计算**: Max EMI（40% DTI限制）+ Max Loan Amount（PMT公式反算）
  - **4大面板功能**: Risk Badge动态颜色、Approval Odds圆形进度条、12月Cashflow/Spending Chart.js图表、Loan Simulator（实时EMI+DTI+FOIR计算）、Top 5产品推荐卡片
  - **路由注册**: FastAPI router注册 + Flask /customer-360/<customer_id>路由（RBAC保护）
- **Phase 9: Loan Products Catalog全面升级** (Nov 14, 2025) - 产品目录系统现代化重建（✅ Architect审查通过）：
  - **新建loan_products.html**: Galaxy Theme风格产品市场页面（搜索+筛选+Modal详情+Select for Evaluation按钮）
  - **新建loan_products_catalog.css（401行）+ loan_products_catalog.js（249行）**: 卡片瀑布流布局，支持Bank/Digital Bank/Fintech筛选，Lowest Rate/Highest Amount排序
  - **创建loan_products_catalog.py FastAPI router**: 统一产品API（GET /api/loan-products/all, /{product_id}, /filter）
  - **更新Flask /loan-products路由**: 调用FastAPI统一产品API，移除SQLite依赖，返回products_json给前端
  - **新增/api/loan-products/select端点**: Session管理selected_product_id，支持产品选择→跳转loan_evaluate功能
  - **创建loan_products_dashboard.html + CSS**: Loan Marketplace Dashboard（三个入口卡片：Personal Loans / SME Loans / Digital Bank Loans）
  - **产品数据归一化**: normalize_product()函数统一Personal + SME产品数据格式（interest_rate.min/max, max_loan_amount）
  - **router注册**: 添加loan_products_catalog router到accounting_app/main.py
  - **完整联动流程**: Loan Products → Select按钮 → Store session → Redirect to /loan-evaluate?product_id=xxx → 前端优先渲染
  - **Bug修复（3轮Architect审查）**: (1) 筛选逻辑重构为三步流程（搜索→类型过滤→排序），(2) Array.sort()克隆避免变异原数组，(3) 字段名统一为max_loan_amount和interest_rate.min/max（卡片+Modal）
- **Phase 8.4: Unified Result Renderer + Code Cleanup** (Nov 14, 2025) - 统一结果渲染系统和代码清理
- **Phase 8.3: Full Automated Mode补齐** (Nov 14, 2025) - 完整文件上传自动评估流程
- **Phase 8.2: Products + AI Advisor API补齐** (Nov 14, 2025) - 产品推荐和AI顾问后端路由
- **Phase 8.1: Modern Loan Evaluate三模式系统** (Nov 14, 2025) - 银行级贷款评估页面全面重建

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. It provides comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing). The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.
User language: Chinese (使用中文与我沟通).

## System Architecture

### UI/UX Decisions
The platform enforces a professional design using a **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders
The design system emphasizes clean layouts with bilingual support (English/Chinese).

**Navigation Structure**:
The main navigation features 7 core modules aligned with business workflow: DASHBOARD, CREDIT CARDS, SAVINGS, RECEIPTS, LOANS, REPORTS, and ADMIN. The **CREDIT CARDS** page is a central hub for uploading statements, managing suppliers, processing payments, and OCR receipts.

### Technical Implementations
The backend uses Flask with SQLite and a context manager for database interactions. Jinja2 handles server-side rendering, complemented by Bootstrap 5 and Bootstrap Icons for the UI. Plotly.js provides client-side data visualization, and PDF.js is used for client-side PDF-to-CSV conversion. A robust notification system provides real-time updates. The AI system uses a unified client architecture supporting multiple providers (Perplexity primary, OpenAI backup) with automatic failover and environment-based configuration.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF OCR, Excel), transaction categorization, savings tracking, dual verification.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization, cash flow prediction, anomaly detection, financial health scoring, and loan eligibility assessment.
- **AI Smart Assistant V3 (Enterprise Intelligence):** Advanced multi-provider AI system with real-time web search. Features floating chatbot UI, cross-module analysis, automated daily financial reports, system analytics, and comprehensive conversation history logging.
- **Income Document System:** Upload, OCR processing, and standardization of income proof documents with intelligent aggregation and confidence scoring.
- **Dual-Engine Loan Evaluation System (CREDITPILOT):** Production-ready dual-mode architecture supporting both legacy DSR/DSCR engines and modern Malaysian banking standards (DTI/FOIR/CCRIS/BRR). Implements comprehensive risk scoring (Personal: DTI/FOIR/CCRIS bucket, SME: BRR/DSCR/DSR/Industry/Cashflow Variance) with intelligent product matching across 12+ banks/Fintech providers. CTOS data serves as the exclusive debt commitment source.
- **Reporting & Export:** Professional Excel/CSV/PDF reports, automated monthly reports.
- **Workflow Automation:** Batch operations, rule engine for transaction matching.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), audit logging, data integrity validation.
- **User Experience:** Unified navigation, context-aware buttons, bilingual i18n, responsive design.
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR for JPG/PNG), Credit Card Ledger, Exception Center.
- **Multi-Channel Notifications:** In-app, email, and SMS.
- **Admin System:** User registration, secure login, evidence archiving with RBAC.
- **CTOS Consent System**: Integrates personal (e-signature + IC upload) and company (SSM upload + company stamp) CTOS consent, generating professional PDF reports.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and advisory.
- **Design Patterns:** Repository Pattern, Template Inheritance, Context Manager, Service Layer, Strategy Pattern (multi-provider AI).
- **Security:** Session secret key, file upload limits, SQL injection prevention, audit logging, API key management.
- **Data Accuracy:** Robust monthly ledger engine ensuring 100% accuracy via previous balance extraction and DR/CR classification.
- **Monthly Statement Architecture:** One monthly statement record per bank + month, aggregating 6 mandatory classification fields.
- **AI Architecture:** Unified client interface with automatic provider switching, graceful degradation, and environment-based configuration.
- **Dual-Engine Loan Architecture:** Legacy DSR/DSCR engines preserved alongside modern risk_engine. API layer supports mode-based routing with backward compatibility. Product matcher recommends 3-10 suitable banks based on risk grade. System uses CTOS commitment data exclusively.

### Security & Access Control
A production-ready Unified RBAC Implementation protects 32 functions. The `@require_admin_or_accountant` decorator supports Flask session-based RBAC and FastAPI token verification. Access levels include Admin (full access) and Accountant (full operational access), with Customer and Unauthenticated roles restricted.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`, `fastapi`, `uvicorn`
- **PDF Processing**: `pdfplumber`, `reportlab`, `pdf.js`
- **OCR**: `pytesseract`, `Pillow`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`, `openai`
- **Visualization**: `plotly.js`
- **UI Framework**: `bootstrap@5.3.0`, `bootstrap-icons@1.11.0`
- **Notification Services**: `sendgrid`, `twilio`, `py-vapid`, `pywebpush`

### External APIs & Integrations
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for interest rates.
- **SendGrid API**: Production email delivery system.
- **Twilio API**: SMS delivery.
- **Perplexity AI API**: Primary AI provider with real-time web search capabilities (Model: `sonar`).
- **OpenAI API**: Backup AI provider (gpt-4o-mini model) with automatic fallback.
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, AI assistant endpoints, and real-time APIs.

### Database
- **SQLite**: Primary file-based relational database (`db/smart_loan_manager.db`).
- **PostgreSQL**: Used for notifications and audit logs.

### File Storage
- A `FileStorageManager` handles standard path generation and directory management, typically `static/uploads/customers/{customer_code}/`.

### SFTP ERP Automation System
A production-ready SFTP synchronization system, implemented with a FastAPI backend (Port 8000) and Paramiko, automatically exports 7 types of financial data to SQL ACC ERP Edition via secure SFTP every 10 minutes.