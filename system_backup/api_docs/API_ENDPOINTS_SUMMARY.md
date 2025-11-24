# API端点总结文档

本文档列出CreditPilot系统中所有可用的API端点。

## 🏗️ 系统架构

### 双服务架构
- **Flask应用** (端口 5000) - 主前端应用
  - 数据库: SQLite (`db/smart_loan_manager.db`)
  - 用途: 客户数据、账单、交易等核心业务
  
- **FastAPI应用** (端口 8000) - 会计后端API
  - 数据库: PostgreSQL (Neon云数据库)
  - 用途: 会计系统、导出、规则引擎等

---

## 📋 Flask API端点 (端口 5000)

### 1. 获取客户列表
```http
GET /api/companies?skip=0&limit=100
```

**查询参数:**
- `skip` (可选): 跳过记录数，默认0
- `limit` (可选): 返回记录数，默认100

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Cheok Jun Yoon",
      "email": "cheok@example.com",
      "phone": "0123456789",
      "customer_code": "Be_rich_CJY",
      "monthly_income": 10000.00,
      "created_at": "2025-05-01 10:00:00",
      "personal_account_name": "Cheok Jun Yoon",
      "personal_account_number": "1234567890",
      "company_account_name": null,
      "company_account_number": null,
      "tag_desc": null
    }
  ],
  "total": 8,
  "skip": 0,
  "limit": 100
}
```

**数据源:** SQLite `customers` 表

---

### 2. 获取银行对账单列表
```http
GET /api/bank-statements?customer_id=1&bank_name=AMBANK&statement_month=2025-05&skip=0&limit=100
```

**查询参数:**
- `customer_id` (可选): 客户ID过滤
- `bank_name` (可选): 银行名称过滤
- `statement_month` (可选): 账单月份过滤 (格式: YYYY-MM)
- `skip` (可选): 跳过记录数，默认0
- `limit` (可选): 返回记录数，默认100

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "customer_id": 1,
      "bank_name": "AMBANK",
      "statement_month": "2025-05",
      "period_start_date": "2025-05-01",
      "period_end_date": "2025-05-31",
      "previous_balance_total": 1234.56,
      "closing_balance_total": 2345.67,
      "owner_balance": 1500.00,
      "gz_balance": 845.67,
      "owner_expenses": 500.00,
      "owner_payments": 300.00,
      "gz_expenses": 200.00,
      "gz_payments": 100.00,
      "file_paths": "/uploads/customer_1/statement.pdf",
      "card_count": 2,
      "transaction_count": 45,
      "validation_score": 98.5,
      "is_confirmed": true,
      "inconsistencies": null,
      "created_at": "2025-06-01 10:00:00",
      "updated_at": "2025-06-01 15:30:00"
    }
  ],
  "total": 117,
  "filters": {
    "customer_id": "1",
    "bank_name": "AMBANK",
    "statement_month": "2025-05"
  },
  "skip": 0,
  "limit": 100
}
```

**数据源:** SQLite `monthly_statements` 表

---

### 3. 上传账单文件
```http
POST /api/bill/upload
Content-Type: multipart/form-data
```

**请求参数:**
- `file` (必需): 账单文件 (PDF/Excel/CSV)
- `customer_id` (必需): 客户ID
- 其他业务参数...

**响应示例:**
```json
{
  "success": true,
  "message": "文件上传成功",
  "file_path": "/uploads/customer_1/20251123_statement.pdf"
}
```

**位置:** app.py 第202行

---

### 4. 获取OCR处理状态
```http
GET /api/bill/ocr-status?file_id=abc123
```
或
```http
POST /api/bill/ocr-status
Content-Type: application/json

{
  "file_id": "abc123"
}
```

**响应示例:**
```json
{
  "success": true,
  "status": "ready",
  "processing": 0,
  "completed": 283,
  "message": "OCR status endpoint ready"
}
```

**位置:** app.py 第508行

---

## 📋 FastAPI端点 (端口 8000)

### 1. 获取客户列表
```http
GET /api/companies?skip=0&limit=100
```

**响应格式:** 与Flask `/api/companies` 相同

**数据源:** SQLite `customers` 表（通过辅助连接函数）

---

### 2. 获取银行对账单
```http
GET /api/bank-statements?customer_id=1&bank_name=AMBANK&statement_month=2025-05
```

**响应格式:** 与Flask `/api/bank-statements` 相同

**数据源:** SQLite `monthly_statements` 表（通过辅助连接函数）

---

### 3. 上传账单文件
```http
POST /api/bill/upload
Content-Type: multipart/form-data
```

**请求参数:**
- `file`: 账单文件
- `customer_id`: 客户ID

**响应示例:**
```json
{
  "success": true,
  "message": "Bill uploaded successfully",
  "file_path": "/static/uploads/customer_1/20251123_123456_statement.pdf",
  "filename": "20251123_123456_statement.pdf",
  "customer_id": 1,
  "file_size": 245678,
  "upload_time": "2025-11-23T10:30:00"
}
```

---

### 4. 获取OCR状态
```http
GET /api/bill/ocr-status?file_id=abc123
```

**响应示例:**
```json
{
  "success": true,
  "ocr_engines": ["Google Document AI (Primary)", "pdfplumber (Fallback)", "pytesseract (Backup)"],
  "supported_banks": ["AMBANK", "AMBANK_ISLAMIC", "UOB", ...],
  "extracted_fields": ["customer_name", "ic_no", "card_type", ...]
}
```

---

## 🔧 技术细节

### CORS配置
- Flask: 通过 `cors_config.py` 配置
- FastAPI: 通过 `CORSMiddleware` 配置
- 允许的域名包括开发和生产环境

### 异常处理
所有端点都包含：
```python
try:
    # 业务逻辑
    return jsonify({"success": True, "data": ...})
except Exception as e:
    logger.error(f"API error: {e}")
    return jsonify({"success": False, "error": str(e)}), 500
```

### 数据库连接
- Flask: 使用 `with get_db() as conn:` context manager
- FastAPI: 
  - PostgreSQL: 使用 `Depends(get_db)` 依赖注入
  - SQLite: 使用 `get_sqlite_connection()` 辅助函数

---

## 🚀 部署配置

### Autoscale部署
```toml
[deployment]
deploymentTarget = "autoscale"
run = ["sh", "-c", "uvicorn accounting_app.main:app --host 0.0.0.0 --port 8000 --workers 2 & gunicorn --bind=0.0.0.0:5000 --workers=4 --timeout=120 --reuse-port app:app"]
```

### 端口映射
- 5000 → 80 (Flask主应用)
- 8000 → 8000 (FastAPI会计API)

---

## 📊 支持的银行

系统支持13家马来西亚银行的PDF解析：
1. AMBANK
2. AMBANK_ISLAMIC
3. UOB
4. OCBC
5. HONG_LEONG
6. HSBC
7. STANDARD_CHARTERED
8. MAYBANK
9. AFFIN_BANK
10. CIMB
11. ALLIANCE_BANK
12. PUBLIC_BANK
13. RHB_BANK

每家银行支持16个标准字段的提取。

---

## 📖 API文档
- FastAPI Swagger UI: `http://localhost:8000/docs`
- FastAPI ReDoc: `http://localhost:8000/redoc`

---

**最后更新:** 2025-11-23
**维护者:** CreditPilot开发团队
