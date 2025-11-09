# 🏦 马来西亚68家金融机构贷款数据采集系统

## 📋 系统概览

### **覆盖范围**

**金融机构（68家）**：
- ✅ 27家商业银行 (Commercial Banks)
- ✅ 16家伊斯兰银行 (Islamic Banks)
- ✅ 6家发展金融机构 (Development Financial Institutions)
- ✅ 5家数字银行 (Digital Banks)
- ✅ 10家P2P平台 (P2P Platforms)
- ✅ 4家非银行信贷提供商 (Non-Bank Credit Providers)

**贷款产品类型（7种）**：
1. 房贷 (Home Loan)
2. 再融资贷款 (Refinance Loan)
3. 个人贷款 (Personal Loan)
4. 债务整合 (Debt Consolidation)
5. 企业贷款 (Business Loan)
6. 中小企业贷款 (SME Loan)
7. 其他融资 (Other Financing)

---

## 🚀 快速开始

### **方式1：使用演示数据（默认，立即可用）**

```bash
# 系统默认使用演示数据，无需配置
# 服务器启动后自动生成3个演示贷款产品
```

### **方式2：启用真实数据采集（68家金融机构）**

#### **步骤1：配置环境变量**

在 Replit Secrets 中添加：

```bash
Key:   USE_REAL_LOAN_DATA
Value: true
```

#### **步骤2：重启服务器**

```bash
# 服务器会自动开始采集真实数据
# 首次采集时间：约5-10分钟（68家机构并发爬取）
```

#### **步骤3：验证数据**

访问以下端点查看数据：

```bash
GET /loans/updates              # 查看所有贷款产品
GET /loans/updates?q=maybank    # 搜索Maybank产品
GET /loans/updates?q=home       # 搜索房贷产品
```

---

## 🛠️ API接口

### **1. 查看贷款产品**

```http
GET /loans/updates?q={keyword}&limit={count}
```

**示例**：
```bash
# 查看所有产品
curl https://your-app.replit.app/loans/updates

# 查看Maybank产品
curl https://your-app.replit.app/loans/updates?q=maybank

# 查看房贷产品
curl https://your-app.replit.app/loans/updates?q=home
```

**响应示例**：
```json
[
  {
    "id": 1,
    "source": "maybank",
    "bank": "Malayan Banking Berhad (Maybank)",
    "product": "Home Loan Flexi",
    "type": "HOME",
    "rate": "3.75%",
    "summary": "灵活房贷方案，支持提前还款",
    "pulled_at": "2025-11-09T04:00:00+00:00"
  },
  {
    "id": 2,
    "source": "cimb",
    "bank": "CIMB Bank Berhad",
    "product": "Personal Loan",
    "type": "PERSONAL",
    "rate": "6.88%",
    "summary": "快速批核个人贷款",
    "pulled_at": "2025-11-09T04:00:00+00:00"
  }
]
```

---

### **2. 手动刷新数据**

```http
POST /loans/updates/refresh
Headers:
  X-Refresh-Key: {LOANS_REFRESH_KEY}
```

**配置刷新密钥**：

在 Replit Secrets 中设置：

```bash
Key:   LOANS_REFRESH_KEY
Value: your_secret_refresh_key_12345
```

**示例**：
```bash
curl -X POST \
  https://your-app.replit.app/loans/updates/refresh \
  -H "X-Refresh-Key: your_secret_refresh_key_12345"
```

**响应**：
```json
{
  "refreshed": true,
  "at": "2025-11-09T04:00:00+00:00",
  "products_count": 156,
  "institutions_count": 68
}
```

---

### **3. 导出CSV**

```http
GET /loans/updates/export.csv?q={keyword}
```

**示例**：
```bash
# 导出所有产品
curl https://your-app.replit.app/loans/updates/export.csv > loans.csv

# 导出Maybank产品
curl "https://your-app.replit.app/loans/updates/export.csv?q=maybank" > maybank_loans.csv
```

---

## 📊 数据源说明

### **真实数据源（USE_REAL_LOAN_DATA=true）**

