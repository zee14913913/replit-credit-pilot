# CreditPilot System Architecture

**Version**: 3.0.0  
**Last Updated**: 2025-11-17  
**Status**: Production-Ready

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Directory Structure](#directory-structure)
3. [Core Entry Points](#core-entry-points)
4. [Configuration Management](#configuration-management)
5. [Active Files Inventory](#active-files-inventory)
6. [Deprecated Files](#deprecated-files)
7. [Dependencies & Imports](#dependencies--imports)
8. [Data Flow](#data-flow)
9. [Critical Files (DO NOT MODIFY)](#critical-files-do-not-modify)
10. [Safe-to-Modify Files](#safe-to-modify-files)

---

## System Overview

CreditPilot is a dual-runtime system:
- **Flask Application** (app.py): Main web server on port 5000
- **FastAPI Backend** (accounting_app/main.py): API services on port 8000

### Technology Stack
- **Backend**: Flask, FastAPI
- **Database**: SQLite (dev), PostgreSQL (prod)
- **AI Services**: Perplexity AI (primary), OpenAI (backup)
- **PDF Processing**: Google Document AI
- **Frontend**: Bootstrap 5, Plotly.js, Jinja2

---

## Directory Structure

```
creditpilot/
├── app.py                          # Flask main entry point (PORT 5000)
├── accounting_app/                 # FastAPI backend (PORT 8000)
│   ├── main.py                     # FastAPI entry point
│   ├── services/                   # Business logic services
│   └── tasks/                      # Background tasks
├── config/                         # ⭐ SINGLE SOURCE OF TRUTH for all configs
│   ├── app_settings.json          # Main application settings
│   ├── colors.json                # UI color palette (v2.0.0)
│   ├── database.json              # Database configurations
│   └── business_rules.json        # Business logic rules
├── db/                            # Database and migrations
│   ├── database.py                # Core DB manager
│   ├── smart_loan_manager.db      # SQLite database file
│   └── migrations/                # SQL migrations
├── templates/                     # Jinja2 HTML templates (101 files)
├── static/                        # Static assets
│   ├── css/                       # Stylesheets (7 files)
│   └── uploads/                   # User-uploaded files
├── ingest/                        # Data ingestion modules
├── validate/                      # Data validation services
├── report/                        # Report generation
├── loan/                          # Loan evaluation engine
├── services/                      # Shared business services
├── scripts/                       # Utility scripts
├── docs/                          # Documentation
├── DEPRECATED/                    # ⚠️ Archived legacy files
└── replit.md                      # Project documentation
```

---

## Core Entry Points

### 1. Flask Application (app.py)
**Purpose**: Main web server serving UI and customer-facing features  
**Port**: 5000  
**Key Routes**:
- `/` - Homepage/Dashboard
- `/credit-cards` - Credit card management
- `/loans` - Loan evaluation
- `/customers` - Customer management
- `/reports` - Report center

**DO NOT MODIFY** unless you understand the entire routing system.

### 2. FastAPI Backend (accounting_app/main.py)
**Purpose**: API backend for audit logs, notifications, AI services  
**Port**: 8000  
**Key Endpoints**:
- `/api/audit` - Audit logging
- `/api/notifications` - Real-time notifications
- `/api/ai-assistant` - AI chat service
- `/health` - Health check

**SAFE TO EXTEND** with new API endpoints.

---

## Configuration Management

### ⭐ SINGLE SOURCE OF TRUTH

**ALL configurations MUST be loaded from `config/` directory:**

| File | Purpose | Used By | Status |
|------|---------|---------|--------|
| `config/app_settings.json` | Application settings, server config, feature flags, basic DB config | app.py, main.py, all services | ✅ Active |
| `config/colors.json` | UI color palette (3-color system) | All frontend, PDF generators, email templates | ✅ Active |
| `config/database.json` | Detailed database configuration (pools, migrations, schema) | Future: db/database.py, migrations | ⏳ Prepared |
| `config/business_rules.json` | Business logic, calculation formulas | loan/, validate/, report/ | ✅ Active |

**NOTE**: `config/database.json` is prepared for future database configuration unification. Current code (db/database.py) still uses hardcoded paths. Migration to unified config is planned for future release.

### ❌ DEPRECATED Config Locations

**DO NOT USE** these old config patterns:
- Hardcoded settings in Python files
- Multiple `settings.json` files in different folders
- Environment variables for non-secret configs
- Inline config dictionaries

### ✅ Correct Config Usage

**Python**:
```python
import json

with open('config/app_settings.json', 'r') as f:
    config = json.load(f)['creditpilot_app']

# Use config values
port = config['server']['flask']['port']
```

**Environment Variables** (secrets only):
```python
import os

api_key = os.getenv('OPENAI_API_KEY')  # ✅ Good - API key
database_url = os.getenv('DATABASE_URL')  # ✅ Good - connection string

# ❌ Bad - Don't use env vars for non-secret configs
port = os.getenv('PORT', 5000)  # Use config/app_settings.json instead
```

---

## Active Files Inventory

### Total Active Files (as of 2025-11-17)

| Type | Count | Status |
|------|-------|--------|
| Python modules | 386 | Active |
| HTML templates | 101 | Active |
| CSS stylesheets | 7 | Active (1 deprecated) |
| Configuration files | 6 | Managed |
| Total project files | ~500 | Under version control |

### Core Python Modules (DO NOT DELETE)

**Database & Migrations**:
- `db/database.py` - Core database manager
- `db/init_db.py` - Database initialization
- `db/migrations_*.py` - Schema migrations

**Data Ingestion**:
- `ingest/statement_parser.py` - Credit card statement parser
- `ingest/savings_parser.py` - Savings account parser
- `ingest/receipt_parser.py` - Receipt OCR processor

**Business Logic**:
- `validate/transaction_validator.py` - Transaction validation
- `validate/categorizer.py` - Transaction categorization
- `loan/dsr_calculator.py` - Debt Service Ratio calculator

**Reporting**:
- `report/monthly_report_generator.py` - Monthly statements
- `report/pdf_generator.py` - PDF report generation
- `accounting_app/services/pdf_report_generator.py` - Accounting reports

**Services**:
- `services/monthly_report_scheduler.py` - Automated report scheduling
- `services/ai_assistant_v3.py` - AI chat service

---

## Deprecated Files

**Location**: `DEPRECATED/` folder

**Current Contents**:
- `DEPRECATED/themes/galaxy-theme.css` - Old UI theme (replaced by unified color system)

**Policy**: See `DEPRECATED/README.md` for full policy.

**⚠️ WARNING**: Never import or use files from `DEPRECATED/` in active code.

---

## Dependencies & Imports

### External Dependencies
See `requirements.txt` for full list. Key dependencies:
- `flask` - Web framework
- `fastapi` - API framework
- `pandas` - Data processing
- `openpyxl` - Excel generation
- `pdfplumber` - PDF parsing
- `reportlab` - PDF creation
- `openai` - OpenAI API client

### Internal Module Structure

**Import Hierarchy**:
```
app.py
├── db.database
├── ingest.*
├── validate.*
├── loan.*
├── report.*
└── services.*

accounting_app/main.py
├── accounting_app.services.*
├── accounting_app.tasks.*
└── db.database
```

**Cross-Module Dependencies**:
- All modules can import from `db/database.py`
- All modules can import from `config/*` (via json.load())
- Report generators can import from `ingest/` and `validate/`

**❌ Circular Import Prevention**:
- Database module (`db/database.py`) MUST NOT import from other modules
- Config files are JSON only - no Python imports

---

## Data Flow

### 1. Credit Card Processing Flow
```
User Upload PDF
    ↓
ingest/statement_parser.py
    ↓
validate/transaction_validator.py
    ↓
validate/categorizer.py
    ↓
db/database.py (save)
    ↓
report/monthly_report_generator.py
```

### 2. Loan Evaluation Flow
```
User Input (CTOS data)
    ↓
loan/dsr_calculator.py
    ↓
loan/risk_engine.py
    ↓
loan/product_matcher.py
    ↓
Display recommendations
```

### 3. AI Assistant Flow
```
User Question
    ↓
accounting_app/services/ai_service.py
    ↓
Perplexity/OpenAI API
    ↓
Response + Conversation history
```

---

## Critical Files (DO NOT MODIFY)

### ⛔ Core System Files

**NEVER modify these without team consultation**:

1. **app.py** - Flask entry point
   - Reason: Central routing hub
   - Risk: Breaking all routes

2. **accounting_app/main.py** - FastAPI entry point
   - Reason: API backend core
   - Risk: Breaking API services

3. **db/database.py** - Database manager
   - Reason: All DB operations go through this
   - Risk: Data corruption

4. **db/smart_loan_manager.db** - Production database
   - Reason: Live customer data
   - Risk: Irreversible data loss

5. **static/css/colors.css** - Generated CSS color variables
   - Reason: Generated from config/colors.json
   - Risk: Changes will be overwritten
   - Action: Edit config/colors.json instead

### ⚠️ Modify with Extreme Caution

**Consult team first**:

- **db/migrations_*.py** - Database migrations
- **ingest/statement_parser.py** - PDF parsing logic
- **validate/categorizer.py** - Transaction classification
- **services/monthly_report_scheduler.py** - Automated tasks

---

## Safe-to-Modify Files

### ✅ You Can Safely Edit These

**Configuration Files** (JSON only - requires team review):
- `config/app_settings.json` - Add new features, change server settings
- `config/colors.json` - Update UI color palette (respects 3-color mandate)
- `config/business_rules.json` - Update business logic rules
- `config/database.json` - Adjust connection pools, schema settings

**IMPORTANT**: config/colors.json changes must preserve the 3-color palette mandate (Black #000000, Hot Pink #FF007F, Dark Purple #322446). Helper colors can be added but core palette is protected.

**Templates** (UI):
- `templates/**/*.html` - Frontend templates
- Use CSS variables from `static/css/colors.css`
- Don't hardcode colors

**Utility Scripts**:
- `scripts/**/*.py` - Utility and admin scripts
- Safe to add new scripts

**Documentation**:
- `docs/**/*.md` - Add/update documentation
- `replit.md` - Project documentation

---

## Configuration Loading Order

### Application Startup Sequence

**Flask (app.py)**:
1. Load environment variables
2. Load `config/app_settings.json`
3. Initialize database (`db/database.py`)
4. Register routes
5. Start server on port 5000

**FastAPI (accounting_app/main.py)**:
1. Load environment variables
2. Load `config/app_settings.json`
3. Initialize services
4. Register API endpoints
5. Start server on port 8000

### Config Priority

**Priority Order** (highest to lowest):
1. Environment variables (secrets only)
2. `config/*.json` files
3. Default values in code

**Example**:
```python
# ✅ Correct priority
api_key = os.getenv('OPENAI_API_KEY')  # 1st priority
if not api_key:
    config = load_config('config/app_settings.json')
    api_key = config.get('openai', {}).get('api_key')  # 2nd priority
if not api_key:
    raise ValueError("API key not configured")  # Fail safely
```

---

## File Naming Conventions

### Python Modules
- `snake_case.py` - All Python files
- `test_*.py` - Test files
- `migrations_*.py` - Database migrations

### HTML Templates
- `kebab-case.html` - Template files
- Organized by feature folder

### CSS Files
- `kebab-case.css` - Stylesheet files
- One primary stylesheet per feature

### Configuration
- `snake_case.json` - Config files
- All configs in `config/` directory

---

## Deployment Configuration

### Development
- Flask: `0.0.0.0:5000` with debug=True
- FastAPI: `0.0.0.0:8000` with reload=True
- Database: SQLite at `db/smart_loan_manager.db`

### Production
- Flask: Gunicorn with 4 workers
- FastAPI: Uvicorn with auto-reload disabled
- Database: PostgreSQL (via DATABASE_URL env var)

**Deploy Config**: See `.replit` file

---

## System Integrity Checks

### Automated Validation

Run these checks regularly:

```bash
# Color compliance check
python3 scripts/check_color_compliance.py

# System integrity check
python3 scripts/check_system_integrity.py

# Import validation
python3 -m pytest tests/test_imports.py
```

### Manual Checks

Before deploying:
1. ✅ All configs in `config/` directory
2. ✅ No hardcoded secrets
3. ✅ No deprecated files imported
4. ✅ Database migrations applied
5. ✅ Tests passing

---

## Troubleshooting

### "Config not found"
**Fix**: Ensure you're loading from `config/*.json`, not old locations

### "Import error"
**Fix**: Check if you're importing from `DEPRECATED/` folder

### "Color violations"
**Fix**: Run `python3 scripts/check_color_compliance.py` and use CSS variables

### "Database locked"
**Fix**: Restart both Flask and FastAPI workflows

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2025-11-17 | Unified config system, color system v2.0.0 |
| 2.5.0 | 2025-11-17 | Added Google Document AI integration |
| 2.0.0 | 2025-11 | Dual-engine loan evaluation system |

---

## Additional Documentation

- **Color System**: `docs/COLOR_USAGE_GUIDE.md`
- **Color Remediation**: `docs/COLOR_REMEDIATION_PLAN.md`
- **Deprecated Files**: `DEPRECATED/README.md`
- **Project Overview**: `replit.md`

---

## Quick Reference

### Where to find things

- **Add new API endpoint**: `accounting_app/main.py`
- **Change UI colors**: Use CSS variables from `static/css/colors.css`
- **Adjust business rules**: Edit `config/business_rules.json`
- **Database queries**: Use `db/database.py` helper functions
- **Add new feature**: Update `config/app_settings.json` feature flags

### Who to ask

- **Architecture questions**: Check this document first
- **Config changes**: Team lead approval required
- **Database migrations**: DBA approval required
- **UI/UX changes**: Design team approval required

---

**Remember**: This is a living document. Update it when you make significant changes to the system architecture.

---

**Last Reviewed**: 2025-11-17  
**Next Review**: 2025-12-01
