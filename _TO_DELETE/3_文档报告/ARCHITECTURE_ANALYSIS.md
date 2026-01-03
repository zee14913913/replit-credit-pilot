# 📊 架构分析：文件解析 + 自动记账 + Management Report 系统

## 🎯 是否需要独立服务？

### **结论：可以安全地集成到现有系统，但需要增强基础设施**

### 分析依据：

#### ✅ **可以集成的理由：**

1. **上传频率可控**
   - 银行月结单：每月1-5次
   - 供应商发票：每天0-20次
   - POS日报：每天1次
   - 总计：每天<30次上传，完全可控

2. **存储量合理**
   - PDF文件：平均2-5MB/文件
   - 每月预计：50-100个文件
   - 月存储：100-500MB
   - 年存储：1-6GB（完全可接受）

3. **报表生成耗时**
   - Balance Sheet/P&L：<2秒
   - Management Report：<5秒
   - PDF生成：<10秒
   - 完全在可接受范围内

4. **技术栈统一**
   - 已有FastAPI框架
   - 已有PostgreSQL数据库
   - 已有文件管理基础
   - 无需额外微服务

#### ⚠️ **需要增强的部分：**

1. **异步处理**
   - PDF解析（特别是OCR）需要异步队列
   - 使用Celery + Redis（或直接用FastAPI Background Tasks）

2. **文件存储升级**
   - 从本地文件系统升级到规范的目录结构
   - 预留对象存储接口（未来可升级到S3/MinIO）

3. **错误处理增强**
   - 解析失败的文件进入待确认队列
   - 不能假装100%成功

4. **性能监控**
   - 添加文件处理时长监控
   - 添加存储空间监控

---

## 🏗️ 系统架构设计

### **整体架构图**

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (Flask Port 5000)            │
│  ┌──────────┬──────────┬──────────┬──────────┬────────────┐ │
│  │ 文件上传 │ 报表查看 │ 文件管理 │ 导出下载 │ 任务管理   │ │
│  └──────────┴──────────┴──────────┴──────────┴────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              业务逻辑层 (FastAPI Port 8000)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  文件解析服务                                         │  │
│  │  ├─ PDF Parser (文本PDF + OCR)                       │  │
│  │  ├─ CSV/Excel Parser                                 │  │
│  │  └─ 智能识别引擎                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  自动记账引擎                                         │  │
│  │  ├─ 银行月结单 → 会计分录                            │  │
│  │  ├─ 供应商发票 → 应付账款分录                        │  │
│  │  ├─ POS日报 → 销售收入分录                           │  │
│  │  └─ 规则匹配引擎                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  报表生成服务                                         │  │
│  │  ├─ Financial Reports (P&L, BS)                      │  │
│  │  ├─ Management Report                                │  │
│  │  ├─ Aging Reports (AR/AP)                            │  │
│  │  └─ PDF/CSV导出                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  文件管理服务                                         │  │
│  │  ├─ 统一文件存储                                      │  │
│  │  ├─ 目录规范管理                                      │  │
│  │  └─ 原件/成品分离                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据持久层 (PostgreSQL)                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ 核心财务 │ 文件索引 │ 待确认队 │ 客户供应 │ 分录日志 │  │
│  │   表     │   表     │   列     │   商表   │   表     │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  文件存储层 (Local/S3)                       │
│  /accounting_data/                                          │
│  ├─ originals/          (上传的原始文件)                    │
│  │  ├─ bank-statements/                                    │
│  │  ├─ supplier-invoices/                                  │
│  │  └─ pos-reports/                                        │
│  └─ generated/          (系统生成的文件)                    │
│     ├─ customer-invoices/                                  │
│     ├─ financial-reports/                                  │
│     └─ management-reports/                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 文件目录规范

### **统一文件结构**

```
/accounting_data/
├─ originals/                          # 原始上传文件
│  ├─ bank-statements/
│  │  └─ {company_id}/
│  │     └─ {year}/
│  │        └─ {month}/
│  │           └─ {bank}_{account}_{date}_{timestamp}.{pdf|csv}
│  ├─ supplier-invoices/
│  │  └─ {company_id}/
│  │     └─ {year}/
│  │        └─ {month}/
│  │           └─ {supplier_code}_{invoice_no}_{date}.{pdf|csv}
│  └─ pos-reports/
│     └─ {company_id}/
│        └─ {year}/
│           └─ {month}/
│              └─ pos_daily_{date}.{pdf|csv}
│
└─ generated/                          # 系统生成文件
   ├─ customer-invoices/
   │  └─ {company_id}/
   │     └─ {year}/
   │        └─ {month}/
   │           └─ INV{invoice_no}_{customer_code}.pdf
   ├─ financial-reports/
   │  └─ {company_id}/
   │     └─ {year}/
   │        └─ {month}/
   │           ├─ balance_sheet_{period}.pdf
   │           ├─ pnl_{period}.pdf
   │           └─ bank_package_{period}.pdf
   └─ management-reports/
      └─ {company_id}/
         └─ {year}/
            └─ {month}/
               └─ management_report_{period}.pdf
```

