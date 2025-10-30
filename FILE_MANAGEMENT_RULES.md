# 文件管理规则 (File Management Rules)

## 核心原则

**所有文件必须统一存放在 `static/uploads/` 目录下，按客户和类型分类。**

绝对禁止：
- ❌ `attached_assets/` - 禁止使用
- ❌ `uploads/` (缺少static前缀) - 禁止使用
- ❌ 任何其他临时目录 - 禁止使用

---

## 标准目录结构

```
static/uploads/customers/{customer_code}/
├── credit_cards/              # 信用卡相关文件
│   ├── {bank_name}/
│   │   └── {YYYY-MM}/
│   │       └── {bank_name}_{last4}_{YYYY-MM-DD}.pdf
│
├── savings/                   # 储蓄/来往账户月结单（统一存放处）
│   ├── {bank_name}/
│   │   └── {YYYY-MM}/
│   │       └── {bank_name}_{last4}_{YYYY-MM-DD}.pdf
│
├── receipts/                  # 收据
│   └── {YYYY-MM}/
│       └── receipt_{timestamp}.{jpg|png|pdf}
│
├── invoices/                  # 发票
│   └── {YYYY-MM}/
│       └── invoice_{supplier}_{timestamp}.pdf
│
├── loans/                     # 贷款文件
│   └── CTOS_{customer_code}_{YYYY-MM-DD}.pdf
│
├── reports/                   # 生成的报告
│   └── {report_type}_{YYYY-MM-DD}.pdf
│
└── documents/                 # 其他文档
    └── {document_type}_{timestamp}.pdf
```

---

## 详细规则

### 1. 储蓄/来往账户月结单 (Savings/Current Account Statements)

**路径格式：**
```
static/uploads/customers/{customer_code}/savings/{bank_name}/{YYYY-MM}/{bank_name}_{last4}_{YYYY-MM-DD}.pdf
```

**示例：**
```
static/uploads/customers/Be_rich_CCC/savings/Public_Bank/2025-03/Public_Bank_9009_2025-03-25.pdf
static/uploads/customers/Be_rich_YCW/savings/Hong_Leong_Bank/2025-09/Hong_Leong_Bank_4645_2025-09-05.pdf
static/uploads/customers/Be_rich_TZL/savings/GX_Bank/2025-08/GX_Bank_8373_2025-08-31.pdf
```

**命名规范：**
- `{bank_name}`: 银行名称，空格替换为下划线
  - Alliance Bank → `Alliance_Bank`
  - Hong Leong Bank → `Hong_Leong_Bank`
  - GX Bank → `GX_Bank`
  - Public Bank → `Public_Bank`
  - Maybank → `Maybank`
  - OCBC → `OCBC`
  - UOB → `UOB`
  
- `{last4}`: 账户后4位数字
- `{YYYY-MM-DD}`: 月结单日期（statement_date）

---

### 2. 信用卡月结单 (Credit Card Statements)

**路径格式：**
```
static/uploads/customers/{customer_code}/credit_cards/{bank_name}/{YYYY-MM}/{bank_name}_{last4}_{YYYY-MM-DD}.pdf
```

**示例：**
```
static/uploads/customers/Be_rich_YCW/credit_cards/Alliance_Bank/2025-06/Alliance_Bank_1234_2025-06-08.pdf
```

---

### 3. 收据 (Receipts)

**路径格式：**
```
static/uploads/customers/{customer_code}/receipts/{YYYY-MM}/receipt_{timestamp}.{jpg|png|pdf}
```

**示例：**
```
static/uploads/customers/Be_rich_YCW/receipts/2025-10/receipt_1730300000000.jpg
```

---

### 4. 发票 (Invoices)

**路径格式：**
```
static/uploads/customers/{customer_code}/invoices/{YYYY-MM}/invoice_{supplier}_{timestamp}.pdf
```

**示例：**
```
static/uploads/customers/Be_rich_CCC/invoices/2025-10/invoice_CHEOK_JUN_YOON_1730300000000.pdf
```

---

## 迁移策略

### 第一步：检查现有文件分布
```sql
SELECT DISTINCT 
    SUBSTRING(file_path, 1, 20) as path_prefix,
    COUNT(*) as count
FROM savings_statements 
WHERE file_path IS NOT NULL
GROUP BY path_prefix;
```

### 第二步：批量迁移
1. 从 `attached_assets/` → `static/uploads/customers/{customer_code}/savings/{bank}/{month}/`
2. 从 `uploads/` → `static/uploads/` (添加static前缀)
3. 规范化所有文件名

### 第三步：更新数据库
```sql
UPDATE savings_statements 
SET file_path = {new_standardized_path}
WHERE id = {statement_id};
```

### 第四步：验证
- 检查所有file_path都以 `static/uploads/customers/` 开头
- 检查所有文件实际存在
- 删除 `attached_assets/` 目录

---

## 自动化规则

### 上传新文件时必须：

1. **验证客户代码**
   ```python
   if not customer_code:
       raise ValueError("必须指定客户代码")
   ```

2. **构建标准路径**
   ```python
   base_dir = f"static/uploads/customers/{customer_code}"
   file_type_dir = f"{base_dir}/{file_type}"  # savings, credit_cards, etc.
   month_dir = f"{file_type_dir}/{bank_name}/{year}-{month:02d}"
   ```

3. **创建目录**
   ```python
   os.makedirs(month_dir, exist_ok=True)
   ```

4. **标准化文件名**
   ```python
   filename = f"{bank_name}_{last4}_{statement_date}.pdf"
   final_path = f"{month_dir}/{filename}"
   ```

5. **保存到数据库**
   ```python
   statement.file_path = final_path
   ```

---

## 禁止事项

❌ **绝对禁止：**
1. 使用 `attached_assets/` 目录
2. 使用 `uploads/` (缺少static前缀)
3. 文件名包含中文字符
4. 文件名包含空格
5. 随意命名文件
6. 跨客户混放文件
7. 不按月份分类

---

## 验证清单

每次文件操作后必须检查：

- [ ] 文件路径以 `static/uploads/customers/` 开头？
- [ ] 包含客户代码？
- [ ] 包含文件类型 (savings/credit_cards/receipts等)？
- [ ] 包含银行名称？
- [ ] 包含年月 (YYYY-MM)？
- [ ] 文件名符合规范？
- [ ] 文件实际存在？
- [ ] 数据库中file_path已更新？

---

## 违规处理

**如果发现文件存放在错误位置：**

1. 立即停止导入
2. 报告错误位置
3. 移动到正确位置
4. 更新数据库
5. 验证修复

**绝不允许："先随便放，以后再整理"**
