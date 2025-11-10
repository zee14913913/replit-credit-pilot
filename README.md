# Smart Credit & Loan Manager

## 🚀 快速开始

### 📚 重要文档位置（永久固定）

#### ⭐ 3个核心文档（永不移动）

1. **系统操作圣经**  
   📄 `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`  
   包含所有录入、验证、分类规则

2. **系统记忆**  
   📄 `replit.md`  
   记录所有变更历史和架构决策

3. **文档索引**  
   📄 `DOCUMENTATION_INDEX.md`  
   快速查找所有文档的位置

---

## 🔍 想要查找...

- **如何录入账单？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **7个供应商是哪些？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **OWNER vs INFINITE怎么分？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **文件命名规则？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **系统有什么功能？** → `docs/core/系统功能完整清单.md`
- **最新变更记录？** → `replit.md`
- **所有文档位置？** → `DOCUMENTATION_INDEX.md`

---

## 🎯 核心规则速查

### 1️⃣ 一家银行一个月 = 一条记录
- 同一客户，同一银行，同一月份，无论有几张卡，都合并成一条记录

### 2️⃣ 7个固定供应商（GZ's Expenses）
1. 7SL
2. HUAWEI
3. PASAR RAYA
4. DINAS
5. RAUB SYC HAINAN
6. AI SMART TECH
7. PUCHONG HERBS

### 3️⃣ 文件命名标准
- 格式：`BankName_YYYY-MM-DD.pdf`
- 例如：`AllianceBank_2024-09-12.pdf`
- ❌ 不要加卡号后4位

### 4️⃣ 3色严格限制
- **Black** (#000000): 背景
- **Hot Pink** (#FF007F): 收入、付款、CR
- **Dark Purple** (#322446): 支出、消费、DR

### 5️⃣ 100%准确性要求
- 手动逐笔验证，零容差
- 系统必须1:1复刻PDF内容
- 所有负数保持负号显示

---

## 🖥️ 启动系统

```bash
python app.py
```

访问：http://localhost:5000

---

## 📁 项目结构

```
项目根目录/
├── README.md                      ⭐ 本文件（快速访问入口）
├── DOCUMENTATION_INDEX.md         ⭐ 文档索引（永久固定）
├── replit.md                      ⭐ 系统记忆（永久固定）
├── docs/
│   ├── CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md  ⭐ 标准文档（永久固定）
│   ├── FILE_STORAGE_ARCHITECTURE.md
│   ├── CLEANUP_SUMMARY_2025-10-26.md
│   ├── business/      （业务文档）
│   ├── core/          （核心技术文档）
│   ├── deployment/    （部署文档）
│   ├── features/      （功能文档）
│   └── archived/      （归档文件）
├── app.py             （主程序）
├── db/                （数据库）
├── templates/         （HTML模板）
├── static/            （静态文件和上传文件）
├── services/          （业务逻辑）
├── ingest/            （PDF解析）
├── validate/          （数据验证）
├── scripts/           （工具脚本）
└── batch_scripts/     （批量操作脚本）
```

---

## 🎉 最新成就

✅ **Chang Choon Chow - Alliance Bank**  
12个月账单（2024年9月 - 2025年8月）已100%录入完成  
- 87笔交易全部验证通过
- INFINITE消费：RM 29,298.00
- Own's Balance: -RM 19,293.54
- GZ Balance: RM 29,298.00
- 最终余额：RM 10,004.46

---

**最后更新**：2025年10月26日

---

## 🏢 Enterprise Features - Accounting API (Port 8000)

### Enterprise-3: 表驱动规则引擎 (Auto-Posting Rules)

**核心功能**：将硬编码的交易匹配逻辑转换为数据库驱动的规则引擎

#### 📍 API端点

```
POST   /api/posting-rules          # 创建规则
GET    /api/posting-rules          # 获取规则列表（分页+过滤）
GET    /api/posting-rules/{id}     # 获取单条规则
PUT    /api/posting-rules/{id}     # 更新规则
DELETE /api/posting-rules/{id}     # 删除规则
POST   /api/posting-rules/test     # 测试规则匹配
```

#### 🔑 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `rule_name` | string | 规则名称（公司内唯一）|
| `source_type` | string | 数据源类型（bank_import, supplier_invoice, pos_report）|
| `match_pattern` | string | 匹配模式（关键词或正则）|
| `is_regex` | boolean | 是否为正则表达式 |
| `priority` | integer | 优先级（1-100，数字越大优先级越高）|
| `debit_account_code` | string | 借方科目代码 |
| `credit_account_code` | string | 贷方科目代码 |

#### 📦 预装规则（20条）

涵盖常见交易场景：工资、EPF、SOCSO、租金、水电、销售、采购等

#### 🚀 技术特性

- **智能缓存**：按source_type缓存，自动失效
- **优先级排序**：支持1-100优先级
- **正则支持**：支持关键词和正则表达式
- **租户隔离**：自动注入company_id
- **审计追踪**：记录创建者、时间和使用统计

---

### Enterprise-4: 表驱动导出模板系统 (CSV Export Templates)

**核心功能**：将硬编码的CSV导出格式转换为数据库驱动的模板系统

#### 📍 API端点

```
POST   /api/export-templates          # 创建模板
GET    /api/export-templates          # 获取模板列表
GET    /api/export-templates/{id}     # 获取单个模板
PUT    /api/export-templates/{id}     # 更新模板
DELETE /api/export-templates/{id}     # 删除模板
POST   /api/export-templates/test     # 测试模板导出
```

#### 🔑 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `template_name` | string | 模板名称（公司内唯一）|
| `software_name` | string | 目标软件（SQL Account, AutoCount, UBS, Generic）|
| `export_type` | string | 导出类型（general_ledger, journal_entry）|
| `column_mappings` | JSONB | 字段映射配置 |
| `date_format` | string | 日期格式 |
| `decimal_places` | integer | 小数位数 |

#### 📦 预装模板（8个）

| 软件 | 类型 | 模板名称 |
|------|------|----------|
| SQL Account | general_ledger | SQL Account - General Ledger |
| SQL Account | journal_entry | SQL Account - Journal Entry |
| AutoCount | general_ledger | AutoCount - General Ledger |
| AutoCount | trial_balance | AutoCount - Trial Balance |
| UBS | general_ledger | UBS - General Ledger |
| Generic | general_ledger | Generic - General Ledger |
| Generic | chart_of_accounts | Generic - Chart of Accounts |

#### 🚀 使用示例

**使用模板导出CSV**：
```bash
GET /api/export/journal/csv?period=2025-10&template_id=5
```

---

## 🔐 Enterprise安全特性

### 多租户隔离
- 所有API自动注入`company_id`
- 双重过滤：`id` + `company_id`
- 数据完全隔离

### 审计追踪
- 创建者（created_by）
- 创建时间（created_at）
- 更新时间（updated_at）
- 使用统计（match_count / usage_count）

---
