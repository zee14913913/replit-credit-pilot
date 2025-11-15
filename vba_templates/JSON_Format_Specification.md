# INFINITE GZ - JSON格式规范文档

## 📌 版本信息

- **版本：** 1.0.0
- **更新日期：** 2024-11-15
- **适用范围：** VBA Parser + Replit API

---

## 🎯 概述

本文档定义VBA解析器导出的标准JSON格式，确保客户端（VBA）和服务器（Replit）之间数据交换的一致性。

---

## 📋 通用字段说明

所有JSON文件必须包含以下顶层字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | String | ✅ | 固定值 `"success"` |
| `document_type` | String | ✅ | `"credit_card"` 或 `"bank_statement"` |
| `parsed_by` | String | ✅ | 解析器版本，如 `"VBA Parser v1.0"` |
| `parsed_at` | String | ✅ | 解析时间，格式 `"yyyy-mm-dd hh:nn:ss"` |
| `account_info` | Object | ✅ | 账户信息对象 |
| `transactions` | Array | ✅ | 交易明细数组 |
| `summary` | Object | ✅ | 汇总统计对象 |

---

## 💳 信用卡账单JSON格式

### 完整示例

```json
{
  "status": "success",
  "document_type": "credit_card",
  "parsed_by": "VBA Parser v1.0",
  "parsed_at": "2024-11-15 14:30:52",
  "account_info": {
    "owner_name": "CHANG CHOON CHOW",
    "bank": "PUBLIC BANK",
    "card_last_4": "1234",
    "card_type": "Visa",
    "statement_date": "12-09-2024",
    "due_date": "02-10-2024",
    "card_limit": 10000.00,
    "previous_balance": 5000.00,
    "closing_balance": 3500.00
  },
  "transactions": [
    {
      "date": "01-09-2024",
      "posting_date": "01-09-2024",
      "description": "SHOPEE PAYMENT",
      "amount": 150.00,
      "dr": 150.00,
      "cr": 0,
      "running_balance": 5150.00,
      "category": "Purchases",
      "sub_category": "网购"
    },
    {
      "date": "05-09-2024",
      "posting_date": "05-09-2024",
      "description": "PAYMENT THANK YOU",
      "amount": 1000.00,
      "dr": 0,
      "cr": 1000.00,
      "running_balance": 4150.00,
      "category": "Payment",
      "sub_category": "还款"
    }
  ],
  "summary": {
    "total_transactions": 25,
    "total_purchases": 4500.00,
    "total_payments": 6000.00,
    "total_finance_charges": 0,
    "balance_verified": true
  }
}
```

### account_info 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `owner_name` | String | ✅ | 持卡人姓名 |
| `bank` | String | ✅ | 银行名称 |
| `card_last_4` | String | ✅ | 卡号后4位 |
| `card_type` | String | ✅ | 卡类型（Visa/Mastercard） |
| `statement_date` | String | ✅ | 账单日期 (dd-mm-yyyy) |
| `due_date` | String | ✅ | 到期日期 (dd-mm-yyyy) |
| `card_limit` | Number | ✅ | 信用额度 |
| `previous_balance` | Number | ✅ | 期初余额 |
| `closing_balance` | Number | ✅ | 期末余额 |

### transactions 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | String | ✅ | 交易日期 (dd-mm-yyyy) |
| `posting_date` | String | ✅ | 入账日期 (dd-mm-yyyy) |
| `description` | String | ✅ | 交易描述 |
| `amount` | Number | ✅ | 交易金额（绝对值） |
| `dr` | Number | ✅ | 借方金额（消费） |
| `cr` | Number | ✅ | 贷方金额（还款） |
| `running_balance` | Number | ✅ | 累计余额 |
| `category` | String | ✅ | 主分类（Purchases/Payment/Finance Charges） |
| `sub_category` | String | ✅ | 子分类（网购/汽油费/还款等） |

### summary 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `total_transactions` | Number | ✅ | 交易总笔数 |
| `total_purchases` | Number | ✅ | 消费总额 |
| `total_payments` | Number | ✅ | 还款总额 |
| `total_finance_charges` | Number | ✅ | 利息费用总额 |
| `balance_verified` | Boolean | ✅ | 余额验证是否通过 |

---

## 🏦 银行流水JSON格式

### 完整示例

```json
{
  "status": "success",
  "document_type": "bank_statement",
  "parsed_by": "VBA Parser v1.0",
  "parsed_at": "2024-11-15 14:35:20",
  "bank_detected": "PUBLIC BANK",
  "account_info": {
    "account_number": "3119090727",
    "account_type": "RM ACE Account",
    "account_holder": "CHANG CHOON CHOW",
    "bank": "PUBLIC BANK",
    "statement_date": "25-09-2024",
    "opening_balance": 469.31,
    "closing_balance": 598.19,
    "total_debits": 800.00,
    "total_credits": 928.88
  },
  "transactions": [
    {
      "date": "01-09-2024",
      "description": "TNB BILL PAYMENT",
      "debit": 150.00,
      "credit": 0,
      "running_balance": 319.31,
      "category": "BILLS",
      "sub_category": "水电费"
    },
    {
      "date": "05-09-2024",
      "description": "SALARY CREDIT",
      "debit": 0,
      "credit": 5000.00,
      "running_balance": 5319.31,
      "category": "INCOME",
      "sub_category": "薪资收入"
    }
  ],
  "summary": {
    "total_transactions": 40,
    "category_breakdown": {
      "INCOME": 5000.00,
      "BILLS": 350.00,
      "CONSUMPTION": 1200.00,
      "EXPENSES": 450.00
    },
    "balance_verified": true,
    "balance_difference": 0.00
  }
}
```

