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

**Navigation Structure** (November 2025):
The main navigation follows business workflow logic with 7 core modules:
1. **DASHBOARD** - Customer management and overview
2. **CREDIT CARDS** - Unified credit card management hub (see details below)
3. **SAVINGS** - Savings account tracking
4. **RECEIPTS** - Legacy route (redirects to CREDIT CARDS OCR section)
5. **LOANS** - Intelligent loan matcher
6. **REPORTS** - Monthly summary reports
7. **ADMIN** - System administration

**CREDIT CARDS Page - Integrated Financial Hub:**
The CREDIT CARDS page serves as the complete credit card management center, integrating all related financial documents and workflows:
1. **Upload Credit Card Statements** - PDF/Excel upload with dual validation
2. **Customer List** - View all customers with statement counts
3. **Supplier Invoices** - Auto-generated invoices for supplier consumption (1% processing fee)
4. **Customer Payments** - Payment receipts from customers to GZ
5. **OCR Receipts** (NEW ✨) - Smart OCR recognition for merchant swipe receipts:
   - Statistics dashboard (Total, Auto-matched, Manual-matched, Pending)
   - Upload form with image recognition (JPG/PNG)
   - Matched receipts table linked to customers and cards
   - Pending receipts management with manual matching

*Integration History: 
- INVOICES successfully integrated (supplier invoices display) ✅
- OCR RECEIPTS successfully integrated (merchant receipt OCR + matching) ✅
- REMINDERS feature planned for future integration (calculated from statement_date and due_date fields) 📅*

### Technical Implementations
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization. A robust notification system provides real-time updates and an auto-redirect feature. Client-side PDF-to-CSV conversion is implemented using PDF.js.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF with OCR, Excel), transaction categorization, savings account tracking, statement validation, and dual verification for 100% data accuracy.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization engine, cash flow prediction, anomaly detection, personalized recommendations, and a financial health scoring system.
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
- **OCR Receipts SQL Implementation:** Uses SQL column aliasing (AS) to map database columns (`created_at`, `amount`, `transaction_date`, `merchant_name`, `match_status`) to UI-friendly names (`uploaded_at`, `ocr_amount`, `ocr_date`, `ocr_merchant`, `match_type`) without requiring schema migrations. This approach maintains backward compatibility while providing semantic clarity for frontend code.

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