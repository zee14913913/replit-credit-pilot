# Smart Credit & Loan Manager

## 🎯 AI V3 Stable Baseline
**Version**: `AI_V3_BASELINE`  
**Date**: 2025-11-13  
**Status**: ✅ STABLE - All AI features tested and running in production

This marks the **stable foundation** for all future AI enhancements. No core AI functionality will be removed or redesigned. All new features will be built on top of this baseline.

**Baseline Documentation**: See `docs/AI_V3_STABLE_BASELINE.md` for complete technical details.

---

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

## Recent Changes
**Latest modifications with dates:**

### 2025-11-14: Income Document System Implementation ✅
- ✅ **收入证明文件管理系统**: 完整的客户收入验证文件上传与OCR处理
  - 新增FastAPI路由: `accounting_app/routes/income_documents.py`（2个端点：上传+查询）
  - 文件类型支持: Salary Slip, Tax Return, EPF Statement, Bank Inflow
  - OCR智能提取: 使用PDFParser + pytesseract自动提取收入金额
  - 数据存储: 复用`file_index`表（module='income'）+ `raw_documents`原件保护
  - 前端页面: `templates/income/upload.html` (上传) + `templates/income/index.html` (列表)
  - Flask路由集成: `/income`, `/income/upload`, `/api/customers/list`
  - 多语言OCR: 支持英文+简体中文（ocr_language='eng+chi_sim'）
  - 置信度评分: 自动评估OCR提取准确度（0.0-1.0）
  - 文件存储路径: `/accounting_data/companies/{company_id}/income_documents/{customer_id}/{YYYY}/{MM}/`
- ✅ **复用现有基础设施**: 
  - `RawDocumentService`: 原件封存（1:1保护，file_hash验证）
  - `UnifiedFileService`: 统一文件索引管理
  - `PDFParser`: 三阶段解析（文本PDF → OCR扫描件 → 人工处理）
  - `AccountingFileStorageManager`: 标准化路径生成
- ✅ **完全兼容AI V3 Baseline**: 不修改任何现有AI文件（ai_assistant.py、ai_predict.py）

### 2025-11-14: AI Predictive Analysis Module (AI V3 Expansion) ✅
- ✅ **AI预测分析模块**: 基于历史数据预测未来3个月财务趋势
  - 新增3个服务引擎: `PredictEngine`, `TrendEngine`, `HealthEngine`
  - 新增3个API端点: `/api/ai-assistant/predict`, `/api/ai-assistant/trends`, `/api/ai-assistant/health-score`
  - Dashboard新增AI智能预测分析卡片（第216-257行）
  - 前端JS模块: `static/js/ai_predict.js` 支持Chart.js可视化
  - 数据源: `monthly_statements` 表（不依赖未启用的analytics模块）
- ✅ **财务健康评分系统**: 0-100分多维度评分（信用利用率、还款能力、债务趋势、数据完整性）
- ✅ **AI洞察生成**: 自动生成50-120字的专业财务建议（使用V3统一AI客户端）
- ✅ **趋势图表**: 支出、还款、余额12个月趋势可视化（Chart.js）
- ✅ **完全兼容AI V3 Baseline**: 不修改现有ai_assistant.py、ai_client.py、AI日报预览区（第339-383行）

### 2025-11-13: AI Assistant V3 + SendGrid Complete Integration ✅
- ✅ **Perplexity AI Migration**: Upgraded from OpenAI to Perplexity AI with real-time web search capabilities
  - Created unified AI client (`accounting_app/utils/ai_client.py`) supporting both Perplexity and OpenAI
  - Implemented intelligent provider switching via `AI_PROVIDER` environment variable
  - Using Perplexity `sonar` model (127K context) for real-time financial data access
  - Cost-optimized: ~$0.015/month vs previous OpenAI costs
- ✅ **SendGrid Email System**: Production-ready email delivery fully configured
  - Verified sender: `info@infinite-gz.com`
  - Configured recipient: `info@infinite-gz.com`
  - HTML email templates with Hot Pink enterprise design
  - Automated daily delivery at 08:10
  - Status: Tested successfully (HTTP 202)
- ✅ **AI Daily Report Automation**: Complete end-to-end automation
  - 08:00: Perplexity AI generates financial health report
  - 08:10: SendGrid sends HTML email with professional formatting
  - Dashboard preview displays last 7 days of reports
- ✅ **Unified AI Architecture**: Single interface for multiple AI providers
  - Automatic fallback from Perplexity to OpenAI on errors
  - Environment-based provider selection
  - Consistent API across all AI features

### 2025-11-12: AI Assistant V2 Enterprise Upgrade Complete
- ✅ **Dashboard Integration**: Added AI daily report preview section in `templates/index.html` with auto-refresh functionality
- ✅ **API Endpoint**: Implemented `/api/ai-assistant/reports` in `accounting_app/routes/ai_assistant.py` returning last 7 days of reports
- ✅ **Email Notification System**: Created `accounting_app/tasks/email_notifier.py` with HTML email templates for daily report delivery
- ✅ **Scheduler Enhancement**: Updated `accounting_app/tasks/scheduler.py` and `app.py` to include email push task at 08:10 daily
- ✅ **Flask Proxy**: Added `/api/ai-assistant/<path>` proxy route in `app.py` for seamless Flask-FastAPI integration

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
The main navigation features 7 core modules aligned with business workflow:
1. **DASHBOARD**
2. **CREDIT CARDS** (unified management hub)
3. **SAVINGS**
4. **RECEIPTS** (redirects to CREDIT CARDS OCR)
5. **LOANS**
6. **REPORTS**
7. **ADMIN**

