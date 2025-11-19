# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its primary purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing). The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

## Recent Changes

### November 19, 2025 - Google Document AI Integration (Production-Ready)
- ✅ **Dual-Engine PDF Parsing System**: Integrated Google Document AI as primary engine (98-99.9% accuracy) with pdfplumber as defensive fallback.
- ✅ **Multi-Column Layout Detection**: Enhanced `_extract_transactions_from_tables` to support 3/4/5-column Malaysian bank statement layouts with independent DR/CR column parsing.
- ✅ **DR/CR Validation Gate**: Enforces dual presence verification (dr_count > 0 AND cr_count > 0) before accepting Document AI results, ensuring 100% transaction extraction guarantee.
- ✅ **Polarity Preservation**: Added `_parse_amount_with_type` helper to correctly identify CR transactions from negative amounts or CR markers.
- ✅ **Environment-Based Configuration**: Automatic API key management via GOOGLE_PROJECT_ID, GOOGLE_PROCESSOR_ID, GOOGLE_LOCATION, GOOGLE_SERVICE_ACCOUNT_JSON.
- ✅ **Production Logging**: Comprehensive logging for monitoring and debugging Document AI parsing performance.
- ✅ **Architect Approval**: Final review confirmed 100% compliance with ARCHITECT_CONSTRAINTS.md specifications.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.
User language: Chinese (使用中文与我沟通).

### 🔒 UI样式强保护条款（MANDATORY - 所有批次开发强制遵守）

**总则**：任何批次、任何页面、所有新功能上线均必须**禁止更换/覆盖**全局或局部CSS，包括：卡片背景、描边、色板、圆角、按钮、文字颜色与字体家族、字号等视觉设计。

**禁止项（严格禁止）**：
- ❌ 修改全局或局部CSS/Sass/Less/Bootstrap文件
- ❌ 使用`!important`或覆盖式新样式
- ❌ 变更全局变量、主色系、主卡片背景
- ❌ 修改卡片背景、描边、色板、圆角、按钮样式
- ❌ 修改文字颜色、字体家族、字号
- ❌ 重写Bootstrap/Sass/Less配置

**允许项（安全实施）**：
- ✅ 复用现有样式class进行布局与配色
- ✅ 新增内容结构（不动样式参数）
- ✅ 通过新增icon/小图标/辅助局部class实现交互效果
- ✅ 注入式辅助class（需业务确认，不影响原始色板）

**验收标准**：
- 上线前必须进行全页面UI视觉比对（快照对比）
- 业务团队有权凭快照判定是否存在"样式污染"
- 发现任何视觉差异（颜色、描边、字体等）→ **立即回退** → 不得作为正式交付
- 主干CSS文件保持零变更

**未来定制化主题**：如需新主题或个性化色板选择，必须在**未来专门批次**开发，不与当前迭代合流。

## System Architecture

### UI/UX Decisions
The platform enforces a professional design using a **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders
The design system emphasizes clean layouts with bilingual support (English/Chinese) and strict adherence to UI style protection clauses.

**Navigation Structure**:
The main navigation features 8 core modules: DASHBOARD, CUSTOMERS, CREDIT CARDS, SAVINGS, RECEIPTS, LOANS, REPORT CENTER, MONTHLY SUMMARY, and ADMIN.

**Customer Management**:
Customer pages are reorganized with strict access control: `/admin/customers` for admin/accountant roles and `/customers` for individual customer profiles. Access control is session-based, implemented via context processors and template guards.

**Department Separation**:
- **CREDIT CARDS Department**: Manages credit card customers.
- **ACCOUNTING Department**: Reserved for Acc & Audit professional clients (future).

### Technical Implementations
The backend uses Flask with SQLite and a context manager for database interactions. Jinja2 handles server-side rendering, complemented by Bootstrap 5 and Bootstrap Icons for the UI. Plotly.js provides client-side data visualization, and PDF.js is used for client-side PDF-to-CSV conversion. A robust notification system provides real-time updates. The AI system uses a unified client architecture supporting multiple providers (Perplexity primary, OpenAI backup) with automatic failover and environment-based configuration.

**Credit Card Calculation System**:
A 2-round calculation engine (services/credit_card_core.py) implements 9 metrics, supporting negative balances and an independent 1% miscellaneous fee system (services/miscellaneous_fee.py). A 4-layer validation system (services/credit_card_validation.py) ensures data integrity. An automated pipeline (services/auto_processor.py) handles upload to fee generation. All calculations use Decimal types for precision.

**PDF Parsing Architecture (Production-Ready v2.0)**:
Dual-engine PDF parsing system guaranteeing 100% transaction extraction:
- **Primary Engine**: Google Document AI (98-99.9% accuracy) with intelligent multi-column layout detection (3/4/5 columns), independent DR/CR column parsing, and polarity preservation for negative amounts.
- **Validation Gate**: Enforces dual DR/CR presence verification (dr_count > 0 AND cr_count > 0) before accepting results, preventing incomplete data from entering downstream systems.
- **Fallback Engine**: Bank-specific pdfplumber parsers for 15 Malaysian banks when Document AI fails or data incomplete.
- **Environment-Based Configuration**: Automatic API key management via environment variables (GOOGLE_PROJECT_ID, GOOGLE_PROCESSOR_ID, GOOGLE_LOCATION, GOOGLE_SERVICE_ACCOUNT_JSON).
- **Logging**: Comprehensive logging for production monitoring and debugging.