#### **第1层：BNM官方API（政府公开数据）**

- **来源**: Bank Negara Malaysia (马来西亚央行)
- **端点**: `https://api.bnm.gov.my`
- **数据**: 
  - 隔夜政策利率 (OPR)
  - 基准利率 (Base Rates)
  - 基准贷款利率 (BLR)
- **费用**: 免费
- **API密钥**: 不需要

#### **第2层：68家金融机构网站爬虫**

**商业银行（16家主要银行）**：
- Maybank (马来亚银行)
- CIMB Bank
- Public Bank
- RHB Bank
- Hong Leong Bank
- HSBC Malaysia
- OCBC Malaysia
- UOB Malaysia
- AmBank
- Affin Bank
- Alliance Bank
- Standard Chartered Malaysia
- Bank of China Malaysia
- ICBC Malaysia
- Bangkok Bank
- 等...

**伊斯兰银行（16家）**：
- Maybank Islamic
- CIMB Islamic
- Bank Islam Malaysia
- Bank Muamalat Malaysia
- Public Islamic Bank
- RHB Islamic Bank
- HSBC Amanah
- Kuwait Finance House Malaysia
- 等...

**数字银行（5家）**：
- GX Bank (Grab × Singtel)
- Boost Bank (Axiata × RHB)
- AEON Bank
- KAF Digital Bank
- YTL Digital Bank (Ryt Bank)

**P2P平台（10家）**：
- Funding Societies Malaysia
- CapBay
- Finpal
- CapSphere
- microLEAP
- QuicKash
- MoneySave
- Fundaztic
- Cofundr
- Alixco

**其他金融机构**：
- 6家发展金融机构 (SME Bank, EXIM Bank, Bank Rakyat等)
- 4家非银行信贷提供商 (AEON Credit, BigPay, Grab Finance)

---

## ⚙️ 高级配置

### **环境变量完整清单**

```bash
# 数据源配置
USE_REAL_LOAN_DATA=true          # 启用真实数据采集（默认：false）

# 数据库路径
LOANS_DB_PATH=/home/runner/loans.db  # SQLite数据库路径

# 刷新设置
MIN_REFRESH_HOURS=20             # 最小刷新间隔（小时）
LOANS_REFRESH_KEY=secret_key     # API刷新密钥

# BNM API（无需配置，公开API）
# 系统会自动调用 https://api.bnm.gov.my
```

---

## 🔧 数据采集流程

### **自动化流程（启用真实数据时）**

```
1. 系统启动
   ↓
2. 检查上次采集时间
   ↓
3. 如果 > MIN_REFRESH_HOURS（默认20小时）
   ↓
4. 开始并发爬取：
   ├─ 获取BNM官方利率
   ├─ 爬取27家商业银行
   ├─ 爬取16家伊斯兰银行
   ├─ 爬取6家发展金融机构
   ├─ 爬取5家数字银行
   ├─ 爬取10家P2P平台
   └─ 爬取4家非银行机构
   ↓
5. 数据验证与清洗
   ↓
6. 存储到SQLite数据库
   ↓
7. 导出CSV备份
   ↓
8. 完成（约5-10分钟）
```

---

## 📈 性能优化

### **并发爬取**

系统使用线程池并发爬取，默认10个并发线程：

```python
# 修改并发数（在 comprehensive_loan_scraper.py）
comprehensive_scraper.scrape_all_institutions(max_workers=20)
```

### **数据缓存**

- 默认缓存时间：20小时
- 修改方法：设置环境变量 `MIN_REFRESH_HOURS`

### **爬虫礼貌性**

- 每个请求间隔：0.5-1秒
- 避免对银行网站造成压力
- 遵守robots.txt规则

---

## 🛡️ 数据质量保证

### **验证机制**

1. **必需字段检查**：
   - source（来源代码）
   - bank（银行名称）
   - product（产品名称）
   - type（贷款类型）

2. **利率格式标准化**：
   - 自动提取百分比格式
   - 支持基准利率格式（BR+2.5%, BLR-1.0%）
   - 未找到利率时标记为"Contact Bank"