The **CREDIT CARDS** page is a central hub for:
- Uploading credit card statements (PDF/Excel with dual validation)
- Viewing customer lists
- Managing supplier invoices
- Processing customer payments
- **OCR Receipts**: Smart recognition for merchant swipe receipts with statistics, upload, and matching functionalities.

### Technical Implementations
The backend uses Flask with SQLite and a context manager for database interactions. Jinja2 handles server-side rendering, complemented by Bootstrap 5 and Bootstrap Icons for the UI. Plotly.js provides client-side data visualization. PDF.js is used for client-side PDF-to-CSV conversion. A robust notification system provides real-time updates via SendGrid (email) and Twilio (SMS). The AI system uses a unified client architecture (`accounting_app/utils/ai_client.py`) supporting multiple providers (Perplexity primary, OpenAI backup) with automatic failover and environment-based configuration.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF OCR, Excel), transaction categorization, savings tracking, dual verification for data accuracy.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization, cash flow prediction, anomaly detection, and financial health scoring.
- **AI Smart Assistant V3 (Enterprise Intelligence):** Advanced multi-provider AI system with real-time web search capabilities. Primary engine: Perplexity AI `sonar` model with automatic OpenAI fallback. Features floating chatbot UI (💬智能顾问) with real-time financial Q&A, cross-module analysis (Savings + Credit Card + Loans), automated daily financial reports (08:00 generation, 08:10 email delivery via SendGrid), system analytics, and comprehensive conversation history logging to `ai_logs` table. Accessible via `/api/ai-assistant/*` endpoints. Dashboard displays last 7 days of AI-generated reports with auto-refresh functionality.
- **Reporting & Export:** Professional Excel/CSV/PDF reports, automated monthly reports.
- **Workflow Automation:** Batch operations, rule engine for transaction matching.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), audit logging, data integrity validation.
- **User Experience:** Unified navigation, context-aware buttons, bilingual i18n (English/Chinese), responsive design.
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR for JPG/PNG), Credit Card Ledger, Exception Center.
- **Multi-Channel Notifications:** In-app, email (SendGrid), and SMS (Twilio).
- **Admin System:** User registration, secure login, evidence archiving with RBAC.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and advisory.
- **Design Patterns:** Repository Pattern, Template Inheritance, Context Manager, Service Layer, Strategy Pattern (multi-provider AI).
- **Security:** Session secret key, file upload limits, SQL injection prevention, audit logging, API key management via Replit Secrets.
- **Data Accuracy:** Robust monthly ledger engine ensuring 100% accuracy via previous balance extraction and DR/CR classification.
- **Monthly Statement Architecture:** One monthly statement record per bank + month, aggregating 6 mandatory classification fields.
- **OCR Receipts SQL:** Uses SQL column aliasing for UI-friendly naming without schema migrations.
- **AI Architecture:** Unified client interface with automatic provider switching, graceful degradation, and environment-based configuration for production/development flexibility.

### Security & Access Control
A production-ready Unified RBAC Implementation protects 32 functions across Core Business Pages, File Download, Statement & Reminder Management, and Customer & Card Creation. The `@require_admin_or_accountant` decorator supports Flask session-based RBAC and FastAPI token verification. Access levels include Admin (full access) and Accountant (full operational access), with Customer and Unauthenticated roles restricted. Security mitigations include ID enumeration prevention, blocked unauthorized mutations, financial data protection, and comprehensive audit trails.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`, `fastapi`, `uvicorn`
- **PDF Processing**: `pdfplumber`, `reportlab`, `pdf.js`
- **OCR**: `pytesseract`, `Pillow`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`, `openai` (used for both Perplexity and OpenAI via unified client)
- **Visualization**: `plotly.js`
- **UI Framework**: `bootstrap@5.3.0`, `bootstrap-icons@1.11.0`
- **Notification Services**: `sendgrid`, `twilio`, `py-vapid`, `pywebpush`
- **AI Providers**: Perplexity AI (primary), OpenAI (backup) via unified client interface

### External APIs & Integrations
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for interest rates.
- **SendGrid API**: Production email delivery system (verified and configured)
  - Verified sender: `info@infinite-gz.com`
  - Primary method for AI daily reports and system notifications
  - HTML templates with enterprise Hot Pink design
  - Daily automated delivery at 08:10
  - Environment variables: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`
- **Twilio API**: SMS delivery via Replit integration.
- **Perplexity AI API**: Primary AI provider with real-time web search capabilities
  - Model: `sonar` (127K context window)
  - Capabilities: Real-time financial data, market rates, currency exchange, bank policies
  - Cost: ~$0.015/month for daily reports
  - Environment variables: `PERPLEXITY_API_KEY`, `AI_PROVIDER=perplexity`
- **OpenAI API**: Backup AI provider (gpt-4o-mini model)
  - Automatic fallback when Perplexity unavailable
  - Managed via Replit integration (`AI_INTEGRATIONS_OPENAI_API_KEY`)
  - Used for general Q&A and chat functionality
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, AI assistant endpoints, and real-time APIs.

### Database
- **SQLite**: Primary file-based relational database (`db/smart_loan_manager.db`). Includes `ai_logs` table for AI assistant conversation history.
- **PostgreSQL**: Used for notifications and audit logs, including SFTP synchronization history.

### File Storage
- A `FileStorageManager` handles standard path generation and directory management, typically `static/uploads/customers/{customer_code}/`.

### SFTP ERP Automation System
A production-ready SFTP synchronization system, implemented with a FastAPI backend (Port 8000) and Paramiko, automatically exports 7 types of financial data to SQL ACC ERP Edition via secure SFTP every 10 minutes. It supports multi-company file organization and robust security features including SSH Host Key Verification, path security, and audit logging for all operations.