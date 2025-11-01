# Accounting API - 会计管理系统API文档

## 🌟 概述

企业级多租户会计管理系统FastAPI后端，提供自动化会计处理、财务报表生成、文件管理和定时任务等功能。

**核心特性：**
- ✅ 多租户隔离架构
- ✅ 自动化月结任务
- ✅ 专业PDF报表生成
- ✅ 安全的文件存储管理
- ✅ 100%数据准确性保证

---

## 🚀 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL数据库
- FastAPI + Uvicorn

### 启动服务
```bash
uvicorn accounting_app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问API文档
服务启动后，访问自动生成的Swagger UI文档：
```
http://localhost:8000/docs
```

---

## 📁 核心模块

### 1. **Management Reports API** (`/api/reports`)

#### 📊 获取月度管理报表
```http
GET /api/reports/management/{period}?format=json&include_details=true
```

**参数：**
- `period`: 报表期间（格式：YYYY-MM）
- `format`: 输出格式（`json` 或 `pdf`）
- `include_details`: 是否包含详细数据（默认：true）

**返回示例：**
```json
{
  "company_info": {
    "company_name": "AI SMART TECH SDN. BHD.",
    "company_code": "TEST001"
  },
  "period": "2025-11",
  "balance_sheet_summary": {
    "total_assets": 125000.50,
    "total_liabilities": 45000.25,
    "total_equity": 80000.25,
    "balance_check": 0
  },
  "pnl_summary": {
    "total_revenue": 85000.00,
    "total_expenses": 42000.00,
    "net_profit": 43000.00,
    "gross_margin": 50.59
  },
  "aging_summary": {
    "accounts_receivable": {
      "current": 15000.00,
      "30_days": 5000.00,
      "total": 20000.00
    }
  }
}
```

#### 📊 应收账款账龄视图（AR Aging）
```http
GET /api/reports/ar-aging/view?company_id=1&as_of_date=2025-11-30
```

**按客户分组，账龄分类：**
- 0-30 days
- 31-60 days
- 61-90 days
- 90+ days

**用途：** 银行贷款审批、客户风险管理

**返回示例：**
```json
{
  "company_id": 1,
  "report_date": "2025-11-30",
  "customers": [
    {
      "customer_id": 1,
      "customer_code": "C001",
      "customer_name": "ABC Corp",
      "aging_0_30": 15000.00,
      "aging_31_60": 5000.00,
      "aging_61_90": 2000.00,
      "aging_90_plus": 1000.00,
      "total_outstanding": 23000.00
    }
  ],
  "total_0_30": 15000.00,
  "total_31_60": 5000.00,
  "total_61_90": 2000.00,
  "total_90_plus": 1000.00,
  "grand_total": 23000.00
}
```

#### 📊 应付账款账龄视图（AP Aging）
```http
GET /api/reports/ap-aging/view?company_id=1&as_of_date=2025-11-30
```

**按供应商分组，账龄分类：**
- 0-30 days
- 31-60 days
- 61-90 days
- 90+ days

**用途：** 银行贷款审批、现金流管理

---

### 2. **PDF Reports API** (`/api/reports/pdf`)

#### 📄 生成资产负债表PDF
```http
GET /api/reports/pdf/balance-sheet?company_id=1&period=2025-11-30
```

**自动功能：**
- ✅ 生成专业PDF报表
- ✅ 自动保存到FileStorageManager
- ✅ 返回PDF供下载

**文件路径：**
```
/accounting_data/companies/{company_id}/reports/balance_sheet/2025/
```

#### 📈 生成损益表PDF
```http
GET /api/reports/pdf/profit-loss?company_id=1&period=2025-11
```

#### 🏦 生成银行贷款包PDF
```http
GET /api/reports/pdf/bank-package?company_id=1&period=2025-11
```

包含完整信息：
- Balance Sheet
- Profit & Loss Statement
- Aging Report Summary
- Bank Account Balances
- Data Quality Metrics

---

### 3. **Files API** (`/api/files`)

#### 📂 列出所有文件
```http
GET /api/files/list/{company_id}
```

**示例：**
```http
GET /api/files/list/1
GET /api/files/list/1?file_type=bank_statement
```

**返回示例：**
```json
{
  "company_id": 1,
  "file_type": "all",
  "total": 15,
  "files": [
    {
      "filename": "company1_balance_sheet_2025-11-30.pdf",
      "file_path": "/companies/1/reports/balance_sheet/2025/...",
      "file_size": 2621440,
      "created_time": "2025-11-01 14:30:00"
    }
  ]
}
```

#### 📊 获取存储统计
```http
GET /api/files/storage-stats/{company_id}
```

**示例：**
```http
GET /api/files/storage-stats/1
```

#### 🗂️ 按类型查看文件
```http
GET /api/files/view?company_id={company_id}&file_type={file_type}
```

**示例：**
```http
GET /api/files/view?company_id=1&file_type=bank_statement
```

支持的文件类型：
- `bank_statement` - 银行月结单
- `balance_sheet` - 资产负债表
- `profit_loss` - 损益表
- `bank_package` - 银行贷款包
- `management_report` - 管理报表
- `supplier_invoice` - 供应商发票
- `pos_report` - POS报告

#### ⬇️ 下载文件
```http
GET /api/files/download?file_path={file_path}
```

**示例：**
```http
GET /api/files/download?file_path=/companies/1/reports/balance_sheet/2025/file.pdf
```

#### 🗑️ 删除文件
```http
DELETE /api/files/delete?file_path={file_path}
```

**示例：**
```http
DELETE /api/files/delete?file_path=/companies/1/reports/balance_sheet/2025/file.pdf
```

---

### 4. **Monthly Close Task** (`/api/tasks`)

#### 🔄 执行月结任务
```http
POST /api/tasks/monthly-close?company_id=1&month=2025-11
Headers: X-Task-Token: <your-secret-token>
```

**自动执行流程：**
1. ✅ 检查未匹配银行流水
2. ✅ 计算试算表（Trial Balance）
3. ✅ 自动生成发票
4. ✅ **生成并保存Management Report JSON**

**返回示例：**
```json
{
  "success": true,
  "company_id": 1,
  "company_name": "AI SMART TECH SDN. BHD.",
  "month": "2025-11",
  "completed_at": "2025-11-01T15:30:00",
  "unmatched_transactions": 3,
  "trial_balance": {
    "total_debits": 125000.00,
    "total_credits": 125000.00,
    "balanced": true
  },
  "management_report": {
    "success": true,
    "report_path": "/accounting_data/companies/1/reports/management/2025/...",
    "balance_sheet_balanced": true,
    "total_revenue": 85000.00,
    "total_expenses": 42000.00
  }
}
```

---

### 5. **Bank Import API** (`/api/import`)

#### 📥 导入银行月结单
```http
POST /api/import/bank?company_id=1
Content-Type: multipart/form-data
```

**支持格式：**
- CSV文件（银行导出格式）
- 自动解析交易记录
- 自动保存原始文件到FileStorageManager

---

## 🔒 安全特性

### 多租户隔离
所有文件操作都经过严格的跨租户访问验证：

```python
# 安全验证示例
AccountingFileStorageManager.validate_path_security(
    file_path="/companies/1/reports/file.pdf",
    company_id=1
)
# ✅ 通过：正确的公司ID
# ❌ 失败：Company 1 无法访问 Company 10 的文件
```

**防护机制：**
- ✅ 使用`os.path.commonpath()`验证
- ✅ 防止路径遍历攻击（`../`）
- ✅ 防止前缀匹配漏洞（Company 1 vs Company 10）

---

## 📂 文件存储结构

```
/accounting_data/companies/{company_id}/
├── bank_statements/
│   └── 2025/
│       └── 11/
│           └── company1_bank_Maybank_567890_2025-11_20251101_143052.csv
├── invoices/
│   ├── supplier/
│   ├── purchase/
│   └── sales/
├── pos_reports/
│   └── 2025/
│       └── 11/
└── reports/
    ├── balance_sheet/
    │   └── 2025/
    │       └── company1_balance_sheet_2025-11-30_20251101_143125.pdf
    ├── profit_loss/
    │   └── 2025/
    │       └── 11/
    │           └── company1_profit_loss_2025-11-01_to_2025-11-30.pdf
    ├── bank_package/
    │   └── 2025/
    │       └── company1_bank_package_2025-11-30_20251101_143215.pdf
    └── management/
        └── 2025/
            └── company1_management_report_2025-11_20251101_150000.json
