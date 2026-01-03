# 📊 Smart Loan Manager - 会计与审计系统完整功能清单

> **生成日期**: 2025年11月11日  
> **系统版本**: Enterprise Edition  
> **架构**: Flask (Port 5000) + FastAPI (Port 8000) 双架构

---

## 🎯 系统概述

Smart Loan Manager 是一个**企业级金融管理 SaaS 平台**，集成了完整的会计和审计功能，专为马来西亚银行客户设计。

### 核心价值主张
- ✅ **100% 数据准确性** - 严格的双重验证机制
- ✅ **全自动化** - 从OCR识别到会计分录自动生成
- ✅ **企业级安全** - 多租户隔离、审计日志、RBAC权限控制
- ✅ **专业报表** - 符合马来西亚会计准则的财务报表

---

## 📁 系统架构

### 双架构设计
| 组件 | 技术栈 | 端口 | 职责 |
|------|--------|------|------|
| **主应用** | Flask + SQLite | 5000 | 客户管理、信用卡对账、储蓄账户、报表展示 |
| **会计API** | FastAPI + PostgreSQL | 8000 | 自动记账、月结任务、PDF报表生成、审计日志 |

---

## 💾 数据库架构

### 1. **客户管理数据** (SQLite)

#### 1.1 客户基础信息
- **customers** (7条记录) - 客户主档案
  - 客户代码、姓名、电话、邮箱、地址
  - 贷款DSR评分、CTOS信息
  - 客户分类（固定薪资打工人 vs 经营企业的生意人）

#### 1.2 客户扩展信息
- **customer_employment_types** - 就业类型和收入验证
- **customer_aliases** - 客户别名管理（OCR识别用）
- **customer_classification_config** - 自动分类配置
- **customer_network** - 客户关系网络
- **customer_resources** - 客户资源

### 2. **财务交易数据** (SQLite)

#### 2.1 信用卡系统
- **statements** (73条记录) - 信用卡月度对账单
  - 对账单日期、到期日
  - 总支出、上期余额、当期应付
  - PDF文件路径、验证状态
  
- **transactions** (1,350条记录) - 信用卡交易明细
  - 交易日期、金额、描述
  - 自动分类（AI分类+置信度）
  - 交易类型（debit/credit）
  - 交易子类型（supplier费用识别）
  - 所属用户、供应商名称
  - 积分记录、卡号后4位

- **monthly_statements** (110条记录) - 月度汇总报表
  - 6个强制分类字段：
    1. total_spent (总支出)
    2. total_fees (总费用)
    3. total_supplier_consumption (供应商消费)
    4. total_customer_payment (客户付款)
    5. total_revenue (总收入 = 费用+供应商费用)
    6. total_refunds (退款)

#### 2.2 储蓄账户系统
- **savings_accounts** (10条记录) - 储蓄账户
  - 账户名称、账户号码
  - 当前余额、利率
  - 所属客户、银行信息

- **savings_transactions** (7,641条记录) - 储蓄账户交易
  - 交易日期、金额、描述
  - 交易类型（deposit/withdrawal/interest/fee）
  - 余额追踪

#### 2.3 付款账户
- **payment_accounts** (9条记录) - 银行付款账户
  - 账户类型（信用卡/储蓄账户）
  - 银行名称、账户号码
  - 关联客户

### 3. **发票与付款系统** (Flask主应用)

#### 3.1 供应商发票 (Supplier Invoices)
- **功能位置**: `/credit-cards` 页面的 "Supplier Invoices" 选项卡
- **用途**: 自动生成供应商消费的1%处理费发票
- **数据来源**: transactions表中标记为supplier的交易
- **字段**:
  - 发票编号、日期
  - 客户信息
  - 消费金额、处理费（1%）
  - 状态（未付款/已付款）

#### 3.2 客户付款 (Customer Payments)
- **功能位置**: `/credit-cards` 页面的 "Customer Payments" 选项卡
- **用途**: 记录客户向GZ支付的款项
- **关联**: 与monthly_statements的customer_payment字段关联
- **支付方式**: 现金、转账、信用卡等

