# Receipt Management System

## Overview
OCR-powered receipt management system for automated reconciliation, reimbursement tracking, and audit compliance.

## Features

### 1. Intelligent OCR Recognition
- **Supported Formats**: JPG, PNG, GIF, BMP, TIFF
- **Extracted Information**:
  - Card number (last 4 digits)
  - Transaction date
  - Amount
  - Merchant name

### 2. Smart Auto-Matching
- **Matching Algorithm**:
  - Card number lookup (last 4 digits)
  - Date tolerance: ±3 days
  - Amount tolerance: ±1%
  - Merchant name fuzzy match
- **Confidence Scoring**: 0.0 to 1.0

### 3. File Organization
- **Auto-filing**: Receipts automatically organized by customer and card
- **Directory Structure**:
  ```
  static/uploads/receipts/
  ├── {customer_id}/
  │   └── {card_last4}/
  │       └── {timestamp}_{filename}.jpg
  └── pending/
      └── {timestamp}_{filename}.jpg
  ```

### 4. Batch Processing
- Upload multiple receipts simultaneously
- Parallel OCR processing
- Bulk matching results

### 5. Manual Matching
- For receipts that fail auto-matching
- Customer and card selection interface
- File auto-relocation after manual match

## Database Schema

```sql
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    card_id INTEGER,
    receipt_type TEXT NOT NULL,              -- 'merchant_swipe' or 'payment'
    file_path TEXT NOT NULL,
    original_filename TEXT,
    transaction_date DATE,
    amount DECIMAL(10,2),
    merchant_name TEXT,
    card_last4 TEXT,
    matched_transaction_id INTEGER,
    match_status TEXT DEFAULT 'pending',     -- 'auto_matched', 'manual_matched', 'pending', 'no_match'
    match_confidence DECIMAL(3,2),           -- 0.00 to 1.00
    ocr_text TEXT,                           -- Full OCR output
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (matched_transaction_id) REFERENCES transactions(id)
);
```

## API Endpoints

### Web Routes
- `GET /receipts` - Receipt management homepage with statistics
- `GET /receipts/upload` - Upload form
- `POST /receipts/upload` - Process uploaded receipts
- `GET /receipts/pending` - View pending/unmatched receipts
- `POST /receipts/manual-match/<id>` - Manually match a receipt
- `GET /receipts/customer/<id>` - View customer's receipts

### API Routes
- `GET /api/customer/<id>/cards` - Get customer's credit cards (JSON)

## Usage

### Uploading Receipts
1. Navigate to "Receipts" in the main menu
2. Click "上传收据" (Upload Receipts)
3. Select receipt type:
   - 商家刷卡收据 (Merchant Swipe Receipt)
   - 信用卡还款凭证 (Payment Receipt)
4. Choose one or multiple image files
5. Click "开始上传" (Start Upload)

### Review Results
- **Auto-matched**: Receipts automatically linked to customer/card
- **Pending**: Requires manual matching
- **Failed**: OCR could not extract required information

### Manual Matching
1. Navigate to "待匹配收据" (Pending Receipts)
2. Review OCR extracted data
3. Select customer from dropdown
4. Select credit card (auto-populated based on customer)
5. Click "确认匹配" (Confirm Match)

## Use Cases

### 1. Account Reconciliation
- Match physical receipts to statement transactions
- Verify transaction accuracy
- Identify missing or duplicate charges

### 2. Reimbursement Tracking
- Store employee expense receipts
- Link receipts to corporate card transactions
- Generate reimbursement reports

### 3. Audit Compliance
- Maintain receipt archive
- Provide transaction evidence
- Support tax and regulatory requirements

## Technical Details

### OCR Processing
- **Engine**: Pytesseract (Tesseract OCR wrapper)
- **Pre-processing**: None (future enhancement opportunity)
- **Confidence Scoring**: Based on number of fields extracted

### Matching Algorithm
```python
# Card lookup
cards = find_cards_by_last4(card_last4)

# Date range
date_start = transaction_date - 3 days
date_end = transaction_date + 3 days

# Amount range
amount_min = amount * 0.99  # -1%
amount_max = amount * 1.01  # +1%

# Find best match
transaction = find_transaction(card_id, date_range, amount_range)

# Calculate confidence
confidence = (date_score * 0.4) + (amount_score * 0.4) + (merchant_score * 0.2)
```

### Security Considerations
- File type validation (images only)
- Secure filename generation
- SQL injection prevention via parameterized queries
- Organized file storage prevents path traversal

## Future Enhancements

### Recommended Improvements (from Architect Review)
1. **OCR Pre-processing**:
   - Grayscale conversion
   - Threshold adjustment
   - Noise reduction
   - Image rotation correction

2. **Retry Strategy**:
   - Multiple OCR attempts with different settings
   - Fallback to alternative OCR engines

3. **Runtime Requirements**:
   - Document Tesseract installation
   - Add to requirements.txt
   - Include setup instructions

### Additional Features
- Receipt thumbnail generation
- Duplicate receipt detection
- Expense category classification
- Multi-currency support
- Export to accounting software
- Mobile app integration
- Email receipt forwarding

## Troubleshooting

### OCR Not Working
- Ensure pytesseract is installed: `pip install pytesseract`
- Install Tesseract OCR engine:
  - Ubuntu/Debian: `apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download from GitHub

### Low Matching Accuracy
- Ensure receipt image is clear and well-lit
- Check date format matches expected patterns
- Verify card number is visible on receipt
- Use manual matching for problematic receipts

### File Upload Issues
- Check file size limit (16MB max)
- Verify image format is supported
- Ensure upload directory has write permissions

## Integration with Existing Systems

### Independent Architecture
- **Separate Database Table**: No coupling with credit card or savings systems
- **Dedicated File Storage**: Independent directory structure
- **Isolated Routes**: Clean separation of concerns

### Data Relationships
- Links to existing customers via `customer_id`
- Links to existing credit cards via `card_id`
- Optional link to transactions via `matched_transaction_id`
- All relationships are optional (nullable foreign keys)

## Galaxy Theme Compliance
All UI components follow the platform's Galaxy Universe theme:
- Pure black background
- Silver/platinum/white gradients (NO GOLD)
- Glass-morphism cards
- Frosted glass effects
- Responsive design
- Bootstrap Icons integration