```

**命名规范：**
```
company{id}_{type}_{details}_{timestamp}.{ext}
```

---

## 🧪 测试

### 运行单元测试
```bash
# 所有单元测试
pytest accounting_app/tests/unit/ -v

# FileStorageManager测试
pytest accounting_app/tests/unit/test_file_storage_manager.py -v

# ManagementReportGenerator测试
pytest accounting_app/tests/unit/test_management_report_generator.py -v
```

### 运行集成测试
```bash
# 所有集成测试
pytest accounting_app/tests/integration/ -v

# PDF Reports API测试
pytest accounting_app/tests/integration/test_pdf_reports_api.py -v

# Files API测试
pytest accounting_app/tests/integration/test_files_api.py -v
```

**测试覆盖范围：**
- ✅ FileStorageManager（12个测试）
  - 路径生成
  - 安全验证（跨租户、路径遍历）
  - 文件操作（保存、读取、删除）
- ✅ ManagementReportGenerator（5个测试）
  - 报表结构验证
  - Balance Sheet计算
  - P&L计算
  - Aging Report结构
- ✅ API集成测试（10+个测试）
  - PDF生成端点
  - 文件管理端点
  - 月结任务端点

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| **Web框架** | FastAPI 0.120+ |
| **数据库** | PostgreSQL + SQLAlchemy 2.0 |
| **ORM** | SQLAlchemy ORM |
| **PDF生成** | ReportLab 4.4+ |
| **服务器** | Uvicorn (ASGI) |
| **测试** | pytest + pytest-asyncio |
| **文件存储** | 本地文件系统（多租户隔离） |

---

## 📈 性能指标

| 操作 | 响应时间 |
|------|---------|
| 生成Balance Sheet PDF | < 2秒 |
| 生成Management Report JSON | < 1秒 |
| 文件列表查询 | < 100ms |
| 月结任务执行 | 5-30秒（取决于数据量） |

---

## 🔧 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@host:5432/dbname

# 任务Token（用于定时任务调用）
TASK_SECRET_TOKEN=your-secure-token-here

# 可选配置
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=password
PGDATABASE=accounting_db
```

