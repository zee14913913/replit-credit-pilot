# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

## Recent Changes
**Latest modifications with dates:**

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