3. **重复数据去除**：
   - 按 source + product 去重
   - 保留最新数据

### **错误处理**

- 单个机构失败不影响整体
- 自动重试机制
- 失败时回退到演示数据
- 详细日志记录

---

## 📁 数据存储

### **SQLite数据库结构**

```sql
-- 贷款产品表
CREATE TABLE loan_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,           -- 机构代码（maybank, cimb, etc.）
    bank TEXT,             -- 银行全称
    product TEXT,          -- 产品名称
    type TEXT,             -- 贷款类型（HOME, PERSONAL, BUSINESS等）
    rate TEXT,             -- 利率
    summary TEXT,          -- 产品摘要
    pulled_at TEXT         -- 采集时间
);

-- 元数据表
CREATE TABLE loan_meta_kv (
    k TEXT PRIMARY KEY,
    v TEXT
);
```

### **数据导出**

系统会自动导出CSV文件：

```bash
/home/runner/malaysia_loans_export.csv
```

CSV格式：
```csv
source,bank,product,type,rate,summary,pulled_at
maybank,Malayan Banking Berhad,Home Loan Flexi,HOME,3.75%,灵活房贷方案,2025-11-09T04:00:00
cimb,CIMB Bank Berhad,Personal Loan,PERSONAL,6.88%,快速批核,2025-11-09T04:00:00
```

---

## 🚨 故障排查

### **问题1：采集失败**

**症状**：日志显示"真实数据采集失败"

**解决方案**：
1. 检查网络连接
2. 验证银行网站是否可访问
3. 查看详细日志：`/tmp/logs/FastAPI_Server_*.log`
4. 系统会自动回退到演示数据

### **问题2：数据为空**

**症状**：API返回空列表

**解决方案**：
1. 检查 `USE_REAL_LOAN_DATA` 环境变量
2. 手动触发刷新：`POST /loans/updates/refresh`
3. 查看数据库文件：`loans.db`

### **问题3：爬取速度慢**

**解决方案**：
1. 增加并发线程数（默认10）
2. 减少爬取机构数量（测试用）
3. 检查网络带宽

---

## 📝 使用示例

### **示例1：查看所有Maybank产品**

```bash
curl "https://your-app.replit.app/loans/updates?q=maybank&limit=50"
```

### **示例2：查看所有房贷产品**

```bash
curl "https://your-app.replit.app/loans/updates?q=home&limit=100"
```

### **示例3：每日自动刷新（Cron Job）**

```bash
# 添加到crontab
0 2 * * * curl -X POST https://your-app.replit.app/loans/updates/refresh \
  -H "X-Refresh-Key: your_secret_key"
```

---

## 🎯 生产部署建议

### **推荐配置**

```bash
# 启用真实数据
USE_REAL_LOAN_DATA=true

# 每天刷新一次（24小时）
MIN_REFRESH_HOURS=24

# 设置强密码
LOANS_REFRESH_KEY=strong_random_password_123456

# 数据库路径
LOANS_DB_PATH=/home/runner/loans.db
```

### **监控建议**

1. 监控采集成功率
2. 设置采集失败告警
3. 定期检查数据质量
4. 备份CSV导出文件

---

## 📞 技术支持

如遇到问题，请查看：

1. **日志文件**: `/tmp/logs/FastAPI_Server_*.log`
2. **数据库**: `/home/runner/loans.db`
3. **导出文件**: `/home/runner/malaysia_loans_export.csv`

---

## 🎉 总结

✅ **68家金融机构** - 覆盖马来西亚全部主要银行  
✅ **7种贷款类型** - 房贷、个人贷款、企业贷款等  
✅ **真实BNM数据** - 官方央行利率数据  
✅ **自动化采集** - 每日自动更新  
✅ **数据导出** - CSV格式，易于分析  
✅ **生产就绪** - 完整错误处理和日志记录  

**系统现在可以一键获取马来西亚全部真实贷款数据！** 🚀
