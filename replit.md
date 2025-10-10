# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. Its purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, budget management, batch operations, and intelligent automation. The platform features a sophisticated dark jewel-tone UI and guarantees 100% data accuracy. It generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions
The platform utilizes a Premium Galaxy-Themed UI with a Pure White + Elephant Gray + Silver Metallic minimalist color scheme. Key design elements include galaxy starfield effects, silver decorations (gradient text, glow, corner accents), layered visual effects (gradients, shimmer animations), and professional Inter typography. It supports multi-language (English/Chinese) and adheres to a design philosophy of zero colorful/childish elements, focusing on a sophisticated, enterprise-grade aesthetic.

### Technical Implementations
The backend is built with Flask, using SQLite with a context manager pattern for the database. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is used for client-side data visualization.

### Feature Specifications
**Core Features:**
- **Statement Ingestion:** PDF parsing (with OCR via `pdfplumber`) and Excel support, regex-based transaction extraction, and batch upload.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system (50% profit-sharing), and consultation request system.
- **Budget Management:** Category-based monthly budgets, real-time tracking, and smart alerts.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Advanced Search & Filter:** Full-text search, advanced filtering, and saved presets.
- **Batch Operations:** Multi-file upload, batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Secure login/registration with SHA-256 hashing and token-based session management.
- **Customer Authorization Agreement:** Bilingual service agreement.
- **Automated News Management System:** Curated 2025 Malaysia banking news with admin approval, deduplication, and scheduled fetching.
- **Instalment Tracking System:** Records instalment plans, generates payment schedules, and tracks remaining balances with principal/interest separation.
- **Galaxy-Themed Monthly Report System 3.0:** Automatically generates **ONE comprehensive galaxy-themed PDF per customer per month** (not per card). Each consolidated report features:
  * **Premium Visual Design:** Pure black background with scattered silver starfield particles (450 stars), silver glowing borders, black/white/gray/silver gradient theme, professional enterprise aesthetic
  * **Cover Page:** INFINITE GZ branding, customer info box with silver accents, 3 key metric highlight boxes (spending, outstanding, instalment)
  * **Per-Card Detail Sections:** Each credit card has its own comprehensive chapter containing:
    - **Complete Transaction Details Table:** Every single transaction recorded line-by-line (date, description, type, amount) - nothing omitted
    - **Category Summary Table:** Customer debit/credit totals, INFINITE debit/credit totals, outstanding balances for both customer and INFINITE
    - **Optimization Proposal Comparison:** Side-by-side comparison table showing current situation vs. optimized scenario with potential savings clearly displayed
    - **Optimization Value Statement:** Specific potential savings amount, 50/50 fee split explanation, customer's net gain calculation, zero-risk guarantee reminder
  * **Overall Analysis Page:** Comprehensive DSR calculation summing all cards, complete 50/50 profit-sharing service workflow with zero-risk guarantee messaging (7-step process: 咨询表达→方案准备→商讨细节→拟定合约→双方签字→执行优化→收取报酬)
  * **Professional Details:** Silver-line footer, page numbers, contact information, sophisticated typography throughout
  * **File Size:** ~180KB per customer report (includes visual effects and complete transaction details)
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score based on various financial metrics with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns and risks.
- **Personalized Recommendation Engine:** Offers credit card, discount, instalment, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, and advisory services.
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, and Context Manager Pattern for database connection handling.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.

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

### File Storage
- **Local File System**: `static/uploads` for uploaded statements and generated PDF reports.