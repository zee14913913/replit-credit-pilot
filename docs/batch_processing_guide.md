# PDF批量处理系统使用指南

## 系统概述

本系统使用Google Document AI自动提取Cheok Jun Yoon的42份信用卡账单PDF，并按照业务规则进行分类、计算和结算。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      PDF批量处理系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │   PDF文件    │  →   │ Document AI  │  →   │ 数据提取  │  │
│  │   (42份)     │      │   提取引擎   │      │          │  │
│  └──────────────┘      └──────────────┘      └──────────┘  │
│                                                      ↓       │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │  Excel报告   │  ←   │  余额计算    │  ←   │ 交易分类  │  │
│  │   (结算)     │      │   引擎       │      │  引擎    │  │
│  └──────────────┘      └──────────────┘      └──────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心功能

### 1. 数据提取 (Document AI)

从PDF中提取15个核心字段：

**基本信息 (5个)**
- statement_date - 账单日期
- due_date - 到期日
- card_number - 信用卡号码
- cardholder_name - 持卡人姓名
- bank_name - 银行名称

**金额字段 (5个)**
- total_amount - 总金额
- minimum_payment - 最低还款额
- previous_balance - 上期余额
- new_charges - 本期新增消费
- payments_credits - 本期还款/贷记

**交易表格 (1个)**
- transactions - 交易记录（日期、描述、金额、分类）

### 2. 交易分类

按照业务规则自动分类：

#### EXPENSES (支出)

**Owners Expenses** (业主消费)
- 默认分类
- Payment备注为空
- Payment备注包含客户姓名

**GZ Expenses** (GZ代付)
- Payment备注包含关键词：
  - "on behalf"
  - "behalf of"
  - "for client"
  - "client request"
  - "payment for"

**Suppliers** (供应商)
- 匹配7个INFINITE供应商：
  - 7SL
  - DINAS
  - RAUB SYC HAINAN
  - AI SMART TECH
  - HUAWEI
  - PASAR RAYA
  - PUCHONG HERBS
- 自动计算1%手续费

#### PAYMENTS (还款)

**Owners Payment** (业主还款)
- 默认分类

**GZ Payment** (GZ还款)
- Payment备注包含GZ关键词

### 3. 余额计算

```
Outstanding Balance = Previous Balance + Total Expenses - Total Payments

其中:
Total Expenses = Owners Expenses + GZ Expenses + Suppliers + Supplier Fee
Total Payments = Owners Payment + GZ Payment
```

**分项余额**
- Owners Balance = Owners Expenses - Owners Payment
- GZ Balance = GZ Expenses - GZ Payment
- Suppliers Balance = Suppliers + Supplier Fee

---

## 文件结构

```
.
├── config/
│   ├── settings.json                  # 系统配置
│   ├── business_rules.json            # 业务规则
│   └── document_ai_schema.json        # Document AI Schema
│
├── scripts/
│   ├── process_cheok_statements.py    # 主处理脚本
│   ├── calculate_balances.py          # 账目计算逻辑
│   └── test_single_pdf.py             # 单文件测试脚本
│
├── services/
│   └── google_document_ai_service.py  # Document AI服务
│
├── static/uploads/customers/Be_rich_CJY/credit_cards/
│   ├── AmBank/                        # AmBank账单
│   ├── HSBC/                          # HSBC账单
│   ├── UOB/                           # UOB账单
│   └── ...                            # 其他银行
│
└── reports/Be_rich_CJY/
    ├── settlement_report_YYYYMMDD.xlsx    # Excel结算报告
    └── processing_results_YYYYMMDD.json   # JSON详细结果
```

---

## 使用步骤

### 第1步：环境准备

确保已设置环境变量：

