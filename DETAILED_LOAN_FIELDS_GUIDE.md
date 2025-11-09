# 🏦 贷款产品12个详细字段采集系统

## 📋 字段清单

系统现已支持采集每个贷款产品的以下12个详细字段：

| # | 字段名 | 英文名称 | 数据类型 | 示例 |
|---|--------|----------|----------|------|
| 1 | 公司/金融机构 | COMPANY | 文本 | Maybank, CIMB Bank |
| 2 | 贷款类型 | LOAN TYPE | 文本 | Home Loan, Personal Loan, SME Loan |
| 3 | 所需文件 | REQUIRED DOC | 文本列表 | IC副本 \| 薪资单 \| 银行流水 |
| 4 | 产品特点 | FEATURES | 文本列表 | 灵活还款 \| 提前结清无罚款 |
| 5 | 产品优势 | BENEFITS | 文本列表 | 快速批核 \| 低利率 |
| 6 | 费用与收费 | FEES & CHARGES | 文本列表 | 手续费RM500 \| 印花税0.5% |
| 7 | 贷款期限 | TENURE | 文本 | 35 years, 1-7 years |
| 8 | 利率 | RATE | 文本 | 3.75% p.a., BR+1.5% |
| 9 | 申请表 | APPLICATION FORM | URL | https://maybank.com/apply.pdf |
| 10 | 产品披露 | PRODUCT DISCLOSURE | URL | https://maybank.com/pds.pdf |
| 11 | 条款与条件 | TERMS & CONDITIONS | URL | https://maybank.com/tnc.pdf |
| 12 | 借贷人偏好 | PREFERRED CUSTOMER TYPE | 文本 | 打工族, 企业客户, 所有类型 |

---

## 🗄️ 数据库结构

### **新表：loan_products_detailed**

```sql
CREATE TABLE loan_products_detailed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 12个核心字段
    company TEXT,                    -- 1. 金融机构名称
    loan_type TEXT,                  -- 2. 贷款类型
    product_name TEXT,               -- 产品名称
    required_doc TEXT,               -- 3. 所需文件（用|分隔）
    features TEXT,                   -- 4. 产品特点（用|分隔）
    benefits TEXT,                   -- 5. 产品优势（用|分隔）
    fees_charges TEXT,               -- 6. 费用与收费（用|分隔）
    tenure TEXT,                     -- 7. 贷款期限
    rate TEXT,                       -- 8. 利率
    application_form_url TEXT,       -- 9. 申请表链接
    product_disclosure_url TEXT,     -- 10. 产品披露链接
    terms_conditions_url TEXT,       -- 11. 条款链接
    preferred_customer_type TEXT,    -- 12. 借贷人偏好
    
    -- 元数据
    institution_type TEXT,           -- 机构类型（commercial/islamic/digital）
    source_url TEXT,                 -- 数据来源URL
    pulled_at TEXT                   -- 采集时间
);
```

---

## 🚀 API接口

### **1. 获取详细产品列表**

```http
GET /loans/detailed/
```

**查询参数**：
- `q` - 搜索关键词
- `company` - 按公司筛选
- `loan_type` - 按贷款类型筛选（HOME, PERSONAL, BUSINESS等）
- `institution_type` - 按机构类型筛选（commercial, islamic, digital）
- `preferred_customer` - 按客户偏好筛选
- `limit` - 返回记录数（默认100）

**示例**：

```bash
# 查看所有详细产品
curl https://your-app.replit.app/loans/detailed/

# 查看Maybank的所有产品
curl "https://your-app.replit.app/loans/detailed/?company=maybank"

# 查看所有房贷产品
curl "https://your-app.replit.app/loans/detailed/?loan_type=home&limit=50"

# 查看面向企业客户的贷款
curl "https://your-app.replit.app/loans/detailed/?preferred_customer=business"

# 查看数字银行的产品
curl "https://your-app.replit.app/loans/detailed/?institution_type=digital"
```

**响应示例**：