---

## 📞 API调用示例

### Python示例
```python
import requests

# 获取Management Report
response = requests.get(
    "http://localhost:8000/api/reports/management/2025-11",
    params={"format": "json", "include_details": True}
)
report_data = response.json()

# 下载Balance Sheet PDF
pdf_response = requests.get(
    "http://localhost:8000/api/reports/pdf/balance-sheet",
    params={"company_id": 1, "period": "2025-11-30"}
)
with open("balance_sheet.pdf", "wb") as f:
    f.write(pdf_response.content)

# 执行月结任务
close_response = requests.post(
    "http://localhost:8000/api/tasks/monthly-close",
    params={"company_id": 1, "month": "2025-11"},
    headers={"X-Task-Token": "your-token"}
)
result = close_response.json()
```

### cURL示例
```bash
# 获取JSON报表
curl "http://localhost:8000/api/reports/management/2025-11?format=json"

# 下载PDF
curl -O "http://localhost:8000/api/reports/pdf/balance-sheet?company_id=1&period=2025-11-30"

# 执行月结
curl -X POST "http://localhost:8000/api/tasks/monthly-close?company_id=1&month=2025-11" \
  -H "X-Task-Token: your-token"
```

---

### 6. **Exception Center API** (`/api/exceptions`)

集中管理所有系统异常，包括PDF解析失败、OCR错误、客户/供应商未匹配、记账失败等。

#### 🚨 获取异常摘要
```http
GET /api/exceptions/summary?company_id=1&status_filter=new
```

**参数：**
- `company_id`: 公司ID（必填）
- `status_filter`: 状态过滤（可选：`new`, `in_progress`, `resolved`, `ignored`）

**返回示例：**
```json
{
  "total": 15,
  "by_type": {
    "pdf_parse": 3,
    "ocr_error": 2,
    "customer_mismatch": 5,
    "supplier_mismatch": 4,
    "posting_error": 1
  },
  "by_severity": {
    "low": 4,
    "medium": 6,
    "high": 4,
    "critical": 1
  },
  "by_status": {
    "new": 10,
    "in_progress": 3,
    "resolved": 2
  },
  "critical_count": 1,
  "high_count": 4
}
```

#### 🚨 获取异常列表（分页）
```http
GET /api/exceptions/?company_id=1&exception_type=customer_mismatch&severity=high&status=new&page=1&page_size=50
```

**过滤参数：**
- `exception_type`: 异常类型
  - `pdf_parse`: PDF解析失败
  - `ocr_error`: OCR识别错误
  - `customer_mismatch`: 客户未匹配
  - `supplier_mismatch`: 供应商未匹配
  - `posting_error`: 记账失败
