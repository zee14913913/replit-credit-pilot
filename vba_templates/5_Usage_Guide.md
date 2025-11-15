# INFINITE GZ - VBA模板使用指南

## 📦 文件清单

本套件包含以下VBA模板：

1. **1_CreditCardParser.vba** - 信用卡账单解析器
2. **2_BankStatementParser.vba** - 银行流水解析器
3. **3_PDFtoExcel_Guide.vba** - PDF转Excel指南
4. **4_DataValidator.vba** - 数据验证器
5. **5_Usage_Guide.md** - 使用说明（本文件）

---

## 🚀 快速开始

### 步骤1：导入VBA模块

1. 打开Excel文件
2. 按 `Alt + F11` 打开VBA编辑器
3. 在左侧项目窗口，右键点击 "VBAProject" → 插入 → 模块
4. 复制粘贴对应的VBA代码到新模块中

**建议导入顺序：**
- 首先导入 `1_CreditCardParser.vba`
- 然后导入 `2_BankStatementParser.vba`
- 最后导入 `4_DataValidator.vba`（可选）

### 步骤2：准备Excel文件

**如果是Excel/CSV账单：**
- 直接打开文件即可

**如果是PDF账单：**
- 使用以下任一方法转换为Excel：
  - Adobe Acrobat Pro导出
  - Tabula (https://tabula.technology/)
  - Python工具（我们提供）

### 步骤3：运行解析器

**信用卡账单：**
```vba
' 按 Alt + F8，选择 ParseCreditCardStatement，点击运行
```

**银行流水：**
```vba
' 按 Alt + F8，选择 ParseBankStatement，点击运行
```

**验证数据质量（可选）：**
```vba
' 按 Alt + F8，选择 GenerateValidationReport，点击运行
```

### 步骤4：获取JSON文件

解析完成后，会在Excel文件同一文件夹生成JSON文件：

- 信用卡：`credit_card_20241115_143052.json`
- 银行流水：`bank_statement_20241115_143052.json`

---

## 📋 JSON格式示例

### 信用卡账单JSON

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

### 银行流水JSON

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
    "total_debits": 0.00,
    "total_credits": 0.00
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
    }
  ],
  "summary": {
    "total_transactions": 40,
    "category_breakdown": {},
    "balance_verified": true,
    "balance_difference": 0.00
  }
}
```

---

## 🌐 上传到Replit系统

### 方法A：手动上传（推荐）

1. 打开Replit网站
2. 登录您的账户
3. 访问上传API端点（详见下方）
4. 选择生成的JSON文件上传

### 方法B：批量上传

如果您有多个JSON文件：

1. 将所有JSON文件放在同一文件夹
2. 使用批量上传API（支持一次上传多个文件）

---

## 🔧 API端点说明

上传到Replit时使用以下端点：

### 单个文件上传

**信用卡账单：**
```
POST https://your-replit-url.repl.co/api/upload/vba-json
Content-Type: multipart/form-data
Body: file=credit_card_20241115_143052.json
```

**银行流水：**
```
POST https://your-replit-url.repl.co/api/upload/vba-json
Content-Type: multipart/form-data
Body: file=bank_statement_20241115_143052.json
```

### 批量上传

```
POST https://your-replit-url.repl.co/api/upload/vba-batch
Content-Type: multipart/form-data
Body: files[]=file1.json&files[]=file2.json
```

---

## ⚠️ 常见问题

### Q1: VBA代码运行出错怎么办？

**A1:** 检查以下几点：
- 确保Excel宏已启用（文件 → 选项 → 信任中心 → 宏设置）
- 检查账单格式是否正确
- 运行 `GenerateValidationReport` 查看详细错误

### Q2: JSON文件没有生成？

**A2:** 可能的原因：
- 文件夹没有写入权限
- 账单格式无法识别
- VBA代码有错误（查看即时窗口的错误信息）

### Q3: PDF转Excel后格式混乱？

**A3:** 解决方法：
- 使用Adobe Acrobat Pro（准确率最高）
- 在Tabula中手动调整表格区域
- 使用我们提供的Python工具

### Q4: 银行格式不支持？

**A4:** 当前支持的银行：
- Public Bank
- Maybank
- CIMB
- RHB
- Hong Leong Bank

如需支持其他银行，请联系我们。

### Q5: 余额验证失败？

**A5:** 可能的原因：
- PDF转Excel时数据丢失
- 账单中有未识别的费用
- 交易明细区域识别错误

**解决方法：**
- 人工检查Excel数据是否完整
- 调整VBA代码中的行号范围
- 联系我们协助调整

---

## 📞 技术支持

如遇到任何问题，请联系：

- **项目负责人：** INFINITE GZ 技术团队
- **Email：** [您的Email]
- **电话：** [您的电话]

---

## 📌 版本历史

**v1.0.0** (2024-11-15)
- 初始版本
- 支持5家银行
- 30+智能分类
- 余额自动验证
- JSON标准格式导出

---

## ✅ 检查清单

在上传JSON文件之前，请确认：

- [ ] VBA代码已正确导入
- [ ] Excel数据格式正确
- [ ] 运行了数据验证（可选）
- [ ] JSON文件已生成
- [ ] 余额验证通过（如适用）
- [ ] 准备好上传到Replit

---

**祝您使用愉快！** 🚀
