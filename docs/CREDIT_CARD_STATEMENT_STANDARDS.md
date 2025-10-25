# 信用卡账单系统设置标准文档

## 📋 目录
1. [数据库架构标准](#1-数据库架构标准)
2. [月度账单合并规则](#2-月度账单合并规则)
3. [OWNER vs INFINITE分类系统](#3-owner-vs-infinite分类系统)
4. [文件存储标准](#4-文件存储标准)
5. [数据验证规则](#5-数据验证规则)
6. [支持的银行列表](#6-支持的银行列表)
7. [PDF解析规则](#7-pdf解析规则)
8. [显示格式标准](#8-显示格式标准)
9. [UI/UX设计标准](#9-uiux设计标准)

---

## 1. 数据库架构标准

### 1.1 monthly_statements 表（核心主表）
**用途**: 存储按银行+月份合并的月度账单数据

**字段定义**:
| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| `id` | INTEGER | PRIMARY KEY | 自增主键 |
| `customer_id` | INTEGER | NOT NULL, FK | 客户ID（外键→customers表） |
| `bank_name` | TEXT | NOT NULL | 银行名称 |
| `statement_month` | TEXT | NOT NULL | 账单月份（YYYY-MM格式） |
| `period_start_date` | TEXT | NULL | 账单周期开始日期（YYYY-MM-DD） |
| `period_end_date` | TEXT | NULL | 账单周期结束日期（YYYY-MM-DD） |
| `due_date` | TEXT | NULL | 还款截止日期（YYYY-MM-DD） |
| `previous_balance_total` | REAL | DEFAULT 0 | 上期总余额（RM） |
| `closing_balance_total` | REAL | DEFAULT 0 | 本期总结余（RM） |
| `owner_balance` | REAL | DEFAULT 0 | **Own's 欠款余额**（RM） |
| `gz_balance` | REAL | DEFAULT 0 | **GZ's 欠款余额**（RM） |
| `owner_expenses` | REAL | DEFAULT 0 | **Own's 本期消费总额**（RM） |
| `owner_payments` | REAL | DEFAULT 0 | **Own's 本期付款总额**（RM，存储为负数） |
| `gz_expenses` | REAL | DEFAULT 0 | **GZ's 本期消费总额**（RM） |
| `gz_payments` | REAL | DEFAULT 0 | **GZ's 本期付款总额**（RM，存储为负数） |
| `file_paths` | TEXT | NULL | 关联的PDF文件路径（JSON数组格式） |
| `card_count` | INTEGER | DEFAULT 0 | 本月度合并的信用卡数量 |
| `transaction_count` | INTEGER | DEFAULT 0 | 交易总笔数 |
| `validation_score` | REAL | DEFAULT 0 | 数据验证置信度得分（0-100） |
| `is_confirmed` | INTEGER | DEFAULT 0 | 是否已人工确认（0/1） |
| `inconsistencies` | TEXT | NULL | 数据不一致记录（JSON格式） |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**唯一性约束**:
```sql
UNIQUE(customer_id, bank_name, statement_month)
```
- 确保每个客户的每家银行每个月只有一条记录
- 即使同一银行有多张卡片，也合并为一条月度账单

**索引**:
```sql
CREATE INDEX idx_monthly_statements_customer 
ON monthly_statements(customer_id, bank_name, statement_month);
```

**核心业务规则**:
1. **Balance Validation**: `owner_balance + gz_balance = closing_balance_total` (100%准确性强制执行)
2. **6 Classification Fields**: 必须同时记录 owner_expenses, owner_payments, gz_expenses, gz_payments, owner_balance, gz_balance
3. **Hong Leong Bank Exception**: 该银行的payments字段存储为**正数**，其他所有银行存储为**负数**

---

### 1.2 monthly_statement_cards 表（关联表）
**用途**: 记录每个月度账单包含哪些信用卡

**字段定义**:
| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| `id` | INTEGER | PRIMARY KEY | 自增主键 |
| `monthly_statement_id` | INTEGER | NOT NULL, FK | 月度账单ID（外键→monthly_statements表） |
| `credit_card_id` | INTEGER | NOT NULL, FK | 信用卡ID（外键→credit_cards表） |
| `card_last4` | TEXT | NOT NULL | 卡号后四位 |
| `individual_balance` | REAL | DEFAULT 0 | 该卡的独立结余（可选） |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**唯一性约束**:
```sql
UNIQUE(monthly_statement_id, credit_card_id)
```

---

### 1.3 transactions 表（交易明细表）
**用途**: 存储所有交易明细

**关键字段**:
| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| `id` | INTEGER | PRIMARY KEY | 自增主键 |
| `monthly_statement_id` | INTEGER | NOT NULL, FK | 月度账单ID |
| `customer_id` | INTEGER | NOT NULL, FK | 客户ID |
| `card_last4` | TEXT | NOT NULL | 卡号后四位（用于多卡区分） |
| `date` | TEXT | NOT NULL | 交易日期（YYYY-MM-DD） |
| `description` | TEXT | NOT NULL | 交易描述 |
| `amount` | REAL | NOT NULL | 交易金额（消费为正，付款为负） |
| `type` | TEXT | NOT NULL | 交易类型（'purchase' / 'payment'） |
| `category` | TEXT | NULL | 交易分类（dining, shopping, etc.） |
| `owner_flag` | TEXT | NOT NULL | **分类标记**（'own' / 'gz'） |
| `classification_source` | TEXT | DEFAULT 'auto' | 分类来源（'auto' / 'manual'） |
| `supplier_name` | TEXT | NULL | 供应商名称（仅INFINITE交易） |
| `supplier_fee` | REAL | DEFAULT 0 | 供应商手续费（默认1%） |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**:
```sql
CREATE INDEX idx_transactions_monthly_statement 
ON transactions(monthly_statement_id);

CREATE INDEX idx_transactions_owner_flag 
ON transactions(owner_flag);
```

---

## 2. 月度账单合并规则

### 2.1 合并原则
**核心规则**: `ONE BANK + ONE MONTH = ONE RECORD`

```
客户A + Maybank + 2024-11 → 一条月度账单记录
（即使该客户在Maybank有3张信用卡）
```

### 2.2 合并逻辑示例

**场景**: 客户CHANG CHOON CHOW 在 Maybank 有3张卡

| 卡号后4位 | 账单月份 | 消费 | 付款 | 结余 |
|-----------|---------|------|------|------|
| 1234 | 2024-11 | 2,500 | -1,000 | 1,500 |
| 5678 | 2024-11 | 1,200 | -500 | 700 |
| 9012 | 2024-11 | 800 | 0 | 800 |

**合并后的 monthly_statements 记录**:
```
customer_id: 1
bank_name: "Maybank"
statement_month: "2024-11"
card_count: 3
transaction_count: (所有交易总和)
closing_balance_total: 3,000 (1,500 + 700 + 800)
owner_balance: (根据OWNER分类计算)
gz_balance: (根据INFINITE分类计算)
owner_expenses: (所有owner_flag='own'且type='purchase'的总和)
owner_payments: (所有owner_flag='own'且type='payment'的总和)
gz_expenses: (所有owner_flag='gz'且type='purchase'的总和)
gz_payments: (所有owner_flag='gz'且type='payment'的总和)
```

### 2.3 重要例外

**AmBank vs AmBank Islamic**:
- 视为**两家独立银行**
- AmBank 2024-11 → 一条记录
- AmBank Islamic 2024-11 → 另一条记录

---

## 3. OWNER vs INFINITE分类系统

### 3.1 分类规则总览

```
交易类型
├── Purchase (消费)
│   ├── OWNER Expense (客户个人消费)
│   └── INFINITE Expense (GZ供应商消费 + 1%手续费)
└── Payment (付款)
    ├── OWNER Payment (客户本人付款)
    └── INFINITE Payment (第三方/公司付款)
```

### 3.2 Expense 分类规则

#### 3.2.1 INFINITE Expense 识别条件
满足以下**任一条件**即为 INFINITE Expense:

1. **交易描述包含7大核心供应商**（系统预设）:
   - `'7SL'`
   - `'HUAWEI'`
   - `'PASAR RAYA'`
   - `'SUPPLIER_4'`
   - `'SUPPLIER_5'`
   - `'SUPPLIER_6'`
   - `'SUPPLIER_7'`

2. **交易描述包含 supplier_aliases 表中的供应商别名**
   - 动态从数据库加载
   - 支持多语言别名（英文、中文、简称）
   - 不区分大小写

**示例**:
```
Transaction: "HUAWEI ONLINE STORE RM 4,299.00"
→ 匹配 'HUAWEI'
→ 分类为 INFINITE Expense
→ owner_flag = 'gz'
→ supplier_fee = 4,299.00 × 1% = 42.99
```

#### 3.2.2 OWNER Expense 识别条件
- 所有**不满足** INFINITE条件的消费
- 即: 非供应商交易 = OWNER消费

### 3.3 Payment 分类规则

#### 3.3.1 OWNER Payment 识别条件
满足以下**任一条件**即为 OWNER Payment:

1. **付款描述包含客户本名别名** (payer_aliases表, payer_type='customer'):
   ```
   "PAYMENT FROM CHANG CHOON CHOW" → OWNER Payment
   "PAYMENT FROM CCChow" → OWNER Payment (别名)
   ```

2. **付款描述包含公司名称** (payer_aliases表, payer_type='company'):
   ```
   "PAYMENT FROM KENG CHOW" → OWNER Payment (视为客户付款)
   ```

#### 3.3.2 INFINITE Payment 识别条件
- 所有**不满足** OWNER条件的付款
- 即: 无法识别付款人身份 = 默认 INFINITE付款

**默认规则**:
```
所有payments WITHOUT customer's name → INFINITE payments
只有明确包含客户姓名的payments → OWNER payments
```

### 3.4 供应商手续费计算

**默认费率**: 1%

**计算公式**:
```python
supplier_fee = amount × 1.0%
```

**可配置费率** (supplier_fee_config表):
```sql
SELECT fee_percentage FROM supplier_fee_config 
WHERE supplier_name = ? AND is_active = 1
```

**示例**:
```
HUAWEI交易 RM 10,000.00
→ supplier_fee = 10,000 × 1% = RM 100.00
```

### 3.5 数据库支持表

#### supplier_aliases 表
```sql
CREATE TABLE supplier_aliases (
    id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL,  -- 标准供应商名称
    alias TEXT NOT NULL,           -- 别名（小写存储）
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 唯一性约束
UNIQUE(supplier_name, alias)
```

#### payer_aliases 表
```sql
CREATE TABLE payer_aliases (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    payer_type TEXT NOT NULL,  -- 'customer' or 'company'
    alias TEXT NOT NULL,        -- 别名（小写存储）
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 唯一性约束
UNIQUE(customer_id, payer_type, alias)
```

#### supplier_fee_config 表
```sql
CREATE TABLE supplier_fee_config (
    id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL UNIQUE,
    fee_percentage REAL DEFAULT 1.0,  -- 手续费百分比
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. 文件存储标准

### 4.1 统一存储架构
**服务**: `FileStorageManager` (services/file_storage_manager.py)

### 4.2 信用卡账单文件路径标准

**格式**:
```
static/uploads/customers/{customer_code}/credit_cards/{bank_name}/{YYYY-MM}/{BankName}_{Last4}_{YYYY-MM-DD}.pdf
```

**Customer Code格式**: `Be_rich_{INITIALS}`

**完整示例**:
```
static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/2024-11/Maybank_1234_2024-11-15.pdf
static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/2024-11/Maybank_5678_2024-11-15.pdf
static/uploads/customers/Be_rich_CCC/credit_cards/HSBC/2024-10/HSBC_9012_2024-10-20.pdf
```

### 4.3 文件命名规则

**组成部分**:
1. **BankName**: 银行名称（英文，首字母大写，无空格）
   - Maybank
   - HSBC
   - Hong_Leong_Bank

2. **Last4**: 信用卡号后四位
   - 1234
   - 5678

3. **Date**: 账单日期（YYYY-MM-DD）
   - 2024-11-15

**命名模式**:
```
{BankName}_{Last4}_{YYYY-MM-DD}.pdf
```

### 4.4 目录结构要求

```
static/uploads/customers/
└── Be_rich_CCC/
    └── credit_cards/
        ├── Maybank/
        │   ├── 2024-10/
        │   │   ├── Maybank_1234_2024-10-15.pdf
        │   │   └── Maybank_5678_2024-10-15.pdf
        │   ├── 2024-11/
        │   │   ├── Maybank_1234_2024-11-15.pdf
        │   │   └── Maybank_5678_2024-11-15.pdf
        │   └── 2024-12/
        ├── HSBC/
        │   └── 2024-11/
        │       └── HSBC_9012_2024-11-20.pdf
        └── Alliance_Bank/
            └── 2024-11/
                └── Alliance_Bank_3456_2024-11-25.pdf
```

### 4.5 存储核心特性

- ✅ **完全客户隔离**: 每个客户独立文件夹
- ✅ **路径即索引**: 文件路径自解释，无需额外索引
- ✅ **时间维度管理**: 按年月自动分类（YYYY-MM/）
- ✅ **类型自动分类**: 按银行名称自动组织
- ✅ **标准化命名**: 统一命名规范
- ✅ **跨平台兼容**: 使用正斜杠，相对路径存储

---

## 5. 数据验证规则

### 5.1 双重验证机制
**目标**: 确保100%数据准确性

#### Validation Method 1: 数学验证
**步骤**:
1. 从PDF提取官方声明的总额（TOTAL DEBIT, TOTAL CREDIT）
2. 计算所有解析交易的总和
3. 交叉比对两者差异

**容差标准**: ± RM 0.01

**验证公式**:
```python
extracted_debit = sum(t['amount'] for t in transactions if t['amount'] > 0)
pdf_declared_debit = extract_from_pdf("TOTAL DEBIT THIS MONTH")

diff = abs(extracted_debit - pdf_declared_debit)
is_valid = (diff <= 0.01)
```

#### Validation Method 2: PDF原文交叉验证
**步骤**:
1. 重新提取PDF原始文本
2. 逐行比对已解析的交易记录
3. 检查遗漏、重复、错误

**检查项**:
- ✅ 交易笔数是否一致
- ✅ 每笔交易金额是否准确
- ✅ 交易日期是否正确
- ✅ 交易描述是否完整

### 5.2 置信度评分系统

**评分标准**:
```python
confidence_score = 100.0

# 数学验证不通过
if debit_diff > 0.01:
    confidence_score -= 30

if credit_diff > 0.01:
    confidence_score -= 20

# PDF交叉验证
missing_transactions = pdf_count - extracted_count
if missing_transactions > 0:
    confidence_score -= (missing_transactions * 5)

# 最终得分范围: 0-100
confidence_score = max(0, min(100, confidence_score))
```

**结果判定**:
| 得分范围 | 状态 | 操作 |
|---------|------|------|
| 95-100 | ✅ PASSED | 自动确认，无需人工复核 |
| 80-94 | ⚠️ WARNING | 触发警告，建议人工复核 |
| 0-79 | ❌ FAILED | 验证失败，必须人工修正 |

### 5.3 Balance Reconciliation（余额对账）

**核心公式**:
```
Previous Balance + Expenses - Payments = Closing Balance
```

**OWNER/INFINITE验证**:
```
owner_balance + gz_balance = closing_balance_total
```

**容差**: RM 0.00（零容差，必须100%准确）

**示例**:
```
closing_balance_total = 10,000.00
owner_balance = 7,000.00
gz_balance = 3,000.00

Validation: 7,000 + 3,000 = 10,000 ✅ PASS
```

---

## 6. 支持的银行列表

### 6.1 信用卡账单支持银行（15家）

| # | 银行名称 | 英文名称 | 系统标识 | PDF Parser状态 |
|---|---------|---------|---------|---------------|
| 1 | 马来亚银行 | Maybank | maybank | ✅ 已实现 |
| 2 | 联昌国际银行 | CIMB | cimb | ✅ 已实现 |
| 3 | 大众银行 | Public Bank | public_bank | ✅ 已实现 |
| 4 | RHB银行 | RHB | rhb | ✅ 已实现 |
| 5 | 丰隆银行 | Hong Leong Bank | hong_leong_bank | ✅ 已实现 |
| 6 | 安联银行 | AmBank | ambank | ✅ 已实现 |
| 7 | 安联伊斯兰银行 | AmBank Islamic | ambank_islamic | ⚠️ 视为独立银行 |
| 8 | 联盟银行 | Alliance Bank | alliance_bank | ✅ 已实现 |
| 9 | 艾芬银行 | Affin Bank | affin_bank | ✅ 已实现 |
| 10 | 汇丰银行 | HSBC | hsbc | ✅ 已实现 |
| 11 | 渣打银行 | Standard Chartered | standard_chartered | ✅ 已实现 |
| 12 | 华侨银行 | OCBC | ocbc | ✅ 已实现 |
| 13 | 大华银行 | UOB | uob | ✅ 已实现 |
| 14 | 伊斯兰银行 | Bank Islam | bank_islam | ✅ 已实现 |
| 15 | 人民银行 | Bank Rakyat | bank_rakyat | ✅ 已实现 |

### 6.2 特殊处理规则

#### Hong Leong Bank (丰隆银行)
**特殊性**: Payments存储为**正数**

```python
# 其他所有银行
payment_amount = -1000.00  # 负数

# Hong Leong Bank
payment_amount = 1000.00   # 正数
```

**原因**: 该银行PDF格式特殊，付款金额原本显示为正数

**影响范围**:
- ✅ 数据库存储: 正数
- ✅ 前端显示: 使用 `abs()` 统一显示为正数
- ✅ 计算逻辑: 需特殊处理

#### AmBank vs AmBank Islamic
- ⚠️ **视为两家独立银行**
- 分别创建月度账单记录
- 不合并处理

---

## 7. PDF解析规则

### 7.1 解析器架构

**Base Parser**: `parsers/base_parser.py`
- 提供通用解析方法
- 定义标准接口

**Bank-Specific Parsers**:
- `parsers/hsbc_parser.py`
- `parsers/hsbc_ocr_parser.py` (OCR扫描版)
- `parsers/maybank_parser.py`
- `parsers/hong_leong_bank_parser.py`
- ... (其他银行)

### 7.2 Regex提取规则（以HSBC为例）

#### 7.2.1 提取卡号
**格式**: `4386 7590 0475 2058`

**Regex**:
```python
r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})'
```

**处理**:
```python
card_number = match.group(1).replace(' ', '')  # 去除空格
card_last4 = card_number[-4:]  # 取后4位
```

#### 7.2.2 提取账单日期
**格式**: `Statement Date 15 Nov 2024` 或 `Statement Date: 15 Nov 2024`

**Regex**:
```python
patterns = [
    r'Statement\s+Date\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
    r'Statement Date:\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
]
```

**转换**:
```python
dt = datetime.strptime(date_str, '%d %b %Y')
statement_date = dt.strftime('%Y-%m-%d')  # 转为 YYYY-MM-DD
```

#### 7.2.3 提取账单总额
**格式**: `Your statement balance   12,814.60`

**Regex**:
```python
patterns = [
    r'Your statement balance\s+([\d,]+\.\d{2})',
    r'Statement\s+Balance\s*\(RM\)\s+([\d,]+\.\d{2})'
]
```

**处理**:
```python
amount_str = match.group(1).replace(',', '')  # 移除逗号
closing_balance = float(amount_str)
```

#### 7.2.4 提取交易明细
**格式**: `13 MAY    12 MAY   GRAB HOLDINGS INC    45.00`

**Regex**:
```python
pattern = r'^\s*(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))\s+(\d{1,2}\s*\d*\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))?\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?$'
```

**捕获组**:
1. `group(1)`: Post Date (记账日期)
2. `group(2)`: Transaction Date (交易日期)
3. `group(3)`: Description (交易描述)
4. `group(4)`: Amount (金额)
5. `group(5)`: CR marker (贷方标记，表示付款/退款)

**交易类型判断**:
```python
if is_credit or 'PAYMENT' in description.upper():
    txn_type = 'payment'
else:
    txn_type = 'purchase'
```

### 7.3 OCR处理规则

**触发条件**: 当PDF为扫描件（无文本层）时

**OCR工具**: `pytesseract` (Tesseract OCR)

**流程**:
1. 使用 `pdf2image` 将PDF转为图片
2. 使用 `pytesseract` 提取文本
3. 应用相同的Regex规则
4. 额外的文本清理（OCR可能产生噪音）

**示例** (`parsers/hsbc_ocr_parser.py`):
```python
# OCR交易格式: DD Mon DESCRIPTION AMOUNT
pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+([A-Z][A-Za-z\s&\.\-]+?)\s+([\d,]+\.\d{2})'
```

---

## 8. 显示格式标准

### 8.1 Admin Dashboard - 月度账单列表

**列顺序**:
```
Due Date → PRE BAL → Owner Expenses → Owner Payments → GZ Expenses → 
GZ Payments → Owner Balance → GZ Balance → Total → Actions
```

**共13列**

#### 8.1.1 列格式定义

| 列名 | 数据字段 | 显示格式 | 颜色 | 说明 |
|-----|---------|---------|------|------|
| Due Date | `due_date` | `YYYY-MM-DD` | 白色 | 还款截止日期 |
| PRE BAL | `previous_balance_total` | `RM X,XXX` | **深紫色 #322446** | 上期总余额（突出显示） |
| Owner Expenses | `owner_expenses` | `RM X,XXX` | 热粉色 #FF007F | Own's 本期消费 |
| Owner Payments | `owner_payments` | `RM X,XXX` | 热粉色 #FF007F | Own's 本期付款（**显示为正数**） |
| GZ Expenses | `gz_expenses` | `RM X,XXX` | 深紫色 #322446 | GZ's 本期消费 |
| GZ Payments | `gz_payments` | `RM X,XXX` | 深紫色 #322446 | GZ's 本期付款（**显示为正数**） |
| Owner Balance | `owner_balance` | `RM X,XXX` | 热粉色 #FF007F | Own's 欠款余额 |
| GZ Balance | `gz_balance` | `RM X,XXX` | 深紫色 #322446 | GZ's 欠款余额 |
| Total | `closing_balance_total` | `RM X,XXX` | 白色 | 本期总结余 |
| Actions | - | 按钮组 | - | 查看详情、编辑等 |

#### 8.1.2 重要显示规则

**Payments显示为正数**:
```python
# 数据库存储（Hong Leong Bank除外）
owner_payments = -1000.00

# 前端显示
display_value = abs(owner_payments)  # 1000.00
formatted = "RM 1,000"
```

**PRE BAL突出显示**:
```html
<td style="color: #322446; font-weight: 700; background-color: rgba(50, 36, 70, 0.1);">
    RM {{ "{:,.0f}".format(previous_balance_total) }}
</td>
```

### 8.2 月度账单详情页

**路由**: `/monthly_statement_detail/<int:statement_id>`

**显示内容**:
1. **账单基本信息**
   - 客户姓名
   - 银行名称
   - 账单月份
   - 卡片数量
   - 交易总数

2. **财务摘要**
   - Previous Balance Total
   - Owner Expenses / Payments / Balance
   - GZ Expenses / Payments / Balance
   - Closing Balance Total

3. **交易明细（按卡号分组）**
   ```
   卡号 XXXX1234:
   - 15 Nov 2024: GRAB HOLDINGS INC    RM 45.00 (Own)
   - 16 Nov 2024: HUAWEI ONLINE STORE  RM 4,299.00 (GZ) [Supplier Fee: RM 42.99]
   
   卡号 XXXX5678:
   - 15 Nov 2024: SHOPEE MALAYSIA      RM 120.00 (Own)
   ```

**卡号标记格式**:
```
"交易描述 (卡XXXX)"
```

示例:
```
"GRAB HOLDINGS INC (卡1234)"
```

---

## 9. UI/UX设计标准

### 9.1 颜色系统（3色严格限制）

**强制规则**: **MINIMAL 3-COLOR PALETTE ONLY**

| 颜色代码 | 颜色名称 | 用途 | 应用场景 |
|---------|---------|------|---------|
| `#000000` | Black | 主背景 | 页面背景、卡片背景 |
| `#FF007F` | Hot Pink | 主强调色 | OWNER数据、收入、积分、Primary按钮 |
| `#322446` | Dark Purple | 次强调色 | INFINITE/GZ数据、支出、边框 |

**辅助色（仅限特定场景）**:
| 颜色代码 | 颜色名称 | 用途 |
|---------|---------|------|
| `#FFFEF0` | Pearl White | 文字、标签、中性数据 |

**⚠️ 禁止使用其他颜色**

### 9.2 Admin Dashboard卡片样式标准

#### 9.2.1 系统统计卡片（第一排）
**数量**: 4个卡片
**内容**: Total Customers, Total Statements, Total Transactions, Active Cards

**样式规格**:
```css
/* 卡片容器 */
.stat-card {
    min-height: 140px;
    background: linear-gradient(135deg, rgba(50, 36, 70, 0.3) 0%, rgba(0, 0, 0, 0.95) 100%);
    border: 1px solid #322446;
}

/* 数字 */
.stat-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #FFFEF0;
    height: 1.8rem;
    line-height: 1.3;
}

/* 标签 */
.stat-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #FFFEF0;
    text-shadow: 0 0 8px rgba(255,254,240,0.3);
    height: 2.6rem;
    line-height: 1.3;
}
```

#### 9.2.2 OWNER财务卡片（第二排）
**数量**: 4个卡片
**内容**: Own's Expenses, Own's Payment, Own's OS Bal, Supplier Invoices

**配色**: 热粉色系 (#FF007F)

**样式**:
```css
.stat-card {
    background: linear-gradient(135deg, rgba(255, 0, 127, 0.1) 0%, rgba(0, 0, 0, 0.95) 100%);
    border: 1px solid #FF007F;
}

.stat-value {
    color: #FF007F;
    font-size: 1.8rem;
}

.stat-label {
    color: #FFFEF0;
    text-shadow: 0 0 8px rgba(255,254,240,0.3);
    font-size: 0.9rem;
}
```

#### 9.2.3 GZ财务卡片（第三排）
**数量**: 4个卡片
**内容**: GZ's Expenses, GZ's Payment, GZ's OS Bal, Total Invoices Amount

**配色**: 深紫色系 (#322446)

**样式**:
```css
.stat-card {
    background: linear-gradient(135deg, rgba(50, 36, 70, 0.3) 0%, rgba(0, 0, 0, 0.95) 100%);
    border: 1px solid #322446;
}

.stat-value {
    color: #322446;
    font-size: 1.8rem;
}

.stat-label {
    color: #FFFEF0;
    text-shadow: 0 0 8px rgba(255,254,240,0.3);
    font-size: 0.9rem;
}
```

#### 9.2.4 统一规格

**所有卡片共同规格**:
- **最小高度**: `140px`
- **数字字体**: `1.8rem` (统一)
- **数字高度**: `1.8rem` (固定，确保垂直对齐)
- **标签字体**: `0.9rem` (统一)
- **标签高度**: `2.6rem` (固定，确保水平对齐)
- **列宽**: `col-md-3` (Bootstrap)

### 9.3 表格样式标准

**月度账单表格**:
```css
/* 表头 */
th {
    background: linear-gradient(135deg, #322446 0%, #1a1329 100%);
    color: #FFFEF0;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 1rem;
    border-bottom: 2px solid #FF007F;
}

/* 表格行 */
tr:hover {
    background: rgba(255, 0, 127, 0.05);
    transition: all 0.3s ease;
}

/* PRE BAL列（特殊突出） */
td.pre-balance {
    color: #322446;
    font-weight: 700;
    background-color: rgba(50, 36, 70, 0.1);
}

/* OWNER数据列 */
td.owner-data {
    color: #FF007F;
    font-weight: 600;
}

/* GZ数据列 */
td.gz-data {
    color: #322446;
    font-weight: 600;
}
```

### 9.4 响应式设计

**断点**:
- `≥1200px`: 4列卡片布局
- `768-1199px`: 2列卡片布局
- `<768px`: 1列卡片布局（手机）

**优化**:
- 卡片高度自适应
- 字体大小保持不变
- 表格水平滚动（小屏幕）

---

## 10. 自动化流程标准

### 10.1 上传流程

```
用户上传PDF → 自动识别银行 → 调用对应Parser → 提取数据 → 
分类OWNER/INFINITE → 双重验证 → 
(验证通过) → 写入数据库 → 生成月度账单记录 → 
关联信用卡 → 存储文件 → 完成
```

### 10.2 月度合并流程

```
检查: (customer_id, bank_name, statement_month) 是否存在？
├── 存在 → 更新现有记录
│   ├── 累加 expenses / payments
│   ├── 更新 balances
│   ├── 增加 card_count
│   ├── 累加 transaction_count
│   └── 追加 file_paths
└── 不存在 → 创建新记录
    ├── 初始化 6 classification fields
    ├── 设置 card_count = 1
    └── 设置 validation_score
```

### 10.3 数据一致性检查

**定期任务** (每日凌晨3点):
```python
for statement in monthly_statements:
    # 检查1: Balance公式
    calculated_balance = previous_balance + expenses - payments
    if abs(calculated_balance - closing_balance) > 0.01:
        flag_inconsistency(statement)
    
    # 检查2: OWNER + GZ = Total
    owner_gz_sum = owner_balance + gz_balance
    if abs(owner_gz_sum - closing_balance_total) > 0.01:
        flag_inconsistency(statement)
    
    # 检查3: 交易笔数
    db_count = count_transactions(statement_id)
    if db_count != statement.transaction_count:
        flag_inconsistency(statement)
```

---

## 11. 批量操作标准

### 11.1 批量上传
- 支持一次上传多个PDF文件
- 自动识别每个文件的银行、客户、月份
- 并行处理（多线程）
- 实时进度反馈

### 11.2 批量导出
- 支持按客户、银行、月份范围导出
- 格式: Excel / CSV / PDF
- 包含OWNER/INFINITE分类
- 包含供应商手续费

---

## 📝 版本历史

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| v1.0 | 2025-10-25 | 初始版本，完整系统标准文档 |

---

## 🔗 相关文档

- [文件存储架构详解](./FILE_STORAGE_ARCHITECTURE.md)
- [OWNER vs INFINITE分类指南](./OWNER_INFINITE_CLASSIFICATION.md)
- [API接口文档](./API_DOCUMENTATION.md)
- [数据库Schema](./DATABASE_SCHEMA.md)

---

**文档维护**: 系统管理员
**最后更新**: 2025-10-25
**状态**: ✅ 生效中