- `severity`: 严重程度（`low`, `medium`, `high`, `critical`）
- `status`: 状态（`new`, `in_progress`, `resolved`, `ignored`）

**返回示例：**
```json
{
  "total": 5,
  "page": 1,
  "page_size": 50,
  "exceptions": [
    {
      "id": 1,
      "company_id": 1,
      "exception_type": "customer_mismatch",
      "severity": "high",
      "source_type": "sales_invoice",
      "source_id": 123,
      "error_message": "客户未找到: ABC Company",
      "raw_data": "{\"customer_name\": \"ABC Company\"}",
      "status": "new",
      "created_at": "2025-11-01T10:30:00Z"
    }
  ]
}
```

#### 🚨 获取单个异常详情
```http
GET /api/exceptions/1
```

#### 🚨 标记异常为已解决
```http
PUT /api/exceptions/1/resolve
Content-Type: application/json

{
  "resolved_by": "admin@example.com",
  "resolution_notes": "手动创建客户后重新导入"
}
```

#### 🚨 忽略异常
```http
PUT /api/exceptions/1/ignore
Content-Type: application/json

{
  "resolved_by": "admin@example.com",
  "resolution_notes": "已确认可忽略"
}
```

#### 🚨 删除异常（谨慎使用）
```http
DELETE /api/exceptions/1
```

**注意：** 建议使用"忽略"而非删除，以保留审计记录。

#### 📋 Python调用示例
```python
import requests

# 获取未解决的异常摘要
response = requests.get(
    "http://localhost:8000/api/exceptions/summary",
    params={"company_id": 1, "status_filter": "new"}
)
summary = response.json()
print(f"严重异常数量: {summary['critical_count']}")

# 列出所有客户未匹配的异常
response = requests.get(
    "http://localhost:8000/api/exceptions/",
    params={
        "company_id": 1,
        "exception_type": "customer_mismatch",
        "status": "new",
        "page": 1,
        "page_size": 50
    }
)
exceptions = response.json()

# 解决异常
requests.put(
    "http://localhost:8000/api/exceptions/1/resolve",
    json={
        "resolved_by": "admin@example.com",
        "resolution_notes": "已处理"
    }
)
```

#### 🔧 Management Report集成

Exception Center已自动集成到Management Report中：

```python
# Management Report会自动包含exception_summary字段
response = requests.get(
    "http://localhost:8000/api/reports/management/2025-11"
)
report = response.json()

# 检查异常摘要
exception_summary = report.get("exception_summary", {})
if exception_summary["critical"] > 0:
    print(f"⚠️ 警告：有 {exception_summary['critical']} 个严重异常需要处理！")
```

**Management Report返回示例：**
```json
{
  "period": "2025-11",
  "pnl_summary": {...},
  "balance_sheet_summary": {...},
  "exception_summary": {
    "total": 15,
    "critical": 2,
    "high": 5,
    "by_type": {
      "pdf_parse": 3,
      "customer_mismatch": 7,
      "posting_error": 5
    },
    "by_status": {
      "new": 10,
      "resolved": 5
    }
  }
}
```

---

### 7. **Auto Posting Rules API** (`/api/posting-rules`)

自动记账规则引擎 - 表驱动化规则管理系统，替代硬编码匹配逻辑。

#### ✨ 核心特性
- **表驱动规则**: 所有匹配规则存储在数据库，支持动态CRUD
- **优先级排序**: 按priority字段排序（数字越小优先级越高）
- **多源类型支持**: bank_import, supplier_invoice, sales_invoice, general
- **模式匹配**: 支持关键字（case-insensitive）和正则表达式
- **匹配统计**: 自动记录match_count和last_matched_at
- **异常集成**: 科目不存在或分录生成失败自动记录Exception Center

#### 📋 规则列表（分页+过滤）
```http
GET /api/posting-rules/?skip=0&limit=10&source_type=bank_import&is_active=true&search=salary
```

**查询参数：**
- `skip`: 跳过记录数（分页）
- `limit`: 返回记录数（分页）
- `source_type`: 过滤source_type（可选）
- `is_active`: 过滤启用状态（可选）
- `search`: 搜索rule_name或pattern（可选）

