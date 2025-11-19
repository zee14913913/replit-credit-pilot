# CreditPilot Architecture Constraints
# 架构约束文档 - 不可变更的系统规则

## 🔒 强制执行级别：CRITICAL

本文档定义了 CreditPilot 系统的核心计算规则和架构约束。
**这些规则是系统的基础，任何修改必须经过完整的业务验证和用户批准。**

---

## 1. 核心计算规则 (Core Calculation Rules)

### 1.1 第一轮计算（6个基础项目）

#### 1.1.1 Owner's Expenses
**公式：**
```
Owner's Expenses = SUM(所有非Suppliers的DR交易)
```

**规则：**
- 只包含 DR (Debit) 类型的交易
- **排除**所有包含7个Supplier关键词的交易
- 7个Suppliers必须严格匹配：
  1. `7SL`
  2. `Dinas`
  3. `Raub Syc Hainan`
  4. `Ai Smart Tech`
  5. `HUAWEI`
  6. `PasarRaya`
  7. `Puchong Herbs`

**⚠️ 约束：**
- Supplier列表不可随意修改
- 大小写不敏感匹配
- 使用包含匹配（contains），不是精确匹配

---

#### 1.1.2 GZ's Expenses
**公式：**
```
GZ's Expenses = SUM(所有Suppliers的DR交易)
```

**规则：**
- 只包含 DR (Debit) 类型的交易
- **仅包含**包含7个Supplier关键词的交易
- 与 Owner's Expenses 互斥（不重复计算）

**⚠️ 约束：**
- GZ's Expenses + Owner's Expenses = 所有DR交易总额
- 必须使用与 Owner's Expenses 相同的Supplier列表

---

#### 1.1.3 Owner's Payment
**公式：**
```
Owner's Payment = SUM(客户自己的CR还款)
```

**识别规则（满足任一条件即可）：**
1. CR记录的描述中包含**客户名字**
2. CR记录**无任何描述**（空白或NULL）

**⚠️ 约束：**
- 必须是 CR (Credit) 类型
- 客户名字匹配不区分大小写
- 空白描述（空字符串、NULL、纯空格）都算作 Owner's Payment

---

#### 1.1.4 GZ's Payment1
**公式（使用排除法）：**
```
GZ's Payment1 = SUM(所有CR记录) - Owner's Payment
```

**规则：**
- 这是**排除法计算**
- 先计算所有CR总额
- 减去已识别的 Owner's Payment

**⚠️ 约束：**
- GZ's Payment1 + Owner's Payment = 所有CR交易总额
- 不需要额外的识别逻辑
- 完全依赖 Owner's Payment 的准确性

---

#### 1.1.5 Owner's Outstanding Balance (Round 1)
**公式：**
```
Owner's OS Bal = Previous Balance + Owner's Expenses - Owner's Payment
```

**⚠️ 关键约束：**
- **必须允许负数！**
- 负数表示客户多还了钱（overpayment）
- 不得对负数结果进行任何截断或警告
- Previous Balance 必须来自账单的明确记录

---

#### 1.1.6 GZ's Outstanding Balance (Round 1)
**公式：**
```
GZ's OS Bal = Previous Balance + GZ's Expenses - GZ's Payment1
```

**⚠️ 关键约束：**
- **必须允许负数！**
- 负数表示GZ多还了钱
- 不得对负数结果进行任何截断或警告
- 使用与 Owner's OS Bal 相同的 Previous Balance

---

### 1.2 第二轮计算

#### 1.2.1 GZ's Payment2
**公式：**
```
GZ's Payment2 = SUM(从9个GZ Bank转账到客户银行账户的金额)
```

**9个GZ Bank的精确组合（银行 + 持卡人）：**

| # | 银行 | 持卡人 |
|---|------|--------|
| 1 | GX Bank | Tan Zee Liang |
| 2 | Maybank | Yeo Chee Wang |
| 3 | GX Bank | Yeo Chee Wang |
| 4 | UOB | Yeo Chee Wang |
| 5 | OCBC | Yeo Chee Wang |
| 6 | OCBC | Teo Yok Chu |
| 7 | Hong Leong Bank | Infinite GZ Sdn Bhd |
| 8 | Public Bank | Ai Smart Tech |
| 9 | Alliance Bank | Ai Smart Tech |