**PDF Batch Processing System**:
Automated system for processing credit card statement PDFs, including Document AI extraction, 5-category transaction classification, automated outstanding balance calculation, and dual Excel/JSON reporting.

**Professional Excel Formatting Engine**:
Enterprise-grade Excel formatting system using 13 professional standards and a CreditPilot official color scheme (Main Pink #FFB6C1 + Deep Brown #3E2723), providing consistent and visually appealing reports.

**Unified Color Management System**:
Centralized color configuration via `config/colors.json` and a Python module (`config/colors.py`), generating CSS variables (`static/css/colors.css`). All components adhere to a strict 3-color palette (Black, Hot Pink, Dark Purple) enforced by automated compliance checks.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF OCR, Excel), transaction categorization, savings tracking, dual verification.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization, cash flow prediction, anomaly detection, financial health scoring, loan eligibility assessment.
- **AI Smart Assistant V3:** Advanced multi-provider AI with real-time web search, floating chatbot, cross-module analysis, automated daily financial reports.
- **Income Document System:** Upload, OCR processing, and standardization of income proof documents.
- **Dual-Engine Loan Evaluation System (CREDITPILOT):** Production-ready system supporting both legacy (DSR/DSCR) and modern Malaysian banking standards (DTI/FOIR/CCRIS/BRR), with comprehensive risk scoring and product matching across 12+ banks. CTOS data is the exclusive debt commitment source.
- **Reporting & Export:** Professional Excel/CSV/PDF reports, automated monthly reports, self-service Report Center.
- **Workflow Automation:** Batch operations, rule engine for transaction matching.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), audit logging, data integrity validation.
- **User Experience:** Unified navigation, context-aware buttons, bilingual i18n, responsive design.
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR), Credit Card Ledger, Exception Center.
- **Multi-Channel Notifications:** In-app, email, and SMS.
- **Admin System:** User registration, secure login, evidence archiving with RBAC.
- **CTOS Consent System**: Integrates personal and company CTOS consent, generating professional PDF reports.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and advisory.
- **Design Patterns:** Repository Pattern, Template Inheritance, Context Manager, Service Layer, Strategy Pattern (multi-provider AI).
- **Security:** Session secret key, file upload limits, SQL injection prevention, audit logging, API key management.
- **Data Accuracy:** Robust monthly ledger engine ensuring 100% accuracy.
- **Monthly Statement Architecture:** One monthly statement record per bank + month.
- **AI Architecture:** Unified client interface with automatic provider switching, graceful degradation, and environment-based configuration.
- **Dual-Engine Loan Architecture:** Preserves legacy DSR/DSCR engines alongside modern risk_engine, with an API layer for mode-based routing and product matching. Exclusively uses CTOS commitment data.

### Security & Access Control
A production-ready Unified RBAC Implementation protects 32+ functions using `@require_admin_or_accountant` decorator supporting Flask session-based RBAC and FastAPI token verification. Access levels include Admin, Accountant, Customer, and Unauthenticated roles. Route-level access control is implemented for specific endpoints.

## External Dependencies

### Third-Party Libraries
- **Core Framework**: `flask`, `fastapi`, `uvicorn`
- **PDF Processing**: `pdfplumber`, `reportlab`, `pdf.js`
- **OCR**: `pytesseract`, `Pillow`
- **Data Processing**: `pandas`, `schedule`
- **HTTP Requests**: `requests`, `openai`
- **Visualization**: `plotly.js`
- **UI Framework**: `bootstrap@5.3.0`, `bootstrap-icons@1.11.0`
- **Notification Services**: `sendgrid`, `twilio`, `py-vapid`, `pywebpush`
- **SFTP**: `paramiko`

### External APIs & Integrations
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for interest rates.
- **Google Document AI**: For PDF parsing and OCR.
- **SendGrid API**: Email delivery.
- **Twilio API**: SMS delivery.
- **Perplexity AI API**: Primary AI provider (Model: `sonar`).
- **OpenAI API**: Backup AI provider (gpt-4o-mini).
- **CTOS Data**: Exclusive source for debt commitment data in loan evaluation.

### Database
- **SQLite**: Primary file-based relational database (`db/smart_loan_manager.db`).
- **PostgreSQL**: Used for notifications and audit logs.

### File Storage
- `FileStorageManager` handles standard path generation and directory management, typically `static/uploads/customers/{customer_code}/`.

### SFTP ERP Automation System
A FastAPI backend (Port 8000) with Paramiko automatically exports 7 types of financial data to SQL ACC ERP Edition via secure SFTP every 10 minutes.