# CreditPilot 技术配置详细文档

**版本**: V2025.11  
**更新日期**: 2025-11-24  
**目标读者**: 系统管理员、开发人员、技术支持

---

## 📋 目录

1. [数据库结构](#数据库结构)
2. [Parser系统配置](#parser系统配置)
3. [计算引擎参数](#计算引擎参数)
4. [API端点清单](#api端点清单)
5. [配置文件详解](#配置文件详解)
6. [环境变量](#环境变量)
7. [部署配置](#部署配置)
8. [性能优化参数](#性能优化参数)

---

## 数据库结构

### 核心数据表（21个）

#### 1. customers（客户表）

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code VARCHAR(20) UNIQUE NOT NULL,  -- 例: LEE_EK_009
    name VARCHAR(100) NOT NULL,                 -- 客户姓名
    email VARCHAR(100),
    phone VARCHAR(20),
    monthly_income DECIMAL(15,2),               -- 月收入
    personal_account_name VARCHAR(100),         -- 个人账户名称
    personal_account_number VARCHAR(50),        -- 个人账户号
    company_account_name VARCHAR(100),          -- 公司账户名称
    company_account_number VARCHAR(50),         -- 公司账户号
    tag_desc VARCHAR(50),                       -- 标签描述
    user_id INTEGER,                            -- 关联用户ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**关键字段说明**：
- `customer_code`: 唯一标识符，格式 `{姓名缩写}_数字`
- `monthly_income`: 用于贷款评估的核心数据
- `personal_account_*`: 用于识别Owner's Payment
- `company_account_*`: 用于识别GZ's Payment2

---

#### 2. credit_cards（信用卡表）

```sql
CREATE TABLE credit_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    bank_name VARCHAR(50) NOT NULL,             -- 银行名称
    card_number VARCHAR(20),                    -- 卡号（后4位）
    card_holder_name VARCHAR(100),              -- 持卡人姓名
    credit_limit DECIMAL(15,2),                 -- 信用额度
    card_type VARCHAR(50),                      -- 卡类型（Visa/MasterCard）
    status VARCHAR(20) DEFAULT 'active',        -- 状态
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

**支持的银行**：
```
AMBANK, AMBANK_ISLAMIC, UOB, HSBC, STANDARD_CHARTERED,
HONG_LEONG_BANK, OCBC, ALLIANCE_BANK, PUBLIC_BANK,
MAYBANK, CIMB, RHB, BSN, AFFIN_BANK
```

---

#### 3. statements（账单表）

```sql
CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    statement_month VARCHAR(7) NOT NULL,        -- 格式: YYYY-MM
    statement_date DATE NOT NULL,               -- 账单日期
    payment_due_date DATE,                      -- 还款截止日期
    statement_total DECIMAL(15,2),              -- 账单总额
    minimum_payment DECIMAL(15,2),              -- 最低还款额
    previous_balance DECIMAL(15,2),             -- 上月余额
    previous_balance_total DECIMAL(15,2),       -- 上月总余额
    
    -- 第1轮计算结果（6个基础项目）
    owner_expenses DECIMAL(15,2),               -- Owner's Expenses
    gz_expenses DECIMAL(15,2),                  -- GZ's Expenses
    owner_payment DECIMAL(15,2),                -- Owner's Payment
    gz_payment1 DECIMAL(15,2),                  -- GZ's Payment1
    owner_os_bal_round1 DECIMAL(15,2),          -- Owner's OS Bal（第1轮）
    gz_os_bal_round1 DECIMAL(15,2),             -- GZ's OS Bal（第1轮）
    
    -- 第2轮计算结果
    gz_payment2 DECIMAL(15,2),                  -- GZ's Payment2
    
    -- 最终结果
    final_owner_os_bal DECIMAL(15,2),           -- FINAL Owner OS Bal
    final_gz_os_bal DECIMAL(15,2),              -- FINAL GZ OS Bal
    
    pdf_path VARCHAR(500),                      -- PDF文件路径
    excel_path VARCHAR(500),                    -- Excel导出路径
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES credit_cards(id)
);
```

**计算字段详解**：
- `owner_expenses`: SUM(所有非Suppliers的DR交易)
- `gz_expenses`: SUM(所有Suppliers的DR交易)
- `owner_payment`: SUM(客户自己的CR还款)
- `gz_payment1`: 所有CR - Owner's Payment
- `owner_os_bal_round1`: Previous Balance + Owner's Expenses - Owner's Payment
- `gz_os_bal_round1`: Previous Balance + GZ's Expenses - GZ's Payment1
- `gz_payment2`: SUM(从9个GZ Bank转账到客户银行的金额)
- `final_owner_os_bal`: owner_os_bal_round1（不变）
- `final_gz_os_bal`: gz_os_bal_round1 - GZ's Payment2

---

#### 4. transactions（交易表）

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    transaction_date DATE NOT NULL,             -- 交易日期
    description TEXT,                           -- 交易描述
    amount DECIMAL(15,2) NOT NULL,              -- 交易金额
    transaction_type VARCHAR(10),               -- DR 或 CR
    category VARCHAR(50),                       -- 分类标签
    
    -- 智能分类结果
    owner_flag VARCHAR(20),                     -- owner / infinite / unassigned
    supplier_match VARCHAR(100),                -- 匹配的供应商名称
    payment_source VARCHAR(100),                -- 付款来源
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**category可能值**：
```
owner_expense      - Owner's Expenses
gz_expense         - GZ's Expenses（Supplier交易）
owner_payment      - Owner's Payment
gz_payment         - GZ's Payment
infinite_expense   - INFINITE Expense（同义gz_expense）
infinite_payment   - INFINITE Payment（同义gz_payment）
```

---

#### 5. monthly_ledger（月度账本 - Customer）

```sql
CREATE TABLE monthly_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    month_start DATE NOT NULL,                  -- 月份（YYYY-MM-01）
    
    opening_balance DECIMAL(15,2),              -- 期初余额
    total_spend DECIMAL(15,2),                  -- 本月消费
    total_payments DECIMAL(15,2),               -- 本月还款
    rolling_balance DECIMAL(15,2),              -- 滚动余额
    
    statement_id INTEGER,                       -- 关联账单ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (statement_id) REFERENCES statements(id),
    UNIQUE (card_id, month_start)
);
```

**计算公式**：
```
rolling_balance = opening_balance + total_spend - total_payments
```

---

#### 6. infinite_monthly_ledger（月度账本 - INFINITE）

```sql
CREATE TABLE infinite_monthly_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    month_start DATE NOT NULL,                  -- 月份（YYYY-MM-01）
    
    opening_balance DECIMAL(15,2),              -- 期初余额
    total_spend DECIMAL(15,2),                  -- 本月消费
    total_payments DECIMAL(15,2),               -- 本月还款
    rolling_balance DECIMAL(15,2),              -- 滚动余额
    
    statement_id INTEGER,                       -- 关联账单ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (statement_id) REFERENCES statements(id),
    UNIQUE (card_id, month_start)
);
```

---

#### 7. loan_products（贷款产品库 - 804个）

```sql
CREATE TABLE loan_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name VARCHAR(100) NOT NULL,            -- 银行名称
    product_name VARCHAR(200) NOT NULL,         -- 产品名称
    product_type VARCHAR(50),                   -- Personal/Home/Car/Business
    
    -- 利率
    interest_rate_min DECIMAL(5,2),             -- 最低利率
    interest_rate_max DECIMAL(5,2),             -- 最高利率
    base_rate VARCHAR(20),                      -- 基准利率（BR/BLR）
    
    -- 贷款额度
    loan_amount_min DECIMAL(15,2),              -- 最低额度
    loan_amount_max DECIMAL(15,2),              -- 最高额度
    
    -- 期限
    tenure_min INTEGER,                         -- 最短期限（月）
    tenure_max INTEGER,                         -- 最长期限（月）
    
    -- 资格要求
    min_income DECIMAL(15,2),                   -- 最低月收入
    max_dsr DECIMAL(5,2),                       -- 最大DSR
    max_dti DECIMAL(5,2),                       -- 最大DTI
    credit_score_min INTEGER,                   -- 最低信用评分
    
    -- 费用
    processing_fee DECIMAL(5,2),                -- 手续费（%）
    early_settlement_fee DECIMAL(5,2),          -- 提前还款费（%）
    
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**产品分布**：
```yaml
Personal Loan: 250个产品
Home Loan: 180个产品
Car Loan: 150个产品
Business Loan: 120个产品
SME Financing: 104个产品
总计: 804个产品
```

---

#### 8. credit_card_products（信用卡产品库 - 156个）

```sql
CREATE TABLE credit_card_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name VARCHAR(100) NOT NULL,
    card_name VARCHAR(200) NOT NULL,
    card_type VARCHAR(50),                      -- Visa/MasterCard/AMEX
    
    -- 奖励
    cashback_rate DECIMAL(5,2),                 -- 现金回赠率（%）
    points_rate DECIMAL(5,2),                   -- 积分回赠率
    annual_fee DECIMAL(10,2),                   -- 年费
    
    -- 特色
    travel_insurance BOOLEAN,                   -- 旅游保险
    lounge_access BOOLEAN,                      -- 机场贵宾室
    fuel_discount BOOLEAN,                      -- 油费折扣
    
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

#### 9. ctos_reports（CTOS报告）

```sql
CREATE TABLE ctos_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    report_type VARCHAR(20),                    -- personal / company
    
    -- Personal CTOS
    ic_number VARCHAR(20),
    full_name VARCHAR(100),
    credit_score INTEGER,                       -- 信用评分
    total_debt DECIMAL(15,2),                   -- 总债务
    monthly_commitment DECIMAL(15,2),           -- 月供承诺
    
    -- Company CTOS
    company_name VARCHAR(200),
    registration_number VARCHAR(50),
    company_debt DECIMAL(15,2),
    
    pdf_path VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

---

#### 10. audit_logs（审计日志）

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,               -- 操作类型
    table_name VARCHAR(50),                     -- 表名
    record_id INTEGER,                          -- 记录ID
    old_value TEXT,                             -- 旧值（JSON）
    new_value TEXT,                             -- 新值（JSON）
    ip_address VARCHAR(50),                     -- IP地址
    user_agent TEXT,                            -- 浏览器信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**记录的操作**：
```
- CREATE_CUSTOMER
- UPDATE_CUSTOMER
- DELETE_CUSTOMER
- UPLOAD_STATEMENT
- GENERATE_REPORT
- EVALUATE_LOAN
- CLASSIFY_TRANSACTION
- LOGIN
- LOGOUT
```

---

## Parser系统配置

### 13家银行Parser配置

**位置**: `config/bank_parser_templates.json`

#### 配置结构

```json
{
  "BANK_NAME": {
    "bank_name": "AMBANK",
    "patterns": {
      "statement_date": {
        "regex": ["pattern1", "pattern2", "pattern3"],
        "validation": "required"
      },
      "payment_due_date": {
        "regex": ["pattern1", "pattern2"],
        "validation": "required"
      },
      "statement_total": {
        "regex": ["pattern1"],
        "validation": "required"
      },
      "minimum_payment": {
        "regex": ["pattern1"],
        "validation": "required"
      },
      "previous_balance": {
        "regex": ["pattern1"],
        "validation": "optional"
      },
      "credit_limit": {
        "regex": ["pattern1"],
        "validation": "optional"
      }
    },
    "transaction_patterns": {
      "transaction_line": {
        "regex": "complete_pattern",
        "groups": {
          "date": 1,
          "description": 2,
          "amount": 3,
          "cr_marker": 4
        }
      }
    },
    "aliases": ["AMBANK", "AM BANK"]
  }
}
```

#### 关键字段提取规则

**必需字段（4个）**：
```yaml
statement_date:
  - 格式: DD-MMM-YY 或 DD MMM YY
  - 示例: "28 OCT 25", "28-OCT-25"
  - 验证: 必须存在，不能为空

payment_due_date:
  - 格式: DD-MMM-YY
  - 示例: "17 NOV 25"
  - 验证: 必须存在，不能为空

statement_total:
  - 格式: 数字（可含逗号）
  - 示例: "15,062.57", "1501.88"
  - 验证: 必须存在，必须>0

minimum_payment:
  - 格式: 数字（可含逗号）
  - 示例: "1,501.88", "150.00"
  - 验证: 必须存在，必须>0
```

**可选字段（4个）**：
```yaml
previous_balance:
  - 允许为0或负数（CR余额）
  - 不强制要求

credit_limit:
  - 信用额度
  - 不强制要求

card_number:
  - 卡号（通常显示后4位）
  - 不强制要求

card_holder_name:
  - 持卡人姓名
  - 不强制要求
```

---

### 交易提取规则

#### DR/CR识别

**方法1: 独立列解析**
```
多数银行使用双列格式:
┌──────┬─────────────────┬────────┬────────┐
│ Date │ Description     │   DR   │   CR   │
├──────┼─────────────────┼────────┼────────┤
│28 OCT│ GRAB FOOD       │ 45.60  │        │
│29 OCT│ PAYMENT RECEIVED│        │ 500.00 │
└──────┴─────────────────┴────────┴────────┘

规则:
  - DR列有值 → transaction_type = 'DR'
  - CR列有值 → transaction_type = 'CR'
```

**方法2: CR标记**
```
部分银行使用单列 + CR标记:
┌──────┬─────────────────┬──────────┐
│ Date │ Description     │  Amount  │
├──────┼─────────────────┼──────────┤
│28 OCT│ GRAB FOOD       │   45.60  │
│29 OCT│ PAYMENT         │  500.00CR│
└──────┴─────────────────┴──────────┘

规则:
  - 金额后有"CR" → transaction_type = 'CR'
  - 否则 → transaction_type = 'DR'
```

**方法3: 关键词识别**
```
CR关键词:
  - PAYMENT
  - REFUND
  - CREDIT
  - BAYARAN
  - CASH DEPOSIT
  
包含任意关键词 → 可能是CR（需双重验证）
```

---

### 验证层级（4层）

```yaml
Layer 1: 文件验证
  - PDF格式检查
  - 文件大小检查（<10MB）
  - 页数检查（<50页）

Layer 2: 字段验证
  - 4个必需字段必须存在
  - 日期格式验证
  - 金额格式验证
  - 数值范围验证

Layer 3: 交易验证
  - DR/CR双列存在性检查
  - 交易日期在账单周期内
  - 金额>0验证
  - 描述非空验证

Layer 4: 逻辑验证
  - 交易合计 ≈ statement_total（±5%容差）
  - Previous Balance + 本月交易 ≈ Statement Total
  - Minimum Payment ≤ Statement Total
```

---

## 计算引擎参数

### 精度设置

```python
# 使用Decimal避免浮点数误差
from decimal import Decimal, ROUND_HALF_UP

# 精度配置
DECIMAL_PLACES = 2
ROUNDING_MODE = ROUND_HALF_UP

# 示例
amount = Decimal('15062.5678')
rounded = amount.quantize(Decimal('0.01'), rounding=ROUNDING_MODE)
# 结果: 15062.57
```

### 容差设置

```python
# 金额比较容差
AMOUNT_TOLERANCE = Decimal('0.01')  # RM 0.01

# 百分比容差
PERCENTAGE_TOLERANCE = Decimal('0.05')  # 5%

# 比较示例
def amounts_equal(a, b):
    return abs(Decimal(a) - Decimal(b)) <= AMOUNT_TOLERANCE
```

### 负数余额处理

```python
# 允许负数余额（表示CR余额）
owner_os_bal = previous_balance + owner_expenses - owner_payment

# 如果结果为负数（例如 -500.00）:
# → 表示客户多还了RM 500.00
# → 显示为 "RM 500.00 CR"
# → 不报错，正常处理
```

---

## API端点清单

### Flask主应用（Port 5000）

#### 客户管理
```
GET    /admin/customers              - 客户列表（Admin/Accountant）
GET    /customers/<customer_id>      - 客户详情
POST   /customers/create             - 创建客户
PUT    /customers/<customer_id>      - 更新客户
DELETE /customers/<customer_id>      - 删除客户
```

#### 信用卡管理
```
GET    /credit-cards                 - 信用卡列表
GET    /credit-cards/<card_id>       - 信用卡详情
POST   /credit-cards/create          - 添加信用卡
POST   /credit-cards/upload-statement - 上传PDF账单
GET    /credit-cards/statement/<statement_id> - 账单详情
POST   /credit-cards/calculate       - 执行计算
```

#### 报告中心
```
GET    /reports                      - 报告中心主页
POST   /reports/generate/monthly     - 生成月度报告
POST   /reports/generate/annual      - 生成年度报告
POST   /reports/export/excel         - 导出Excel
POST   /reports/export/pdf           - 导出PDF
GET    /reports/download/<report_id> - 下载报告
```

#### 贷款评估
```
GET    /loans/evaluate               - 贷款评估表单
POST   /loans/evaluate               - 提交评估
POST   /loans/upload-ctos            - 上传CTOS报告
GET    /loans/results/<eval_id>      - 评估结果
GET    /loans/products               - 产品目录
```

#### AI助手
```
POST   /ai/chat                      - AI聊天
GET    /ai/daily-report              - 每日报告
POST   /ai/analyze-cashflow          - 现金流分析
POST   /ai/recommend-cards           - 信用卡推荐
```

---

### FastAPI后端（Port 8000）

#### 审计日志
```
POST   /api/audit/log                - 记录审计日志
GET    /api/audit/logs               - 查询审计日志
GET    /api/audit/logs/<user_id>     - 用户审计记录
```

#### 通知服务
```
POST   /api/notifications/send       - 发送通知
GET    /api/notifications/<user_id>  - 获取用户通知
PUT    /api/notifications/<notif_id>/read - 标记已读
```

#### 健康检查
```
GET    /health                       - 健康状态
GET    /health/database              - 数据库连接检查
GET    /health/ai                    - AI服务检查
```

---

## 配置文件详解

### config/colors.json

```json
{
  "palette": {
    "primary": {
      "black": "#000000",
      "hot_pink": "#FF007F",
      "dark_purple": "#322446"
    },
    "creditpilot_official": {
      "main_pink": "#FFB6C1",
      "deep_brown": "#3E2723"
    },
    "semantic": {
      "revenue": "#FF007F",
      "expense": "#322446",
      "success": "#28a745",
      "warning": "#ffc107",
      "danger": "#dc3545"
    }
  },
  "usage_rules": {
    "strict_3_color_only": true,
    "allow_semantic_override": false,
    "excel_colors": ["#FFB6C1", "#3E2723"]
  }
}
```

---

### config/app_settings.json（部分）

```json
{
  "creditpilot_app": {
    "server": {
      "flask": {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": false
      },
      "fastapi": {
        "host": "0.0.0.0",
        "port": 8000
      }
    },
    "features": {
      "ai_assistant": true,
      "daily_reports": true,
      "sms_notifications": true,
      "email_notifications": true,
      "ctos_integration": true
    },
    "limits": {
      "max_file_size_mb": 10,
      "max_pdf_pages": 50,
      "max_transactions_per_statement": 1000
    }
  }
}
```

---

## 环境变量

### 必需的环境变量

```bash
# AI服务
PERPLEXITY_API_KEY=pplx-xxx...              # Perplexity AI密钥
OPENAI_API_KEY=sk-xxx...                    # OpenAI备用密钥

# 通知服务
SENDGRID_API_KEY=SG.xxx...                  # SendGrid邮件
TWILIO_ACCOUNT_SID=ACxxx...                 # Twilio SMS
TWILIO_AUTH_TOKEN=xxx...                    # Twilio认证令牌

# 数据库（生产环境）
DATABASE_URL=postgresql://user:pass@host/db

# 安全
SESSION_SECRET_KEY=random-secret-key-here   # Flask会话密钥

# CTOS（如果使用）
CTOS_API_KEY=xxx...                         # CTOS API密钥
CTOS_API_URL=https://api.ctos.com.my
```

### 可选的环境变量

```bash
# Google Document AI（如果使用）
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id

# SFTP ERP导出
SFTP_HOST=erp.example.com
SFTP_PORT=22
SFTP_USERNAME=creditpilot
SFTP_PASSWORD=xxx...

# 性能监控
SENTRY_DSN=https://xxx@sentry.io/xxx        # 错误追踪

# 日志
LOG_LEVEL=INFO                              # DEBUG/INFO/WARNING/ERROR
LOG_FILE=/var/log/creditpilot/app.log
```

---

## 部署配置

### Replit部署

**Workflows配置**：
```yaml
- name: "Server"
  command: "python app.py"
  output_type: "webview"
  wait_for_port: 5000

- name: "Accounting API"
  command: "uvicorn accounting_app.main:app --host 0.0.0.0 --port 8000 --reload"
  output_type: "console"
  wait_for_port: 8000
```

---

### 生产部署（Render/Railway）

**Start Command**:
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 app:app
```

**Environment**:
```
PYTHON_VERSION=3.11
NODE_VERSION=20
```

---

## 性能优化参数

### 数据库优化

```python
# SQLite优化
PRAGMA journal_mode = WAL;          # 写前日志模式
PRAGMA synchronous = NORMAL;        # 同步模式
PRAGMA cache_size = -64000;         # 缓存64MB
PRAGMA temp_store = MEMORY;         # 临时表存储在内存
```

### 批量操作

```python
# 批量插入
BATCH_SIZE = 1000

# 批量更新
UPDATE_BATCH_SIZE = 500

# 并发限制
MAX_CONCURRENT_UPLOADS = 5
```

### 缓存设置

```python
# AI响应缓存
AI_CACHE_TTL = 3600  # 1小时

# 报告缓存
REPORT_CACHE_TTL = 1800  # 30分钟

# 产品目录缓存
PRODUCT_CACHE_TTL = 86400  # 24小时
```

---

**© 2025 CreditPilot - Technical Configuration Documentation**