### 4. **OCR收据识别系统**

#### 4.1 OCR Receipts
- **功能位置**: `/credit-cards` 页面的 "OCR Receipts" 选项卡
- **数据表**: ocr_receipts (已创建)
- **功能**:
  - 上传商户刷卡收据图片（JPG/PNG）
  - 自动OCR识别：金额、日期、商户名
  - 智能匹配：自动关联到客户和信用卡交易
  - 手动匹配：未自动匹配的收据可手动处理
  - 状态追踪：Pending/Auto-matched/Manual-matched

- **统计面板**:
  - Total Receipts（总收据数）
  - Auto-matched（自动匹配成功）
  - Manual-matched（手动匹配）
  - Pending（待处理）

### 5. **审计日志系统**

#### 5.1 审计日志 (Audit Logs)
- **audit_logs** (98条记录) - 完整审计追踪
  - 用户ID、操作类型
  - 实体类型、实体ID
  - 操作描述、IP地址
  - 时间戳

- **记录的操作**:
  - LOGIN - 用户登录
  - CREATE - 创建记录
  - UPDATE - 更新记录
  - DELETE - 删除记录
  - UPLOAD - 文件上传
  - EXPORT - 数据导出
  - VIEW - 查看敏感数据

### 6. **银行对账单**

#### 6.1 Bank Statements
- **bank_statements** (0条记录) - 银行对账单导入
  - 支持CSV/Excel导入
  - 自动匹配交易
  - 未匹配项标记
  - 对账功能

---

## 🚀 FastAPI 会计系统功能 (Port 8000)

### 1. **多租户会计核心**

#### 1.1 公司管理 (Companies)
- 公司代码、名称、注册号
- 税号、业务类型
- 银行账户信息
- 财政年度结束日期

#### 1.2 会计科目表 (Chart of Accounts)
- 5大类科目：Asset, Liability, Equity, Income, Expense
- 支持父子科目层级
- 科目激活状态控制

### 2. **日记账分录系统**

#### 2.1 Journal Entries (journal_entries)
- 分录编号、日期、描述
- 分录类型：
  - manual - 手动分录
  - auto - 自动生成
  - bank_import - 银行导入
  - invoice - 发票
  - payment - 付款
  - payroll - 工资单
  - tax_adjustment - 税务调整

#### 2.2 Journal Entry Lines (journal_entry_lines)
- 借方金额 (debit_amount)
- 贷方金额 (credit_amount)
- 关联会计科目
- 原始凭证追溯（raw_line_id防虚构交易）

### 3. **供应商管理**

#### 3.1 Suppliers (suppliers)
- 供应商代码、名称
- 联系人、电话、邮箱
- 付款条款（默认30天）
- 状态管理

#### 3.2 Purchase Invoices (purchase_invoices)
- 发票号码、日期、到期日
- 总金额、已付金额、余额
- 状态：unpaid, partial, paid, overdue
- 自动生成会计分录

#### 3.3 Supplier Payments (supplier_payments)
- 付款编号、日期、金额
- 付款方式、参考号
- 付款分配到多张发票

### 4. **客户管理（会计视角）**

#### 4.1 Customers (customers - PostgreSQL)
- 客户代码、名称
- 信用额度、付款条款
- 状态管理

#### 4.2 Sales Invoices (sales_invoices)
- 发票号码、日期、到期日
- 总金额、已收金额、余额
- 自动生成标记（auto_generated）
- 状态：unpaid, partial, paid, overdue

### 5. **POS报表处理**

#### 5.1 POS Reports (pos_reports)
- 报表日期、编号
- 总销售额、交易笔数
- 付款方式（现金/卡/在线/混合）
- PDF解析状态
- 自动生成发票标记

### 6. **银行对账系统**

