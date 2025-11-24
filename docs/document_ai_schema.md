# Document AI Custom Extractor Schema

## 概述

本文档定义了用于马来西亚银行信用卡账单的Google Document AI自定义提取器Schema配置。

---

## Schema 结构

### 1. 基本信息字段

| 字段名 | 数据类型 | 描述 | 示例 |
|--------|---------|------|------|
| `statement_date` | `datetime` | 账单日期 | `2025-05-28` |
| `due_date` | `datetime` | 到期日 | `2025-06-17` |
| `card_number` | `string` | 信用卡号码（后4位） | `6354` |
| `cardholder_name` | `string` | 持卡人姓名 | `CHEOK JUN YOON` |
| `bank_name` | `string` | 银行名称 | `AmBank` |

### 2. 金额字段

| 字段名 | 数据类型 | 描述 | 示例 |
|--------|---------|------|------|
| `total_amount` | `money` | 总金额 | `5,234.56` |
| `minimum_payment` | `money` | 最低还款额 | `261.73` |
| `previous_balance` | `money` | 上期余额 | `4,123.45` |
| `new_charges` | `money` | 本期新增消费 | `1,234.56` |
| `payments_credits` | `money` | 本期还款/贷记 | `123.45` |

### 3. 交易明细表格

**字段名**: `transactions`  
**数据类型**: `table`  
**描述**: 交易记录明细表

#### 表格列定义

| 列名 | 数据类型 | 描述 | 示例 |
|------|---------|------|------|
| `transaction_date` | `date` | 交易日期 | `15 MAY` |
| `description` | `string` | 交易描述 | `MCDONALD'S-KOTA WARISAN SEPANG MY` |
| `amount` | `money` | 金额 | `36.60` |
| `category` | `string` | 分类 | `Owners` / `GZ` / `Suppliers` |

---

## Schema JSON 格式

```json
{
  "displayName": "Malaysian Credit Card Statement Extractor",
  "description": "提取马来西亚银行信用卡账单关键字段",
  "entityTypes": [
    {
      "name": "statement_date",
      "displayName": "账单日期",
      "baseTypes": ["datetime"]
    },
    {
      "name": "due_date",
      "displayName": "到期日",
      "baseTypes": ["datetime"]
    },
    {
      "name": "card_number",
      "displayName": "信用卡号码",
      "baseTypes": ["string"]
    },
    {
      "name": "cardholder_name",
      "displayName": "持卡人姓名",
      "baseTypes": ["string"]
    },
    {
      "name": "bank_name",
      "displayName": "银行名称",
      "baseTypes": ["string"]
    },
    {
      "name": "total_amount",
      "displayName": "总金额",
      "baseTypes": ["money"]
    },
    {
      "name": "minimum_payment",
      "displayName": "最低还款额",
      "baseTypes": ["money"]
    },
    {
      "name": "previous_balance",
      "displayName": "上期余额",
      "baseTypes": ["money"]
    },
    {
      "name": "new_charges",
      "displayName": "本期新增消费",
      "baseTypes": ["money"]
    },
    {
      "name": "payments_credits",
      "displayName": "本期还款/贷记",
      "baseTypes": ["money"]
    },
    {
      "name": "transactions",
      "displayName": "交易记录",
      "baseTypes": ["table"],
      "properties": [
        {
          "name": "transaction_date",
          "displayName": "交易日期",
          "baseTypes": ["date"]
        },
        {
          "name": "description",
          "displayName": "交易描述",
          "baseTypes": ["string"]
        },
        {
          "name": "amount",
          "displayName": "金额",
          "baseTypes": ["money"]
        },
        {
          "name": "category",
          "displayName": "分类",
          "baseTypes": ["string"],
          "enumValues": ["Owners", "GZ", "Suppliers"]
        }
      ]
    }
  ]
}
```

---

## 字段提取规则

### 1. 基本信息字段提取规则

#### statement_date (账单日期)
- **搜索关键词**: `Statement Date`, `Tarikh Penyata`, `STATEMENT DATE`
- **格式**: `DD MMM YY` 或 `DD MMM YYYY`
- **示例**: `28 MAY 25`, `28 MAY 2025`

#### due_date (到期日)
- **搜索关键词**: `Payment Due Date`, `Tarikh Matang Bayaran`, `DUE DATE`
- **格式**: `DD MMM YY` 或 `DD MMM YYYY`
- **示例**: `17 JUN 25`, `17 JUN 2025`

#### card_number (信用卡号码)
- **搜索关键词**: 16位卡号（空格分隔）
- **格式**: `XXXX XXXX XXXX XXXX`
- **提取**: 后4位
- **示例**: `4031 4899 9530 6354` → 提取 `6354`

