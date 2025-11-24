# CreditPilot 会计与审计系统完整手册

**版本**: V2025.11  
**更新日期**: 2025-11-24  
**系统**: FastAPI后端（Port 8000）

---

## 📋 目录

1. [会计系统概述](#会计系统概述)
2. [核心功能模块](#核心功能模块)
3. [审计日志系统](#审计日志系统)
4. [RBAC权限系统](#rbac权限系统)
5. [会计分录引擎](#会计分录引擎)
6. [财务报表生成](#财务报表生成)
7. [SFTP ERP同步](#sftp-erp同步)
8. [API端点详解](#api端点详解)

---

## 会计系统概述

### 什么是会计系统？

**CreditPilot Accounting System**（Port 8000）是一个**银行贷款合规会计系统**，专门用于：

```yaml
核心功能:
  - 将银行月结单自动转换为会计分录
  - 生成符合银行审核标准的财务报表
  - 自动化SFTP导出到SQL ACC ERP系统
  - 完整的审计追踪（Audit Trail）

支持报表:
  - Suppliers Aging（供应商账龄）
  - Customer Ledger（客户账本）
  - P&L Statement（损益表）
  - Balance Sheet（资产负债表）
  - Payroll Reports（工资单）
  - Tax Adjustments（税务调整）
  - Auto Invoices（自动发票）
```

---

### 双引擎架构

```
┌─────────────────────────────────────────────────┐
│         CreditPilot 双引擎架构                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  Flask主应用（Port 5000）                        │
│  ├─ 信用卡管理                                   │
│  ├─ PDF解析                                     │
│  ├─ 贷款评估                                    │
│  ├─ 客户管理                                    │
│  └─ 前端UI                                      │
│                                                 │
│  FastAPI会计后端（Port 8000）                    │
│  ├─ 会计分录生成                                 │
│  ├─ 财务报表                                    │
│  ├─ 审计日志                                    │
│  ├─ RBAC权限                                    │
│  └─ SFTP ERP同步                                │
│                                                 │
└─────────────────────────────────────────────────┘
```

**通信方式**:
- Flask → FastAPI：通过HTTP API调用
- CORS配置：允许localhost:5000访问
- 数据共享：通过SQLite数据库

---

## 核心功能模块

### 1. 银行对账单管理（Bank Statements）

**功能**：
- 上传银行月结单（PDF/Excel）
- 自动解析交易记录
- 验证数据完整性
- 设为主对账单

**API端点**：
```
POST   /api/bank-statements/upload        - 上传对账单
GET    /api/bank-statements                - 获取对账单列表
PUT    /api/bank-statements/{id}/verify   - 验证对账单
POST   /api/bank-statements/{id}/post     - 入账（生成会计分录）
PUT    /api/bank-statements/{id}/set-primary - 设为主对账单
```

**操作流程**：
```yaml
Step 1: 上传银行月结单
  → PDF或Excel文件
  → 系统自动解析

Step 2: 验证对账单
  → 检查数据完整性
  → 标记为"已验证"

Step 3: 入账（生成会计分录）
  → 自动生成借贷分录
  → 保存到会计系统

Step 4: 设为主对账单（可选）
  → 标记为主要对账单
  → 用于财务报表生成
```

---

### 2. 会计分录生成（Journal Entries）

**自动分录规则**：

#### 银行交易分录
```
收入交易（CR）:
  借: 银行存款账户
  贷: 收入账户

支出交易（DR）:
  借: 费用账户
  贷: 银行存款账户

供应商付款:
  借: 应付账款
  贷: 银行存款

客户收款:
  借: 银行存款
  贷: 应收账款
```

#### 信用卡交易分录
```
信用卡消费:
  借: 费用账户
  贷: 信用卡应付

信用卡还款:
  借: 信用卡应付
  贷: 银行存款
```

---

### 3. 供应商管理（Suppliers）

**功能**：
- 供应商账龄报告（Aging Report）
- 自动发票生成
- 付款追踪
- 对账功能

**供应商账龄示例**：
```
┌─────────────┬────────┬────────┬────────┬────────┬────────┐
│ 供应商      │ 当前   │ 30天   │ 60天   │ 90天+  │ 总额   │
├─────────────┼────────┼────────┼────────┼────────┼────────┤
│ 7SL         │ 1,500  │   800  │   200  │    0   │ 2,500  │
│ Dinas Raub  │ 3,200  │ 1,500  │   500  │   100  │ 5,300  │
│ Ai Smart    │   500  │   200  │     0  │     0  │   700  │
│ HUAWEI      │ 2,100  │   900  │   300  │     0  │ 3,300  │
├─────────────┼────────┼────────┼────────┼────────┼────────┤
│ 总计        │ 7,300  │ 3,400  │ 1,000  │   100  │11,800  │
└─────────────┴────────┴────────┴────────┴────────┴────────┘
```

---

### 4. 财务报表生成（Reports）

#### 支持的报表类型

**1. 损益表（P&L Statement）**
```yaml
收入:
  营业收入: RM 150,000
  其他收入: RM 10,000
  收入合计: RM 160,000

支出:
  营业成本: RM 80,000
  管理费用: RM 30,000
  营销费用: RM 15,000
  财务费用: RM 5,000
  支出合计: RM 130,000

净利润: RM 30,000
净利润率: 18.75%
```

**2. 资产负债表（Balance Sheet）**
```yaml
资产:
  流动资产:
    现金及银行存款: RM 50,000
    应收账款: RM 30,000
    存货: RM 20,000
  固定资产:
    设备: RM 100,000
  资产合计: RM 200,000

负债:
  流动负债:
    应付账款: RM 25,000
    信用卡应付: RM 15,000
  长期负债:
    银行贷款: RM 80,000
  负债合计: RM 120,000

股东权益: RM 80,000

负债及权益合计: RM 200,000
```

**3. 客户账本（Customer Ledger）**
```yaml
客户: LEE E KAI

日期       │ 描述          │ 借方    │ 贷方    │ 余额
──────────┼──────────────┼─────────┼─────────┼────────
2025-10-01│ 期初余额      │         │         │  8,000
2025-10-15│ 信用卡消费    │ 14,515  │         │ 22,515
2025-10-20│ 还款          │         │  8,000  │ 14,515
2025-10-31│ 期末余额      │         │         │ 14,515
```

---

## 审计日志系统

### 什么是审计日志？

**Audit Log**是系统中所有操作的完整记录，用于：
- ✅ 合规性追踪
- ✅ 安全审计
- ✅ 问题排查
- ✅ 用户行为分析

---

### 记录的操作类型

```yaml
file_upload:
  - PDF账单上传
  - Excel文件上传
  - CTOS报告上传
  - 收据图片上传

create:
  - 创建客户
  - 创建信用卡
  - 创建贷款申请

update:
  - 更新客户信息
  - 修改交易分类
  - 调整计算结果

delete:
  - 删除客户
  - 删除账单
  - 删除交易记录

view:
  - 查看客户详情
  - 查看财务报告
  - 导出数据

login/logout:
  - 用户登录
  - 用户登出
  - 会话过期
```

---

### 审计日志字段

```yaml
基本信息:
  id: 日志ID
  created_at: 创建时间（UTC）
  action_type: 操作类型（file_upload/create/update/delete/view）

操作人信息:
  username: 操作人用户名
  company_id: 公司ID
  ip_address: IP地址
  user_agent: 浏览器信息

操作对象:
  entity_type: 实体类型（customer/statement/transaction）
  entity_id: 实体ID

操作详情:
  description: 操作描述
  old_value: 旧值（JSON）
  new_value: 新值（JSON）

结果:
  success: 是否成功（true/false）
  error_message: 错误消息（如果失败）
```

---

### 审计日志查询

#### API端点
```
GET /api/audit-logs?company_id=1&limit=100
```

#### 查询参数
```yaml
过滤条件:
  company_id: 公司ID
  action_type: 操作类型
  entity_type: 实体类型
  username: 操作人
  start_date: 开始时间
  end_date: 结束时间
  success: 是否成功

分页:
  limit: 返回数量（默认100，最大1000）
  offset: 偏移量（默认0）

排序:
  按created_at倒序（最新的在前）
```

---

### 审计日志示例

```json
{
  "id": 12345,
  "created_at": "2025-11-24T05:30:00Z",
  "action_type": "file_upload",
  "username": "lee.ekai@example.com",
  "company_id": 1,
  "entity_type": "credit_card_statement",
  "entity_id": 567,
  "description": "Flask上传事件: credit_card_statement | 文件名: AmBank_Oct_2025.pdf | 大小: 524288 bytes | 客户: LEE E KAI",
  "ip_address": "203.192.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "old_value": null,
  "new_value": {
    "upload_type": "credit_card_statement",
    "filename": "AmBank_Oct_2025.pdf",
    "file_size": 524288,
    "file_path": "static/uploads/customers/LEE_EK_009/statements/AmBank_Oct_2025.pdf",
    "customer_id": 1,
    "customer_code": "LEE_EK_009",
    "customer_name": "LEE E KAI",
    "source": "flask_5000"
  },
  "success": true,
  "error_message": null
}
```

---

## RBAC权限系统

### 5个角色层级

```
┌────────────────────────────────────────────┐
│            角色权限金字塔                    │
├────────────────────────────────────────────┤
│                                            │
│            👑 Admin（管理员）               │
│                  ↓                         │
│         💼 Accountant（会计师）             │
│                  ↓                         │
│      📊 Loan Officer（贷款专员）            │
│                  ↓                         │
│       ✏️ Data Entry（数据录入员）           │
│                  ↓                         │
│          👁️ Viewer（查看者）                │
│                                            │
└────────────────────────────────────────────┘
```

---

### 角色权限详解

#### 1. Admin（管理员）
**权限级别**: 最高  
**可访问资源**: 全部

```yaml
权限:
  ✅ 所有功能完全访问
  ✅ 用户管理（创建/编辑/删除用户）
  ✅ 角色分配
  ✅ 系统设置
  ✅ API密钥管理
  ✅ 审计日志查看
  ✅ 数据备份/恢复
  ✅ SFTP配置

典型使用场景:
  - 系统初始化
  - 用户账户管理
  - 安全配置
  - 系统维护
```

---

#### 2. Accountant（会计师）
**权限级别**: 高  
**可访问资源**: 除用户管理外的所有功能

```yaml
权限:
  ✅ 仪表板（Dashboard）
  ✅ 财务报表（Reports）- 查看、生成
  ✅ 银行对账单（Bank Statements）- 全部操作
  ✅ 发票管理（Invoices）- 全部操作
  ✅ POS数据（POS Data）- 全部操作
  ✅ 异常处理（Exceptions）- 全部操作
  ✅ 客户账本（Customer Ledger）
  ✅ 供应商账龄（Suppliers Aging）
  ✅ 会计分录（Journal Entries）
  ❌ 用户管理
  ❌ 系统设置

典型使用场景:
  - 日常会计操作
  - 财务报表生成
  - 对账单验证
  - 发票管理
```

---

#### 3. Loan Officer（贷款专员）
**权限级别**: 中  
**可访问资源**: 贷款评估相关功能

```yaml
权限:
  ✅ 贷款评估（Loan Evaluation）
  ✅ CTOS报告上传
  ✅ 客户信息查看
  ✅ 贷款产品目录
  ✅ 贷款报告生成
  ✅ AI贷款建议
  ⚠️ 财务报表（仅查看）
  ❌ 修改会计数据
  ❌ 银行对账单入账

典型使用场景:
  - 客户贷款申请处理
  - CTOS报告分析
  - 贷款产品推荐
  - 贷款报告生成
```

---

#### 4. Data Entry（数据录入员）
**权限级别**: 低  
**可访问资源**: 数据录入功能

```yaml
权限:
  ✅ 上传PDF账单
  ✅ 上传Excel文件
  ✅ 上传收据图片
  ✅ 录入基本信息
  ⚠️ 查看自己录入的数据
  ❌ 查看财务报表
  ❌ 生成报告
  ❌ 修改已验证的数据

典型使用场景:
  - 批量文件上传
  - 基础数据录入
  - 文档扫描上传
```

---

#### 5. Viewer（查看者）
**权限级别**: 最低  
**可访问资源**: 只读查看

```yaml
权限:
  ✅ 查看仪表板
  ✅ 查看财务报表
  ✅ 查看客户信息
  ❌ 上传文件
  ❌ 修改数据
  ❌ 生成报告
  ❌ 任何写操作

典型使用场景:
  - 管理层查看财务数据
  - 外部审计员只读访问
  - 临时访问权限
```

---

### 权限矩阵

| 功能 | Admin | Accountant | Loan Officer | Data Entry | Viewer |
|------|:-----:|:----------:|:------------:|:----------:|:------:|
| **用户管理** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **系统设置** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **审计日志** | ✅ | ✅ | ⚠️ | ❌ | ❌ |
| **财务报表** | ✅ | ✅ | ⚠️ | ❌ | ⚠️ |
| **银行对账单** | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| **贷款评估** | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| **上传文件** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **修改数据** | ✅ | ✅ | ⚠️ | ❌ | ❌ |

**图例**:
- ✅ 完全访问
- ⚠️ 部分访问/只读
- ❌ 无权访问

---

## 会计分录引擎

### 自动分录规则引擎

**功能**：根据预设规则自动生成会计分录

#### 规则配置示例

```json
{
  "rule_id": 1,
  "rule_name": "信用卡消费自动分录",
  "trigger": {
    "transaction_type": "DR",
    "source": "credit_card"
  },
  "actions": {
    "debit_account": "费用账户",
    "credit_account": "信用卡应付",
    "category_mapping": {
      "餐饮": "620100 - 餐饮费",
      "购物": "620200 - 办公用品",
      "交通": "620300 - 交通费",
      "其他": "620900 - 其他费用"
    }
  }
}
```

---

### 会计科目表（Chart of Accounts）

```yaml
资产类（1xxxx）:
  11000: 现金
  11100: 银行存款 - Maybank
  11101: 银行存款 - CIMB
  11102: 银行存款 - Public Bank
  12000: 应收账款
  13000: 存货

负债类（2xxxx）:
  21000: 应付账款
  21100: 信用卡应付 - AmBank
  21101: 信用卡应付 - UOB
  22000: 银行贷款

股东权益（3xxxx）:
  31000: 实收资本
  32000: 留存收益

收入类（4xxxx）:
  41000: 营业收入
  42000: 其他收入

费用类（6xxxx）:
  62010: 餐饮费
  62020: 办公用品
  62030: 交通费
  62040: 租金
  62050: 水电费
  62060: 通讯费
  62090: 其他费用
```

---

## 财务报表生成

### 报表生成流程

```yaml
Step 1: 选择报表类型
  - 损益表（P&L）
  - 资产负债表（Balance Sheet）
  - 现金流量表（Cash Flow）
  - 客户账本（Customer Ledger）
  - 供应商账龄（Suppliers Aging）

Step 2: 设置参数
  - 报表期间（开始日期 - 结束日期）
  - 公司ID
  - 比较期间（可选）

Step 3: 系统生成
  - 查询数据库
  - 执行计算
  - 应用格式

Step 4: 导出
  - Excel格式（专业格式）
  - PDF格式（打印版）
  - CSV格式（数据分析）
```

---

### 银行贷款报表包

**用途**：申请银行贷款时提交的财务报表

**包含内容**：
```yaml
1. 公司基本信息
   - 公司名称、注册号
   - 营业执照
   - 董事信息

2. 损益表（过去3年）
   - 2023年
   - 2024年
   - 2025年（至今）

3. 资产负债表（最近1年）
   - 期初
   - 期末

4. 现金流量表（最近1年）
   - 经营活动现金流
   - 投资活动现金流
   - 筹资活动现金流

5. 银行对账单（最近6个月）
   - 每月对账单
   - 余额证明

6. 应收应付明细
   - 客户账龄
   - 供应商账龄

7. 贷款用途说明
   - 资金需求
   - 还款计划
```

---

## SFTP ERP同步

### 功能概述

**自动化数据同步**到SQL ACC ERP系统

```yaml
同步频率: 每10分钟
同步方式: SFTP
目标系统: SQL ACC ERP Edition
数据格式: CSV（UTF-8编码）
```

---

### 导出的数据类型（7种）

```yaml
1. 客户主数据（Customers）
   - 客户代码、姓名
   - 联系方式
   - 银行账户信息

2. 信用卡数据（Credit Cards）
   - 卡号、银行名称
   - 信用额度
   - 持卡人信息

3. 交易记录（Transactions）
   - 交易日期、描述
   - 金额、类型（DR/CR）
   - 分类标签

4. 月度账本（Monthly Ledger）
   - Customer账本
   - INFINITE账本
   - 滚动余额

5. 供应商发票（Supplier Invoices）
   - 发票号、日期
   - 供应商名称
   - 金额、税额

6. CTOS报告（CTOS Reports）
   - 个人信用评分
   - 公司信用评分
   - 债务承诺数据

7. 审计日志（Audit Logs）
   - 操作类型、时间
   - 操作人、IP地址
   - 操作详情
```

---

### SFTP配置

```yaml
服务器配置:
  Host: erp.example.com
  Port: 22
  Protocol: SFTP
  Authentication: Username + Password

导出路径:
  /import/customers_{YYYYMMDD_HHMMSS}.csv
  /import/credit_cards_{YYYYMMDD_HHMMSS}.csv
  /import/transactions_{YYYYMMDD_HHMMSS}.csv
  /import/monthly_ledger_{YYYYMMDD_HHMMSS}.csv
  /import/supplier_invoices_{YYYYMMDD_HHMMSS}.csv
  /import/ctos_reports_{YYYYMMDD_HHMMSS}.csv
  /import/audit_logs_{YYYYMMDD_HHMMSS}.csv

文件格式:
  编码: UTF-8
  分隔符: 逗号（,）
  引号: 双引号（"）
  换行符: CRLF（\r\n）
```

---

### 同步状态监控

```yaml
监控指标:
  - 上次同步时间
  - 同步成功/失败次数
  - 导出文件数量
  - 数据行数
  - 错误日志

异常处理:
  - 连接失败 → 自动重试（最多3次）
  - 权限错误 → 发送通知给Admin
  - 磁盘空间不足 → 清理旧文件
  - 数据格式错误 → 跳过并记录日志
```

---

## API端点详解

### 认证相关
```
POST   /api/auth/login          - 用户登录
POST   /api/auth/logout         - 用户登出
GET    /api/auth/me             - 获取当前用户信息
POST   /api/auth/refresh        - 刷新Token
```

### 审计日志
```
GET    /api/audit-logs          - 查询审计日志
GET    /api/audit-logs/{id}     - 获取日志详情
POST   /api/audit-logs/upload-event - 记录上传事件（Flask调用）
```

### 银行对账单
```
POST   /api/bank-statements/upload      - 上传对账单
GET    /api/bank-statements             - 获取对账单列表
PUT    /api/bank-statements/{id}/verify - 验证对账单
POST   /api/bank-statements/{id}/post   - 入账
```

### 财务报表
```
POST   /api/reports/pl                  - 生成损益表
POST   /api/reports/balance-sheet       - 生成资产负债表
POST   /api/reports/cash-flow           - 生成现金流量表
POST   /api/reports/customer-ledger     - 生成客户账本
POST   /api/reports/suppliers-aging     - 生成供应商账龄
```

### 供应商管理
```
GET    /api/suppliers                   - 获取供应商列表
POST   /api/suppliers                   - 创建供应商
GET    /api/suppliers/{id}              - 获取供应商详情
PUT    /api/suppliers/{id}              - 更新供应商
DELETE /api/suppliers/{id}              - 删除供应商
GET    /api/suppliers/{id}/aging        - 获取供应商账龄
```

### SFTP同步
```
POST   /api/sftp/sync                   - 手动触发同步
GET    /api/sftp/status                 - 获取同步状态
GET    /api/sftp/history                - 获取同步历史
PUT    /api/sftp/config                 - 更新SFTP配置
```

---

## 常见问题

### Q1: Accountant和Admin的区别？
**A**: 
- **Admin**: 拥有所有权限，包括用户管理、系统设置
- **Accountant**: 拥有所有会计功能权限，但不能管理用户和系统设置

### Q2: 如何查看审计日志？
**A**: 
```
方式1: API调用
GET /api/audit-logs?company_id=1&limit=100

方式2: 管理后台
访问 http://localhost:8000/accounting → 审计日志页面
```

### Q3: SFTP同步失败怎么办？
**A**:
```yaml
Step 1: 检查SFTP配置
  - Host、Port正确？
  - 用户名、密码正确？

Step 2: 检查网络连接
  - 防火墙是否阻止？
  - SFTP服务器是否在线？

Step 3: 查看错误日志
  GET /api/sftp/history

Step 4: 手动重试
  POST /api/sftp/sync
```

### Q4: 如何生成银行贷款报表包？
**A**:
```yaml
Step 1: 准备数据
  - 上传过去3年的银行对账单
  - 上传供应商发票
  - 上传客户收款记录

Step 2: 生成报表
  - 损益表（3年）
  - 资产负债表（1年）
  - 现金流量表（1年）
  - 银行对账单汇总

Step 3: 导出PDF
  - 点击"生成贷款报表包"
  - 下载PDF文件
  - 提交给银行
```

---

**© 2025 CreditPilot - 会计与审计系统完整手册**
