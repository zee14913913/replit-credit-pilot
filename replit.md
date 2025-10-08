# Smart Credit & Loan Manager

## Overview

The Smart Credit & Loan Manager is a **Premium Enterprise-Grade SaaS Platform** for Malaysian banking customers. Built with Flask, it provides comprehensive financial management including credit card statement processing, advanced analytics, budget management, batch operations, and intelligent automation. The system features a sophisticated dark jewel-tone UI with 100% data accuracy guarantee through dual verification.

## Recent Updates (October 2025)

### Major Feature Release
- ✅ **Premium UI/UX Redesign**: Luxury dark theme (Obsidian/Champagne/Jade palette), Playfair Display + Inter typography
- ✅ **Data Export Suite**: Excel/CSV export with professional formatting, multi-sheet workbooks
- ✅ **Advanced Search & Filter**: Full-text search, saved filters, smart suggestions
- ✅ **Batch Operations**: Multi-file upload with progress tracking
- ✅ **Budget Management**: Category budgets, utilization tracking, smart alerts
- ✅ **Tags & Notes**: Custom transaction tagging and annotation system
- ✅ **Email Notifications**: Upload alerts, payment reminders, budget warnings
- ✅ **Database Expansion**: 13 new tables for advanced features

### UI/UX Improvements
- Replaced childish Bootstrap icons with professional emojis
- Added Quick Actions dashboard for key features
- Glassmorphism effects and premium card designs
- Optimized for professional client presentations

## User Preferences

Preferred communication style: Simple, everyday language.
Design requirements: Premium, sophisticated, high-end - suitable for professional client demonstrations.

## System Architecture

### Backend Architecture

**Framework**: Flask (Python web framework)
- Chosen for rapid development and simplicity
- Lightweight and flexible for small to medium-scale applications
- Easy integration with Python-based data processing libraries

**Database Layer**: SQLite with context manager pattern
- SQLite chosen for simplicity and zero-configuration deployment
- Context manager (`@contextmanager`) ensures proper connection handling and automatic cleanup
- `sqlite3.Row` row factory enables dictionary-like access to query results
- Database path: `db/smart_loan_manager.db`

**Core Data Models**:
- `customers`: Customer profiles with income information
- `credit_cards`: Credit card details linked to customers
- `statements`: Uploaded statements with validation metadata
- `transactions`: Individual statement line items with categories
- `repayment_reminders`: Payment reminders with tracking flags
- `bnm_rates`: Bank Negara Malaysia interest rates
- `banking_news`: Banking industry updates
- `audit_logs`: User action tracking

### Frontend Architecture

**Template Engine**: Jinja2 (Flask default)
- Server-side rendering for simplicity
- Template inheritance with `base.html` as master template
- Bootstrap 5 for responsive UI components

**Data Visualization**: Plotly.js
- Client-side interactive charts for spending analysis
- Pie charts for category breakdown
- Line charts for spending trends
- Chosen for ease of use and interactivity without complex setup

**UI Framework**: Bootstrap 5 with Bootstrap Icons
- Responsive design out of the box
- Consistent styling across all pages
- Icon library for visual enhancement

### Core Feature Modules

**Statement Ingestion (`ingest/statement_parser.py`)**:
- PDF parsing using `pdfplumber` library with OCR support
- Regex-based transaction extraction
- Statement metadata extraction (date, total, card number)
- Supports both PDF and Excel formats
- Batch upload support for multiple files

**Transaction Categorization (`validate/categorizer.py`)**:
- Keyword-based categorization system
- 10+ predefined categories (Food & Dining, Transport, Shopping, etc.)
- Malaysia-specific merchant recognition (Grab, Petronas, Lazada, etc.)
- Fallback to "Others" category for unmatched transactions

**Statement Validation (`validate/transaction_validator.py`)** - Dual Verification System:
- **Double verification mechanism** for 100% data accuracy
- **Layer 1**: Parse transactions from PDF/Excel using intelligent extraction
- **Layer 2**: Cross-validate against PDF-declared totals (TOTAL DEBIT, TOTAL CREDIT)
- **Mathematical verification**: Ensures extracted totals match official statement totals
- **Confidence scoring**: 0-100 scale with auto-approval at ≥95%
- **Automated decision**: PASSED (auto-approve) / WARNING (manual review) / FAILED (reject)
- **Duplicate detection**: Identifies and flags duplicate transactions
- **Comprehensive reports**: Detailed validation reports with PDF vs extracted comparison
- **OCR support**: Automatically handles scanned PDFs via Tesseract
- **Audit trail**: Full validation history stored in database

