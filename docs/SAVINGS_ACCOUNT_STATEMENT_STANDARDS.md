# 储蓄/来往户口月结单系统设置标准文档
## SAVINGS & CURRENT ACCOUNT STATEMENT PROCESSING STANDARDS

**创建日期**: 2025-10-29  
**版本**: 1.0  
**准确性要求**: 100% - 零容差 (Zero Tolerance for Errors)

---

## 📋 目录 (TABLE OF CONTENTS)

1. [系统概述](#系统概述)
2. [数据库架构](#数据库架构)
3. [支持的银行列表](#支持的银行列表)
4. [文件存储标准](#文件存储标准)
5. [PDF解析规则](#pdf解析规则)
6. [核心算法: Balance-Change Algorithm](#核心算法-balance-change-algorithm)
7. [交易分类规则](#交易分类规则)
8. [双重验证机制](#双重验证机制)
9. [上传操作流程](#上传操作流程)
10. [数据展示标准](#数据展示标准)

---

## 系统概述

### 核心目标
**100% 准确记录所有储蓄/来往户口的转账交易，不遗漏任何一笔！**

### 核心原则
1. **1:1 PDF复制** - 月结单上的每一笔交易必须100%准确记录到系统
2. **余额验证** - 每笔交易的余额必须与PDF一致
3. **零容差** - 不接受任何数据误差或丢失
4. **双重验证** - 人工验证 + 系统验证

---

## 数据库架构

### 1. savings_accounts (储蓄账户主表)
```sql
CREATE TABLE savings_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,                    -- 关联客户
    bank_name TEXT NOT NULL,                -- 银行名称
    account_number_last4 TEXT NOT NULL,     -- 账户号码后4位
    account_type TEXT DEFAULT 'Savings',    -- 账户类型
    account_holder_name TEXT,               -- 账户持有人姓名
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
```

**关键字段说明**:
- `account_number_last4`: 账户号码后4位（用于识别账户）
- `account_type`: 账户类型（Savings/Current/RM ACE等）

### 2. savings_statements (账单记录表)
```sql
CREATE TABLE savings_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    savings_account_id INTEGER NOT NULL,    -- 关联储蓄账户
    statement_date TEXT NOT NULL,           -- 账单日期 (YYYY-MM-DD)
    file_path TEXT,                         -- PDF文件路径
    file_type TEXT,                         -- 文件类型 (pdf/excel)
    total_transactions INTEGER DEFAULT 0,   -- 交易总数
    is_processed INTEGER DEFAULT 0,         -- 是否已处理
    verification_status TEXT DEFAULT 'pending',  -- 验证状态
    verified_by TEXT,                       -- 验证人
    verified_at TIMESTAMP,                  -- 验证时间
    discrepancy_notes TEXT,                 -- 差异备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (savings_account_id) REFERENCES savings_accounts(id)
)
```

**验证状态 (verification_status)**:
- `pending`: 待验证
- `verified`: 已验证通过
- `discrepancy`: 发现差异（需要人工复核）

### 3. savings_transactions (交易记录表)
```sql
CREATE TABLE savings_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    savings_statement_id INTEGER NOT NULL,  -- 关联账单
    transaction_date TEXT NOT NULL,         -- 交易日期
    description TEXT NOT NULL,              -- 交易描述
    amount REAL NOT NULL,                   -- 交易金额（绝对值）
    transaction_type TEXT,                  -- 交易类型 (credit/debit)
    balance REAL,                           -- 交易后余额
    reference_number TEXT,                  -- 参考号码
    customer_name_tag TEXT,                 -- 客户名称标签（用于搜索）
    is_prepayment INTEGER DEFAULT 0,        -- 是否为预付款
    notes TEXT,                             -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (savings_statement_id) REFERENCES savings_statements(id)
)
```

**交易类型 (transaction_type)**:
- `credit`: 存入 (Money In / Deposit / CR)
- `debit`: 取出 (Money Out / Withdrawal / DR)

**关键字段说明**:
- `amount`: 存储绝对值（正数）
- `balance`: 交易后的账户余额（必须与PDF一致）
- `customer_name_tag`: 用于搜索客户付款记录

---

## 支持的银行列表

### 当前支持的8家银行（已有专用解析器）

| 序号 | 银行名称 | 英文名称 | 解析器函数 | 状态 |
|------|---------|---------|-----------|------|
| 1 | Maybank | Malayan Banking Berhad | `parse_maybank_savings` | ✅ 已测试 |
| 2 | GX Bank | GX Bank | `parse_gxbank_savings` | ✅ 已测试 |
| 3 | Hong Leong Bank | HLB | `parse_hlb_savings` | ✅ 已测试 |
| 4 | CIMB | CIMB Bank Berhad | `parse_cimb_savings` | ✅ 已测试 |
| 5 | UOB | United Overseas Bank | `parse_uob_savings` | ✅ 已测试 |
| 6 | OCBC | OCBC Bank | `parse_ocbc_savings` | ✅ 已测试 |
| 7 | Public Bank | Public Bank Berhad | `parse_publicbank_savings` | ✅ 已测试 |
| 8 | Alliance Bank | Alliance Bank Malaysia | `parse_alliance_savings` | ✅ 已测试 |

### 通用解析器 (Fallback)
- **函数**: `parse_generic_savings`
- **用途**: 处理其他银行或格式标准的月结单
- **特点**: 基于表格结构自动识别列，灵活性高

---

## 文件存储标准

### 统一命名规则
```
{BankName}_{AccountLast4}_{YYYY-MM-DD}.pdf
```

**示例**:
- `Public_Bank_0727_2025-10-31.pdf` (Public Bank, 账户 ****0727, 2025年10月)
- `Gx_Bank_8388_2025-09-30.pdf` (GX Bank, 账户 ****8388, 2025年9月)

### 文件夹层级结构
```
static/uploads/customers/{customer_code}/
└── savings/
    └── {bank_name}/
        └── {YYYY-MM}/
            └── {BankName}_{AccountLast4}_{YYYY-MM-DD}.pdf
```

**完整路径示例**:
```
static/uploads/customers/Be_rich_CCC/savings/Public_Bank/2025-10/Public_Bank_0727_2025-10-31.pdf
```

### 客户代码格式
- **格式**: `Be_rich_{INITIALS}`
- **示例**:
  - `Be_rich_CCC` - CHANG CHOON CHOW
  - `Be_rich_CJY` - CHEOK JUN YOON
  - `Be_rich_TZL` - TAN ZEE LIANG

---

## PDF解析规则

### 自动银行检测
系统会按以下顺序检测银行：

1. **文件名检测**
   ```python
   'maybank' in filename → Maybank
   'gxbank' or 'gx_bank' → GX Bank
   'publicbank' or 'public bank' → Public Bank
   ```

2. **PDF内容检测**
   ```python
   'MAYBANK' in PDF text → Maybank
   'GX BANK' in PDF text → GX Bank
   'PUBLIC BANK' in PDF text → Public Bank
   ```

### 通用字段提取规则

#### 1. 账单日期 (Statement Date)
- **优先级1**: PDF中的"Statement Date"字段
- **优先级2**: 文件名中的日期 `_{YYYY-MM-DD}.pdf`
- **优先级3**: 最后一笔交易的日期

#### 2. 账户号码 (Account Number)
- **提取**: 账户号码的后4位
- **Regex**: `(?:ACCOUNT|A/C).*?(\d{4})`
- **示例**: "Account No: 1234567890" → "7890"

#### 3. 账户类型 (Account Type)
- **提取**: "Savings Account", "Current Account", "RM ACE Account"
- **默认**: "Savings"

#### 4. 期初余额 (Opening Balance)
- **关键词**: "Opening Balance", "Previous Balance", "B/F Balance"
- **格式**: 支持 `RM 1,234.56` / `1,234.56 CR` / `(1,234.56)`

#### 5. 期末余额 (Closing Balance)
- **关键词**: "Closing Balance", "Ending Balance", "C/F Balance"
- **验证**: 必须等于最后一笔交易的余额

---

## 核心算法: Balance-Change Algorithm

### 算法目的
**根据余额变化确定交易类型（credit/debit）和准确金额，确保100%准确性！**

### 算法逻辑

```python
def apply_balance_change_algorithm(transactions, opening_balance):
    """
    核心算法：根据余额变化确定交易类型
    
    输入:
        transactions: 初步提取的交易列表（可能有不准确的金额）
        opening_balance: 期初余额
    
    输出:
        准确的交易列表（类型、金额、余额全部正确）
    """
    prev_balance = opening_balance
    final_transactions = []
    
    for txn in transactions:
        current_balance = txn['balance']  # PDF中的余额（100%准确）
        
        # 计算余额变化
        balance_change = current_balance - prev_balance
        
        if balance_change > 0:
            # 余额增加 = 存入 (Credit)
            txn['type'] = 'credit'
            txn['amount'] = abs(balance_change)
        
        elif balance_change < 0:
            # 余额减少 = 取出 (Debit)
            txn['type'] = 'debit'
            txn['amount'] = abs(balance_change)
        
        else:
            # 余额无变化（跳过此交易）
            continue
        
        prev_balance = current_balance
        final_transactions.append(txn)
    
    return final_transactions
```

### 算法优势
1. **不依赖PDF中的金额标记** - 即使PDF格式混乱，也能确保准确
2. **余额为唯一真理来源** - 余额是银行系统生成的，100%可靠
3. **自动纠正解析错误** - 如果初步提取的金额有误，算法会自动纠正

### 示例

**PDF原始数据**:
```
Date        Description              Amount      Balance
01/10/2025  Opening Balance          -           RM 1,000.00
05/10/2025  Salary Deposit           RM 5,000    RM 6,000.00
10/10/2025  ATM Withdrawal          (RM 200)     RM 5,800.00
15/10/2025  Online Transfer         (RM 1,500)   RM 4,300.00
```

**算法处理**:
```
1. Opening Balance = 1,000.00
2. Transaction #1:
   - Balance change = 6,000 - 1,000 = +5,000
   - Type = credit (存入)
   - Amount = 5,000.00 ✅
   
3. Transaction #2:
   - Balance change = 5,800 - 6,000 = -200
   - Type = debit (取出)
   - Amount = 200.00 ✅
   
4. Transaction #3:
   - Balance change = 4,300 - 5,800 = -1,500
   - Type = debit (取出)
   - Amount = 1,500.00 ✅
```

### 无期初余额的处理策略
如果PDF无法提取Opening Balance：
1. **策略1**: 假设Opening Balance = 0
2. **策略2**: 从前两笔交易的余额差值反推
3. **策略3**: 要求用户手动输入Opening Balance

**当前实现**: 使用策略1（假设Opening Balance = 0）

---

## 交易分类规则

### 1. 金额格式清理 (clean_balance_string)

**支持的格式**:
```
RM 1,234.56       → 1234.56
1,234.56 CR       → 1234.56 (正数)
(1,234.56)        → -1234.56 (负数)
1,234.56 DR       → -1234.56 (负数)
-1,234.56         → -1234.56
MYR 1234.56       → 1234.56
```

**优先级顺序**:
1. CR/DR标记（最高优先级）
2. 括号格式 `(123.45)`
3. 负号 `-123.45`

### 2. 交易类型识别

| PDF标记 | 系统类型 | 说明 |
|--------|---------|------|
| CR / Credit / Deposit / Money In | `credit` | 存入 |
| DR / Debit / Withdrawal / Money Out | `debit` | 取出 |
| (Amount) | `debit` | 括号表示支出 |
| +Amount | `credit` | 正号表示收入 |
| -Amount | `debit` | 负号表示支出 |

### 3. 特殊交易识别

#### 客户付款记录（用于信用卡还款搜索）
**关键词**:
```python
payment_keywords = [
    'PAYMENT', 'FPX', 'TRANSFER', 'DUITNOW',
    'CREDIT CARD', 'VISA', 'MASTERCARD',
    'ONLINE TRANSFER', 'IBG', 'GIRO'
]
```

**用途**: 在Admin Dashboard搜索客户的信用卡还款来源

#### 第三方转账
**关键词**:
```python
transfer_keywords = [
    'TRANSFER', 'IBG', 'GIRO', 'INSTANT TRANSFER',
    'INTERBANK', 'DUITNOW', 'RENTAS'
]
```

---

## 双重验证机制

### 第一重验证：系统自动验证

#### 1. 余额连续性验证
```python
# 每笔交易的余额必须等于：
# 上一笔余额 ± 本笔金额 = 本笔余额

for i in range(len(transactions)):
    if i == 0:
        expected_balance = opening_balance + (
            transactions[i]['amount'] if transactions[i]['type'] == 'credit' 
            else -transactions[i]['amount']
        )
    else:
        prev_balance = transactions[i-1]['balance']
        expected_balance = prev_balance + (
            transactions[i]['amount'] if transactions[i]['type'] == 'credit' 
            else -transactions[i]['amount']
        )
    
    actual_balance = transactions[i]['balance']
    
    if abs(expected_balance - actual_balance) > 0.01:
        raise ValidationError(f"余额不连续！期望: {expected_balance}, 实际: {actual_balance}")
```

#### 2. 交易数量验证
```python
# 系统记录的交易数量必须等于PDF中的交易数量
total_transactions_in_db == total_transactions_in_pdf
```

#### 3. 期末余额验证
```python
# 最后一笔交易的余额必须等于PDF中的Closing Balance
last_transaction_balance == closing_balance_in_pdf
```

### 第二重验证：双重人工验证（Mandatory）

#### 核心要求：零容差、100%准确性

每条存入系统的交易记录的**序号、日期、描述、金额、类型、余额**都必须与PDF原件完全一致，一字不差。

#### 双重验证工作流程

**第一步：运行验证脚本**
```bash
# 显示对比表
python3 scripts/verify_savings_statement.py <statement_id>
```

**第二步：第一遍人工验证**
1. 打开PDF原件（从输出的PDF路径）
2. 逐行对比：序号、日期、描述、金额、类型、余额
3. 重点检查：
   - 描述内容是否有多字、少字、错字
   - 特殊字符（空格、标点符号）是否一致
   - 日期格式是否准确
   - 金额小数点后2位是否正确
4. 在纸上记录：第1遍验证通过 ✓

**第三步：第二遍人工验证**
1. 休息5分钟，让眼睛放松
2. 重新从第1笔交易开始，再次逐行对比
3. 特别注意第一遍标记的疑问点
4. 在纸上记录：第2遍验证通过 ✓

**第四步：标记为已验证**
```bash
# 确认两遍验证都通过后
python3 scripts/mark_statement_verified.py <statement_id>
# 输入 YES 确认
```

#### 验证标准（100%准确性）
- [x] 交易总数：系统记录数 = PDF交易总数
- [x] 交易日期：100%一致
- [x] 交易描述：100%一致（一字不差，包括空格和标点）
- [x] 交易金额：小数点后2位完全相同
- [x] 交易类型：CR/DR标识正确
- [x] 每笔余额：余额连续性正确
- [x] Total Credit：系统汇总 = PDF汇总
- [x] Total Debit：系统汇总 = PDF汇总
- [x] Closing Balance：期末余额完全一致

**不合格标准**：任何一项不符合100%要求，整个账单验证失败。

#### 详细验证流程

完整的双重验证工作流程、检查清单、质量标准，请参见：
**`docs/MANUAL_VERIFICATION_WORKFLOW.md`**

---

## 上传操作流程

### 完整14步上传流程

#### 步骤1: 准备PDF文件
- ✅ 确保PDF清晰可读
- ✅ 文件命名：`{BankName}_{AccountLast4}_{YYYY-MM-DD}.pdf`
- ✅ 检查PDF包含完整的交易记录

#### 步骤2: 登录系统
- 访问: `/savings/upload`
- 需要Admin权限

#### 步骤3: 选择客户
- 从下拉列表选择客户
- 或创建新客户

#### 步骤4: 上传PDF文件
- 支持批量上传（多个文件）
- 支持拖拽上传

#### 步骤5: 系统自动检测银行
- 系统会自动识别银行名称
- 如未识别，可手动选择

#### 步骤6: 系统自动解析
- 提取账单日期
- 提取账户号码
- 提取所有交易记录

#### 步骤7: 应用Balance-Change算法
- 根据余额变化确定交易类型
- 计算准确金额

#### 步骤8: 系统自动验证
- 验证余额连续性
- 验证交易数量
- 验证期末余额

#### 步骤9: 保存到数据库
- 创建/更新储蓄账户记录
- 保存账单记录
- 保存所有交易记录

#### 步骤10: 文件归档
- 移动文件到标准位置
- 重命名为标准格式

#### 步骤11: 显示上传结果
- 显示成功/失败信息
- 显示交易总数

#### 步骤12: 双重人工验证（必须！）
```bash
# 运行验证脚本
python3 scripts/verify_savings_statement.py <statement_id>
```
- 打开PDF原件
- 第一遍：逐行对比序号、日期、描述、金额、类型、余额
- 休息5分钟
- 第二遍：重新逐行对比一遍

#### 步骤13: 标记验证状态
```bash
# 确认两遍验证都通过后
python3 scripts/mark_statement_verified.py <statement_id>
```
- 输入 `YES` 确认
- 系统更新验证状态为 `verified`
- 记录验证时间戳

#### 步骤14: 完成
- 验证状态：`verified`
- 数据可用于后续分析
- 详细验证流程：`docs/MANUAL_VERIFICATION_WORKFLOW.md`

### 批量上传注意事项

1. **一次最多上传20个文件**
2. **文件大小限制**: 每个文件最大16MB
3. **支持格式**: PDF, Excel (.xlsx, .xls)
4. **建议**: 按客户、按月份分批上传

---

## 数据展示标准

### Admin Dashboard显示

#### 列表视图（所有账单）
```
客户名称 | 银行 | 账户后4位 | 账单日期 | 交易数 | 转账金额 | 验证状态 | 操作
-------|------|----------|---------|--------|---------|---------|------
CHANG  | PBB  | 0727     | 2025-10 | 45     | RM 12K  | ✅已验证 | 查看
CHEOK  | GXB  | 8388     | 2025-09 | 67     | RM 8.5K | ⏳待验证 | 查看
```

#### 详细视图（单个账单）
```
账单信息：
- 银行名称: Public Bank
- 账户号码: ****0727
- 账单日期: 2025-10-31
- 总交易数: 45 笔
- 验证状态: 已验证 ✅

交易记录表格：
日期       | 描述                    | 类型  | 金额        | 余额        | CR/DR
----------|------------------------|-------|------------|------------|-------
2025-10-01| Opening Balance        | -     | -          | RM 1,000   | -
2025-10-05| Salary Credit          | 存入  | RM 5,000   | RM 6,000   | CR
2025-10-10| ATM Withdrawal         | 取出  | RM 200     | RM 5,800   | DR
2025-10-15| Credit Card Payment    | 取出  | RM 1,500   | RM 4,300   | DR
```

### 颜色标准（3色系统）

| 项目 | 颜色 | 用途 |
|------|------|------|
| 背景色 | #000000 (Black) | 主背景 |
| Credit交易 | #FF007F (Hot Pink) | 存入/收入 |
| Debit交易 | #FFFEF0 (Ivory White) | 取出/支出 |
| 边框/装饰 | #322446 (Dark Purple) | 表格边框 |

### 表格样式标准

```css
/* 表头 */
thead th {
    font-size: 0.85rem;
    padding: 1rem 1.2rem;
    background: linear-gradient(135deg, #322446, #1a1a1a);
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* 内容 */
tbody td {
    font-size: 0.80rem;
    padding: 0.9rem 1.2rem;
    white-space: nowrap;
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* Credit行 */
.credit-row {
    background: rgba(255, 0, 127, 0.05);
    color: #FF007F;
}

/* Debit行 */
.debit-row {
    background: rgba(255, 254, 240, 0.02);
    color: #FFFEF0;
}
```

---

## 常见问题解答 (FAQ)

### Q1: 如果PDF格式不标准怎么办？
**A**: 系统会使用通用解析器(`parse_generic_savings`)，但建议人工验证。

### Q2: 如果PDF没有Opening Balance怎么办？
**A**: 系统会假设Opening Balance = 0，但建议手动输入正确值。

### Q3: 如何搜索客户的信用卡还款记录？
**A**: 在Admin Dashboard使用"Search by Name"功能，输入客户名称即可。

### Q4: 支持Excel格式吗？
**A**: 支持！系统会自动识别列（Date, Description, Amount, Balance）。

### Q5: 如何处理同一客户的多个储蓄账户？
**A**: 系统会根据账户号码后4位自动区分不同账户。

### Q6: 验证状态有什么用？
**A**: 
- `pending`: 刚上传，待人工验证
- `verified`: 已验证，数据可用
- `discrepancy`: 发现差异，需要复核

### Q7: 可以删除已上传的账单吗？
**A**: 可以，但会保留在备份表(`deleted_savings_statements_backup`)中。

### Q8: 系统如何处理重复上传？
**A**: 系统会检测文件MD5哈希值，拒绝重复上传。

---

## 附录

### A. 银行专用解析器特性

#### Maybank
- 支持双列格式（Withdrawal / Deposit）
- 支持单列格式（Amount with CR/DR）

#### GX Bank
- 支持"Money In" / "Money Out"列
- 支持Balance列验证

#### Hong Leong Bank
- 支持表格提取
- 支持余额变化算法

#### CIMB / UOB / OCBC
- 通用表格格式
- 支持CR/DR标记

#### Public Bank
- 支持RM ACE Account格式
- 支持特殊日期格式

#### Alliance Bank
- 支持Current Account格式
- 支持多页PDF

### B. 系统统计数据（当前）

| 项目 | 数量 |
|------|------|
| 储蓄账户总数 | 4 |
| 账单总数 | 38 |
| 交易总数 | 4,334 |
| 支持银行数 | 8 + 通用 |

### C. 相关文档链接

- **信用卡系统标准**: `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **系统记忆文件**: `replit.md`
- **文档索引**: `DOCUMENTATION_INDEX.md`

---

**最后更新**: 2025-10-29  
**维护者**: Smart Credit & Loan Manager Team  
**版本**: 1.0 (Initial Release)
