# Smart Credit & Loan Manager

## Recent Changes (2025-10-26)

**Session 3: 用户新标准实施 - 文件命名、界面优化、标准文档最终版**:
- ✅ 修改文件命名规则：从`Bank_Last4_Date.pdf`改为`Bank_Date.pdf`（移除卡号后4位）
- ✅ Admin Dashboard优化：添加"Statement OS"列，调整为标准13列布局
- ✅ 修正GZ数据显示颜色：从粉色改为深紫色(#322446)，符合3色标准
- ✅ 后端数据传递修正：closing_balance_total正确别名为closing_balance
- ✅ 创建最终标准文档(`docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`)：
  - 7个固定供应商列表（7SL, HUAWEI, PASAR RAYA等）
  - 手动验证流程（100%准确，零容差）
  - 第一个月Previous Balance = 100% Own's余额规则
  - 完整上传流程（14步，含提醒系统）
  - 月度报表生成规则（30/31号生成，1号发送）
- ✅ Architect审查通过，所有修改符合要求

**Session 2: 系统标准化文档**:
- ✅ 创建完整的《信用卡账单系统设置标准文档》(`docs/CREDIT_CARD_STATEMENT_STANDARDS.md`)
  - 11个主要章节，涵盖所有系统设置细节
  - 数据库架构标准（表结构、字段定义、约束、索引）
  - 月度账单合并规则（ONE BANK + ONE MONTH = ONE RECORD）
  - OWNER vs INFINITE分类系统完整规则
  - 文件存储标准（统一命名规范、目录结构）
  - 双重验证机制（数学验证 + PDF交叉验证）
  - 15家支持银行列表及特殊处理规则
  - PDF解析Regex规则及OCR处理
  - UI/UX显示格式标准（3色严格限制）
  - 自动化流程和批量操作标准

**Session 1: 系统清理 - 删除废弃功能和代码**:
- ✅ 删除废弃的upload_statement_deprecated路由（324行代码）
- ✅ 删除废弃的数据库表（banking_news, pending_news, budgets）
- ✅ 从db/init_db.py移除废弃表的CREATE语句
- ✅ 在statements表添加废弃标记注释（保留用于历史数据查询）
- ✅ 整理迁移脚本到migrations/archived/和scripts/archived/文件夹
- ✅ 创建归档README说明迁移历史
- ✅ 修复端口5000占用问题，服务器正常运行
- ✅ Architect审查通过，确认所有更改安全且正确

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation, guaranteeing 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions
The platform features a strict professional design with **MINIMAL 3-COLOR PALETTE ONLY**:
- **Black (#000000)**: Primary background
- **Hot Pink (#FF007F)**: Primary accent, highlights, revenue, income, credits
- **Dark Purple (#322446)**: Secondary accent, expenses, debits, borders

No other colors are permitted. The design system emphasizes clean, professional layouts with bilingual support (English/Chinese). All CSS styling follows this strict color constraint.

### Technical Implementations
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization.

### Feature Specifications

**Core Features:**
- **Statement Ingestion:** Supports PDF parsing (with OCR via `pdfplumber`) and Excel, with regex-based transaction extraction and batch upload for 15 major Malaysian banks.
- **Savings Account Tracking System:** Records all transactions from savings account statements (Maybank, GX Bank, HLB, CIMB, UOB, OCBC, Public Bank) with search-by-customer-name for prepayment settlement.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system, and consultation request system.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Multi-role permission system (Admin/Customer) with secure SHA-256 hashing.
- **Customer Authorization Agreement:** Bilingual service agreement.
- **Statement Organization System:** Organizes statements by `statement_date` with automatic monthly folder structure.
- **Automated Monthly Report System:** Auto-generates and sends comprehensive galaxy-themed PDF reports per customer monthly, including detailed transactions, category summaries, optimization proposals, DSR calculation, and a profit-sharing service workflow.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View:** Visual calendar grid for each credit card showing statement coverage, amounts, transaction counts, and verification status across a rolling 12-month window.
- **Intelligent Loan Matcher System:** CTOS report parsing, DSR calculation, and smart loan product matching. Automatically extracts monthly commitments from CTOS PDFs, calculates debt service ratio, and matches clients with eligible loan products from a comprehensive banking database.
- **Receipt Management System:** OCR-powered receipt upload system supporting JPG/PNG images. Features automatic card number, date, amount, and merchant name extraction using pytesseract. Intelligent matching engine auto-matches receipts to customers and credit cards based on card_last4, transaction date (±3 days), and amount (±1%). Receipts are organized by customer/card number with auto-filing.
- **OWNER vs INFINITE Classification System:** Advanced dual-classification system for credit card transactions with 1% supplier fee tracking. Classifies expenses into OWNER (customer personal spending) vs INFINITE (7 configurable supplier merchants with 1% fee), and payments into OWNER (customer payments) vs INFINITE (third-party payer payments). Features first-statement baseline initialization (Previous Balance = 100% OWNER debt), supplier configuration management, customer alias support, and monthly ledger tracking. Implements independent statement-level reconciliation ensuring each bank's monthly statement is recorded separately without aggregation.
- **Credit Card Ledger (3-Layer Navigation):** Professional hierarchical navigation system for OWNER vs INFINITE analysis, providing customer list, year-month timeline, and detailed monthly statement reports.

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns.
- **Personalized Recommendation Engine:** Offers credit card, discount, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements (legacy), monthly_statements (active), monthly_statement_cards, transaction_owner_overrides, transactions, BNM rates, audit logs, authentication, advisory services, supplier_config, customer_aliases, account_baselines, monthly_ledger, and infinite_monthly_ledger (with mandatory OWNER/INFINITE tracking fields).
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, Context Manager Pattern for database connection handling, and Service Layer Pattern for OWNER/INFINITE classification logic.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Implemented robust previous balance extraction and monthly ledger engine overhaul to ensure 100% accuracy in financial calculations and DR/CR classification, including a universal balance-change algorithm for all bank statements. Independent statement-level reconciliation guarantees each monthly statement is tracked separately without data aggregation.
- **Monthly Statement Architecture**: Each bank + month combination creates ONE monthly statement record in the `monthly_statements` table, with a unique constraint on (customer_id, bank_name, statement_month). This table aggregates 6 mandatory classification fields (owner_expenses, owner_payments, gz_expenses, gz_payments, owner_balance, gz_balance), ensuring `owner_balance + gz_balance = closing_balance_total`. The `monthly_statement_cards` table links contributing credit cards, and the `transactions` table includes `monthly_statement_id`, `card_last4`, `owner_flag`, and `classification_source`.

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

#### Unified File Storage Architecture
A `FileStorageManager` handles standardized path generation, directory management, and file operations.
- **Standard Directory Structure**: `static/uploads/customers/{customer_code}/`
  - **Customer Code Format**: `Be_rich_{INITIALS}` (e.g., Be_rich_CCC for CHANG CHOON CHOW)
  - **Credit Cards**: `credit_cards/{bank_name}/{YYYY-MM}/{BankName}_{Last4}_{YYYY-MM-DD}.pdf`
  - **Savings Accounts**: `savings/{bank_name}/{YYYY-MM}/{BankName}_{AccountNum}_{YYYY-MM-DD}.pdf`
  - **Payment Receipts**: `receipts/payment_receipts/{YYYY-MM}/{YYYY-MM-DD}_{Merchant}_{Amount}_{card_last4}.{jpg|png}`
  - **Merchant Receipts**: `receipts/merchant_receipts/{YYYY-MM}/`
  - **Supplier Invoices**: `invoices/supplier/{YYYY-MM}/Invoice_{SupplierName}_{InvoiceNum}_{Date}.pdf`
  - **Customer Invoices**: `invoices/customer/{YYYY-MM}/`
  - **Monthly Reports**: `reports/monthly/{YYYY-MM}/Monthly_Report_{YYYY-MM}.pdf`
  - **Annual Reports**: `reports/annual/{YYYY}/Annual_Report_{YYYY}.pdf`
  - **Loan Applications**: `loans/applications/{YYYY-MM}/`
  - **CTOS Reports**: `loans/ctos_reports/{YYYY-MM}/`
  - **Documents**: `documents/{contracts|identification|misc}/`
- **Core Characteristics**:
  - Full customer isolation with independent folders.
  - Self-explanatory file paths (`path as index`).
  - Time-dimensional management (automatic year-month classification).
  - Automatic type-based organization.
  - Standardized naming conventions for all files.
  - Scalable for future file types.
  - Cross-platform compatibility using relative paths.