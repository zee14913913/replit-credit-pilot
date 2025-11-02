# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation, ensuring 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

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
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization. A robust notification system provides real-time updates and an auto-redirect feature for user convenience. Client-side PDF-to-CSV conversion is implemented using PDF.js, ensuring 100% data preservation and system-level validation.

### Feature Specifications
**Core Features:**
- **Statement Ingestion:** PDF parsing (with OCR), Excel support, regex-based transaction extraction, batch upload for 15 major Malaysian banks.
- **Savings Account Tracking System:** Records all transactions from savings account statements.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation.
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Multi-role permission system (Admin/Customer) with secure SHA-256 hashing.
- **Automated Monthly Report System:** Auto-generates and sends comprehensive galaxy-themed PDF reports per customer monthly.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View:** Visual calendar grid for each credit card showing statement coverage and status.
- **Intelligent Loan Matcher System:** CTOS report parsing, DSR calculation, and smart loan product matching.
- **Receipt Management System:** OCR-powered receipt upload system supporting JPG/PNG images with intelligent matching.
- **OWNER vs INFINITE Classification System:** Advanced dual-classification for credit card transactions with 1% supplier fee tracking.
- **Credit Card Ledger (3-Layer Navigation):** Hierarchical navigation for OWNER vs INFINITE analysis.
- **Rule Engine:** Table-driven rule engine for transaction matching and accounting entry generation.
- **Exception Center:** Centralized management for 5 types of exceptions with 4 severity levels.
- **AR/AP Aging Business Views:** Provides accounts receivable and payable aging reports.
- **Unified File Storage Manager:** Multi-tenant isolated storage for accounting data.
- **Data Integrity Validation System:** Four-layer data protection ensuring 100% source-document traceability.
- **Multi-Channel Notification System:** Comprehensive notification infrastructure with in-app, email (SendGrid), and SMS (Twilio) delivery channels.
  - **In-App Notifications:** Real-time notification center with unread badges and action buttons.
  - **Email Notifications:** Template-based email delivery via SendGrid with automatic fallback.
  - **SMS Notifications:** Emergency alerts via Twilio with international number support.
  - **Notification History:** Full-featured history page with filtering by status (all/read/unread).
  - **Notification Settings:** User preference management for selecting notification channels.
  - **Auto-Delivery:** Automatic multi-channel notification dispatch based on user preferences and priority levels.

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns.
- **Personalized Recommendation Engine:** Offers credit card, discount, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, advisory services, and specific ledger tracking.
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, Context Manager Pattern for database connection handling, and Service Layer Pattern for classification logic.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging for all admin routes and API key creation.
- **Data Accuracy:** Robust previous balance extraction and monthly ledger engine to ensure 100% accuracy in financial calculations and DR/CR classification.
- **Monthly Statement Architecture**: Each bank + month combination creates ONE monthly statement record, aggregating 6 mandatory classification fields ensuring `owner_balance + gz_balance = closing_balance_total`.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`, `fastapi`, `uvicorn`
- **PDF Processing**: `pdfplumber`, `reportlab`, `pdf.js` (client-side)
- **OCR**: `pytesseract`, `Pillow`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`
- **Visualization**: `plotly.js` (CDN)
- **UI Framework**: `bootstrap@5.3.0` (CDN), `bootstrap-icons@1.11.0` (CDN)
- **Notification Services**: `sendgrid` (email), `twilio` (SMS), `py-vapid` & `pywebpush` (Web Push)

### External APIs & Integrations
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for fetching current interest rates.
- **SendGrid API**: Email delivery service for transactional notifications (requires SENDGRID_API_KEY).
- **Twilio API**: SMS delivery service for urgent alerts (auto-configured via Replit integration).
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, and real-time API endpoints.

### Database
- **SQLite**: File-based relational database (`db/smart_loan_manager.db`) with WAL mode.
- **PostgreSQL**: Used for notifications and audit logs.

### File Storage
A `FileStorageManager` handles standardized path generation, directory management, and file operations.
- **Standard Directory Structure**: `static/uploads/customers/{customer_code}/` with subdirectories for various document types.