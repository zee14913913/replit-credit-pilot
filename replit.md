# Smart Credit & Loan Manager

## Overview

The Smart Credit & Loan Manager is a Flask-based web application designed to help customers manage their credit card statements, analyze spending patterns, evaluate loan eligibility, and stay informed about banking rates and payment reminders. The system ingests credit card statements (PDF/Excel), categorizes transactions, calculates Debt Service Ratio (DSR), simulates loan scenarios, and generates monthly financial reports.

## User Preferences

Preferred communication style: Simple, everyday language.

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
- PDF parsing using `pdfplumber` library
- Regex-based transaction extraction
- Statement metadata extraction (date, total, card number)
- Supports both PDF and Excel formats (Excel parsing code not shown but referenced)

**Transaction Categorization (`validate/categorizer.py`)**:
- Keyword-based categorization system
- 10+ predefined categories (Food & Dining, Transport, Shopping, etc.)
- Malaysia-specific merchant recognition (Grab, Petronas, Lazada, etc.)
- Fallback to "Others" category for unmatched transactions

**Statement Validation**:
- Validation score calculation
- Inconsistency detection (referenced but implementation not shown)
- Manual confirmation workflow before finalizing statements

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

**Report Generation (`report/pdf_generator.py`)**:
- ReportLab library for PDF creation
- Monthly financial summary reports
- Customer info, spending breakdown, DSR analysis
- Professional formatting with custom styles and tables

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