**返回示例：**
```json
{
  "total": 20,
  "skip": 0,
  "limit": 10,
  "rules": [
    {
      "id": 1,
      "company_id": 1,
      "rule_name": "工资支付 - Payout",
      "source_type": "bank_import",
      "pattern": "payout",
      "is_regex": false,
      "priority": 10,
      "debit_account_code": "salary_expense",
      "credit_account_code": "bank",
      "is_active": true,
      "match_count": 127,
      "last_matched_at": "2025-11-01T14:25:30",
      "created_at": "2025-11-01T10:00:00"
    }
  ]
}
```

#### 🆕 创建规则
```http
POST /api/posting-rules/
Content-Type: application/json
```

**请求体：**
```json
{
  "rule_name": "银行利息收入",
  "source_type": "bank_import",
  "pattern": "interest.*credit",
  "is_regex": true,
  "priority": 50,
  "debit_account_code": "bank",
  "credit_account_code": "interest_income",
  "description": "银行利息收入自动识别"
}
```

**验证规则：**
- ✅ `company_id`自动注入（从get_current_company_id）
- ✅ 会计科目存在性验证（debit_account_code和credit_account_code）
- ✅ source_type必须是：bank_import, supplier_invoice, sales_invoice, general
- ✅ CRUD后自动清除缓存

**返回：** 创建成功的规则对象（RuleResponse）

#### ✏️ 更新规则
```http
PUT /api/posting-rules/{rule_id}
Content-Type: application/json
```

**请求体：**（所有字段可选，仅更新提供的字段）
```json
{
  "rule_name": "工资支付（更新）",
  "priority": 5,
  "is_active": false
}
```

**安全特性：**
- ✅ 双重过滤：rule_id + company_id（防止跨租户修改）
- ✅ 会计科目验证（如果修改了debit/credit_account_code）
- ✅ 更新后清除缓存

#### 🗑️ 删除规则
```http
DELETE /api/posting-rules/{rule_id}
```

**返回：**
```json
{
  "message": "Rule '工资支付 - Payout' deleted successfully"
}
```

**安全特性：**
- ✅ 双重过滤：rule_id + company_id
- ✅ 删除后清除缓存

#### 🧪 测试规则匹配
```http
POST /api/posting-rules/test
Content-Type: application/json
```

**请求体：**
```json
{
  "description": "PAYOUT TO EMPLOYEE - SALARY NOVEMBER",
  "source_type": "bank_import"
}
```

**返回：**
```json
{
  "matched": true,
  "rule": {
    "id": 1,
    "rule_name": "工资支付 - Payout",
    "pattern": "payout",
    "priority": 10,
    "debit_account_code": "salary_expense",
    "credit_account_code": "bank"
  },
  "test_description": "PAYOUT TO EMPLOYEE - SALARY NOVEMBER"
}
```

**未匹配返回：**
```json
{
  "matched": false,
  "rule": null,
  "test_description": "UNKNOWN TRANSACTION"
}
```

#### 🔄 银行导入集成

Rules API已集成到`accounting_app/services/bank_matcher.py`：

**匹配流程：**
1. ✅ **优先使用Rule Engine**：从数据库按优先级匹配规则
2. ✅ **自动生成分录**：调用`RuleEngine.apply_rule_to_bank_statement()`
3. ✅ **更新统计**：自动更新match_count和last_matched_at
4. ⚠️ **Fallback机制**：如果数据库无匹配，使用硬编码MATCHING_RULES（向后兼容）
5. ❌ **异常记录**：失败自动记录Exception Center (posting_error)

**日志示例：**
```
✅ RuleEngine匹配成功: 工资支付 - Payout | 交易: PAYOUT TO EMPLOYEE
✅ 会计分录已生成: JE-20251101-142530-1234
⚠️ 使用硬编码规则匹配: salary | 交易: SALARY PAYMENT (fallback)
⏭️ 无匹配规则，跳过: UNKNOWN TRANSACTION
```

#### 📊 规则优先级设计

**推荐优先级范围：**
- **1-50**: 高优先级（工资、法定缴纳）
- **50-200**: 中优先级（EPF, SOCSO, 租金）
- **200-500**: 普通优先级（日常支出、收入）
- **500+**: 低优先级（杂项、通用规则）

**示例：**
```sql
-- 优先级10: 最高
INSERT INTO auto_posting_rules (..., priority) VALUES (..., 10);  -- 工资支付

-- 优先级50: 法定缴纳
INSERT INTO auto_posting_rules (..., priority) VALUES (..., 50);  -- EPF

-- 优先级200: 日常支出
INSERT INTO auto_posting_rules (..., priority) VALUES (..., 200); -- 租金

-- 优先级900: 最低
INSERT INTO auto_posting_rules (..., priority) VALUES (..., 900); -- 银行手续费
```