#### cardholder_name (持卡人姓名)
- **搜索关键词**: 收件人姓名（通常在地址上方）
- **格式**: 大写英文字母
- **示例**: `CHEOK JUN YOON`

#### bank_name (银行名称)
- **搜索关键词**: Logo区域、抬头位置
- **支持的银行**: 
  - `AmBank` / `AmBank Islamic`
  - `HSBC`
  - `Standard Chartered`
  - `UOB`
  - `Hong Leong Bank`
  - `OCBC`

### 2. 金额字段提取规则

#### total_amount (总金额)
- **搜索关键词**: `Total Amount`, `Total Current Balance`, `Jumlah Keseluruhan`
- **格式**: `RM X,XXX.XX`
- **示例**: `RM 5,234.56`

#### minimum_payment (最低还款额)
- **搜索关键词**: `Minimum Payment`, `Bayaran Minimum`, `MIN PAYMENT`
- **格式**: `RM X,XXX.XX`
- **示例**: `RM 261.73`

#### previous_balance (上期余额)
- **搜索关键词**: `Previous Balance`, `Baki Terdahulu`, `PREVIOUS BALANCE`
- **格式**: `RM X,XXX.XX`
- **示例**: `RM 4,123.45`

#### new_charges (本期新增消费)
- **搜索关键词**: `New Charges`, `Purchases`, `Caj Baharu`
- **格式**: `RM X,XXX.XX`
- **示例**: `RM 1,234.56`

#### payments_credits (本期还款/贷记)
- **搜索关键词**: `Payments`, `Credits`, `Bayaran`, `CR`
- **格式**: `RM X,XXX.XX CR`
- **示例**: `RM 123.45 CR`

### 3. 交易明细表格提取规则

#### transactions (交易记录表)
- **位置**: 通常在 `PREVIOUS BALANCE` 和 `Total Current Balance` 之间
- **表格结构**: 多行记录

#### 列提取规则：

**transaction_date (交易日期)**
- **格式**: `DD MMM`
- **示例**: `15 MAY`, `28 JUN`

**description (交易描述)**
- **格式**: 商家名称 + 地点
- **示例**: `MCDONALD'S-KOTA WARISAN SEPANG MY`

**amount (金额)**
- **格式**: `X,XXX.XX` 或 `X,XXX.XX CR`
- **示例**: `36.60`, `984.79 CR`

**category (分类)**
- **自动分类规则**:
  - `Owners`: 默认类别
  - `GZ`: 包含关键词 `on behalf`, `for client`, `client request`
  - `Suppliers`: 匹配供应商列表（7SL, DINAS, RAUB SYC HAINAN等）

---

## 训练样本要求

### 最少样本数量
- **推荐**: 50-100个标注样本
- **最少**: 20个标注样本

### 样本多样性
需要包含以下银行的样本：
- ✅ AmBank (含AmBank Islamic)
- ✅ HSBC
- ✅ Standard Chartered
- ✅ UOB
- ✅ Hong Leong Bank
- ✅ OCBC

### 标注质量要求
- ✅ 所有字段准确标注
- ✅ 交易表格完整标注
- ✅ 金额包含货币符号
- ✅ 日期格式统一

---

## 使用指南

### 1. 创建Custom Processor

```bash
# 使用自动化脚本创建
python3 scripts/create_document_ai_schema.py
```

### 2. 上传训练样本

1. 在Google Cloud Console访问Document AI
2. 选择创建的Processor
3. 上传标注好的PDF样本
4. 开始训练

### 3. 测试验证

```python
from services.google_document_ai_service import GoogleDocumentAIService

service = GoogleDocumentAIService()
result = service.parse_pdf('test_statement.pdf')
fields = service.extract_bank_statement_fields(result)

print(f"账单日期: {fields['statement_date']}")
print(f"交易数量: {len(fields['transactions'])}")
```

---

## 准确度目标

| 字段类型 | 目标准确度 |
|---------|-----------|
| 基本信息字段 | ≥ 98% |
| 金额字段 | ≥ 99% |
| 交易表格 | ≥ 95% |
| 总体准确度 | ≥ 97% |

---

## 常见问题

### Q: 为什么交易表格提取不准确？
A: 需要更多样本训练，确保标注了完整的表格结构。

### Q: 如何处理多语言账单？
A: Schema支持英文和马来文关键词，训练时包含两种语言样本。

### Q: 如何更新Schema？
A: 运行 `python3 scripts/update_document_ai_schema.py` 更新配置。

---

## 更新日志

- **2025-11-17**: 初始版本创建
  - 定义15个核心字段
  - 支持7家马来西亚银行
  - 包含交易分类逻辑