**⚠️ 约束：**
- 必须**同时匹配**银行名称和持卡人名称
- 不是"所有Maybank卡"，而是"Maybank + Yeo Chee Wang"
- 大小写不敏感
- 支持银行简称（如 HLB = Hong Leong Bank）

**数据来源：**
- 客户的银行流水记录（bank_transfers表）
- 必须是 CR (转入) 记录
- 必须在账单月份范围内

---

### 1.3 最终计算

#### 1.3.1 FINAL Owner Outstanding Balance
**公式：**
```
FINAL Owner OS Bal = Owner's OS Bal（第1轮）
```

**⚠️ 约束：**
- 不受 GZ's Payment2 影响
- 直接使用第1轮结果
- 允许负数

---

#### 1.3.2 FINAL GZ Outstanding Balance
**公式：**
```
FINAL GZ OS Bal = GZ's OS Bal（第1轮）- GZ's Payment2
```

**⚠️ 约束：**
- 扣除 GZ's Payment2
- 允许负数
- 这是最终的GZ未结余额

---

## 2. 手续费系统 (Miscellaneous Fee System)

### 2.1 计算规则
**公式：**
```
Miscellaneous Fee = GZ's Expenses × 1%
```

### 2.2 独立性约束
**⚠️ 关键约束：**
- 手续费**完全独立**
- **不参与** DR/CR 平衡验证
- **不影响** Outstanding Balance 计算
- 单独生成 Invoice PDF

### 2.3 Invoice 生成规范
**存储路径：**
```
/CreditPilot/Invoices/YYYY-MM/MF_{customer_code}_{year_month}.pdf
```

**Invoice编号格式：**
```
MF-{customer_code}-{year_month}
例如：MF-C001-2024-09
```

**⚠️ 约束：**
- 每月每客户只能有一个手续费Invoice
- PDF必须使用批准的3色调色板
- 必须包含：GZ's Expenses、费率、手续费金额

---

## 3. 验证系统 (Validation System)

### 3.1 DR/CR 平衡验证
**规则：**
```
total_dr 必须等于 total_cr
允许误差：±0.01
```

**⚠️ 约束：**
- 使用 Decimal 类型进行精确计算
- 误差范围不可修改
- 不平衡时必须阻止账单提交

### 3.2 数据完整性验证
**必检项：**
1. Previous Balance 存在且有效
2. 账单月份存在
3. 银行名称存在
4. 持卡人名称存在
5. 所有交易有金额
6. 所有交易有类型（DR/CR）

### 3.3 分类完整性验证
**规则：**
- 所有DR交易必须有分类（Owner's Expenses 或 GZ's Expenses）
- CR交易自动分类（Owner's Payment 或 GZ's Payment1）

### 3.4 异常检测阈值
**大额交易阈值：**
```
RM 10,000.00
```

**⚠️ 约束：**
- 超过阈值的交易需要二次验证
- 但不阻止账单提交
- 只作为警告提示

---

## 4. 数据类型约束 (Data Type Constraints)

### 4.1 金额字段
**强制类型：**
```python
Decimal  # 不允许使用 float
```

**精度要求：**
```
DECIMAL(10, 2)  # 10位总长度，2位小数
```

**⚠️ 约束：**
- 禁止使用 float 进行金额计算
- 所有金额必须使用 Decimal 类型
- 数据库存储必须使用 DECIMAL 字段

### 4.2 日期字段
**格式：**
```
YYYY-MM-DD  # 标准 ISO 格式
账单月份：YYYY-MM
```

---

## 5. 色彩系统约束 (Color System Constraints)

### 5.1 批准的3色调色板
**唯一批准的颜色：**
```css
Black:       #000000
Hot Pink:    #FF007F
Dark Purple: #322446
```