```bash
GOOGLE_PROJECT_ID=famous-tree-468019-b9
DOCUMENT_AI_PROCESSOR_ID=您的处理器ID
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### 第2步：安装依赖

```bash
pip install google-cloud-documentai openpyxl pandas
```

### 第3步：测试单个PDF

```bash
python3 scripts/test_single_pdf.py
```

测试单个PDF文件，验证系统正常工作。

### 第4步：批量处理

```bash
python3 scripts/process_cheok_statements.py
```

处理所有42份PDF文件，生成完整报告。

---

## 输出报告

### Excel报告 (settlement_report_YYYYMMDD.xlsx)

包含4个工作表：

**1. 账单汇总**
- 文件名
- 银行
- 卡号
- 账单日期
- 到期日
- 上期余额
- 本期消费
- 本期还款
- Outstanding Balance
- 交易笔数

**2. 交易明细**
- 文件名
- 银行
- 卡号
- 分类 (Owners/GZ/Suppliers)
- 交易日期
- 交易描述
- 金额
- 供应商手续费
- 是否贷记

**3. 分类汇总**
- 文件名
- 银行
- 卡号
- 分类 (owners_expenses/gz_expenses/suppliers/owners_payment/gz_payment)
- 金额

**4. 错误记录**
- 文件名
- 错误信息

### JSON报告 (processing_results_YYYYMMDD.json)

包含完整的处理结果：
- 客户信息
- 处理时间
- 成功/失败统计
- 详细的提取数据
- 分类结果
- 计算结果

---

## 业务规则配置

编辑 `config/business_rules.json` 修改：

### 修改GZ关键词

```json
{
  "classification_rules": {
    "categories": {
      "gz": {
        "keywords": [
          "on behalf",
          "新增关键词"
        ]
      }
    }
  }
}
```

### 修改供应商列表

```json
{
  "classification_rules": {
    "categories": {
      "suppliers": {
        "supplier_list": [
          "7SL",
          "新供应商"
        ]
      }
    }
  }
}
```

### 修改供应商手续费

```json
{
  "calculation_rules": {
    "supplier_fee": {
      "enabled": true,
      "rate": 0.01    // 1% = 0.01, 2% = 0.02
    }
  }
}
```

---

## 处理示例

### 输入：PDF账单

```
AmBank信用卡账单
账单日期: 28 MAY 2025
卡号: 4031 4899 9530 6354
上期余额: RM 5,000.00

交易记录:
15 MAY  MCDONALD'S-KOTA WARISAN        36.60
16 MAY  7SL TRADING SDN BHD         1,000.00
17 MAY  PAYMENT RECEIVED           2,000.00 CR
```

### 输出：分类结果

```
Owners Expenses:  RM    36.60
Suppliers:        RM 1,000.00
Supplier Fee:     RM    10.00
Owners Payment:   RM 2,000.00

Outstanding Balance: RM 4,046.60
```

---

## 常见问题

### Q1: 如果Document AI提取失败怎么办？

A: 系统会记录错误并继续处理其他文件。检查 `错误记录` 工作表查看失败原因。

### Q2: 如何验证计算准确性？

A: 对比Excel报告中的 `Outstanding Balance` 与银行账单的 `Total Amount`。

### Q3: 如何处理新的供应商？

A: 编辑 `config/business_rules.json`，在 `supplier_list` 中添加供应商名称。

### Q4: 并发处理数量如何调整？

A: 修改 `process_cheok_statements.py` 中的 `max_workers` 参数（默认3）。

### Q5: 如何重新处理某个PDF？

A: 使用 `test_single_pdf.py` 脚本测试单个文件。

---

## 性能指标

- **处理速度**: 约10-15秒/PDF（Document AI API延迟）
- **并发数**: 3个（可调整）
- **准确度目标**: ≥95%
- **支持银行**: 7家马来西亚银行

---

## 技术支持

如遇问题，请检查：

1. **环境变量**: 确保Google Cloud凭证正确
2. **API配额**: Document AI API配额是否充足
3. **PDF格式**: 确保PDF清晰可读
4. **日志文件**: 查看 `logs/system.log`

---

## 更新日志

- **2025-11-17**: 初始版本
  - 支持42份PDF批量处理
  - 实现5类交易分类
  - 集成Document AI提取
  - 生成Excel/JSON双报告
