# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, budget management, and intelligent automation, guaranteeing 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

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
- **Budget Management:** Category-based monthly budgets, real-time tracking, and smart alerts.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Secure login/registration with SHA-256 hashing and token-based session management.
- **Customer Authorization Agreement:** Bilingual service agreement.
- **Automated News Management System:** Curated 2025 Malaysia banking news with admin approval and deduplication.
- **Instalment Tracking System:** Records instalment plans, generates payment schedules, and tracks remaining balances.
- **Statement Organization System:** Organizes statements by `statement_date` with automatic monthly folder structure.
- **Automated Monthly Report System:** Auto-generates and sends comprehensive galaxy-themed PDF reports per customer monthly, including detailed transactions, category summaries, optimization proposals, DSR calculation, and a profit-sharing service workflow.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View:** Visual calendar grid for each credit card showing statement coverage, amounts, transaction counts, and verification status across a rolling 12-month window.

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns.
- **Personalized Recommendation Engine:** Offers credit card, discount, instalment, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, and advisory services.
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, and Context Manager Pattern for database connection handling.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Implemented robust previous balance extraction and monthly ledger engine overhaul to ensure 100% accuracy in financial calculations and DR/CR classification.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`
- **PDF Processing**: `pdfplumber`, `reportlab`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`
- **Visualization**: `plotly.js` (CDN)
- **UI Framework**: `bootstrap@5.3.0` (CDN), `bootstrap-icons@1.11.0` (CDN)

### External APIs
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for fetching current interest rates.

### Database
- **SQLite**: File-based relational database (`db/smart_loan_manager.db`).
- **Concurrency Optimization**: WAL mode enabled with 30-second timeout.
- **Centralized Connection Management**: `db/database.py` provides unified `get_db()` context manager.

### File Storage
- **Local File System**: `static/uploads` for uploaded statements and generated PDF reports.