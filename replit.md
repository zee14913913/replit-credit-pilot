# Smart Credit & Loan Manager

## Overview
The Smart Credit & Loan Manager is a Premium Enterprise-Grade SaaS Platform for Malaysian banking customers, built with Flask. Its purpose is to provide comprehensive financial management, including credit card statement processing, advanced analytics, budget management, batch operations, and intelligent automation. The platform features a sophisticated dark jewel-tone UI and guarantees 100% data accuracy. It generates revenue through AI-powered advisory services, offering credit card recommendations, financial optimization suggestions (debt consolidation, balance transfers, loan refinancing), and a success-based fee model. The business vision includes expanding into exclusive mortgage interest discounts and SME financing.

## User Preferences
Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### UI/UX Decisions
The platform utilizes a Premium Enterprise UI with **Vibrant Orange + Black + Silver** color scheme. Key design elements include orange header/footer sections, silver-white navigation buttons with black-gold text, orange accent borders and glows, and professional Inter typography. It supports multi-language (English/Chinese), dark/light theme toggle, and adheres to a sophisticated, high-end enterprise aesthetic.

**Color Scheme (Updated 2025-10-11 - BRIGHT ORANGE THEME):**
- **Header/Footer**: Bright orange gradient (#FF7043 → #FF5722) with luminous white text (rgba(255,255,255,0.98)) + subtle glow (text-shadow: 0 0 5px rgba(255,255,255,0.15))
- **Navigation Buttons**: Silver-white gradient background (#F5F5F5 → #E0E0E0) with black-gold bold text (#3D3020, font-weight 900, hover: #2C2416)
- **Main Content**: Bright orange gradient backgrounds (#FF7043 → #FF5722) with white borders and bright white bold typography
  - Cards: Bright orange gradient background + 3px white border (rgba(255,255,255,0.9))
  - All text: Bright white (rgba(255,255,255,0.95)) with bold weights (700-900) - FORCED with !important
  - Headings h1-h6: rgba(255,255,255,0.95) font-weight 700-900 with white glow
  - Body text: rgba(255,255,255,0.95) font-weight 700
  - Table headers: rgba(255,255,255,0.95) font-weight 900
  - Table data cells: rgba(255,255,255,0.95) font-weight 700
  - Stat values: rgba(255,255,255,0.95) font-weight 900 with white glow
  - Stat labels: rgba(255,255,255,0.95) font-weight 900
  - Decorative corners: White (rgba(255,255,255,0.5))
- **Theme Toggle**: Sun/moon icon button in navigation, localStorage persistence (main content only)
- **Card Title System (Updated 2025-10-11)**: Two variant classes for different visual emphasis
  - .card-title-gold: Light golden-white tone (#F5DEB3) with soft glow effect for subtle elegance
  - .card-title-glow: Luminous white (rgba(255,255,255,0.98)) with strong multi-layer glow for premium emphasis
- **Navigation Hover Effects (Updated 2025-10-11)**: Pure white glow on all navigation elements (no yellow/gold tints)
  - nav-link:hover: White text-shadow and white box-shadow only
  - Language buttons: White glow on hover and active states
  - Theme toggle: White border and glow effects on hover

**Typography Enhancement:**
- Company name (header): rgba(255,255,255,0.98) font-weight 900 + text-shadow: 0 0 5px rgba(255,255,255,0.15)
- Company name (footer): rgba(255,255,255,0.98) font-weight 900 + text-shadow: 0 0 8px rgba(255,255,255,0.2)
- Footer headings: font-size 1.35rem, font-weight 900, letter-spacing 0.08em (increased from 1rem for better distinction)
- Footer links: font-size 0.95rem, font-weight 700
- All content typography: Silver-white (#C0C0C0) with bold weights (700-900)

**Button Design System (Updated 2025-10-11):**
- **Primary Action Buttons**: White glowing buttons (.btn-white-glow) with black-gold bold text (#3D3020, hover: #2C2416), silver borders, and gold-tinted glow effects. Used for all major actions (submit, confirm, publish, advisory requests).
- **Secondary Action Buttons**: Outline buttons (.btn-outline-*) for secondary actions (cancel, view, back).
- **Navigation Buttons**: Professional white buttons (.btn-professional) with black-gold bold text (#3D3020, hover: #2C2416, font-weight 900) for navigation and less critical actions.
- **All white background buttons now feature black-gold text instead of pure black for premium aesthetic.**

**Compact Layout Optimization (Updated 2025-10-10):**
- **Spacing System**: Reduced all spacing variables by ~20-30% for tighter, more professional layout
  - Container padding: 2rem 1.5rem (was 4rem 3rem)
  - Card padding: 1.25rem (was 2rem)
  - Table/Form padding: Reduced to 0.625rem-0.875rem range
- **Typography**: Optimized line-height (1.5 for body, 1.3 for headings) and reduced margin-bottom across all elements
- **Visual Density**: Compact stat cards, tighter dividers, reduced alert/form spacing for professional enterprise feel
- **Responsive**: Maintained compact spacing across all breakpoints

**Customer Registration/Login Form Design (Updated 2025-10-11 - BRIGHT ORANGE THEME):**
- **Modern Orange-Themed Forms**: Complete redesign with bright orange backgrounds (#FF7043 → #FF5722), white borders, and silver-white bold typography
- **Registration Form** (800px container):
  - **Orange Header**: 120px circular icon with white glow, stars icon, white bold title (3.2rem font-weight 700), white subtitle (font-weight 600)
  - **Progressive 3-Step Layout**: Separate orange gradient cards with numbered badges (1-2-3)
    - Step 1: Your Identity (Full Name, Email, Phone)
    - Step 2: Financial Profile (Monthly Income with RM prefix)
    - Step 3: Account Security (Password, Confirm Password)
  - **Card Styling**: Orange gradient backgrounds (#E64A19 → #D84315), 3px white border, 2.5rem padding
  - **Enhanced Inputs**: 1.15rem font, 1.25rem padding, dark semi-transparent bg, white glow on focus
  - **Submit Button**: 1.5rem padding, white glow effect, rocket icon
- **Login Form - Two-Column Layout** (1400px container):
  - **Left Column (col-lg-5)**: Login form card with orange background
    - **Orange Hero Section**: White shield icon (rgba(255,255,255,0.95)) with white glow, white divider line, "Customer Portal" white bold title (font-weight 700) with text-shadow glow, white subtitle (font-weight 600)
    - Email and Password fields in orange card (3rem padding)
    - **All Labels**: White (#FFFFFF) font-weight 700 with white icon decorations
    - **Enhanced Inputs**: 1.15rem font, 1.25rem padding, dark semi-transparent bg, white glow on focus
    - **Submit Button**: White glow login button with arrow icon (1.5rem padding)
    - Helper text: rgba(255,255,255,0.85) font-weight 600
    - Register link: rgba(255,255,255,0.95) font-weight 700 with white glow on hover
  - **Right Column (col-lg-7)**: Platform features showcase with orange background
    - **"Why Choose INFINITE GZ?"** section with white bold title (font-weight 700) + white stars icon
    - **4 Core Features** with 60px icon cards (white icons) and white bold descriptions:
      1. AI-Powered Financial Advisory (CPU icon)
      2. Zero-Risk Guarantee 50% Profit Sharing (Cash-coin icon)
      3. Complete Financial Management (Graph icon)
      4. Bank-Grade Security (Shield icon)
    - **All Feature Text**: Titles #FFFFFF font-weight 700, descriptions rgba(255,255,255,0.9) font-weight 600
    - **Trust Indicators** section: Orange background with white borders
      - Values: #FFFFFF font-weight 900 (100%, 24/7, 50%)
      - Labels: rgba(255,255,255,0.95) font-weight 900
    - All content fully translated (EN/ZH) using i18n system
- **Shared Features**: 
  - slideDown animations for alerts
  - White icon decorations on all labels
  - White glow effects on links (text-shadow)
  - Full i18n support with all text translatable (EN/ZH)
  - Responsive design maintaining visual impact (stacks on mobile)
  - Consistent orange theme: bright orange backgrounds + white borders + bright white bold text

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