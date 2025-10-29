# Supplier Invoices Table Schema Update

**Date:** 2025-10-29

## Changes Made

### 1. Added Field: `monthly_statement_id`

- **Type:** INTEGER
- **Nullable:** YES (NULL allowed for legacy records)
- **Purpose:** Reference to `monthly_statements.id` (new architecture)
- **Foreign Key:** Should reference `monthly_statements(id)` (not enforced in SQLite ALTER TABLE)

### 2. Retained Field: `statement_id`

- **Type:** INTEGER  
- **Nullable:** YES (NULL allowed)
- **Purpose:** Legacy field for historical reference to deprecated `statements` table
- **Status:** Will eventually be removed after full migration

## New Schema Definition

```sql
CREATE TABLE supplier_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    statement_id INTEGER,                      -- Legacy field (nullable)
    monthly_statement_id INTEGER,              -- NEW: Reference to monthly_statements
    supplier_name TEXT NOT NULL,
    invoice_number TEXT UNIQUE NOT NULL,
    total_amount REAL NOT NULL,
    supplier_fee REAL NOT NULL,
    invoice_date TEXT NOT NULL,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (monthly_statement_id) REFERENCES monthly_statements(id)
);
```

## Migration Notes

1. All new invoice records **MUST** populate `monthly_statement_id`
2. `statement_id` is optional and only for legacy data reference
3. Invoice generation code updated to use `monthly_statement_id`
4. PDF generation code updated to query from `monthly_statements` architecture

## Code Changes Required

- ✅ `services/monthly_ledger_engine.py` - Update `_generate_supplier_invoices()`
- ✅ `services/invoice_generator.py` - Update to use monthly_statement_id
- ✅ `app.py` - Update invoice queries to JOIN monthly_statements

## Testing Checklist

- [ ] Create new invoice with monthly_statement_id
- [ ] Verify PDF generation works
- [ ] Verify invoice list page displays correctly
- [ ] Verify invoice view/download works