### 5.2 使用规范
**⚠️ 严格禁止：**
- ❌ 绿色 (#00FF00 或任何绿色)
- ❌ 橙色 (#FFA500 或任何橙色)
- ❌ 红色 (#FF0000 或任何红色)
- ❌ 金色 (#FFD700 或任何金色)
- ❌ 任何未经批准的颜色

**允许的中性色：**
- ✅ 白色 (#FFFFFF) - 仅用于背景和文字
- ✅ 灰色半透明 (rgba) - 仅用于UI辅助元素

### 5.3 PDF报表颜色
**必须使用：**
```python
reportlab_colors.HexColor('#FF007F')  # 表头
reportlab_colors.HexColor('#000000')  # 文字
reportlab_colors.HexColor('#322446')  # 边框
reportlab_colors.HexColor('#FFFFFF')  # 背景
```

---

## 6. API 自动化约束 (API Automation Constraints)

### 6.1 上传触发规则
**触发条件：**
```
客户上传信用卡账单PDF时自动触发：
1. PDF解析
2. 交易分类
3. 计算引擎
4. 验证系统
5. 生成报表
```

**⚠️ 约束：**
- 必须100%自动化
- 不需要人工干预
- 失败时必须记录错误日志

### 6.2 错误处理
**必须捕获的错误：**
1. PDF解析失败
2. DR/CR不平衡
3. 数据完整性失败
4. 分类失败

**错误处理规则：**
- 不能静默失败
- 必须通知用户
- 必须记录详细日志

---

## 7. 数据库架构约束 (Database Schema Constraints)

### 7.1 核心表
**必须存在的表：**
1. `customers` - 客户表
2. `credit_cards` - 信用卡表
3. `statements` - 账单表
4. `transactions` - 交易表
5. `monthly_statements` - 月度汇总表
6. `miscellaneous_fee_invoices` - 手续费Invoice表
7. `bank_transfers` - 银行流水表（用于GZ's Payment2）

### 7.2 关键字段约束
**transactions 表：**
```sql
transaction_type TEXT NOT NULL CHECK (transaction_type IN ('DR', 'CR'))
amount DECIMAL(10, 2) NOT NULL
category TEXT  -- 'Owner's Expenses', 'GZ's Expenses', 等
```

**statements 表：**
```sql
previous_balance_total DECIMAL(10, 2) NOT NULL
statement_month TEXT NOT NULL  -- 格式: YYYY-MM
```

---

## 8. 修改流程 (Modification Process)

### 8.1 禁止直接修改
**以下规则禁止直接修改：**
1. 7个Supplier列表
2. 9个GZ Bank组合
3. 核心计算公式
4. DR/CR平衡误差范围
5. 3色调色板

### 8.2 修改审批流程
**如果必须修改，需要：**
1. ✅ 用户明确书面批准
2. ✅ 业务逻辑验证
3. ✅ 完整的测试
4. ✅ 更新本文档
5. ✅ Architect 审查

### 8.3 版本控制
**本文档版本：**
```
Version: 1.1.0
Created: 2025-11-18
Last Updated: 2025-11-19
Status: ENFORCED
Modification: 修正7个Suppliers名称为正确版本
```

**⚠️ 修改本文档需要：**
- 增加版本号
- 记录修改人
- 记录修改原因
- 获得用户批准

---

## 9. 实施检查清单 (Implementation Checklist)

开发任何新功能时，必须检查：

- [ ] 是否使用了批准的3色调色板？
- [ ] 金额计算是否使用了 Decimal 类型？
- [ ] DR/CR平衡验证是否正确实施？
- [ ] 是否允许负数Outstanding Balance？
- [ ] Supplier列表是否正确（7个）？
- [ ] GZ Bank组合是否正确（9个）？
- [ ] 手续费是否独立计算？
- [ ] 是否实施了完整的验证系统？
- [ ] 错误处理是否完善？
- [ ] 是否记录了审计日志？

---

## 10. 联系人 (Contact)

**架构问题咨询：**
- Architect Agent
- 系统管理员

**业务规则变更：**
- 必须联系用户获得批准
- 禁止自行决定修改

---

**📌 重要提示：**
> 本文档是系统的"宪法"，所有开发工作必须严格遵守这些约束。
> 违反这些约束的代码将被拒绝合并。
> 如有疑问，请先咨询，不要猜测。

---

**END OF DOCUMENT**
