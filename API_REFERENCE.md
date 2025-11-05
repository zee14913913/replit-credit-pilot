# CreditPilot Loans & CTOS Intelligence System

**INFINITE GZ SDN. BHD. – API Specification v1.0**

**Base URL**: `https://portal.creditpilot.digital`

---

## 1. Loans Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/loans/updates` | List latest loan products |
| GET | `/loans/intel` | Retrieve bank preferences & market feedback |
| POST | `/loans/updates/refresh` | Manual refresh (admin key required) |
| GET | `/loans/updates/export.csv` | Export loan data |
| GET | `/loans/intel/export.csv` | Export intelligence data |
| POST | `/loans/dsr/calc` | Compute monthly installment & DSR ratio |
| GET | `/loans/ranking` | Weighted Top-3 ranking (60% DSR / 25% Sentiment / 15% Preference) |
| GET | `/loans/ranking/pdf` | Export Top-3 ranking PDF |
| GET | `/loans/top3/cards` | Visual Top-3 cards component |
| POST | `/loans/compare/add` | Add product to compare basket |
| GET | `/loans/compare/json` | Get compare basket (JSON) |
| GET | `/loans/compare/list` | Get compare basket (list) |
| POST | `/loans/compare/remove` | Remove single product |
| POST | `/loans/compare/clear` | Clear basket |
| POST | `/loans/compare/snapshot` | Save compare snapshot |
| GET | `/loans/compare/pdf/{code}` | Export compare snapshot PDF |

---

## 2. CTOS Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ctos/page?key=` | CTOS authorization form |
| POST | `/ctos/submit?key=` | Submit consent & documents |
| GET | `/ctos/admin?key=&ak=` | CTOS admin queue |

---

## 3. Security & Keys

| Variable | Description |
|----------|-------------|
| `PORTAL_KEY` | Client access control |
| `ADMIN_KEY` | Administrator operations |
| `LOANS_REFRESH_KEY` | Secure manual refresh |
| `FERNET_KEY` | Encryption for PII |
| `TZ` | Asia/Kuala_Lumpur |
| `ENV` | prod |

---

© INFINITE GZ SDN. BHD. All rights reserved.
