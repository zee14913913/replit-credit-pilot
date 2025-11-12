# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

## Recent Changes
**Latest modifications with dates:**

### 2025-11-12: AI Assistant V2 Enterprise Upgrade Complete
- ✅ **Dashboard Integration**: Added AI daily report preview section in `templates/index.html` with auto-refresh functionality
- ✅ **API Endpoint**: Implemented `/api/ai-assistant/reports` in `accounting_app/routes/ai_assistant.py` returning last 7 days of reports
- ✅ **Email Notification System**: Created `accounting_app/tasks/email_notifier.py` with HTML email templates for daily report delivery
- ✅ **Scheduler Enhancement**: Updated `accounting_app/tasks/scheduler.py` and `app.py` to include email push task at 08:10 daily
- ✅ **Flask Proxy**: Added `/api/ai-assistant/<path>` proxy route in `app.py` for seamless Flask-FastAPI integration
- ⚠️ **SMTP Configuration Required**: Email delivery requires SMTP credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`) or SendGrid API key

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
The backend uses Flask with SQLite and a context manager for database interactions. Jinja2 handles server-side rendering, complemented by Bootstrap 5 and Bootstrap Icons for the UI. Plotly.js provides client-side data visualization. PDF.js is used for client-side PDF-to-CSV conversion. A robust notification system provides real-time updates.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF OCR, Excel), transaction categorization, savings tracking, dual verification for data accuracy.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization, cash flow prediction, anomaly detection, and financial health scoring.
- **AI Smart Assistant (Savings Module):** Integrated ChatGPT-powered assistant using OpenAI gpt-4o-mini model. Features floating chatbot UI (💬智能顾问) with real-time financial Q&A, cross-module analysis (Savings + Credit Card + Loans), system analytics, and conversation history logging to `ai_logs` table. Accessible via `/api/ai-assistant/*` endpoints.
- **Reporting & Export:** Professional Excel/CSV/PDF reports, automated monthly reports.
- **Workflow Automation:** Batch operations, rule engine for transaction matching.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), audit logging, data integrity validation.
- **User Experience:** Unified navigation, context-aware buttons, bilingual i18n (English/Chinese), responsive design.
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR for JPG/PNG), Credit Card Ledger, Exception Center.
- **Multi-Channel Notifications:** In-app, email (SendGrid), and SMS (Twilio).
- **Admin System:** User registration, secure login, evidence archiving with RBAC.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and advisory.
- **Design Patterns:** Repository Pattern, Template Inheritance, Context Manager, Service Layer.
- **Security:** Session secret key, file upload limits, SQL injection prevention, audit logging.
- **Data Accuracy:** Robust monthly ledger engine ensuring 100% accuracy via previous balance extraction and DR/CR classification.
- **Monthly Statement Architecture:** One monthly statement record per bank + month, aggregating 6 mandatory classification fields.
- **OCR Receipts SQL:** Uses SQL column aliasing for UI-friendly naming without schema migrations.

### Security & Access Control
A production-ready Unified RBAC Implementation protects 32 functions across Core Business Pages, File Download, Statement & Reminder Management, and Customer & Card Creation. The `@require_admin_or_accountant` decorator supports Flask session-based RBAC and FastAPI token verification. Access levels include Admin (full access) and Accountant (full operational access), with Customer and Unauthenticated roles restricted. Security mitigations include ID enumeration prevention, blocked unauthorized mutations, financial data protection, and comprehensive audit trails.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`, `fastapi`, `uvicorn`
- **PDF Processing**: `pdfplumber`, `reportlab`, `pdf.js`
- **OCR**: `pytesseract`, `Pillow`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`
- **Visualization**: `plotly.js`
- **UI Framework**: `bootstrap@5.3.0`, `bootstrap-icons@1.11.0`
- **Notification Services**: `sendgrid`, `twilio`, `py-vapid`, `pywebpush`

### External APIs & Integrations
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for interest rates.
- **SendGrid API**: Email delivery.
- **Twilio API**: SMS delivery.
- **OpenAI API**: AI smart assistant integration using gpt-4o-mini model, with API key managed via Replit Secrets (`AI_INTEGRATIONS_OPENAI_API_KEY`).
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, AI assistant endpoints, and real-time APIs.
- **SMTP Configuration (Optional)**: For AI daily report email delivery, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` environment variables. Falls back to `ADMIN_PASSWORD` if `SMTP_PASSWORD` not set.

### Database
- **SQLite**: Primary file-based relational database (`db/smart_loan_manager.db`). Includes `ai_logs` table for AI assistant conversation history.
- **PostgreSQL**: Used for notifications and audit logs, including SFTP synchronization history.

### File Storage
- A `FileStorageManager` handles standard path generation and directory management, typically `static/uploads/customers/{customer_code}/`.

### SFTP ERP Automation System
A production-ready SFTP synchronization system, implemented with a FastAPI backend (Port 8000) and Paramiko, automatically exports 7 types of financial data to SQL ACC ERP Edition via secure SFTP every 10 minutes. It supports multi-company file organization and robust security features including SSH Host Key Verification, path security, and audit logging for all operations.