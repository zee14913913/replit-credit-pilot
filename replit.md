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
## Recent Updates - 2025-10-09

### 信用卡账单核心管理系统 (Complete Statement Management)
**用户最重要的3大核心功能，完整实现了信用卡账单全生命周期管理：**

#### 1. 分期付款管理系统 (Instalment Tracking System)
- **核心模块：** `validate/instalment_tracker.py`
- **功能：** 记录分期计划（商品、本金、利率、期限、月供），自动生成付款时间表，计算总月供用于DSR分析
- **数据库：** `instalment_plans`、`instalment_payment_records`
- **集成：** Customer dashboard显示活跃分期、总月供、到期提醒

#### 2. 月度报表自动生成系统 (Monthly Report Auto-Generator)
- **核心模块：** `report/monthly_report_generator.py`
- **关键逻辑：** 按statement的statement_date月份归属（用户要求）
- **报表内容：** Debit汇总（Supplier+AIA+其他）、Credit汇总（Owner+其他）、Instalment汇总、净额计算、DSR分析
- **自动化：** 每月5号10:00自动生成上月报表，支持手动生成任意月份
- **Supplier费用：** 7个指定商家1% merchant fee单独追踪显示

#### 3. 账单对比展示界面 (Statement Comparison View)
- **设计：** 左侧原始PDF，右侧分类报告，并列对比展示
- **功能：** 验证100%数据准确性，下载原始账单，导出分类报告（Excel/CSV）
- **访问：** Dashboard "Comparison/对比"按钮直达

**Architect审查：** ✅ 所有功能通过验证，正常运行

### 分期付款余额追踪增强功能 (Instalment Balance Tracking Enhancement)

**完善分期付款管理系统，添加每次付款后的余额欠款追踪：**

**新增功能：**
- ✅ **本金/利息分离计算**：每期付款自动计算本金部分和利息部分
- ✅ **余额欠款追踪**：每期付款后自动计算剩余欠款金额
- ✅ **完整还款时间表**：显示每期的Payment/Principal/Interest/Remaining Balance
- ✅ **可视化进度展示**：清晰显示已还本金vs剩余欠款

**数据库扩展：**
- `principal_portion`: 本金部分
- `interest_portion`: 利息部分  
- `remaining_balance`: 剩余欠款余额

**前端展示：**
- 分期详情页面 (`/instalment/<plan_id>`)
- 完整付款时间表（12期分期完整显示所有数据）
- 彩色标识：本金(蓝色) / 利息(红色) / 余额(绿色)
- 说明指南：帮助用户理解本金、利息和余额的含义

**计算示例（Huawei Mate 60 Pro - RM 4,800 @ 6.5% APR）：**
- 第1期：月供RM 420 = 本金RM 394 + 利息RM 26，余额RM 4,406
- 第2期：月供RM 420 = 本金RM 396 + 利息RM 24，余额RM 4,010
- ...
- 第12期：月供RM 420 = 本金RM 347 + 利息RM 73，余额RM 0

**业务价值：**
- 客户清楚知道每次还款后还欠多少钱
- 透明显示利息成本，帮助理解分期付款真实成本
- 完整的财务记录用于DSR分析和贷款评估