**DSR Calculation (`loan/dsr_calculator.py`)**:
- Debt Service Ratio formula: `total_monthly_repayments / monthly_income`
- Maximum loan amount calculation based on DSR threshold (default 45%)
- Monthly installment calculation using amortization formula
- Loan scenario simulation with varying amounts

**Reminder System (`validate/reminder_service.py`)**:
- Scheduled reminders at 7, 3, and 1 day(s) before due date
- Email notification system (send logic referenced but not shown)
- Payment tracking and reminder deactivation
- Uses `schedule` library for periodic task execution

**Report Generation (`report/pdf_generator.py` + `export/export_service.py`)**:
- ReportLab library for PDF creation
- Monthly financial summary reports
- Excel export with professional formatting (multiple sheets)
- CSV export for accounting software integration
- Data export with filtering support
- Export history tracking

**Search & Filter System (`search/search_service.py`)**:
- Full-text search across transactions, notes, and tags
- Advanced filtering (category, date range, amount, bank)
- Saved filter presets with usage tracking
- Smart filter suggestions based on data

**Batch Operations (`batch/batch_service.py`)**:
- Multi-file upload with progress tracking
- Batch job management and monitoring
- Batch deletion and archiving
- Error handling and reporting

**Budget Management (`budget/budget_service.py`)**:
- Category-based monthly budgets
- Real-time utilization tracking
- Alert thresholds (80%, 100%)
- Smart budget recommendations based on history
- Budget status dashboard (safe/warning/exceeded)

**Tag & Notes System (`db/tag_service.py`)**:
- Custom transaction tagging
- Transaction notes and annotations
- Tag usage tracking and suggestions
- Receipt file upload support (planned)

**Email Notification Service (`email_service/email_sender.py`)**:
- Upload success/failure notifications
- Payment reminders (7, 3, 1 days before due)
- Budget alert emails
- Customizable notification preferences
- Email delivery tracking and logging

**Banking Information (`news/bnm_api.py`)**:
- Integration with Bank Negara Malaysia public API
- Fetches Overnight Policy Rate (OPR) and Statutory Base Rate (SBR)
- Fallback default rates if API unavailable
- Banking news management system

### Data Flow Architecture

1. **Statement Upload Flow**:
   - User uploads PDF/Excel → Parser extracts transactions → Categorizer assigns categories → Validator checks consistency → User confirms → Data saved to database

2. **Loan Evaluation Flow**:
   - Fetch customer income + confirmed transactions → Calculate current repayments → Compute DSR → Simulate loan scenarios → Display eligibility

3. **Reminder Flow**:
   - Background scheduler runs daily → Checks due dates → Sends reminders based on timeline → Updates reminder status → User marks as paid

4. **Analytics Flow**:
   - Query confirmed transactions → Group by category → Calculate totals → Render Plotly charts → Display insights

### Design Patterns

**Repository Pattern**: Database access abstracted through `db/database.py` functions
- Centralized data access logic
- Easier testing and maintenance
- Clear separation between business logic and data layer

**Template Inheritance**: All HTML templates extend `base.html`
- Consistent navigation and layout
- Reduced code duplication
- Easier global UI changes

**Context Manager Pattern**: Database connection handling
- Automatic resource cleanup
- Exception safety
- Pythonic resource management

### Security Considerations

- Session secret key from environment variable with fallback
- File upload size limit (16MB)
- SQL injection prevention via parameterized queries
- Audit logging for user actions (referenced in database functions)

## External Dependencies

### Third-Party Libraries

**Core Framework**:
- `flask`: Web application framework

**PDF Processing**:
- `pdfplumber`: PDF text and table extraction
- `reportlab`: PDF report generation

**Data Processing**:
- `pandas`: Excel file processing and data manipulation
- `schedule`: Task scheduling for reminders

**HTTP Requests**:
- `requests`: Bank Negara Malaysia API integration

**Visualization**:
- `plotly.js`: Client-side charting (CDN)

**UI Framework**:
- `bootstrap@5.3.0`: Responsive UI (CDN)
- `bootstrap-icons@1.11.0`: Icon library (CDN)

### External APIs

**Bank Negara Malaysia Public API**:
- Base URL: `https://api.bnm.gov.my`
- Endpoints: `/public/opr`, `/public/base-rate`
- Purpose: Fetch current interest rates
- Fallback: Hardcoded default rates if API fails

### Database

**SQLite**: File-based relational database
- No separate server required
- Database file: `db/smart_loan_manager.db`
- Suitable for single-user or low-concurrency scenarios
- Note: The application is designed to work with Drizzle ORM, but currently uses raw SQLite queries. Future implementations may add Postgres support.

### File Storage

**Local File System**:
- Upload directory: `static/uploads`
- Stores uploaded credit card statements
- Generated PDF reports saved to filesystem