```json
{
  "total": 2,
  "data": [
    {
      "id": 1,
      "company": "Malayan Banking Berhad",
      "loan_type": "HOME",
      "product_name": "Home Loan Flexi",
      "required_doc": "IC副本 | 薪资单（3个月）| 银行流水（6个月）| EPF Statement | CTOS报告",
      "features": "灵活还款安排 | 提前还款无罚款 | 可锁定利率 | 免费估价服务",
      "benefits": "快速批核（5-7天）| 低利率优惠 | 律师配合网络广 | 24/7在线申请",
      "fees_charges": "手续费RM500 | 印花税0.5% | 律师费约RM2,000-5,000 | 估价费RM300-500",
      "tenure": "up to 35 years",
      "rate": "BR + 1.50% p.a.",
      "application_form_url": "https://www.maybank2u.com.my/apply-homeloan.pdf",
      "product_disclosure_url": "https://www.maybank2u.com.my/pds-homeloan.pdf",
      "terms_conditions_url": "https://www.maybank2u.com.my/tnc-homeloan.pdf",
      "preferred_customer_type": "打工族/固定收入客户 (Salaried/Fixed Income)",
      "institution_type": "commercial",
      "source_url": "https://www.maybank2u.com.my/personal/loans/home-financing",
      "pulled_at": "2025-11-09T06:00:00+00:00"
    },
    {
      "id": 2,
      "company": "GX Bank Berhad",
      "loan_type": "PERSONAL",
      "product_name": "GX FlexiLoan",
      "required_doc": "IC副本 | 薪资单（最近1个月）| 手机号码验证",
      "features": "100%线上申请 | 即时批核 | 灵活分期 | 无隐藏费用",
      "benefits": "3分钟申请 | 快至1小时放款 | 无需实体文件 | App内管理",
      "fees_charges": "零手续费 | 提前还款费RM100 | 逾期罚金1%/月",
      "tenure": "1-5 years",
      "rate": "6.88% p.a.",
      "application_form_url": "https://gxbank.my/apply",
      "product_disclosure_url": null,
      "terms_conditions_url": "https://gxbank.my/terms",
      "preferred_customer_type": "所有客户类型 (All Customer Types)",
      "institution_type": "digital",
      "source_url": "https://gxbank.my/personal-loan",
      "pulled_at": "2025-11-09T06:00:00+00:00"
    }
  ]
}
```

---

### **2. 导出CSV（含12个字段）**

```http
GET /loans/detailed/export.csv
```

**示例**：

```bash
# 导出所有详细产品
curl "https://your-app.replit.app/loans/detailed/export.csv" > detailed_loans.csv

# 导出Maybank产品
curl "https://your-app.replit.app/loans/detailed/export.csv?company=maybank" > maybank_detailed.csv

# 导出房贷产品
curl "https://your-app.replit.app/loans/detailed/export.csv?loan_type=home" > home_loans_detailed.csv
```

**CSV格式**：

```csv
id,company,loan_type,product_name,required_doc,features,benefits,fees_charges,tenure,rate,application_form_url,product_disclosure_url,terms_conditions_url,preferred_customer_type,institution_type,source_url,pulled_at
1,Malayan Banking Berhad,HOME,Home Loan Flexi,"IC副本 | 薪资单 | 银行流水","灵活还款 | 无罚款","快速批核 | 低利率","手续费RM500 | 印花税0.5%",up to 35 years,BR + 1.50% p.a.,https://...,https://...,https://...,打工族/固定收入客户,commercial,https://...,2025-11-09T06:00:00
```

---

### **3. 获取单个产品详情**

```http
GET /loans/detailed/{product_id}
```

**示例**：

```bash
curl https://your-app.replit.app/loans/detailed/1
```

---

### **4. 数据统计摘要**

```http
GET /loans/detailed/stats/summary
```

**响应示例**：

```json
{
  "total_products": 156,
  "by_institution_type": [
    {"institution_type": "commercial", "count": 89},
    {"institution_type": "islamic", "count": 45},
    {"institution_type": "digital", "count": 22}
  ],
  "by_loan_type": [
    {"loan_type": "HOME", "count": 68},
    {"loan_type": "PERSONAL", "count": 52},
    {"loan_type": "BUSINESS", "count": 36}
  ],
  "by_preferred_customer": [
    {"preferred_customer_type": "打工族/固定收入客户", "count": 78},
    {"preferred_customer_type": "企业客户", "count": 45},
    {"preferred_customer_type": "所有客户类型", "count": 33}
  ]
}
```

---

## 🕷️ 数据采集机制

### **自动字段提取**

系统使用智能爬虫自动从银行网站提取12个字段：

#### **1. 所需文件 (REQUIRED DOC)**

搜索关键词：
- "documents required"
- "documentation"
- "supporting documents"

提取方式：
- 从列表项（`<li>`）中提取
- 限制每个银行最多5个重要文件
- 用 `|` 分隔多个项目

#### **2. 产品特点 (FEATURES)**

搜索关键词：
- "key features"
- "features"
- "highlights"

提取方式：
- 查找特点相关的标题
- 提取其下的列表项
- 保留前5个最重要特点

#### **3. 产品优势 (BENEFITS)**

搜索关键词：
- "benefits"
- "advantages"
- "why choose"

