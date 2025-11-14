# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing). The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.
User language: Chinese (使用中文与我沟通).

## Recent Changes
- **Phase 6: Modern Loan & SME Frontend Complete UI Coverage** (Nov 14, 2025) - Comprehensive frontend interface for Modern/SME loan engines featuring:
  - **3 New Frontend Pages**: `/loan-evaluate` (Modern Loan Engine), `/sme-loan-evaluate` (SME Loan Engine), `/loan-reports` (Report Generator Hub)
  - **7 New Flask Routes**: All protected with `@require_admin_or_accountant` RBAC, handling form-to-API marshalling, error handling, and audit logging
  - **Enhanced loan_matcher_result.html**: Conditional rendering of complete risk analytics (DTI/FOIR/CCRIS/BRR/DSCR/Risk Grade/Approval Odds) and AI Risk Advisor explanations panel when `is_modern_mode=True`
  - **Updated Navigation**: Loan Matcher dropdown now contains 5 entries (Smart Matcher, Modern Engine, SME Loans, Reports, Products) with visual separators
  - **Design Compliance**: All new pages strictly follow galaxy-theme (Black #000000, Pink #FF007F, Purple #322446) with bilingual support
  - **Data Mode Toggle**: Manual vs Auto enrichment modes for flexible data collection
  - **Backward Compatible**: No modifications to Phase 1-5 legacy routes or existing functionality
- **Dual-Engine Loan Evaluation System (CREDITPILOT)** - Production-ready dual-mode architecture supporting both legacy DSR/DSCR engines and modern Malaysian banking standards (DTI/FOIR/CCRIS/BRR).
- **AI Smart Assistant V3 (Enterprise Intelligence)** - Multi-provider architecture (Perplexity primary, OpenAI fallback) with real-time web search and automated daily financial reports (08:00 generation, 08:10 email delivery via SendGrid).
- **Income Document System** - Upload, OCR processing, and standardization of income proof documents with intelligent aggregation and confidence scoring.
- **Multi-Channel Notifications** - Unified notification system supporting in-app, email (SendGrid), and SMS (Twilio) channels.

## System Architecture

### UI/UX Decisions
The platform enforces a professional design using a **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders
The design system emphasizes clean layouts with bilingual support (English/Chinese).

**Navigation Structure**:
The main navigation features 7 core modules aligned with business workflow: DASHBOARD, CREDIT CARDS (unified management hub), SAVINGS, RECEIPTS, LOANS, REPORTS, and ADMIN. The **CREDIT CARDS** page is a central hub for uploading statements, managing suppliers, processing payments, and OCR receipts.

### Technical Implementations
The backend uses Flask with SQLite and a context manager for database interactions. Jinja2 handles server-side rendering, complemented by Bootstrap 5 and Bootstrap Icons for the UI. Plotly.js provides client-side data visualization, and PDF.js is used for client-side PDF-to-CSV conversion. A robust notification system provides real-time updates via SendGrid (email) and Twilio (SMS). The AI system uses a unified client architecture (`accounting_app/utils/ai_client.py`) supporting multiple providers (Perplexity primary, OpenAI backup) with automatic failover and environment-based configuration.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF OCR, Excel), transaction categorization, savings tracking, dual verification.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization, cash flow prediction, anomaly detection, financial health scoring, and loan eligibility assessment.
- **AI Smart Assistant V3 (Enterprise Intelligence):** Advanced multi-provider AI system (Perplexity AI primary, OpenAI fallback) with real-time web search. Features floating chatbot UI, cross-module analysis, automated daily financial reports (08:00 generation, 08:10 email delivery via SendGrid), system analytics, and comprehensive conversation history logging.
- **Income Document System:** Upload, OCR processing, and standardization of income proof documents (Salary Slip, Tax Return, EPF, Bank Inflow) with intelligent aggregation and confidence scoring.
- **Dual-Engine Loan Evaluation System (CREDITPILOT):** Production-ready dual-mode architecture supporting both legacy DSR/DSCR engines and modern Malaysian banking standards (DTI/FOIR/CCRIS/BRR). API routes (`/api/loans/eligibility`, `/api/business-loans/eligibility`) support `mode=dsr|modern` parameter for backward-compatible gradual migration. Modern mode implements comprehensive risk scoring (Personal: DTI/FOIR/CCRIS bucket, SME: BRR/DSCR/DSR/Industry/Cashflow Variance) with intelligent product matching across 12+ banks/Fintech providers. CTOS data serves as the exclusive debt commitment source.
- **Reporting & Export:** Professional Excel/CSV/PDF reports, automated monthly reports.
- **Workflow Automation:** Batch operations, rule engine for transaction matching.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), audit logging, data integrity validation.
- **User Experience:** Unified navigation, context-aware buttons, bilingual i18n, responsive design.
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR for JPG/PNG), Credit Card Ledger, Exception Center.
- **Multi-Channel Notifications:** In-app, email (SendGrid), and SMS (Twilio).
- **Admin System:** User registration, secure login, evidence archiving with RBAC.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and advisory.
- **Design Patterns:** Repository Pattern, Template Inheritance, Context Manager, Service Layer, Strategy Pattern (multi-provider AI).
- **Security:** Session secret key, file upload limits, SQL injection prevention, audit logging, API key management.
- **Data Accuracy:** Robust monthly ledger engine ensuring 100% accuracy via previous balance extraction and DR/CR classification.
- **Monthly Statement Architecture:** One monthly statement record per bank + month, aggregating 6 mandatory classification fields.
- **AI Architecture:** Unified client interface with automatic provider switching, graceful degradation, and environment-based configuration.
- **Dual-Engine Loan Architecture:** Legacy DSR/DSCR engines preserved (`loan_eligibility_engine.py`, `business_loan_engine.py`) alongside modern risk_engine (`risk_utils.py`, `personal_rules.py`, `sme_rules.py`, `scoring_matrix.py`, `risk_tables.py`). API layer supports mode-based routing with backward compatibility. Product matcher (`loan_products.py`) recommends 3-10 suitable banks based on risk grade. System uses CTOS commitment data exclusively, never credit card fields, with graceful defaults for missing data (CCRIS bucket=0, CTOS SME Score=650, Cashflow Variance=0.30).

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
- **SendGrid API**: Production email delivery system for AI daily reports and system notifications.
- **Twilio API**: SMS delivery.
- **Perplexity AI API**: Primary AI provider with real-time web search capabilities (Model: `sonar`).
- **OpenAI API**: Backup AI provider (gpt-4o-mini model) with automatic fallback.
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, AI assistant endpoints, and real-time APIs.

### Database
- **SQLite**: Primary file-based relational database (`db/smart_loan_manager.db`), including `ai_logs` table.
- **PostgreSQL**: Used for notifications and audit logs, including SFTP synchronization history.

### File Storage
- A `FileStorageManager` handles standard path generation and directory management, typically `static/uploads/customers/{customer_code}/`.

### SFTP ERP Automation System
A production-ready SFTP synchronization system, implemented with a FastAPI backend (Port 8000) and Paramiko, automatically exports 7 types of financial data to SQL ACC ERP Edition via secure SFTP every 10 minutes.