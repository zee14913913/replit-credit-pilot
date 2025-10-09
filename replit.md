# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a **Premium Enterprise-Grade SaaS Platform** built with Flask for Malaysian banking customers. It offers comprehensive financial management, including credit card statement processing, advanced analytics, budget management, batch operations, and intelligent automation. The platform features a sophisticated dark jewel-tone UI and guarantees 100% data accuracy. It aims to generate revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions
The platform features a **Premium Galaxy-Themed UI** with a **Pure White + Elephant Gray + Silver Metallic** minimalist color scheme, inspired by modern SaaS platforms. Key design elements include:
- **Color Palette**: Pure white, elephant gray, and silver metallic accents.
- **Text Brightness**: Enhanced readability with light text on dark backgrounds.
- **Galaxy Starfield Effects**: Subtle twinkling stars in headers/footers with multi-layer radial gradients.
- **Silver Decorations**: Silver gradient text for H1, silver glow for H2, and silver corner accents for cards.
- **Layered Visual Effects**: Black-to-gray gradients, shimmer animations, and decorative gradients.
- **Professional Typography**: Inter font family with modern letter spacing.
- **Company Branding**: INFINITE GZ SDN BHD prominently displayed.
- **Multi-language Support**: Complete language separation (English/Chinese) with bilingual UI elements.
- **Design Philosophy**: Zero colorful/childish elements, focusing on a premium, sophisticated, enterprise-grade aesthetic.

### Technical Implementations
The backend is built with **Flask**. The database layer uses **SQLite** with a context manager pattern. Jinja2 is used for server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js handles client-side data visualization.

### Feature Specifications
**Core Features:**
- **Statement Ingestion:** PDF parsing (with OCR via `pdfplumber`) and Excel support, regex-based transaction extraction, and batch upload.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy by cross-validating parsed transactions.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system (50% profit-sharing, zero fees if no savings), and consultation request system.
- **Budget Management:** Category-based monthly budgets, real-time utilization tracking, and smart alerts.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Advanced Search & Filter:** Full-text search, advanced filtering, and saved presets.
- **Batch Operations:** Multi-file upload, batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Secure customer login/registration with SHA-256 hashing and token-based session management.
- **Customer Authorization Agreement:** Bilingual service agreement.
- **Automated News Management System:** Curated 2025 Malaysia banking news with admin approval workflow, intelligent deduplication, and scheduled auto-fetching.

**Latest Advisory Workflow (50/50 Consultation Service):**
- **Optimization Proposal System:** Generates debt consolidation and credit card recommendations, displaying current vs. optimized solutions and calculating savings with 50% profit share.
- **Consultation Booking System:** Allows customers to book consultations post-proposal acceptance.
- **Service Contract Generator:** Creates bilingual authorization agreement PDFs with dual-party signature workflow.
- **Payment-on-Behalf Management:** Records payment transactions, calculates actual savings/earnings, and applies the 50/50 profit split with a "zero fee if no savings" guarantee.

**Admin Portfolio Management Dashboard:**
- **Portfolio Overview:** Aggregates key client metrics.
- **Client Workflow Tracking:** Monitors client progress through the 5-stage advisory pipeline.
- **Revenue Breakdown:** Analyzes income streams.
- **Risk Client Identification:** Flags high-risk clients.
- **Client Detail View:** Comprehensive drill-down for each client.

**AI Advanced Analytics System (v2.0 Premium Edition):**
- **Financial Health Scoring System:** 0-100 score based on repayment, DSR, utilization, spending health, and stability, with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast with scenario comparison.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system and escalating benefits.
- **AI Anomaly Detection System:** Real-time monitoring for large unclassified spending, credit card overdrafts, abnormal spending patterns, DSR spikes, and overdue risks.
- **Personalized Recommendation Engine:** Offers credit card, supplier discount, installment payment, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates all analytical features with dynamic charts and real-time warnings.

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