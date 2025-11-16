# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. Its purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation for 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization (debt consolidation, balance transfers, loan refinancing). The long-term vision includes expanding into exclusive mortgage interest discounts and SME financing.

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

**分批次开发承诺**：
- 🟩 第一批：主结构和核心导航优化 - 纯入口增补，旧UI色不动
- 🟦 第二批：账单上传、流水明细、异常批量处理 - 复用现有卡片/表格/按钮样式class
- 🟨 第三批：客户体验升级、管理端批量处理 - 全部复用当前样式文件，无全局UI变量变更
- 🟫 终极批次：全站统一双语切换 - 仅限内容级变化，UI风格/色彩/主题/边框/卡片背景/字体保持一致

**未来定制化主题**：如需新主题或个性化色板选择，必须在**未来专门批次**开发，不与当前迭代合流。

## System Architecture

### UI/UX Decisions
The platform enforces a professional design using a **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders
The design system emphasizes clean layouts with bilingual support (English/Chinese).

**Navigation Structure**:
The main navigation features 7 core modules aligned with business workflow: DASHBOARD, CREDIT CARDS, SAVINGS, RECEIPTS, LOANS, REPORTS, and ADMIN.

**Department Separation (CRITICAL)**:
- **CREDIT CARDS Department**: Manages credit card customers (CHANG CHOON CHOW, CHEOK JUN YOON, etc.). All files stored in `credit_card_files/{customer_name}/` with Excel exports, monthly statements, and transaction details.
- **ACCOUNTING Department** (Future): Reserved exclusively for Acc & Audit professional clients. Completely separate from credit card management. Files will be stored in `accounting_files/` when implemented.

The **CREDIT CARDS** page is a central hub for uploading statements, managing suppliers, processing payments, OCR receipts, and viewing Excel files.

### Technical Implementations
The backend uses Flask with SQLite and a context manager for database interactions. Jinja2 handles server-side rendering, complemented by Bootstrap 5 and Bootstrap Icons for the UI. Plotly.js provides client-side data visualization, and PDF.js is used for client-side PDF-to-CSV conversion. A robust notification system provides real-time updates. The AI system uses a unified client architecture supporting multiple providers (Perplexity primary, OpenAI backup) with automatic failover and environment-based configuration.

**VBA Hybrid Architecture (INFINITE GZ Extension):** The system implements a client-server hybrid architecture where VBA (Windows Excel client) handles primary statement parsing, and Replit receives standardized JSON data via REST API. This architecture prioritizes accuracy and cost-efficiency: VBA directly reads Excel cells with 95%+ accuracy, avoiding expensive OCR services. PDF statements are converted to Excel using Tabula/Adobe Acrobat Pro client-side, then parsed by VBA. The system provides 5 VBA templates, Python PDF conversion tools, and dual API endpoints (/api/upload/vba-json for single files, /api/upload/vba-batch for batch uploads) with JSON format validation. Python Excel parsers are retained as backup for system resilience.

### Feature Specifications
**Core Features:**
- **Financial Management:** Statement ingestion (PDF OCR, Excel), transaction categorization, savings tracking, dual verification.
- **AI-Powered Advisory:** Credit card recommendations, financial optimization, cash flow prediction, anomaly detection, financial health scoring, and loan eligibility assessment.
- **AI Smart Assistant V3 (Enterprise Intelligence):** Advanced multi-provider AI system with real-time web search, floating chatbot UI, cross-module analysis, automated daily financial reports, system analytics, and comprehensive conversation history logging.
- **Income Document System:** Upload, OCR processing, and standardization of income proof documents with intelligent aggregation and confidence scoring.
- **Dual-Engine Loan Evaluation System (CREDITPILOT):** Production-ready dual-mode architecture supporting both legacy DSR/DSCR engines and modern Malaysian banking standards (DTI/FOIR/CCRIS/BRR). Implements comprehensive risk scoring (Personal: DTI/FOIR/CCRIS bucket, SME: BRR/DSCR/DSR/Industry/Cashflow Variance) with intelligent product matching across 12+ banks/Fintech providers. CTOS data serves as the exclusive debt commitment source.
- **Reporting & Export:** Professional Excel/CSV/PDF reports, automated monthly reports.
- **Workflow Automation:** Batch operations, rule engine for transaction matching.
- **Security & Compliance:** Multi-role authentication & authorization (RBAC), audit logging, data integrity validation.
- **User Experience:** Unified navigation, context-aware buttons, bilingual i18n, responsive design.
- **Specialized Systems:** Intelligent Loan Matcher (CTOS parsing, DSR calculation), Receipt Management (OCR for JPG/PNG), Credit Card Ledger, Exception Center.
- **Multi-Channel Notifications:** In-app, email, and SMS.
- **Admin System:** User registration, secure login, evidence archiving with RBAC.
- **CTOS Consent System**: Integrates personal (e-signature + IC upload) and company (SSM upload + company stamp) CTOS consent, generating professional PDF reports.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, and advisory.
- **Design Patterns:** Repository Pattern, Template Inheritance, Context Manager, Service Layer, Strategy Pattern (multi-provider AI).
- **Security:** Session secret key, file upload limits, SQL injection prevention, audit logging, API key management.
- **Data Accuracy:** Robust monthly ledger engine ensuring 100% accuracy via previous balance extraction and DR/CR classification.
- **Monthly Statement Architecture:** One monthly statement record per bank + month, aggregating 6 mandatory classification fields.
- **AI Architecture:** Unified client interface with automatic provider switching, graceful degradation, and environment-based configuration.
- **Dual-Engine Loan Architecture:** Legacy DSR/DSCR engines preserved alongside modern risk_engine. API layer supports mode-based routing with backward compatibility. Product matcher recommends 3-10 suitable banks based on risk grade. System uses CTOS commitment data exclusively.