#### 6.1 Bank Statements (bank_statements - PostgreSQL)
- 银行名称、账户号码
- 对账单月份（2025-01格式）
- 交易日期、描述、参考号
- 借方金额、贷方金额、余额
- 匹配状态、自动分类
- 原始数据追溯（raw_line_id）

### 7. **自动记账规则引擎**

#### 7.1 Auto Posting Rules (auto_posting_rules)
- **表驱动规则管理** - 替代硬编码
- **优先级排序** - priority字段（1-1000）
- **模式匹配**:
  - 关键字匹配（case-insensitive）
  - 正则表达式匹配
- **多源类型**:
  - bank_import - 银行导入
  - supplier_invoice - 供应商发票
  - sales_invoice - 销售发票
  - general - 通用规则

#### 7.2 预定义规则（20条种子数据）
| 优先级 | 规则名称 | 模式 | 借方科目 | 贷方科目 |
|--------|----------|------|----------|----------|
| 10 | 工资支付 | payout | salary_expense | bank |
| 20 | EPF缴纳 | epf | epf_expense | bank |
| 30 | SOCSO缴纳 | socso | socso_expense | bank |
| 50 | 租金支付 | rent | rent_expense | bank |
| 100 | 水电费 | utilities | utilities_expense | bank |
| 200 | 银行手续费 | bank.*fee | bank_charges | bank |
| 900 | 银行利息收入 | interest | bank | interest_income |

#### 7.3 匹配统计
- match_count - 匹配次数自动累计
- last_matched_at - 最后匹配时间

### 8. **异常中心 (Exception Center)**

#### 8.1 Exceptions (exceptions)
- **异常类型**:
  - pdf_parse - PDF解析失败
  - ocr_error - OCR识别错误
  - customer_mismatch - 客户未匹配
  - supplier_mismatch - 供应商未匹配
  - posting_error - 记账失败

- **严重程度**:
  - low - 低
  - medium - 中
  - high - 高
  - critical - 严重

- **状态流转**:
  - new → in_progress → resolved/ignored

#### 8.2 异常统计
- 按类型统计
- 按严重程度统计
- 按状态统计
- 严重/高优先级异常数量

### 9. **文件存储管理**

#### 9.1 FileStorageManager
- **多租户隔离** - 按company_id严格隔离
- **安全验证** - 防路径遍历、防跨租户访问
- **标准化路径**:
  ```
  /accounting_data/companies/{company_id}/
  ├── bank_statements/2025/11/
  ├── invoices/supplier/
  ├── invoices/purchase/
  ├── invoices/sales/
  ├── pos_reports/2025/11/
  └── reports/
      ├── balance_sheet/2025/
      ├── profit_loss/2025/11/
      ├── bank_package/2025/
      └── management/2025/
  ```

### 10. **专业报表生成**

#### 10.1 Management Reports
- **Balance Sheet**（资产负债表）
  - Total Assets, Liabilities, Equity
  - 自动平衡检查
  
- **Profit & Loss Statement**（损益表）
  - Total Revenue, Expenses
  - Net Profit, Gross Margin
  
- **Aging Reports**:
  - AR Aging（应收账款账龄）
  - AP Aging（应付账款账龄）
  - 账龄分类：0-30, 31-60, 61-90, 90+天

#### 10.2 PDF Reports
- **Balance Sheet PDF** - 专业格式资产负债表
- **Profit & Loss PDF** - 损益表
- **Bank Package PDF** - 银行贷款申请包
  - 包含：Balance Sheet + P&L + Aging Summary + 数据质量指标

### 11. **月结任务自动化**

#### 11.1 Monthly Close Task
- **自动执行流程**:
  1. 检查未匹配银行流水
  2. 计算试算表（Trial Balance）
  3. 自动生成发票
  4. 生成Management Report JSON
  5. 保存到FileStorageManager

- **触发方式**:
  - API调用：`POST /api/tasks/monthly-close`
  - 定时任务（Cron）
  - 手动触发

---

## 🔐 安全特性

### 1. **多租户隔离**
- ✅ Company ID强制过滤
- ✅ 文件路径安全验证
- ✅ 防路径遍历攻击
- ✅ 防跨租户数据访问

