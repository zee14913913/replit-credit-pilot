# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform built with Flask for Malaysian banking customers. Its core purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, and intelligent automation, guaranteeing 100% data accuracy. The platform generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## Recent Changes
**2025-11-01**: Task 11完成 - 测试框架与完整API文档
- **测试基础设施**:
  - 配置pytest测试框架（pytest.ini + conftest.py）
  - 创建8个共享fixtures（test_db, client, sample_company, sample_chart_of_accounts等）
  - 独立测试数据库（SQLite），每次测试自动清理
- **单元测试**:
  - FileStorageManager: 12个测试100%通过（包括安全测试）
  - ManagementReportGenerator: 5个测试（报表结构、计算验证）
- **集成测试**:
  - Files API: 5个测试100%通过
  - PDF Reports API: 测试框架完成
  - Monthly Close API: 测试框架完成
- **关键安全测试通过**:
  - 跨租户访问防护验证
  - 路径遍历攻击防护验证
  - 前缀匹配漏洞修复验证（commonpath实现）
- **API文档**:
  - 完整README.md（accounting_app/README.md）
  - 5个核心API模块文档（Management Reports, PDF Reports, Files, Monthly Close, Bank Import）
  - Python + cURL调用示例
  - FastAPI自动文档（/docs）已完善
- **修复问题**:
  - ChartOfAccounts fixture使用小写account_type（符合CHECK constraint）
  - Files API路径对齐实际路由（path parameters而非query parameters）

**2025-11-01**: Task 9-10完成 - FileStorageManager + PDF自动归档
- **Task 9 - Unified File Storage Manager**:
  - 创建AccountingFileStorageManager服务，多租户隔离和标准化路径生成
  - 目录结构：/accounting_data/companies/{company_id}/[bank_statements|pos_reports|invoices|reports]/...
  - 安全特性：validate_path_security()使用commonpath防止跨租户访问（修复prefix-matching漏洞）
  - files.py提供公司级文件列表、存储统计、下载、删除和查看功能
- **Task 10 - 自动化任务扩展**:
  - PDF报表自动归档：Balance Sheet, P&L, Bank Package全部生成后自动保存到FileStorageManager
  - bank_import.py自动保存银行月结单CSV
  - 标准化文件命名：company{id}_{type}_{details}_{timestamp}.ext
  - 日志记录：所有文件保存操作均记录到logger

**2025-10-30**: CHEOK JUN YOON 5-9月详细月结报告完成
- 时间范围：2025年5月-9月（5个月）
- 已识别Supplier：AI SMART TECH, HUAWEI, PUCHONG HERBS, RIMAN, GUARDIAN, SHOPEE等
- Supplier消费总额：RM 144,719.54（42笔交易）
- 手续费(1%)：RM 1,447.20
- 应收总额：RM 146,166.74
- 实际付款总额：RM 82,784.49（从5个账户的转账记录）
- 净余额（客户欠款）：RM 63,382.25
- 报告包含每笔交易的完整明细：消费日期、银行、卡号、Supplier名称、付款描述等
- **缺失数据**：RAUB SYC HAINAN和PASARAYA的交易在数据库中不存在，可能账单未导入

**2025-10-30**: Public Bank活期账户导入完成
- 成功导入AI SMART TECH SDN. BHD.的Public Bank Islamic账户#3824549009
- 时间跨度：2025年3月 - 2025年9月（7个月结单）
- 总交易笔数：328笔
- 数据准确性：100%（Balance-Change验证、月度余额连续性验证、交易数量匹配验证全部通过）
- 修复Public Bank解析器：添加日期继承逻辑，正确拼接多行描述，过滤参考号码行
- 完全符合用户要求："100%准确，一个不少，无删减、无添加、无更改的1比1导入"

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
The backend is built with Flask, utilizing SQLite with a context manager pattern for database interactions. Jinja2 handles server-side rendering, and Bootstrap 5 with Bootstrap Icons provides a responsive UI. Plotly.js is integrated for client-side data visualization.