### account_info 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_number` | String | ✅ | 账户号码 |
| `account_type` | String | ✅ | 账户类型 |
| `account_holder` | String | ✅ | 账户持有人 |
| `bank` | String | ✅ | 银行名称 |
| `statement_date` | String | ✅ | 账单日期 (dd-mm-yyyy) |
| `opening_balance` | Number | ✅ | 期初余额 |
| `closing_balance` | Number | ✅ | 期末余额 |
| `total_debits` | Number | ✅ | 借方总额 |
| `total_credits` | Number | ✅ | 贷方总额 |

### transactions 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | String | ✅ | 交易日期 (dd-mm-yyyy) |
| `description` | String | ✅ | 交易描述 |
| `debit` | Number | ✅ | 借方金额（支出） |
| `credit` | Number | ✅ | 贷方金额（收入） |
| `running_balance` | Number | ✅ | 累计余额 |
| `category` | String | ✅ | 主分类（INCOME/BILLS/CONSUMPTION/EXPENSES） |
| `sub_category` | String | ✅ | 子分类（薪资收入/水电费/汽油费等） |

### summary 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `total_transactions` | Number | ✅ | 交易总笔数 |
| `category_breakdown` | Object | ✅ | 分类汇总对象 |
| `balance_verified` | Boolean | ✅ | 余额验证是否通过 |
| `balance_difference` | Number | ✅ | 余额差异（应为0） |

---

## 📂 分类标准

### 信用卡分类

#### 主分类 (category)

| 分类 | 说明 |
|------|------|
| `Purchases` | 消费支出 |
| `Payment` | 还款 |
| `Finance Charges` | 利息费用 |

#### 子分类 (sub_category)

| 子分类 | 适用场景 |
|--------|----------|
| `网购` | Shopee/Lazada等 |
| `汽油费` | Petronas/Shell等 |
| `餐饮` | 餐厅/咖啡店 |
| `还款` | Payment交易 |
| `利息费用` | Interest/Finance Charge |
| `消费` | 其他一般消费 |

### 银行流水分类

#### 主分类 (category)

| 分类 | 说明 |
|------|------|
| `INCOME` | 收入 |
| `BILLS` | 账单费用 |
| `CONSUMPTION` | 日常消费 |
| `EXPENSES` | 其他支出 |

#### 子分类 (sub_category)

| 子分类 | 适用场景 |
|--------|----------|
| `薪资收入` | Salary/Gaji |
| `利息收入` | Interest/Faedah |
| `退款` | Refund/Return |
| `水电费` | TNB/Syabas |
| `通讯费` | Maxis/Celcom/Digi/Unifi |
| `网购` | Shopee/Lazada/Grab |
| `汽油费` | Petronas/Shell |
| `保险` | Insurance/Takaful |
| `贷款还款` | Loan/PTPTN |
| `银行费用` | Bank Charge/Fee |
| `转账` | Transfer/IBFT |
| `ATM提款` | ATM/Withdrawal |
| `其他收入` | 未分类收入 |
| `其他支出` | 未分类支出 |

---

## ✅ 验证规则

### 必填字段验证

所有JSON文件必须：
- ✅ `status` = `"success"`
- ✅ `document_type` 为 `"credit_card"` 或 `"bank_statement"`
- ✅ `account_info` 对象存在且完整
- ✅ `transactions` 数组存在（可为空数组）
- ✅ `summary` 对象存在

### 数据类型验证

- 所有金额字段为 `Number` 类型（保留2位小数）
- 所有日期字段为 `String` 类型，格式 `dd-mm-yyyy`
- `balance_verified` 为 `Boolean` 类型（`true` / `false`）

### 逻辑验证

**信用卡：**
```
期末余额 = 期初余额 + 总消费 - 总还款 + 总利息
```

**银行流水：**
```
期末余额 = 期初余额 + 总贷方 - 总借方
```

---

## 🚫 常见错误

### 错误1：status字段错误

❌ **错误示例：**
```json
{
  "status": "failed"
}
```

✅ **正确示例：**
```json
{
  "status": "success"
}
```

### 错误2：日期格式错误

❌ **错误示例：**
```json
{
  "date": "2024-11-15"
}
```

✅ **正确示例：**
```json
{
  "date": "15-11-2024"
}
```

### 错误3：金额格式错误

❌ **错误示例：**
```json
{
  "amount": "RM 1,500.00"
}
```

✅ **正确示例：**
```json
{
  "amount": 1500.00
}
```

---

## 📞 技术支持

如对JSON格式有疑问，请联系：
- **项目：** INFINITE GZ
- **Email：** [Your Email]

---

**版本 1.0.0 | 2024-11-15**
