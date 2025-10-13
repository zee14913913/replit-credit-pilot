# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, budget management, and intelligent automation, guaranteeing 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions
**Current Theme: Galaxy Universe (October 2025 Update)**
The platform features an **elegant, mysterious, high-end Galaxy Universe theme** with pure black background, golden gradients, and starfield effects - matching the INFINITE GZ Finance Optimization Monthly Report cover aesthetic. 

**Design System:**
- **Color Palette:** Pure black (#000000) background, golden accents for borders/decorations (#D4AF37), silver-pearl text colors (#F5F5F5, #E8E8E8)
- **Visual Effects:** Animated silver dust sparkle, aurora borealis light waves (25s cycle), frosted glass cards with golden borders, glowing hover effects, dark area silver dust pattern
- **Typography:** Inter font family with silver-pearl gradient headings (#FFFFFF → #F5F5F5 → #E8E8E8), elegant letter-spacing, and white glow text shadows
- **Interactive Elements:** Golden glow on hover, shimmer animations, smooth transitions
- **Components:** Navigation with golden shimmer, glass-morphism cards, elegant tables, sophisticated footer
- **Responsive Design:** Fully responsive with breakpoints at 1200px, 768px, and 480px
- **Multi-language:** English/Chinese support with theme toggle
- **CSS Architecture:** `galaxy-theme.css` - comprehensive styling for all page elements (navigation, cards, forms, tables, alerts, badges, footer)

### Technical Implementations
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization.

### Feature Specifications
**Core Features:**
- **Statement Ingestion:** Supports PDF parsing (with OCR via `pdfplumber`) and Excel, with regex-based transaction extraction and batch upload for 15 major Malaysian banks (Local Commercial, Foreign, and Islamic banks).
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system (50% profit-sharing), and consultation request system.
- **Budget Management:** Category-based monthly budgets, real-time tracking, and smart alerts.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Secure login/registration with SHA-256 hashing and token-based session management.
- **Customer Authorization Agreement:** Bilingual service agreement.
- **Automated News Management System:** Curated 2025 Malaysia banking news with admin approval and deduplication.
- **Instalment Tracking System:** Records instalment plans, generates payment schedules, and tracks remaining balances.
- **Statement Organization System:** Organizes statements by statement_date (not due_date) with automatic monthly folder structure.
- **Automated Monthly Report System:** Every month 30th at 10:00 AM - auto-generates all customer monthly reports; Every month 1st at 9:00 AM - auto-sends reports via email to all customers.
- **Galaxy-Themed Monthly Report System 3.0:** Generates one comprehensive galaxy-themed PDF per customer per month, featuring:
    - Premium Visual Design: Pure black background with silver starfield, glowing borders, and professional typography.
    - Cover Page: Branding, customer info, and key metric highlights.
    - Per-Card Detail Sections: Complete transaction details, category summaries, and optimization proposal comparisons with clear savings.
    - Overall Analysis Page: Comprehensive DSR calculation and a 7-step profit-sharing service workflow.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View (Oct 2025):** Visual calendar grid for each credit card showing statement coverage across rolling 12-month window:
    - Organized by statement_date for accurate monthly positioning
    - Green checkmarks for months with statements, gray dash for missing months
    - Displays amount, transaction count, and verification status per month
    - Interactive click-to-view or upload missing statements
    - Coverage percentage indicator for quick assessment
    - Service module: `services/card_timeline.py`
    - Reusable component: `templates/components/card_timeline_12months.html`

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
- **Concurrency Optimization**: WAL mode enabled with 30-second timeout for concurrent access handling.
- **Centralized Connection Management**: `db/database.py` provides unified `get_db()` context manager for all modules.

### File Storage
- **Local File System**: `static/uploads` for uploaded statements and generated PDF reports.