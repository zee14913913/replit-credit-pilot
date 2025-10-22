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
- **Authentication & Authorization:** Secure login/registration with SHA-256 hashing and token-based session management.
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
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, advisory services, supplier_config, customer_aliases, account_baselines, and monthly_ledger.
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, Context Manager Pattern for database connection handling, and Service Layer Pattern for OWNER/INFINITE classification logic.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Implemented robust previous balance extraction and monthly ledger engine overhaul to ensure 100% accuracy in financial calculations and DR/CR classification, including a universal balance-change algorithm for all bank statements. Independent statement-level reconciliation guarantees each monthly statement is tracked separately without data aggregation.

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
- **Local File System with 4-Level Hierarchical Organization**: 
  - **Mandatory organized structure** using `StatementOrganizer` service with category/bank separation:
    - **Credit Cards**: `static/uploads/{customer_name}/credit_cards/{bank_name}/{YYYY-MM}/`
    - **Savings Accounts**: `static/uploads/{customer_name}/savings/{bank_name}/{YYYY-MM}/`
    - File naming: `{BankName}_{Last4Digits}_{YYYY-MM-DD}.pdf`
  - **Receipts**: 
    - Matched: `static/uploads/receipts/{customer_id}/{card_last4}/`
    - Unmatched: `static/uploads/receipts/pending/`
  - **All file uploads are automatically organized by customer → category → bank → month**
  - **File paths are stored in database and served via `/view_statement_file/<statement_id>` route**
  
  **Organization Benefits:**
  - Easy browsing: Navigate by customer → view categories (credit cards vs savings) → select bank → pick month
  - Clear separation: Credit card and savings statements never mix
  - Bank isolation: Each bank's statements stored independently
  - Scalability: Structure supports unlimited customers, banks, and months