### 2. **审计追踪**
- ✅ 所有操作记录audit_logs
- ✅ IP地址记录
- ✅ 用户操作追踪
- ✅ 时间戳精确到秒

### 3. **数据完整性**
- ✅ 借贷必平衡检查
- ✅ 原始凭证追溯（raw_line_id）
- ✅ 防虚构交易（NOT NULL约束）
- ✅ 外键约束保护

### 4. **权限控制**
- ✅ RBAC角色权限系统
- ✅ API Key认证
- ✅ Session管理
- ✅ 多级权限（admin/manager/user）

---

## 📊 可导出到 SQL Account 的数据

### 数据映射表

| Smart Loan Manager 数据源 | 数据量 | SQL Account 目标 | 用途 |
|----------------------------|--------|------------------|------|
| **transactions** (debit) | 1,350 | Journal Entry (SALES) | 每日销售记录 |
| **savings_transactions** | 7,641 | Bank Reconciliation | 银行对账单 |
| **monthly_statements** | 110 | Journal Entry Summary | 月度汇总 |
| **supplier invoices** (可创建) | - | Purchase Invoice | 供应商发票 |
| **customer payments** (可创建) | - | Customer Payment Entry | 客户付款 |
| **payroll** (可创建) | - | Journal Entry (PAYROLL) | 工资单 |
| **loan interest** (贷款利息) | - | Journal Entry (INTEREST) | 贷款利息费用 |

### SQL Account 格式示例

根据您上传的图片，SQL Account使用以下格式：

```
Journal Entry:
- G/L Code: 500-000 (SALES), 320-000 (CASH IN HAND), 320-001 (CREDIT CARD)
- GL Description: SALES, CASH IN HAND, CREDIT CARD, MAYBANK-DU
- Document Type: SALES
```

---

## 🎯 系统统计摘要

| 类别 | 数量 | 说明 |
|------|------|------|
| **客户数量** | 7 | 活跃客户账户 |
| **信用卡交易** | 1,350 | 所有信用卡交易记录 |
| **储蓄账户交易** | 7,641 | 所有储蓄账户交易 |
| **月度报表** | 110 | 月度财务汇总 |
| **信用卡对账单** | 73 | PDF对账单 |
| **储蓄账户** | 10 | 银行储蓄账户 |
| **付款账户** | 9 | 信用卡+储蓄账户 |
| **审计记录** | 98 | 操作审计日志 |
| **自动记账规则** | 20+ | 表驱动规则引擎 |

---

## 🚀 下一步集成方案

### 选项1：Excel导出（推荐立即实施）
创建一个"SQL Account Export"页面，一键导出所有财务数据为Excel格式：
- ✅ Journal Entries（日记账分录）
- ✅ Sales Invoices（销售发票）
- ✅ Purchase Invoices（采购发票）
- ✅ Payments（付款记录）
- ✅ Bank Reconciliation（银行对账）

### 选项2：REST API集成（需要API凭证）
直接通过SQL Account官方API推送数据：
- API文档：https://docs.sql.com.my/sqlacc/category/sql-account-api
- 需要Client ID和Client Secret
- 支持实时同步

### 选项3：sFTP自动上传
自动将Excel文件上传到sFTP服务器：
- SQL Account自动下载并导入
- 无需手动操作
- 支持定时任务

---

## 📝 结论

您的Smart Loan Manager系统拥有**完整的企业级会计和审计功能**，包括：

1. ✅ **7个客户**的完整财务数据
2. ✅ **1,350笔信用卡交易**，可作为每日销售
3. ✅ **7,641笔储蓄账户交易**，可作为银行对账单
4. ✅ **110个月度财务报表**
5. ✅ **98条审计日志**确保数据追溯
6. ✅ **FastAPI会计系统**支持自动记账、PDF报表、异常管理
7. ✅ **多租户架构**支持扩展到多个公司

**所有数据都可以导出到SQL Account ERP Edition！**
