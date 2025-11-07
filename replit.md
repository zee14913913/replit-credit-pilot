# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation, ensuring 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.
User language: Chinese (使用中文与我沟通).

## System Architecture

### UI/UX Decisions
The platform features a strict professional design with a **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders
No other colors are permitted. The design system emphasizes clean, professional layouts with bilingual support (English/Chinese).

**Navigation Structure** (Final Version - November 2025):
The main navigation follows a streamlined business workflow logic with 6 core modules:
1. **DASHBOARD** - Customer management and overview
2. **CREDIT CARDS** - Unified credit card management center integrating:
   - Credit card statements (PDF/Excel upload with OCR)
   - Transaction receipts (OCR matching and verification)
   - Supplier invoices (auto-generated from 7 designated suppliers)
   - Payment reminders (calculated from statement_date and due_date)
   - Monthly consolidated reporting (combining all three data sources)
3. **SAVINGS** - Savings account tracking and bank statement management
4. **LOANS** - Intelligent loan matcher with CTOS parsing and DSR calculation
5. **REPORTS** - Monthly summary reports and professional financial statements
6. **ADMIN** - System administration, user management, and audit logs

*Design Rationale: The integration of RECEIPTS and INVOICES into the CREDIT CARDS module creates a unified workflow for complete monthly reconciliation. This allows users to:*
- *Upload credit card statements → Match transaction receipts → Review supplier invoices → Generate consolidated monthly reports*
- *All credit card related data (statements + receipts + invoices) are managed in one place for streamlined monthly closing*
- *Eliminates navigation overhead and improves data accuracy through centralized verification*

### Technical Implementations
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization. A robust notification system provides real-time updates and an auto-redirect feature. Client-side PDF-to-CSV conversion is implemented using PDF.js.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF with OCR, Excel), transaction categorization, savings account tracking, statement validation, and dual verification for 100% data accuracy.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization engine, cash flow prediction, anomaly detection, personalized recommendations, and a financial health scoring system.
- **Professional Invoice Generation:** Three enterprise-grade invoice formats in black/white formal style:
  - **Service Invoice**: Professional services billing (audit, tax, consulting) with itemized breakdown, tax calculations, payment terms, and authorized signatory
  - **Debit Note**: Late payment interest, adjustment notices with computer-generated certification
  - **Itemised Tax Invoice**: Detailed fee breakdown with sectioned tables (e.g., airline-style itemization with service tax calculations)
  - All formats support ReportLab PDF generation, customizable company branding, and automated numbering
- **Reporting & Export:** Professional Excel/CSV export and PDF report generation, automated monthly reports, and report versioning.
- **Workflow Automation:** Batch operations, reminder system, rule engine for transaction matching, and auto-posting rules.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), comprehensive audit logging, data integrity validation, and period locking.
- **User Experience:** Unified navigation, context-aware smart buttons, bilingual i18n system (English/Chinese), unified error handling, loading state optimization, responsive design, and accessibility (A11y).
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR for JPG/PNG), OWNER vs INFINITE Classification, Credit Card Ledger, Exception Center, AR/AP Aging Business Views, and Unified File Storage Manager.
- **Multi-Channel Notifications:** In-app, email (SendGrid), and SMS (Twilio) delivery with history and user settings.
- **Admin System:** User registration, secure login, and evidence archiving with strict RBAC and audit trails.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, and advisory services.
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance, Context Manager Pattern for database connections, and Service Layer Pattern for classification logic.
- **Security:** Session secret key, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Robust previous balance extraction and monthly ledger engine ensuring 100% accuracy and DR/CR classification.
- **Monthly Statement Architecture:** One monthly statement record per bank + month, aggregating 6 mandatory classification fields.

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
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, and real-time APIs.

### Database
- **SQLite**: File-based relational database (`db/smart_loan_manager.db`).
- **PostgreSQL**: Used for notifications and audit logs.

### File Storage
- A `FileStorageManager` handles standardized path generation and directory management.
- **Standard Directory Structure**: `static/uploads/customers/{customer_code}/` with subdirectories.
- 