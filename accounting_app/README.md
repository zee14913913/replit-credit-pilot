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