**命名规则说明：**
- `{company_id}`: 公司ID（例：1, 2, 3）
- `{year}`: 年份（例：2025）
- `{month}`: 月份（例：01, 02, 12）
- `{date}`: 完整日期（例：20250801）
- `{timestamp}`: 时间戳（例：103045）
- `{period}`: 期间（例：2025-08）

---

## 🗄️ 数据库表设计

### **新增表清单：**

1. **pending_documents** - 待人工确认的文档
2. **suppliers** - 供应商主数据
3. **customers** - 客户主数据
4. **purchase_invoices** - 采购发票
5. **sales_invoices** - 销售发票
6. **file_index** - 文件索引表
7. **processing_logs** - 文件处理日志

### **增强现有表：**

1. **journal_entries** - 增加来源类型字段
2. **journal_entry_lines** - 增加外键关联
3. **companies** - 增加文件配置字段

---

## 🔄 数据流转图

### **1. 银行月结单流程**

```
上传PDF/CSV
    ↓
PDF解析 (pdf_parser.py)
    ↓
提取交易明细
    ↓
写入 bank_statements
    ↓
规则匹配引擎 (bank_matcher.py)
    ↓
生成会计分录
    ↓
写入 journal_entries + journal_entry_lines
    ↓
可导出CSV分录文件
```

### **2. 供应商发票流程**

```
上传PDF/CSV
    ↓
PDF解析 + 提取发票信息
    ↓
重复检测 (supplier + invoice_no + date)
    ├─ 已存在 → 拒绝
    └─ 新发票 ↓
供应商匹配/创建
    ↓
写入 purchase_invoices
    ↓
生成应付账款分录
    ↓
更新 AP Aging
    ↓
原文件归档到 /originals/supplier-invoices/
```

### **3. POS日报流程**

```
上传CSV/PDF (每日营业报表)
    ↓
解析交易明细
    ↓
客户匹配 (customers表)
    ├─ 匹配成功 ↓
    └─ 匹配失败 → 进入 pending_documents
按客户汇总当日交易
    ↓
生成销售发票 (sales_invoices)
    ↓
生成PDF发票文件
    ↓
存储到 /generated/customer-invoices/
    ↓
生成收入会计分录
    ↓
更新 AR Aging
```

### **4. Management Report生成流程**

```
指定期间 (例: 2025-08)
    ↓
查询当月 P&L 数据
    ↓
查询当月末 Balance Sheet
    ↓
查询 AR/AP Aging
    ↓
查询银行账户余额汇总
    ↓
查询未匹配项 (pending_documents)
    ↓
汇总成 JSON 数据
    ↓
生成 PDF 报告 (ReportLab)
    ↓
存储到 /generated/management-reports/
    ↓
返回下载链接
```

---

## 🔑 关键技术选型

### **PDF处理**
```python
# 文本型PDF
import pdfplumber

# OCR扫描件
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
```

### **PDF生成**
```python
# 专业报表生成
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
```

### **异步任务（可选）**
```python
# 方案1：FastAPI Background Tasks (简单场景)
from fastapi import BackgroundTasks

# 方案2：Celery + Redis (复杂场景)
from celery import Celery
```

---

## 📋 实施优先级

### **Phase 1: 核心基础（1-2天）**
1. 数据库建表SQL
2. PDF解析服务
3. 文件管理统一接口
4. pending_documents队列

### **Phase 2: 银行月结单增强（1天）**
1. PDF上传支持
2. CSV分录导出接口

### **Phase 3: 供应商发票（1-2天）**
1. 供应商表+发票表
2. 上传解析路由
3. AP分录生成
4. Aging更新

### **Phase 4: POS日报（1-2天）**
1. 客户表+销售发票表
2. POS解析路由
3. 发票PDF生成
4. AR分录生成

### **Phase 5: Management Report（2-3天）**
1. 数据汇总逻辑
2. PDF模板设计
3. JSON/PDF双输出
4. 未匹配项展示

### **Phase 6: 自动化与优化（1天）**
1. 定时任务扩展
2. 测试与文档
3. 性能优化

---

## ⚙️ 环境变量配置

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/accounting_db

# 文件存储
FILES_BASE_DIR=/accounting_data
MAX_FILE_SIZE_MB=50

# PDF处理
PDF_DPI=300
OCR_LANGUAGE=eng+chi_sim
ENABLE_OCR=true

# PDF生成
REPORT_LOGO_PATH=/static/company_logo.png
REPORT_COMPANY_NAME="Your Company Ltd"

# 任务调度
ENABLE_SCHEDULED_TASKS=true
TASK_SECRET_TOKEN=your-secret-token

# 性能设置
MAX_CONCURRENT_UPLOADS=5
ASYNC_PROCESSING=true
```

---

## ✅ 总结

### **推荐方案：集成到现有系统**

**优点：**
- 代码库统一，易维护
- 数据一致性好
- 无需额外部署
- 成本低

**需要注意：**
- 添加异步处理（PDF解析）
- 规范文件存储结构
- 完善错误处理
- 添加性能监控

**扩展路径：**
- 初期：集成到现有FastAPI
- 中期（文件量>10000/月）：考虑独立文件处理服务
- 长期（多租户）：微服务架构 + 对象存储

当前阶段完全适合集成方案！