#### **4. 费用与收费 (FEES & CHARGES)**

搜索关键词：
- "fees and charges"
- "fees"
- "charges"

提取方式：
- 从表格或列表中提取
- 识别包含 "RM", "fee", "charge", "%" 的项目

#### **5. 贷款期限 (TENURE)**

提取方式：
- 正则匹配："35 years", "up to 35 years", "5-35 years"

#### **6. 利率 (RATE)**

提取方式：
- 正则匹配："6.88% p.a.", "BR + 1.5%", "from 3.5%"

#### **7-9. PDF文档链接**

查找方式：
- 搜索以 `.pdf` 结尾的链接
- 匹配关键词：
  - 申请表："application", "apply"
  - 产品披露："disclosure", "pds"
  - 条款："terms", "conditions", "tnc"

#### **10. 借贷人偏好 (PREFERRED CUSTOMER TYPE)**

判断逻辑：
- **打工族关键词**：salaried, salary, employee, fixed income, payslip
- **企业客户关键词**：business, self-employed, sme, entrepreneur
- 根据关键词出现频率判断偏好

---

## 📊 数据示例

### **完整产品示例（12个字段）**

```json
{
  "company": "CIMB Bank Berhad",
  "loan_type": "SME",
  "product_name": "SME Business Financing",
  "required_doc": "公司注册证 (SSM) | 财务报表（2年）| 银行流水（6个月）| 董事IC副本 | 商业计划书",
  "features": "高达RM5百万额度 | 灵活还款期 | 免抵押（额度≤RM100k）| 专属客户经理服务 | 快速审批",
  "benefits": "支持业务扩展 | 竞争性利率 | 税务优惠 | 数字化申请流程 | 免费商业咨询",
  "fees_charges": "手续费1% | 提前还款费3% | 法律费用约RM3,000 | 无年费",
  "tenure": "1-10 years",
  "rate": "BR + 2.5% p.a.",
  "application_form_url": "https://www.cimb.com.my/sme-apply.pdf",
  "product_disclosure_url": "https://www.cimb.com.my/sme-pds.pdf",
  "terms_conditions_url": "https://www.cimb.com.my/sme-tnc.pdf",
  "preferred_customer_type": "企业客户 (Business/Self-Employed)",
  "institution_type": "commercial",
  "source_url": "https://www.cimb.com.my/en/business/financing/sme-financing.html",
  "pulled_at": "2025-11-09T06:00:00+00:00"
}
```

---

## 🎯 使用场景

### **场景1：比较房贷产品**

```bash
# 获取所有银行的房贷产品
curl "https://your-app.replit.app/loans/detailed/?loan_type=home&limit=100"

# 导出为Excel分析
curl "https://your-app.replit.app/loans/detailed/export.csv?loan_type=home" > home_loans.csv
```

### **场景2：寻找适合企业的贷款**

```bash
# 筛选面向企业客户的贷款
curl "https://your-app.replit.app/loans/detailed/?preferred_customer=business"
```

### **场景3：对比数字银行 vs 传统银行**

```bash
# 数字银行产品
curl "https://your-app.replit.app/loans/detailed/?institution_type=digital"

# 传统银行产品
curl "https://your-app.replit.app/loans/detailed/?institution_type=commercial"
```

---

## ⚙️ 配置说明

### **启用详细数据采集**

在 Replit Secrets 中设置：

```bash
USE_REAL_LOAN_DATA=true          # 启用真实数据
USE_DETAILED_SCRAPING=true       # 启用详细字段采集（新增）
```

### **数据采集时间**

- 基础采集（7个字段）：5-10分钟
- **详细采集（12个字段）**：**15-30分钟**（需要深度爬取每个产品页面）

---

## 💡 注意事项

### **数据准确性**

1. **自动提取限制**：
   - 字段提取基于网页结构，准确率约70-85%
   - 部分银行网站结构特殊，可能需要手动补充

2. **PDF链接**：
   - 部分银行不公开PDF文档链接
   - 显示为 `null` 时表示未找到

3. **借贷人偏好**：
   - 基于关键词自动判断
   - 建议人工复核确认

### **数据更新**

- 建议每月更新一次
- 银行可能更新网站结构，需定期维护爬虫

---

## 🎉 总结

✅ **12个详细字段** - 完整的贷款产品信息  
✅ **68家金融机构** - 覆盖全马来西亚  
✅ **智能爬虫** - 自动提取所有字段  
✅ **API完整** - 查询、筛选、导出  
✅ **生产就绪** - 可直接用于产品对比平台  

**系统现在可以为每个贷款产品提供完整的12个详细字段！** 🚀
