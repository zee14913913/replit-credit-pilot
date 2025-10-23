# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation, guaranteeing 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions
The platform features an elegant, mysterious, high-end Galaxy Universe theme with a pure black background, golden gradients, and starfield effects. The design system includes a specific color palette (pure black, golden accents, silver-pearl text), visual effects (animated sparkles, aurora borealis, frosted glass), Inter font family with gradient headings, and interactive elements with silver-white glow on hover. Components include navigation with golden shimmer, glass-morphism cards, and elegant tables. It is fully responsive with multi-language support (English/Chinese). CSS styling is managed through `galaxy-theme.css`.

### Technical Implementations
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization.

### Feature Specifications

**Core Features:**
- **Statement Ingestion:** Supports PDF parsing (with OCR via `pdfplumber`) and Excel, with regex-based transaction extraction and batch upload for 15 major Malaysian banks.
- **Savings Account Tracking System:** Records all transactions from savings account statements (Maybank, GX Bank, HLB, CIMB, UOB, OCBC, Public Bank) with search-by-customer-name for prepayment settlement. Includes a specialized GX Bank parser for unique statement formats.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system, and consultation request system.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Multi-role permission system (Admin/Customer) with secure SHA-256 hashing. Admin users can access all customer data; Customer users can only access their own data. All sensitive routes protected with @login_required and @customer_access_required decorators.
- **Customer Authorization Agreement:** Bilingual service agreement.
- **Statement Organization System:** Organizes statements by `statement_date` with automatic monthly folder structure.
- **Automated Monthly Report System:** Auto-generates and sends comprehensive galaxy-themed PDF reports per customer monthly, including detailed transactions, category summaries, optimization proposals, DSR calculation, and a profit-sharing service workflow.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View:** Visual calendar grid for each credit card showing statement coverage, amounts, transaction counts, and verification status across a rolling 12-month window.
- **Intelligent Loan Matcher System:** CTOS report parsing, DSR calculation, and smart loan product matching. Automatically extracts monthly commitments from CTOS PDFs, calculates debt service ratio, and matches clients with eligible loan products from a comprehensive banking database.
- **Receipt Management System:** OCR-powered receipt upload system supporting JPG/PNG images. Features automatic card number, date, amount, and merchant name extraction using pytesseract. Intelligent matching engine auto-matches receipts to customers and credit cards based on card_last4, transaction date (±3 days), and amount (±1%). Receipts are organized by customer/card number with auto-filing. Supports batch upload, manual matching for failed auto-matches, and provides reconciliation, reimbursement tracking, and audit capabilities. Independent database table (receipts) keeps receipt data separate from credit card and savings systems.
- **OWNER vs INFINITE Classification System:** Advanced dual-classification system for credit card transactions with 1% supplier fee tracking. Classifies expenses into OWNER (customer personal spending) vs INFINITE (7 configurable supplier merchants with 1% fee), and payments into OWNER (customer payments) vs INFINITE (third-party payer payments). Features first-statement baseline initialization (Previous Balance = 100% OWNER debt), supplier configuration management, customer alias support, and monthly ledger tracking. Implements independent statement-level reconciliation ensuring each bank's monthly statement is recorded separately without aggregation.
- **Credit Card Ledger (3-Layer Navigation):** Professional hierarchical navigation system for OWNER vs INFINITE analysis. Layer 1: Customer List (displays all customers with full names and auto-generated codes like CCC_ALL for CHANG CHOON CHOW). Layer 2: Year-Month Timeline Grid (CCC_ALL_2024/2025 format with 12-month calendar showing statement availability). Layer 3: Monthly Statement Report (comprehensive analysis including client summary, accounts overview, transaction details per card, monthly summary with OWNER/INFINITE totals, and reconciliation verification). Each layer provides complete bilingual (EN/中文) support.

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns.
- **Personalized Recommendation Engine:** Offers credit card, discount, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, advisory services, supplier_config, customer_aliases, account_baselines, and monthly_ledger (with mandatory OWNER/INFINITE tracking fields: owner_expenses, owner_payments, infinite_expenses, infinite_payments, owner_balance, infinite_balance).
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, Context Manager Pattern for database connection handling, and Service Layer Pattern for OWNER/INFINITE classification logic.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Implemented robust previous balance extraction and monthly ledger engine overhaul to ensure 100% accuracy in financial calculations and DR/CR classification, including a universal balance-change algorithm for all bank statements. Independent statement-level reconciliation guarantees each monthly statement is tracked separately without data aggregation.
- **🚨 CRITICAL RULE - Monthly Statement Aggregation:** When a single PDF contains multiple credit cards from the same bank (e.g., Hong Leong Bank cards 2033 and 4170), the system MUST aggregate them into ONE statement per month with:
  - `statement.previous_balance` = SUM of all cards' previous balances
  - `statement.total` = SUM of all cards' current balances
  - ALL transactions from all cards stored under the same statement_id
  - Each transaction MUST have `card_last4` field to identify which card it belongs to
  - Display format: Monthly summary shows aggregated totals, with transaction details grouped by card number
  - This ensures monthly reports show "all cards from same bank in same month" as ONE consolidated view, not separate statements per card.

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
- **Local File System with Customer-ID-Based Isolation**: 
  - **Mandatory organized structure** using `StatementOrganizer` service with complete customer isolation:
    - **Base Structure**: `static/uploads/customers/customer_{id}/`
    - **Credit Cards**: `customer_{id}/credit_cards/{bank_name}/{YYYY-MM}/`
    - **Savings Accounts**: `customer_{id}/savings/{bank_name}/{YYYY-MM}/`
    - **Receipts**: `customer_{id}/receipts/{card_last4}/`
    - File naming: `{BankName}_{Last4Digits}_{YYYY-MM-DD}.pdf`
  - **Pending Receipts**: `static/uploads/pending_receipts/`
  - **All file uploads are automatically organized by customer_id → category → bank → month**
  - **File paths are stored in database and served via `/view_statement_file/<statement_id>` route**
  
  **Organization Benefits:**
  - **Complete Customer Isolation**: Each customer has their own folder identified by ID
  - **Avoid Name Conflicts**: Uses customer_id instead of name (no special character issues)
  - **Easy Backup**: Backup single customer by copying their folder
  - **Scalability**: Supports thousands of customers without root directory clutter
  - **Security**: Customer data physically separated on filesystem
  - **Easy Navigation**: customer_id → category (credit_cards/savings/receipts) → bank → month