#### 💾 种子数据

系统启动时自动加载20条预定义规则（`seed_posting_rules.sql`）：

| 优先级 | 规则名称 | 模式 | 会计分录 |
|--------|----------|------|----------|
| 10 | 工资支付 - Payout | payout | salary_expense → bank |
| 20 | 工资支付 - Infinite.GZ | infinite.gz | salary_expense → bank |
| 50 | EPF缴纳 - KWSP | kumpulan wang simpanan pekerja | epf_payable → bank |
| 200 | 租金支出 - Rental | rental | rent_expense → bank |
| 400 | 服务收入 - Service | service | bank → service_income |
| 900 | 银行手续费 - Fee | fee | bank_charges → bank |

**查看所有规则：**
```sql
SELECT priority, rule_name, pattern, 
       debit_account_code || ' → ' || credit_account_code as entry
FROM auto_posting_rules
WHERE company_id = (SELECT id FROM companies WHERE company_code = 'DEFAULT')
ORDER BY priority;
```

#### 🛡️ 安全特性

**多租户隔离：**
- ✅ 所有端点使用`Depends(get_current_company_id)`
- ✅ CREATE端点强制使用注入的company_id（不接受用户输入）
- ✅ 单记录操作双重过滤（id + company_id）

**缓存管理：**
- ✅ 按source_type隔离缓存（防止跨类型规则混淆）
- ✅ CRUD操作后自动清除缓存（确保新规则立即生效）
- ✅ 并发安全（每请求独立RuleEngine实例）

**数据验证：**
- ✅ 会计科目存在性验证
- ✅ CHECK约束限制source_type值域
- ✅ 优先级排序确保确定性匹配

#### 📝 Python调用示例

```python
import requests

# 1. 创建规则
response = requests.post('http://localhost:8000/api/posting-rules/', json={
    "rule_name": "银行利息收入",
    "source_type": "bank_import",
    "pattern": "interest",
    "is_regex": false,
    "priority": 50,
    "debit_account_code": "bank",
    "credit_account_code": "interest_income"
})

# 2. 测试匹配
response = requests.post('http://localhost:8000/api/posting-rules/test', json={
    "description": "INTEREST CREDITED TO ACCOUNT",
    "source_type": "bank_import"
})
print(response.json()['matched'])  # True

# 3. 查询规则列表
response = requests.get('http://localhost:8000/api/posting-rules/?source_type=bank_import')
print(f"Total rules: {response.json()['total']}")
```

---

## 📝 开发指南

### 添加新的报表类型
1. 在`PDFReportGenerator`中添加生成方法
2. 在`FileStorageManager`中添加路径生成器
3. 在`pdf_reports.py`中添加API端点
4. 添加自动归档逻辑
5. 编写单元测试和集成测试

### 扩展月结任务
在`monthly_close.py`的`run_monthly_close()`函数中添加新步骤：
```python
# 5. 新的自动化任务
try:
    # 你的自动化逻辑
    new_task_result = your_automation_function(db, company_id, month)
except Exception as e:
    logger.error(f"新任务失败: {str(e)}")
    new_task_result = {"error": str(e)}

return {
    ...,
    "new_task": new_task_result
}
```

---

## 🐛 故障排查

### 常见问题

**Q: PDF生成后用户看不到变化？**
A: PDF会自动保存到FileStorageManager，同时返回给客户端。确认服务已重启。

**Q: 跨租户访问被拒绝？**
A: 检查`company_id`参数是否正确，系统使用`commonpath`严格验证路径。

**Q: 月结任务失败？**
A: 检查日志中的`management_report`字段，确保数据库中有足够的记录。

**Q: 测试失败？**
A: 确保测试数据库独立，运行前清理`test_accounting.db`。

---

## 📚 相关文档

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0文档](https://docs.sqlalchemy.org/)
- [ReportLab用户指南](https://www.reportlab.com/docs/reportlab-userguide.pdf)

---

## 🤝 贡献指南

1. 遵循PEP 8代码规范
2. 为所有新功能编写测试
3. 更新API文档（docstrings）
4. 确保所有测试通过
5. 遵循多租户隔离原则

---

## 📄 许可证

企业级专有软件 - 保留所有权利

---

**版本：** 1.0.0  
**最后更新：** 2025-11-01  
**作者：** AI SMART TECH Development Team