### Security & Access Control
A production-ready Unified RBAC Implementation protects 32 functions. The `@require_admin_or_accountant` decorator supports Flask session-based RBAC and FastAPI token verification. Access levels include Admin (full access) and Accountant (full operational access), with Customer and Unauthenticated roles restricted.

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

### External APIs & Integrations
- **Bank Negara Malaysia Public API**: `https://api.bnm.gov.my` for interest rates.
- **SendGrid API**: Production email delivery system.
- **Twilio API**: SMS delivery.
- **Perplexity AI API**: Primary AI provider with real-time web search capabilities (Model: `sonar`).
- **OpenAI API**: Backup AI provider (gpt-4o-mini model) with automatic fallback.
- **FastAPI Backend (Port 8000)**: Handles audit logging, notifications, AI assistant endpoints, and real-time APIs.

### Database
- **SQLite**: Primary file-based relational database (`db/smart_loan_manager.db`).
- **PostgreSQL**: Used for notifications and audit logs.

### File Storage
- A `FileStorageManager` handles standard path generation and directory management, typically `static/uploads/customers/{customer_code}/`.

### SFTP ERP Automation System
A production-ready SFTP synchronization system, implemented with a FastAPI backend (Port 8000) and Paramiko, automatically exports 7 types of financial data to SQL ACC ERP Edition via secure SFTP every 10 minutes.

## Recent Changes

### Nov 16, 2025 - 双语系统Session持久化修复

**发现问题**：系统已有完整的i18n基础架构（2127行翻译资源、后端session管理、前端JavaScript框架），但前端切换语言时未调用后端API保存session，导致刷新页面后语言重置。

**实施修复**（100%符合UI样式强保护条款）：
1. **static/js/i18n.js** - 添加`fetch('/set-language/${lang}')`调用，确保session持久化
2. **templates/layout.html** - 优化语言切换按钮UI（添加图标，高亮当前语言）

**修复验证**：
- ✅ 零CSS文件变更（`git diff` 无输出）
- ✅ 100%复用现有样式class（`.lang-btn`, `.lang-btn.active`）
- ✅ 零新增样式规则
- ✅ Architect专业审查通过
- ✅ 符合"零样式污染、零视觉变化"保护原则

**功能状态**：
- ✅ 用户点击语言按钮 → 全站即时切换（EN ⇄ 中文）
- ✅ 刷新页面后语言保持一致
- ✅ 2000+翻译条目自动应用
- ✅ 可安全上线生产环境

**技术文档**：详见 `BILINGUAL_SYSTEM_IMPLEMENTATION_REPORT.md`

### Nov 15, 2024

### VBA Hybrid Architecture Implementation
Added complete VBA-based hybrid processing system for INFINITE GZ credit card and bank statement parsing:

**Client-Side Components (vba_templates/):**
- `1_CreditCardParser.vba`: Credit card statement parser with 30+ intelligent categories
- `2_BankStatementParser.vba`: Bank statement parser supporting PBB/MBB/CIMB/RHB/HLB
- `3_PDFtoExcel_Guide.vba`: PDF conversion workflow documentation
- `4_DataValidator.vba`: Balance verification and data quality checker
- `5_Usage_Guide.md`: Quick start guide for VBA templates
- `JSON_Format_Specification.md`: Standard JSON format specification
- `COMPLETE_INTEGRATION_GUIDE.md`: End-to-end integration documentation

**PDF Conversion Tools (tools/pdf_converter/):**
- `pdf_to_excel.py`: Python tool using Tabula/PDFPlumber for batch PDF-to-Excel conversion
- `README.md`: Tool usage instructions and troubleshooting guide

**Server-Side API (app.py):**
- `POST /api/upload/vba-json`: Single JSON file upload endpoint with format validation
- `POST /api/upload/vba-batch`: Batch JSON upload endpoint supporting multiple files

**Python Backup Parsers (services/excel_parsers/):**
- `bank_statement_excel_parser.py`: Server-side Excel parser for bank statements
- `credit_card_excel_parser.py`: Server-side Excel parser for credit cards
- `bank_detector.py`: Automatic bank format detection
- `transaction_classifier.py`: 30+ transaction classification rules

**Architecture Decision:** VBA client-side processing chosen for high accuracy (95%+), low cost (no OCR fees), and team expertise. PDF-to-Excel conversion happens client-side using Tabula/Adobe tools. Standardized JSON format ensures reliable data exchange. Python parsers retained as backup for system resilience.