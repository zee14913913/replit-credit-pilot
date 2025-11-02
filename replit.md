# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation, guaranteeing 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## Recent Changes
### Security Refactoring (2025-01-02)
**System Hardening & Permission Tightening** - Completed 10 of 14 planned tasks (71%):
1. ✅ Admin routes now require authentication via FastAPI `/api/auth/me`
2. ✅ API Key creation restricted to Admin role only
3. ✅ Export functions tiered: CSV/Excel for admin/accountant, PDF for all users
4. ✅ Feature toggles added: `FEATURE_ADVANCED_ANALYTICS` and `FEATURE_CUSTOMER_TIER` (default: false)
5. ✅ Homepage customer list filtered by role: Admin sees all, Customer sees self only
6. ✅ Swagger documentation protected: requires login to access `/docs` and `/redoc`
7. ✅ OCR receipt matching disabled: all matches require manual confirmation
8. ✅ Upload failure messages clarified: explicitly states "file saved but validation failed"
9. ✅ System operation manual updated with new permission model
10. ✅ Workflows restarted and verified running without errors

**Remaining Tasks** (architectural improvements, can be done later):
- Task 2: Unify authentication source
- Task 6: Merge batch upload logic
- Task 8: Unify file paths to FILES_BASE_DIR

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.
User language: Chinese (使用中文与我沟通).

## System Architecture

### UI/UX Decisions
The platform features a strict professional design with **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders

No other colors are permitted. The design system emphasizes clean, professional layouts with bilingual support (English/Chinese). All CSS styling follows this strict color constraint.

### Technical Implementations
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization.

### Feature Specifications
**Core Features:**
- **Statement Ingestion:** PDF parsing (with OCR), Excel support, regex-based transaction extraction, batch upload for 15 major Malaysian banks.
- **Savings Account Tracking System:** Records all transactions from savings account statements with customer search for prepayment settlement.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation.
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Multi-role permission system (Admin/Customer) with secure SHA-256 hashing.
- **Automated Monthly Report System:** Auto-generates and sends comprehensive galaxy-themed PDF reports per customer monthly, including detailed transactions, category summaries, optimization proposals, DSR calculation, and a profit-sharing service workflow.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View:** Visual calendar grid for each credit card showing statement coverage and status.
- **Intelligent Loan Matcher System:** CTOS report parsing, DSR calculation, and smart loan product matching.
- **Receipt Management System:** OCR-powered receipt upload system supporting JPG/PNG images with intelligent matching to customers and credit cards.
- **OWNER vs INFINITE Classification System:** Advanced dual-classification system for credit card transactions with 1% supplier fee tracking. Classifies expenses and payments into OWNER (customer personal spending/payments) vs INFINITE (7 configurable supplier merchants with 1% fee / third-party payer payments). Features first-statement baseline initialization and independent statement-level reconciliation.
- **Credit Card Ledger (3-Layer Navigation):** Professional hierarchical navigation system for OWNER vs INFINITE analysis.
- **Rule Engine:** Table-driven rule engine for transaction matching and accounting entry generation, supporting keyword and regex patterns with priority-based matching. Includes caching and tenant isolation.
- **Exception Center:** Centralized management for 5 types of exceptions (pdf_parse, ocr_error, customer_mismatch, supplier_mismatch, posting_error) with 4 severity levels and lifecycle management.
- **AR/AP Aging Business Views:** Provides accounts receivable and payable aging reports grouped by customer/supplier, with aging buckets (0-30/31-60/61-90/90+ days).
- **Unified File Storage Manager:** Multi-tenant isolated storage for accounting data with standardized paths and security features.
- **Data Integrity Validation System (补充改进①-④):** Four-layer data protection ensuring 100% source-document traceability:
  - ① **Completeness Field**: raw_line_id foreign key on all transaction tables linking to source PDF text
  - ② **Business Layer Gate**: DataIntegrityValidator service blocks records with missing raw_line_id from entering reports
  - ③ **Validation Status Tracking**: raw_documents.validation_status marks line-count reconciliation results (passed/failed/pending)
  - ④ **API Key Permission Model**: Default permissions restricted to upload only; export operations require explicit authorization

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns.
- **Personalized Recommendation Engine:** Offers credit card, discount, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, advisory services, supplier_config, customer_aliases, account_baselines, monthly_ledger, and infinite_monthly_ledger (with mandatory OWNER/INFINITE tracking fields).
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, Context Manager Pattern for database connection handling, and Service Layer Pattern for OWNER/INFINITE classification logic.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Robust previous balance extraction and monthly ledger engine overhaul to ensure 100% accuracy in financial calculations and DR/CR classification, including a universal balance-change algorithm for all bank statements and independent statement-level reconciliation.
- **Monthly Statement Architecture**: Each bank + month combination creates ONE monthly statement record in the `monthly_statements` table, aggregating 6 mandatory classification fields (owner_expenses, owner_payments, gz_expenses, gz_payments, owner_balance, gz_balance), ensuring `owner_balance + gz_balance = closing_balance_total`.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`
- **PDF Processing**: `pdfplumber`, `reportlab`
- **OCR**: `pytesseract`, `Pillow`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`
- **Visualization**: `plotly.js` (CDN)
- **UI Framework**: `bootstrap@5.3.0` (CDN), `bootstrap-icons@1.11.0` (CDN)

### External APIs
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for fetching current interest rates.

### Database
- **SQLite**: File-based relational database (`db/smart_loan_manager.db`), with WAL mode and centralized connection management.

### File Storage
A `FileStorageManager` handles standardized path generation, directory management, and file operations.
- **Standard Directory Structure**: `static/uploads/customers/{customer_code}/` with subdirectories for `credit_cards`, `savings`, `receipts`, `invoices`, `reports`, `loans`, and `documents`.
- **Core Characteristics**: Full customer isolation, self-explanatory file paths (`path as index`), time-dimensional management, automatic type-based organization, standardized naming conventions, scalability, and cross-platform compatibility.