### Feature Specifications
**Core Features:**
- **Statement Ingestion:** PDF parsing (with OCR via `pdfplumber`) and Excel support, regex-based transaction extraction, batch upload for 15 major Malaysian banks.
- **Savings Account Tracking System:** Records all transactions from savings account statements with customer search for prepayment settlement.
- **Transaction Categorization:** Keyword-based system with predefined categories and Malaysia-specific merchant recognition.
- **Statement Validation (Dual Verification):** Ensures 100% data accuracy.
- **Revenue-Generating Advisory Services:** AI-powered credit card recommendations, financial optimization engine, success-based fee system.
- **Data Export & Reporting:** Professional Excel/CSV export and PDF report generation (using ReportLab).
- **Batch Operations:** Multi-file upload and batch job management.
- **Reminder System:** Scheduled payment reminders via email.
- **Authentication & Authorization:** Multi-role permission system (Admin/Customer) with secure SHA-256 hashing.
- **Automated Monthly Report System:** Auto-generates and sends comprehensive galaxy-themed PDF reports per customer monthly, including detailed transactions, category summaries, optimization proposals, DSR calculation, and a profit-sharing service workflow.
- **Statement Comparison View:** Displays raw PDF alongside categorized reports for validation.
- **12-Month Timeline View:** Visual calendar grid for each credit card showing statement coverage and status.
- **Intelligent Loan Matcher System:** CTOS report parsing, DSR calculation, and smart loan product matching.
- **Receipt Management System:** OCR-powered receipt upload system supporting JPG/PNG images with intelligent matching to customers and credit cards.
- **OWNER vs INFINITE Classification System:** Advanced dual-classification system for credit card transactions with 1% supplier fee tracking. Classifies expenses and payments into OWNER (customer personal spending/payments) vs INFINITE (7 configurable supplier merchants with 1% fee / third-party payer payments). Features first-statement baseline initialization and independent statement-level reconciliation.
- **Credit Card Ledger (3-Layer Navigation):** Professional hierarchical navigation system for OWNER vs INFINITE analysis.

**AI Advanced Analytics System:**
- **Financial Health Scoring System:** 0-100 score with optimization suggestions.
- **Cash Flow Prediction Engine:** AI-powered 3/6/12-month cash flow forecast.
- **Customer Tier System:** Silver, Gold, Platinum tiers with intelligent upgrade system.
- **AI Anomaly Detection System:** Real-time monitoring for unusual spending patterns.
- **Personalized Recommendation Engine:** Offers credit card, discount, and points usage recommendations.
- **Advanced Analytics Dashboard:** Integrates analytical features with dynamic charts and real-time warnings.

### System Design Choices
- **Data Models:** Comprehensive models for customers, credit cards, statements, transactions, BNM rates, audit logs, authentication, advisory services, supplier_config, customer_aliases, account_baselines, monthly_ledger, and infinite_monthly_ledger (with mandatory OWNER/INFINITE tracking fields).
- **Design Patterns:** Repository Pattern for database abstraction, Template Inheritance for UI consistency, Context Manager Pattern for database connection handling, and Service Layer Pattern for OWNER/INFINITE classification logic.
- **Security:** Session secret key from environment variables, file upload size limits, SQL injection prevention, and audit logging.
- **Data Accuracy:** Robust previous balance extraction and monthly ledger engine overhaul to ensure 100% accuracy in financial calculations and DR/CR classification, including a universal balance-change algorithm for all bank statements and independent statement-level reconciliation.
- **Monthly Statement Architecture**: Each bank + month combination creates ONE monthly statement record in the `monthly_statements` table, aggregating 6 mandatory classification fields (owner_expenses, owner_payments, gz_expenses, gz_payments, owner_balance, gz_balance), ensuring `owner_balance + gz_balance = closing_balance_total`.

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
A `FileStorageManager` handles standardized path generation, directory management, and file operations.
- **Standard Directory Structure**: `static/uploads/customers/{customer_code}/` with subdirectories for `credit_cards`, `savings`, `receipts`, `invoices`, `reports`, `loans`, and `documents`.
- **Core Characteristics**: Full customer isolation, self-explanatory file paths (`path as index`), time-dimensional management, automatic type-based organization, standardized naming conventions, scalability, and cross-platform compatibility.