# Smart Credit & Loan Manager

## Overview

The Smart Credit & Loan Manager is a **Premium Enterprise-Grade SaaS Platform** for Malaysian banking customers, built with Flask. Its purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, budget management, batch operations, and intelligent automation. The platform features a sophisticated dark jewel-tone UI and guarantees 100% data accuracy through a dual verification system. It aims to generate revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences

Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions

The platform features a **Premium Luxury UI** with a **Deep Violet + Purple Gradient + Pearl White + Silver Bright White** color scheme (深紫罗兰色 + 紫色渐层 + 珍珠白 + 银亮白), inspired by modern SaaS platforms like Stripe, Vercel, and Linear. The design uses:
- **Deep Violet Primary Colors**: #5B21B6, #7C3AED, #8B5CF6 with purple gradient backgrounds
- **Pearl White Text**: #F8FAFC, #F1F5F9 for maximum readability
- **Silver Bright White Accents**: #E2E8F0, #CBD5E1 for secondary elements
- **Purple Glow Effects**: Enhanced with sophisticated shadow and glow effects throughout
- **Professional Typography**: Inter font family with modern letter spacing
- **Company Branding**: INFINITE GZ SDN BHD prominently displayed with enhanced logo size (120px) and purple glow effects
- **Multi-language Support**: Complete language separation (English/Chinese) with bilingual UI elements
- **No Emojis**: Clean, professional design without childish elements

### Technical Implementations

The backend is built with **Flask**, chosen for rapid development and flexibility. The database layer uses **SQLite** with a context manager pattern for efficient connection handling, with a design consideration for Drizzle ORM and potential Postgres support. Jinja2 is used for server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js handles client-side data visualization.

### Feature Specifications

**Core Features:**
- **Statement Ingestion:** PDF parsing (with OCR via `pdfplumber`) and Excel support, regex-based transaction extraction, and batch upload.
- **Transaction Categorization:** Keyword-based system with 10+ predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy by cross-validating parsed transactions against PDF totals, with confidence scoring, duplicate detection, and OCR support.
- **Revenue-Generating Advisory Services:**
    - **AI-Powered Credit Card Recommendations:** Analyzes spending patterns for optimal card suggestions from 11+ Malaysian banks.
    - **Financial Optimization Engine:** Offers debt consolidation, balance transfer, and loan refinancing suggestions based on BNM rates.
    - **Success-Based Fee System:** 50% profit-sharing model; zero fees if no savings are achieved.
    - **Consultation Request System:** Facilitates client consultation requests.
- **Budget Management:** Category-based monthly budgets, real-time utilization tracking, and smart alerts.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Advanced Search & Filter:** Full-text search, advanced filtering, and saved filter presets.
- **Batch Operations:** Multi-file upload, batch job management, and error handling.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Secure customer login/registration with SHA-256 password hashing and token-based session management.
- **Customer Authorization Agreement:** Bilingual (EN/CN) service agreement including Credit Card Management, Debt Optimization, Bank Loan Advisory, Audit & Accounting, Mortgage Interest Discount, and SME Financing.

### System Design Choices

- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and new models for authentication (customer_logins, customer_sessions) and advisory services (credit_card_products, card_recommendations, financial_optimization_suggestions, consultation_requests, success_fee_calculations, customer_employment_types, service_terms).
- **Design Patterns:** Utilizes Repository Pattern for database abstraction, Template Inheritance for consistent UI, and Context Manager Pattern for database connection handling.
- **Security:** Implements session secret key from environment variables, file upload size limits, SQL injection prevention via parameterized queries, and audit logging.

## External Dependencies

### Third-Party Libraries

- **Core Framework**: `flask`
- **PDF Processing**: `pdfplumber`, `reportlab`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`
- **Visualization**: `plotly.js` (CDN)
- **UI Framework**: `bootstrap@5.3.0` (CDN), `bootstrap-icons@1.11.0` (CDN)

### External APIs

- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for fetching current interest rates (OPR, SBR) with a fallback to default rates.

### Database

- **SQLite**: File-based relational database (`db/smart_loan_manager.db`) used for its simplicity and zero-configuration deployment.

### File Storage

- **Local File System**: `static/uploads` for storing uploaded statements and generated PDF reports.