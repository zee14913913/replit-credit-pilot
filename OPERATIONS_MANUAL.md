# Operations & Maintenance Guide

**INFINITE GZ SDN. BHD.**

---

## 1. Deployment

Environment variables (required) already configured in Replit Secrets.

**Run server:**
```bash
uvicorn accounting_app.main:app --host 0.0.0.0 --port 5000
```

---

## 2. Health Checks

```bash
curl -s https://portal.creditpilot.digital/health
curl -s https://portal.creditpilot.digital/loans/updates | jq 'length'
curl -s https://portal.creditpilot.digital/loans/intel | jq 'length'
```

---

## 3. Backup & Recovery

- **Weekly SQLite dump**: `/home/runner/pgdump_*.sql`
- **Rollback**: via Replit History → tag `prod-stable`.

---

## 4. Monitoring

**Key metrics endpoints:**
- `/stats` – storage usage
- `/loans/updates/last` – last harvest time

---

## 5. Security Policy

- All PII fields AES-Fernet encrypted.
- Rate limit 120 requests per minute per IP.
- HSTS, X-Frame-Options, X-Content-Type-Options enabled.

---

## 6. Cron Schedule

- **Automatic loan harvest**: 11:00 AM Kuala Lumpur daily
- **20-hour cool-down window**

---

## 7. Support

**Email**: support@infinitegz.com

---

© INFINITE GZ SDN. BHD. All rights reserved.
