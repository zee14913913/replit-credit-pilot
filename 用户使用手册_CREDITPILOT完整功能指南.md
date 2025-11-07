# CreditPilot 完整功能使用手册
**版本**: 1.0 | **更新日期**: 2025年11月7日

---

## 📖 目录

1. [信用卡管理模块](#1-信用卡管理模块)
2. [企业发票生成系统](#2-企业发票生成系统)
3. [智能贷款匹配系统](#3-智能贷款匹配系统)
4. [CTOS信用报告解析](#4-ctos信用报告解析)
5. [系统管理工具](#5-系统管理工具)
6. [数据库管理](#6-数据库管理)

---

## 1. 信用卡管理模块

### 1.1 交易明细管理

#### **功能描述**
管理和查看信用卡交易记录，自动分类为OWNER（个人）和INFINITE（公司）两种类型。

#### **访问方式**
```
URL: http://localhost:5000/credit-cards/transactions
方法: GET (浏览器直接访问)
```

#### **操作步骤**
1. 在浏览器中打开上述URL
2. 页面显示所有交易记录列表
3. 每笔交易显示：日期、描述、金额、分类标签、收据匹配状态

#### **显示字段说明**
| 字段 | 说明 | 示例 |
|------|------|------|
| **日期** | 交易发生日期 | 2025-11-05 |
| **描述** | 商户名称/交易描述 | DINAS RESTAURANT |
| **金额** | 交易金额（RM） | 85.00 |
| **标签** | OWNER或INFINITE | INFINITE |
| **收据状态** | matched/pending/missing | matched |

#### **使用场景**
- **每日对账**：核对当天的信用卡消费
- **月度总结**：查看本月所有交易记录
- **分类统计**：区分个人和公司支出
- **收据核对**：检查哪些交易还没有匹配收据

#### **实际效果**
```
示例数据：
┌────────────┬──────────────────┬────────┬──────────┬─────────┐
│   日期     │     描述         │  金额  │   分类   │  收据   │
├────────────┼──────────────────┼────────┼──────────┼─────────┤
│ 2025-11-05 │ DINAS RESTAURANT │ 85.00  │ INFINITE │ matched │
│ 2025-11-04 │ GRAB RIDE        │ 12.50  │ OWNER    │ pending │
│ 2025-11-03 │ SHOPEE ONLINE    │ 156.00 │ OWNER    │ missing │
└────────────┴──────────────────┴────────┴──────────┴─────────┘

统计：
✓ 已匹配: 1笔
⚠ 待处理: 1笔
✗ 缺失: 1笔
```

---

### 1.2 收据匹配系统

#### **功能描述**
通过OCR技术自动识别收据图片，并与信用卡交易进行智能匹配，计算相似度分数。

#### **访问方式**
```
页面访问: http://localhost:5000/credit-cards/receipts
OCR接口: POST http://localhost:5000/credit-cards/receipts/ocr
匹配接口: POST http://localhost:5000/credit-cards/receipts/match
```

#### **操作步骤（页面版）**
1. 访问收据匹配页面
2. 点击"上传收据"按钮
3. 选择JPG/PNG格式的收据图片
4. 系统自动OCR识别：
   - 商户名称
   - 金额
   - 日期
   - 置信度分数
5. 系统自动匹配最相似的未匹配交易
6. 显示匹配度评分（优秀/良好/一般/差）
7. 用户确认或手动选择交易

#### **OCR识别示例**
```json
请求:
POST /credit-cards/receipts/ocr
Content-Type: multipart/form-data
文件: receipt.jpg

响应:
{
  "ok": true,
  "extracted": {
    "merchant_name": "KFC RESTAURANT",
    "amount": 23.40,
    "date": "2025-11-05",
    "confidence_score": 0.88
  }
}
```

#### **匹配计算逻辑**
系统使用多因素评分模型：
- **金额相似度** (40%权重)：OCR金额 ÷ 交易金额
- **日期匹配** (30%权重)：完全匹配1.0，相近日期0.7
- **商户匹配** (20%权重)：名称相似度（模糊匹配）
- **置信度** (10%权重)：OCR识别置信度

**评分标准**：
- ≥ 90分：优秀 ⭐⭐⭐⭐⭐
- 80-89分：良好 ⭐⭐⭐⭐
- 60-79分：一般 ⭐⭐⭐
- < 60分：差 ⭐⭐

#### **匹配接口示例**
```bash
curl -X POST "http://localhost:5000/credit-cards/receipts/match" \
  -F "tx_date=2025-11-05" \
  -F "tx_amount=85.00" \
  -F "ocr_date=2025-11-05" \
  -F "ocr_amount=85.00" \
  -F "merchant=DINAS RESTAURANT"

响应:
{
  "ok": true,
  "score": 0.95,
  "level": "优秀"
}
```

#### **使用场景**
- **月底结账**：批量匹配当月所有收据
- **报销审核**：验证收据真实性和金额准确性
- **异常检测**：发现金额或商户不符的可疑交易
- **合规审计**：确保所有公司支出都有收据支持

#### **当前状态说明**
⚠️ **注意**：OCR功能当前返回模拟数据，真实OCR需要配置 `OCR_API_KEY`（可选）

---

### 1.3 供应商发票管理 ⭐ **已启用数据库**

#### **功能描述**
自动汇总指定月份所有供应商的交易金额，并计算1%服务费。系统直接从PostgreSQL数据库读取真实数据。

#### **访问方式**
```
URL: http://localhost:5000/credit-cards/supplier-invoices
可选参数: ?y=2025&m=11  （指定年月，默认当月）
方法: GET
```

#### **操作步骤**
1. 浏览器访问URL
2. 系统自动执行SQL聚合查询
3. 显示所有供应商的月度汇总表
4. 显示总计和服务费

#### **数据库查询逻辑**
```sql
-- 系统自动执行的查询（SQLAlchemy ORM）
SELECT 
  s.supplier_name,
  s.address,
  COALESCE(SUM(t.amount), 0) AS total
FROM suppliers s
LEFT JOIN supplier_transactions t 
  ON t.supplier_id = s.id 
  AND EXTRACT(YEAR FROM t.txn_date) = 2025
  AND EXTRACT(MONTH FROM t.txn_date) = 11
GROUP BY s.id, s.supplier_name, s.address
ORDER BY s.supplier_name ASC;
```

#### **显示格式**
```
═══════════════════════════════════════════════════════
            供应商月度账单 (2025年11月)
═══════════════════════════════════════════════════════

供应商              地址                月度总额      服务费(1%)
────────────────────────────────────────────────────────
DINAS RESTAURANT   Kuala Lumpur       RM 850.00     RM 8.50
HUAWEI            Petaling Jaya       RM 1200.00    RM 12.00
PASAR RAYA        Subang Jaya         RM 500.00     RM 5.00
────────────────────────────────────────────────────────
                                    总计(INFINITE): RM 2550.00
                                         服务费(1%): RM 25.50
═══════════════════════════════════════════════════════
```

#### **计费逻辑**
- **INFINITE公司消费**：需向供应商支付原价
- **INFINITE向客户收费**：原价 + 1%服务费
- **示例**：
  - 供应商账单：RM 2550.00
  - 客户账单：RM 2550.00 + RM 25.50 = **RM 2575.50**

#### **按月查询示例**
```bash
# 查询2025年10月数据
http://localhost:5000/credit-cards/supplier-invoices?y=2025&m=10

# 查询当前月份（默认）
http://localhost:5000/credit-cards/supplier-invoices
```

#### **使用场景**
- **月度结算**：每月月底生成供应商账单
- **财务对账**：核对供应商消费总额
- **利润计算**：服务费即为毛利
- **客户报价**：依据1%加价向客户报价

#### **实际数据验证**
```bash
# 当前数据库状态
供应商数量: 3家
交易记录: 5笔
总消费: RM 2550.00
服务费: RM 25.50
```

---

### 1.4 月结报告

#### **功能描述**
生成信用卡月度综合报告，包括收据覆盖率评级和OWNER/INFINITE支出汇总。

#### **访问方式**
```
URL: http://localhost:5000/credit-cards/monthly-report
方法: GET
```

#### **操作步骤**
1. 访问月结报告页面
2. 系统自动计算：
   - 收据覆盖率（已匹配交易数 ÷ 总交易数）
   - OWNER卡片支出统计
   - INFINITE卡片支出统计 + 服务费
   - 评级（A/B/C/D）

#### **评级标准**
```
A级: 收据覆盖率 ≥ 90%  ⭐⭐⭐⭐⭐ (优秀)
B级: 收据覆盖率 ≥ 70%  ⭐⭐⭐⭐   (良好)
C级: 收据覆盖率 ≥ 50%  ⭐⭐⭐     (及格)
D级: 收据覆盖率 < 50%  ⭐⭐       (需改进)
```

#### **报告内容示例**
```
═══════════════════════════════════════════════════════
              月度财务总结 (2025年11月)
═══════════════════════════════════════════════════════

📊 收据覆盖率: 75% (评级: B)
   已匹配: 15笔 / 总计: 20笔

💳 OWNER 卡片:
   消费: RM 8,500.00
   已付: RM 6,000.00
   结存: RM 2,500.00

💼 INFINITE 卡片:
   消费: RM 3,200.00
   已付: RM 2,800.00
   服务费收入: RM 32.00  ← (3200 × 1%)
   结存: RM 400.00
═══════════════════════════════════════════════════════
```

#### **使用场景**
- **月度绩效评估**：检查收据管理是否达标
- **现金流管理**：查看应付账款余额
- **业绩统计**：服务费收入统计
- **合规检查**：确保收据覆盖率达到公司要求（如≥80%）

---

## 2. 企业发票生成系统

### 2.1 发票格式概览

系统支持**3种专业发票格式**，全部使用黑白正式排版：

| 格式 | 参数值 | 适用场景 | 关键特征 |
|------|--------|---------|---------|
| **服务发票** | `layout=service` | 审计/税务/咨询服务 | 按服务项目逐行计费 |
| **催款通知** | `layout=debit` | 逾期利息/调整 | 电脑生成认证，严肃正式 |
| **明细税务发票** | `layout=itemised` | 复杂费用明细 | 航空风格，分段表格 |

---

### 2.2 发票预览功能

#### **功能描述**
在浏览器中直接预览3种发票格式的样板PDF，无需填写真实数据。

#### **访问方式**
```bash
# 服务发票（英文）
http://localhost:5000/invoices/preview.pdf?layout=service&lang=en

# 催款单（中文）
http://localhost:5000/invoices/preview.pdf?layout=debit&lang=zh

# 明细发票（英文）
http://localhost:5000/invoices/preview.pdf?layout=itemised&lang=en
```

#### **参数说明**
| 参数 | 必填 | 可选值 | 默认值 | 说明 |
|------|------|--------|--------|------|
| `layout` | 否 | service / debit / itemised | service | 发票格式 |
| `lang` | 否 | en / zh | en | 语言（英文/中文） |

#### **操作步骤**
1. 复制上述任一URL
2. 在浏览器中打开
3. PDF自动在浏览器中显示
4. 可直接打印或另存为

#### **预览数据说明**
预览模式使用固定演示数据：
- 发票编号：DEMO-0001
- 客户名称：Demo Client Sdn Bhd
- 金额：RM 280.00
- 日期：当前日期

#### **使用场景**
- **格式选择**：决定使用哪种发票格式
- **客户演示**：向客户展示发票样式
- **打印测试**：测试打印效果和排版
- **模板定制**：作为定制开发的参考

---

### 2.3 正式发票生成 ⭐ **自动编号+数据库存档**

#### **功能描述**
生成正式的PDF发票，自动分配唯一编号（INV-YYYY-0001格式），并保存记录到数据库。

#### **访问方式**
```
URL: http://localhost:5000/invoices/make
方法: GET
响应: PDF文件（自动下载）
```

#### **完整参数列表**
| 参数 | 必填 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| `layout` | ✅ 是 | string | 发票格式 | service / debit / itemised |
| `bill_to_name` | ✅ 是 | string | 客户名称 | ABC Corporation Sdn Bhd |
| `amount` | ✅ 是 | float | 金额（税前） | 1000.00 |
| `number` | ❌ 否 | string | 自定义编号（不填则自动生成） | INV-2025-0001 |
| `bill_to_addr` | ❌ 否 | string | 客户地址 | Kuala Lumpur, Malaysia |
| `bill_to_reg` | ❌ 否 | string | 客户注册号 | 202501234567 |
| `lang` | ❌ 否 | string | 语言 | en / zh |

#### **自动编号机制**
```
格式: INV-YYYY-NNNN
示例: INV-2025-0001, INV-2025-0002, ...

规则:
1. 每年从0001重新开始
2. 使用数据库序列保证唯一性
3. 事务安全，不会重复
4. 如果手动指定number参数，则使用指定值
```

#### **税费计算**
系统自动计算SST（销售与服务税，马来西亚6%）：
```
税前金额: RM 1000.00
SST (6%):  RM 60.00
────────────────────────
总计:      RM 1060.00
```

#### **实际使用示例**

**示例1: 基础服务发票（自动编号）**
```bash
curl "http://localhost:5000/invoices/make?layout=service&bill_to_name=测试客户&amount=500" -o invoice.pdf

# 生成结果:
# - 文件名: INV-2025-0001.pdf
# - 编号: INV-2025-0001 (自动生成)
# - 客户: 测试客户
# - 金额: RM 500.00 + RM 30.00 (SST) = RM 530.00
# - 数据库已保存
```

**示例2: 详细催款单（中文）**
```bash
curl "http://localhost:5000/invoices/make?\
layout=debit&\
bill_to_name=拖欠公司&\
amount=200&\
bill_to_addr=吉隆坡&\
bill_to_reg=ABC123456&\
lang=zh" -o debit.pdf

# 生成结果:
# - 编号: INV-2025-0002
# - 语言: 中文
# - 包含客户地址和注册号
```

**示例3: 自定义编号**
```bash
curl "http://localhost:5000/invoices/make?\
layout=service&\
bill_to_name=VIP客户&\
amount=5000&\
number=VIP-2025-001" -o vip.pdf

# 生成结果:
# - 编号: VIP-2025-001 (使用自定义编号)
```

#### **数据库存档**
每张发票自动保存以下信息到 `invoices` 表：
```sql
id          | 1
number      | INV-2025-0001
lang        | en
layout      | service
bill_to_name| ABC Corporation
bill_to_addr| Kuala Lumpur
bill_to_reg | 202501234567
amount      | 1000.00
tax_rate    | 0.06
total       | 1060.00
created_at  | 2025-11-07 17:30:00
```

#### **使用场景**

**场景1: 月度服务账单**
```bash
# 每月向客户发送服务费发票
for customer in customers; do
  curl "http://localhost:5000/invoices/make?\
  layout=service&\
  bill_to_name=$customer&\
  amount=$monthly_fee&\
  lang=en" -o "invoices/${customer}_$(date +%Y%m).pdf"
done
```

**场景2: 逾期利息催收**
```bash
# 向逾期客户发送催款单
curl "http://localhost:5000/invoices/make?\
layout=debit&\
bill_to_name=逾期客户ABC&\
amount=50.00&\
lang=zh" -o debit_notice.pdf

# 自动邮件发送（需配置SendGrid）
```

**场景3: 批量发票生成**
```bash
# 从CSV读取客户列表批量生成
while IFS=, read -r name amount; do
  curl "http://localhost:5000/invoices/make?\
  layout=itemised&\
  bill_to_name=$name&\
  amount=$amount" -o "${name// /_}.pdf"
done < customers.csv
```

---

### 2.4 发票格式详解

#### **格式A: 服务发票 (Service Invoice)**

**视觉特征**：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    SERVICE INVOICE                      
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

发票方（左上）:
INFINITE GZ SDN BHD
Registration: 202301234567 (ABC)
Address: Kuala Lumpur, Malaysia
Email: admin@infinitegz.com

客户方（右上）:
BILL TO:
[客户名称]
[客户地址]
[客户注册号]

发票信息（中间）:
Invoice #: INV-2025-0001
Date: 2025-11-07
Due: 2025-11-21 (14天)

明细表格:
┌─────────────────────────────┬─────┬────────┬─────────┐
│ Description                 │ Qty │  Price │  Amount │
├─────────────────────────────┼─────┼────────┼─────────┤
│ Professional Consulting     │  1  │ 1000.00│ 1000.00 │
└─────────────────────────────┴─────┴────────┴─────────┘
                                    Subtotal:  1000.00
                                    SST (6%):    60.00
                                    ━━━━━━━━━━━━━━━━━━
                                    TOTAL:      1060.00

页脚:
Payment Terms: Net 14 days
Bank: Maybank | Account: 1234567890
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Authorized By: [签名线]
```

**适用场景**：
- 专业服务（审计、税务、咨询）
- 项目里程碑付款
- 月度服务费

---

#### **格式B: 催款通知 (Debit Note)**

**视觉特征**：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                      DEBIT NOTE                         
                 (Computer Generated)                     
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ URGENT - PAYMENT OVERDUE

Reference #: INV-2025-0001
Date: 2025-11-07

客户信息：
[客户名称]
[客户地址]

催款原因：
REASON: Late Payment Interest
ORIGINAL INVOICE: INV-2025-9999
DAYS OVERDUE: 30 days
INTEREST RATE: 2% per month

金额明细：
Original Amount:     RM 1000.00
Interest (2%):       RM   20.00
Admin Fee:           RM   10.00
                     ━━━━━━━━━━━━
TOTAL DUE:           RM 1030.00

⏰ PAYMENT DEADLINE: 2025-11-14

This is a computer-generated document.
No signature required.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**适用场景**：
- 逾期利息通知
- 账户调整
- 补充收费

---

#### **格式C: 明细税务发票 (Itemised Tax Invoice)**

**视觉特征**：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              ITEMISED TAX INVOICE                       
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Invoice #: INV-2025-0001
Date: 2025-11-07

分段明细（航空风格）：

┌─────────────────────────────────────────────────────┐
│ SECTION A: BASE SERVICES                            │
├──────────────────────────────┬──────────────────────┤
│ Professional Consulting      │            RM 800.00 │
│ Documentation Fee            │            RM 150.00 │
│ Processing Charge            │            RM  50.00 │
├──────────────────────────────┼──────────────────────┤
│ SUBTOTAL (Section A)         │            RM 1000.00│
└──────────────────────────────┴──────────────────────┘

┌─────────────────────────────────────────────────────┐
│ SECTION B: TAXES & FEES                             │
├──────────────────────────────┬──────────────────────┤
│ Service Tax (6%)             │            RM  60.00 │
│ Administrative Levy          │            RM  10.00 │
├──────────────────────────────┼──────────────────────┤
│ SUBTOTAL (Section B)         │            RM  70.00 │
└──────────────────────────────┴──────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRAND TOTAL:                               RM 1070.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GST/SST Reg: XXX-XXXX-XXXX
```

**适用场景**：
- 复杂项目账单
- 多项费用明细
- 需要详细税务分解的场景

---

### 2.5 发票编号系统技术细节

#### **编号格式**
```
INV-[YEAR]-[SEQUENCE]
│   │      └─ 4位序列号（0001-9999）
│   └──────── 4位年份
└──────────── 前缀（可定制）

示例:
INV-2025-0001
INV-2025-0002
...
INV-2025-9999
INV-2026-0001  ← 新年度重置
```

#### **数据库表结构**
```sql
-- invoice_sequences 表
CREATE TABLE invoice_sequences (
  id SERIAL PRIMARY KEY,
  prefix VARCHAR(10) NOT NULL,    -- 前缀 (如 "INV")
  year INTEGER NOT NULL,           -- 年份 (如 2025)
  next_seq INTEGER NOT NULL,       -- 下一个序列号
  UNIQUE(prefix, year)             -- 防止重复
);

-- invoices 表
CREATE TABLE invoices (
  id SERIAL PRIMARY KEY,
  number VARCHAR(50) UNIQUE,       -- 发票编号
  lang VARCHAR(5),                 -- 语言
  layout VARCHAR(20),              -- 格式
  bill_to_name TEXT,               -- 客户名称
  bill_to_addr TEXT,               -- 客户地址
  bill_to_reg VARCHAR(50),         -- 客户注册号
  amount NUMERIC(12,2),            -- 税前金额
  tax_rate NUMERIC(5,4),           -- 税率
  total NUMERIC(12,2),             -- 总金额
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **并发安全机制**
```python
# 使用数据库事务保证原子性
with get_session() as db:
    # 1. 查询或创建序列记录
    seq = db.query(InvoiceSequence).filter_by(
        prefix="INV", 
        year=2025
    ).with_for_update().first()  # 行锁
    
    # 2. 生成编号
    number = f"INV-2025-{seq.next_seq:04d}"
    
    # 3. 递增序列
    seq.next_seq += 1
    
    # 4. 保存发票记录
    db.add(Invoice(number=number, ...))
    
    # 5. 提交事务
    db.commit()
```

**关键保护措施**：
- ✅ 使用 `with_for_update()` 行级锁
- ✅ 事务内完成所有操作
- ✅ UNIQUE约束防止重复编号
- ✅ 每年自动重置序列

---

## 3. 智能贷款匹配系统

### 3.1 贷款产品库

#### **功能描述**
实时展示马来西亚所有银行的贷款产品，包括最新利率（来自Bank Negara Malaysia公共API）。

#### **访问方式**
```
页面: http://localhost:5000/loans/page
API: http://localhost:5000/loans/intel
导出: http://localhost:5000/loans/intel/export.csv
```

#### **操作步骤**
1. 访问贷款产品页面
2. 查看所有银行的贷款产品列表
3. 点击"查看详情"展开产品细节
4. 点击"导出CSV"下载数据

#### **显示字段**
| 字段 | 说明 | 示例 |
|------|------|------|
| **银行名称** | 贷款机构 | Maybank |
| **产品名称** | 贷款产品 | Home Loan - Fixed Rate |
| **利率** | 年利率 | 3.5% |
| **最高贷款额** | 可贷金额上限 | RM 2,000,000 |
| **贷款期限** | 还款年限 | 30 years |
| **最低月入** | 申请条件 | RM 5,000 |

#### **使用场景**
- **客户咨询**：快速查询最新贷款利率
- **产品比较**：对比不同银行的贷款条件
- **市场调研**：分析贷款市场趋势
- **报告生成**：导出CSV用于分析

---

### 3.2 贷款利率更新

#### **功能描述**
从Bank Negara Malaysia (BNM) API获取最新利率数据，更新本地贷款产品库。

#### **访问方式**
```
查看更新: http://localhost:5000/loans/updates
手动刷新: POST http://localhost:5000/loans/updates/refresh
导出: http://localhost:5000/loans/updates/export.csv
```

#### **操作步骤（手动刷新）**
```bash
curl -X POST "http://localhost:5000/loans/updates/refresh" \
  -H "X-Refresh-Key: YOUR_LOANS_REFRESH_KEY"

响应:
{
  "ok": true,
  "updated": 25,
  "timestamp": "2025-11-07T17:30:00Z"
}
```

#### **自动更新机制**
系统使用`schedule`库定期自动更新：
```python
# 每天凌晨2点自动刷新
schedule.every().day.at("02:00").do(refresh_bnm_rates)
```

#### **数据来源**
```
API端点: https://api.bnm.gov.my/public/kijang-emas
频率: 每日更新
覆盖范围: 所有持牌银行
```

#### **使用场景**
- **每日运维**：确保利率数据最新
- **紧急查询**：遇到利率变动时手动刷新
- **合规要求**：保持数据时效性

---

### 3.3 DSR计算器（债务收入比）

#### **功能描述**
计算客户的Debt Service Ratio（债务收入比），判断贷款申请的可行性。

#### **访问方式**
```
API: POST http://localhost:5000/loans/dsr/calc
```

#### **计算公式**
```
DSR = (月度还款总额) / (月收入) × 100%

马来西亚银行标准:
✓ DSR < 60%: 可申请
✗ DSR ≥ 60%: 拒绝（或需额外担保）
```

#### **请求示例**
```bash
curl -X POST "http://localhost:5000/loans/dsr/calc" \
  -H "Content-Type: application/json" \
  -d '{
    "monthly_income": 8000,
    "existing_loans": [
      {"monthly_payment": 1500},
      {"monthly_payment": 800}
    ],
    "new_loan_monthly": 2000
  }'

响应:
{
  "ok": true,
  "dsr": 53.75,
  "status": "approved",
  "details": {
    "monthly_income": 8000,
    "existing_payments": 2300,
    "new_payment": 2000,
    "total_payments": 4300,
    "remaining_income": 3700
  }
}
```

#### **评估标准**
```
DSR ≤ 40%: 优秀 ⭐⭐⭐⭐⭐ (高批准率)
DSR 41-50%: 良好 ⭐⭐⭐⭐   (正常批准)
DSR 51-59%: 偏高 ⭐⭐⭐     (需审慎评估)
DSR ≥ 60%: 拒绝 ⭐⭐       (不符合标准)
```

#### **使用场景**
- **贷款预审**：申请前快速评估可行性
- **客户咨询**：帮助客户了解贷款能力
- **风险评估**：判断客户财务健康度
- **产品推荐**：基于DSR推荐合适贷款额

---

### 3.4 贷款产品对比

#### **功能描述**
选择多个贷款产品进行并排对比，生成对比报告。

#### **访问方式**
```
对比页面: http://localhost:5000/loans/compare/page
添加产品: POST /loans/compare/add
查看列表: GET /loans/compare/list
生成PDF: GET /loans/ranking/pdf
```

#### **操作步骤**
1. 访问贷款产品库页面
2. 点击"加入对比"按钮（最多5个产品）
3. 访问对比页面查看并排对比
4. 点击"生成PDF"下载对比报告

#### **对比维度**
- ✓ 利率差异
- ✓ 月供金额（相同贷款额计算）
- ✓ 总利息支出（相同期限）
- ✓ 申请条件对比
- ✓ 优惠活动对比

#### **对比示例**
```
═══════════════════════════════════════════════════════
            贷款产品对比报告 (3款产品)
═══════════════════════════════════════════════════════

贷款额: RM 500,000 | 期限: 30年

┌──────────┬────────┬─────────┬──────────┬──────────┐
│  银行    │ 利率   │ 月供    │ 总利息   │  总支出  │
├──────────┼────────┼─────────┼──────────┼──────────┤
│ Maybank  │ 3.50% │ RM 2,245│ RM 308,000│ RM 808,000│
│ CIMB     │ 3.65% │ RM 2,289│ RM 324,000│ RM 824,000│
│ RHB      │ 3.40% │ RM 2,216│ RM 298,000│ RM 798,000│
└──────────┴────────┴─────────┴──────────┴──────────┘

💡 推荐: RHB (节省 RM 10,000 利息)
═══════════════════════════════════════════════════════
```

#### **分享功能**
```bash
# 生成永久分享链接
POST /loans/compare/snapshot

响应:
{
  "ok": true,
  "share_code": "abc123xyz",
  "url": "http://localhost:5000/loans/compare/share/abc123xyz"
}

# 客户访问链接即可查看对比结果
```

#### **使用场景**
- **客户演示**：向客户展示产品优势
- **决策支持**：帮助客户选择最优方案
- **销售工具**：生成专业对比报告
- **数据分析**：分析不同产品的竞争力

---

### 3.5 贷款产品排名

#### **功能描述**
基于利率、月供、申请条件等因素，智能排名推荐最优贷款产品。

#### **访问方式**
```
排名页面: http://localhost:5000/loans/ranking
PDF报告: http://localhost:5000/loans/ranking/pdf
```

#### **排名算法**
```python
得分 = 40% × 利率分数 
     + 30% × 月供分数
     + 20% × 申请条件分数
     + 10% × 优惠活动分数

利率分数 = (最高利率 - 当前利率) / (最高利率 - 最低利率) × 100
```

#### **操作步骤**
1. 访问排名页面
2. 输入贷款需求：
   - 贷款额度
   - 还款期限
   - 月收入
3. 系统自动计算并排名
4. 显示Top 10推荐产品
5. 下载PDF报告

#### **排名报告示例**
```
═══════════════════════════════════════════════════════
        智能贷款排名 TOP 10 (2025-11-07)
═══════════════════════════════════════════════════════
贷款需求: RM 500,000 | 30年 | 月收入: RM 10,000

🥇 第1名 - RHB Bank (评分: 95.5)
   利率: 3.40% | 月供: RM 2,216 | DSR: 22%
   优势: 最低利率，月供最低

🥈 第2名 - Maybank (评分: 92.3)
   利率: 3.50% | 月供: RM 2,245 | DSR: 22%
   优势: 申请门槛低，批准快

🥉 第3名 - CIMB (评分: 88.7)
   利率: 3.65% | 月供: RM 2,289 | DSR: 23%
   优势: 首年利率优惠

...
═══════════════════════════════════════════════════════
```

#### **使用场景**
- **快速推荐**：1分钟找到最优方案
- **客户报告**：生成专业PDF演示
- **批量咨询**：处理多个客户查询
- **市场分析**：了解市场最优产品

---

## 4. CTOS信用报告解析

### 4.1 CTOS报告上传

#### **功能描述**
上传CTOS信用报告PDF，自动解析关键信用指标。

#### **访问方式**
```
上传页面: http://localhost:5000/ctos/page
提交接口: POST /ctos/submit
```

#### **操作步骤**
1. 访问CTOS上传页面
2. 点击"上传CTOS PDF"
3. 选择CTOS报告文件
4. 点击"提交解析"
5. 等待解析完成（约10-30秒）
6. 查看解析结果

#### **解析内容**
系统自动提取以下信息：
```
个人信息:
- 姓名
- 身份证号 (MyKad)
- 地址

信用评分:
- CTOS Score (300-850)
- 评级 (AAA / AA / A / B / C / D)

负债情况:
- 现有贷款数量
- 总债务金额
- 逾期记录
- 破产状态

信用卡:
- 信用卡数量
- 总信用额度
- 已用额度
- 逾期记录
```

#### **解析结果示例**
```json
{
  "ok": true,
  "parsed": {
    "name": "AHMAD BIN ALI",
    "ic": "900101-01-1234",
    "ctos_score": 720,
    "rating": "AA",
    "total_debt": 250000,
    "num_loans": 3,
    "credit_cards": 2,
    "credit_limit": 50000,
    "overdue_accounts": 0,
    "bankruptcy": false,
    "recommendation": "Approved - Good credit standing"
  }
}
```

#### **评分标准**
```
AAA (750-850): 优秀信用 ⭐⭐⭐⭐⭐
AA  (700-749): 良好信用 ⭐⭐⭐⭐
A   (650-699): 及格信用 ⭐⭐⭐
B   (600-649): 一般信用 ⭐⭐
C   (500-599): 较差信用 ⭐
D   (300-499): 不良信用 ❌
```

#### **使用场景**
- **贷款审批**：快速评估客户信用
- **风险评估**：判断贷款风险等级
- **额度计算**：基于信用分数决定贷款额
- **客户分级**：VIP客户识别

---

### 4.2 CTOS管理后台

#### **功能描述**
查看所有已解析的CTOS报告历史记录，批量管理和统计。

#### **访问方式**
```
管理页面: http://localhost:5000/ctos/admin
```

#### **操作步骤**
1. 访问管理后台
2. 查看所有CTOS解析记录
3. 筛选条件：
   - 按日期范围
   - 按信用评分
   - 按审批结果
4. 导出Excel报表

#### **统计分析**
```
今日解析: 15份
本月解析: 342份

信用评分分布:
AAA: 20% (68份)
AA:  35% (120份)
A:   30% (103份)
B:   10% (34份)
C:    4% (14份)
D:    1% (3份)

平均DSR: 42.5%
平均CTOS分数: 685
```

#### **使用场景**
- **业绩统计**：统计本月处理客户数
- **风险分析**：分析客户信用分布
- **合规审计**：查看历史审批记录
- **数据导出**：生成月度报表

---

## 5. 系统管理工具

### 5.1 文件转换服务

#### **功能描述**
将PDF文件转换为纯文本或Word文档，支持OCR识别扫描件。

#### **访问方式**
```
上传页面: http://localhost:5000/files/pdf-to-text
提交接口: POST /files/pdf-to-text/submit
查询结果: GET /files/pdf-to-text/result/{task_id}
```

#### **操作步骤**
1. 访问文件转换页面
2. 上传PDF文件
3. 获得task_id
4. 轮询查询转换结果
5. 下载TXT或DOCX文件

#### **支持格式**
```
输入: PDF (文字版或扫描版)
输出: 
- TXT (纯文本)
- DOCX (Word文档)
```

#### **使用示例**
```bash
# 1. 上传文件
curl -X POST "http://localhost:5000/files/pdf-to-text/submit" \
  -F "file=@statement.pdf"

响应:
{
  "task_id": "abc123",
  "status": "processing"
}

# 2. 查询结果
curl "http://localhost:5000/files/pdf-to-text/result/abc123"

响应:
{
  "status": "completed",
  "download_txt": "/files/result/txt/abc123",
  "download_docx": "/files/result/docx/abc123"
}
```

#### **使用场景**
- **数据提取**：从PDF账单提取数据
- **文档编辑**：将PDF转为可编辑格式
- **批量处理**：批量转换合同文件
- **归档整理**：统一文档格式

---

### 5.2 处理历史记录

#### **功能描述**
查看所有文件处理任务的历史记录和状态。

#### **访问方式**
```
历史页面: http://localhost:5000/files/history
删除任务: DELETE /files/history/{task_id}
```

#### **显示内容**
```
任务ID: abc123
文件名: bank_statement.pdf
状态: 已完成
创建时间: 2025-11-07 14:30:00
完成时间: 2025-11-07 14:30:45
处理时长: 45秒
```

#### **使用场景**
- **进度查询**：查看批量任务进度
- **错误排查**：检查失败任务
- **性能监控**：分析处理速度
- **清理存储**：删除旧任务释放空间

---

### 5.3 系统健康检查

#### **功能描述**
检查系统各模块运行状态，确保服务可用。

#### **访问方式**
```
健康检查: http://localhost:5000/health
```

#### **检查项目**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-07T17:30:00Z",
  "checks": {
    "database": "ok",
    "disk_space": "ok",
    "memory": "ok",
    "api_keys": {
      "database_url": "configured",
      "ocr_api_key": "not_configured",
      "sendgrid_api_key": "not_configured"
    }
  },
  "uptime": "3 days, 5 hours"
}
```

#### **使用场景**
- **服务监控**：定期检查系统状态
- **故障排查**：快速定位问题
- **负载均衡**：健康检查端点
- **自动化运维**：脚本定期检测

---

### 5.4 统计仪表盘

#### **功能描述**
可视化展示系统使用统计数据。

#### **访问方式**
```
仪表盘: http://localhost:5000/stats
```

#### **统计指标**
```
今日处理:
- PDF转换: 25份
- CTOS解析: 8份
- 发票生成: 12张

本月累计:
- 总交易数: 1,245笔
- 供应商数: 15家
- 发票金额: RM 125,000

系统资源:
- CPU使用率: 35%
- 内存使用: 1.2GB / 4GB
- 磁盘空间: 45GB / 100GB
```

#### **使用场景**
- **业务分析**：了解系统使用情况
- **容量规划**：预测资源需求
- **性能优化**：识别瓶颈
- **报告生成**：月度运营报告

---

## 6. 数据库管理

### 6.1 演示数据生成

#### **功能描述**
一键生成演示数据，用于测试和演示系统功能。**幂等设计，可重复调用**。

#### **访问方式**
```
生成接口: POST http://localhost:5000/admin/seed/demo
```

#### **操作步骤**
```bash
curl -X POST "http://localhost:5000/admin/seed/demo"

响应:
{
  "ok": true,
  "message": "Demo data seeded successfully",
  "created": {
    "suppliers": 3,
    "transactions": 5,
    "total_amount": 2550.00
  }
}
```

#### **生成数据详情**
```
供应商（3家）:
1. DINAS RESTAURANT
   - 地址: Kuala Lumpur
   - 交易数: 2笔
   - 总金额: RM 850.00

2. HUAWEI
   - 地址: Petaling Jaya
   - 交易数: 2笔
   - 总金额: RM 1200.00

3. PASAR RAYA
   - 地址: Subang Jaya
   - 交易数: 1笔
   - 总金额: RM 500.00

交易记录（5笔）:
- 2025-11-05 | DINAS | RM 400.00
- 2025-11-05 | DINAS | RM 450.00
- 2025-11-05 | HUAWEI | RM 600.00
- 2025-11-05 | HUAWEI | RM 600.00
- 2025-11-05 | PASAR RAYA | RM 500.00
```

#### **幂等性说明**
重复调用不会创建重复数据：
- 检查供应商是否已存在（按名称）
- 已存在则跳过，不存在则创建
- 安全可靠，不会污染数据库

#### **使用场景**
- **系统演示**：快速准备演示数据
- **功能测试**：测试供应商发票功能
- **培训教学**：培训新用户时使用
- **开发调试**：开发新功能时提供测试数据

---

### 6.2 数据库状态查询

#### **当前数据库统计**
```
数据库类型: PostgreSQL
总表数: 49张

核心业务数据:
- 供应商: 3家
- 供应商交易: 5笔
- 发票存档: 4张
- 用户: 0个（待创建）
- 公司: 0个（待创建）

最近活动:
- 最后交易: 2025-11-05
- 最后发票: INV-2025-0004
- 数据库大小: ~50MB
```

#### **表清单（按功能分类）**

**核心业务表：**
- `suppliers` - 供应商主表
- `supplier_transactions` - 供应商交易
- `invoices` - 发票存档
- `invoice_sequences` - 发票编号序列
- `customers` - 客户管理
- `bank_statements` - 银行对账单
- `chart_of_accounts` - 会计科目

**财务管理表：**
- `journal_entries` - 会计分录
- `journal_entry_lines` - 分录明细
- `sales_invoices` - 销售发票
- `purchase_invoices` - 采购发票
- `customer_receipts` - 客户收款
- `supplier_payments` - 供应商付款
- `payment_allocations` - 付款分配
- `receipt_allocations` - 收款分配

**自动化表：**
- `auto_posting_rules` - 自动过账规则
- `auto_invoice_rules` - 自动发票规则
- `exceptions` - 异常中心
- `processing_logs` - 处理日志

**用户与权限表：**
- `users` - 用户账户
- `companies` - 公司/租户
- `user_company_roles` - 用户角色
- `permissions` - 权限定义
- `api_keys` - API密钥

**通知系统表：**
- `notifications` - 通知记录
- `notification_preferences` - 通知偏好
- `push_subscriptions` - 推送订阅

**报表与审计表：**
- `management_reports` - 管理报表
- `report_snapshots` - 报表快照
- `audit_logs` - 审计日志
- `export_templates` - 导出模板

**其他功能表：**
- `file_index` - 文件索引
- `raw_documents` - 原始文档
- `raw_lines` - 文档行数据
- `pending_documents` - 待处理文档
- `upload_staging` - 上传暂存
- `pos_reports` - POS报告
- `pos_transactions` - POS交易
- `tax_adjustments` - 税务调整
- `period_closing` - 期间结账
- `migration_logs` - 迁移日志
- `system_config_versions` - 配置版本
- `task_runs` - 任务运行记录
- `employees` - 员工管理
- `payroll_runs` - 工资运行
- `payroll_items` - 工资项目
- `financial_report_mapping` - 财务报表映射

---

## 7. 常见使用场景完整流程

### 场景1: 月度财务结算完整流程

#### **目标**
完成11月份的财务结算，生成客户账单。

#### **操作步骤**

**步骤1: 查看供应商月度汇总**
```bash
# 访问供应商发票页面
浏览器打开: http://localhost:5000/credit-cards/supplier-invoices?y=2025&m=11

# 确认数据:
# - DINAS: RM 850.00
# - HUAWEI: RM 1200.00
# - PASAR RAYA: RM 500.00
# - 总计: RM 2550.00
# - 服务费: RM 25.50
```

**步骤2: 生成客户发票**
```bash
# 生成INFINITE公司的月度服务费发票
curl "http://localhost:5000/invoices/make?\
layout=itemised&\
bill_to_name=INFINITE%20GZ%20SDN%20BHD&\
bill_to_addr=Kuala%20Lumpur&\
bill_to_reg=202301234567&\
amount=25.50&\
lang=zh" -o INFINITE_202511_Service_Fee.pdf

# 发票编号: INV-2025-0005
# 金额: RM 25.50 + RM 1.53 (SST) = RM 27.03
```

**步骤3: 查看信用卡收据匹配情况**
```bash
# 访问收据匹配页面
浏览器打开: http://localhost:5000/credit-cards/receipts

# 检查覆盖率:
# - 目标: ≥ 90% (A级)
# - 当前: 若低于目标，需补充收据
```

**步骤4: 生成月结报告**
```bash
# 访问月结报告页面
浏览器打开: http://localhost:5000/credit-cards/monthly-report

# 查看评级和统计
# 导出PDF存档
```

**完成效果**：
✅ 供应商账单清晰  
✅ 客户发票已生成  
✅ 收据管理达标  
✅ 月度报告存档

---

### 场景2: 客户贷款咨询完整流程

#### **目标**
客户咨询房贷，找到最优方案并生成对比报告。

#### **客户信息**
- 贷款需求: RM 600,000
- 期限: 30年
- 月收入: RM 12,000
- 现有贷款: 车贷 RM 1,200/月

#### **操作步骤**

**步骤1: DSR预审**
```bash
curl -X POST "http://localhost:5000/loans/dsr/calc" \
  -H "Content-Type: application/json" \
  -d '{
    "monthly_income": 12000,
    "existing_loans": [{"monthly_payment": 1200}],
    "new_loan_monthly": 2700
  }'

响应:
{
  "dsr": 32.5,
  "status": "approved",
  "rating": "excellent"
}
# ✅ DSR 32.5% < 60%，可申请
```

**步骤2: CTOS信用检查**
```bash
# 上传客户CTOS报告
浏览器访问: http://localhost:5000/ctos/page
上传文件: customer_ctos.pdf

解析结果:
{
  "ctos_score": 735,
  "rating": "AA",
  "recommendation": "Approved"
}
# ✅ 信用良好
```

**步骤3: 查看贷款产品排名**
```bash
浏览器访问: http://localhost:5000/loans/ranking

输入参数:
- 贷款额: RM 600,000
- 期限: 30年
- 月收入: RM 12,000

系统推荐:
🥇 RHB Bank - 3.40% (月供 RM 2,659)
🥈 Maybank - 3.50% (月供 RM 2,694)
🥉 CIMB - 3.65% (月供 RM 2,747)
```

**步骤4: 生成对比报告**
```bash
# 添加3款产品到对比
POST /loans/compare/add (RHB, Maybank, CIMB)

# 生成PDF报告
浏览器访问: http://localhost:5000/loans/ranking/pdf

# 下载: loan_comparison_2025-11-07.pdf
```

**步骤5: 客户沟通**
```
推荐方案: RHB Bank
理由:
✓ 利率最低 (3.40%)
✓ 月供最低 (RM 2,659)
✓ 30年总节省 RM 12,600 (vs CIMB)
✓ DSR: 32.5% (优秀)

申请材料:
- 身份证
- 工资单(3个月)
- EPF Statement
- 房产估价报告
```

**完成效果**：
✅ DSR预审通过  
✅ 信用评估优秀  
✅ 找到最优方案  
✅ 对比报告生成

---

### 场景3: 批量发票生成（月底结算）

#### **目标**
月底向所有客户批量生成服务费发票。

#### **客户列表（CSV格式）**
```csv
customer_name,monthly_fee,address,reg_no
INFINITE GZ SDN BHD,25.50,Kuala Lumpur,202301234567
ABC TRADING,18.00,Petaling Jaya,201912345678
XYZ SERVICES,32.00,Subang Jaya,202205432109
```

#### **批量生成脚本**
```bash
#!/bin/bash

while IFS=, read -r name fee addr reg; do
  # 跳过标题行
  if [ "$name" == "customer_name" ]; then
    continue
  fi
  
  # 生成发票
  curl "http://localhost:5000/invoices/make?\
layout=service&\
bill_to_name=$(echo $name | sed 's/ /%20/g')&\
amount=$fee&\
bill_to_addr=$(echo $addr | sed 's/ /%20/g')&\
bill_to_reg=$reg&\
lang=en" -o "invoices/${name// /_}_202511.pdf"
  
  echo "✓ Generated invoice for $name"
  sleep 1
done < customers.csv

echo "✅ All invoices generated!"
```

#### **执行结果**
```
✓ Generated invoice for INFINITE GZ SDN BHD
✓ Generated invoice for ABC TRADING
✓ Generated invoice for XYZ SERVICES
✅ All invoices generated!

生成文件:
- INFINITE_GZ_SDN_BHD_202511.pdf (INV-2025-0006)
- ABC_TRADING_202511.pdf (INV-2025-0007)
- XYZ_SERVICES_202511.pdf (INV-2025-0008)

数据库自动记录:
- invoices表新增3条记录
- invoice_sequences更新: next_seq = 9
```

**完成效果**：
✅ 批量生成3张发票  
✅ 自动编号无冲突  
✅ 数据库已存档  
✅ 文件规范命名

---

## 8. 故障排查指南

### 问题1: 供应商发票显示RM 0.00

**症状**：
访问 `/credit-cards/supplier-invoices` 显示所有金额为0

**可能原因**：
1. 数据库中没有交易记录
2. 查询月份不正确
3. 交易日期字段格式问题

**解决方法**：
```bash
# 1. 检查数据库是否有数据
curl -X POST http://localhost:5000/admin/seed/demo

# 2. 确认查询月份
http://localhost:5000/credit-cards/supplier-invoices?y=2025&m=11

# 3. 检查数据库
python3 -c "
from accounting_app.db import get_session
from accounting_app.models import Transaction
with get_session() as db:
    count = db.query(Transaction).count()
    print(f'交易记录数: {count}')
"
```

---

### 问题2: 发票编号重复

**症状**：
生成发票时提示"编号已存在"

**可能原因**：
数据库序列表损坏或并发冲突

**解决方法**：
```bash
# 重置序列
python3 -c "
from accounting_app.db import get_session
from accounting_app.models import InvoiceSequence
from datetime import date

with get_session() as db:
    seq = db.query(InvoiceSequence).filter_by(
        prefix='INV',
        year=date.today().year
    ).first()
    
    if seq:
        # 找出最大编号
        from accounting_app.models import Invoice
        max_inv = db.query(Invoice).filter(
            Invoice.number.like(f'INV-{date.today().year}-%')
        ).order_by(Invoice.number.desc()).first()
        
        if max_inv:
            last_num = int(max_inv.number.split('-')[-1])
            seq.next_seq = last_num + 1
            db.commit()
            print(f'序列已重置为: {seq.next_seq}')
"
```

---

### 问题3: OCR识别返回模拟数据

**症状**：
上传真实收据但总是返回"KFC RESTAURANT"

**可能原因**：
`OCR_API_KEY` 未配置，系统使用模拟模式

**解决方法**：
```bash
# 1. 确认密钥状态
curl http://localhost:5000/health

# 2. 配置OCR密钥
# 在Replit Secrets中添加:
# OCR_API_KEY=your_actual_api_key

# 3. 重启服务器
# 点击Replit的"Stop"和"Run"按钮
```

**替代方案**：
如果不需要真实OCR，可以使用模拟数据进行开发和测试。

---

## 9. 性能优化建议

### 建议1: 数据库索引

**当前状态**：基础索引已创建  
**优化建议**：为高频查询添加复合索引

```sql
-- 供应商交易查询优化
CREATE INDEX idx_supplier_txn_date 
ON supplier_transactions(supplier_id, txn_date);

-- 发票查询优化
CREATE INDEX idx_invoice_number 
ON invoices(number);

-- 用户查询优化
CREATE INDEX idx_user_company 
ON user_company_roles(user_id, company_id);
```

**预期效果**：
- 供应商月度汇总查询提速 70%
- 发票检索提速 50%

---

### 建议2: 缓存策略

**适用场景**：贷款产品库、BNM利率

```python
# 使用Redis缓存贷款产品
@cache(ttl=3600)  # 缓存1小时
def get_loan_products():
    return fetch_from_database()
```

**预期效果**：
- API响应时间从 200ms 降至 10ms
- 数据库负载降低 80%

---

### 建议3: 批量操作

**场景**：批量生成发票时

```python
# 优化前: 逐个保存
for customer in customers:
    db.add(Invoice(...))
    db.commit()  # N次提交

# 优化后: 批量保存
invoices = [Invoice(...) for customer in customers]
db.bulk_save_objects(invoices)
db.commit()  # 1次提交
```

**预期效果**：
- 100张发票生成时间从 30秒 降至 5秒

---

## 10. 安全注意事项

### ⚠️ 生产环境部署前检查

**必须完成的安全配置**：

1. **更改默认密钥**
```bash
# 重新生成FERNET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 更新Replit Secrets
```

2. **启用HTTPS**
```bash
# Replit自动提供HTTPS
# 确认ENV=prod时禁用/docs和/openapi.json
```

3. **配置CORS**
```bash
# 限制允许的域名
CORS_ALLOW=https://yourdomain.com
```

4. **API限流**
```python
# 已内置SimpleRateLimitMiddleware
# 默认: 100请求/分钟
# 可在main.py调整
```

5. **数据库备份**
```bash
# 设置每日自动备份
# Replit会自动备份PostgreSQL数据
```

---

## 附录A: 快速参考

### A.1 常用URL清单

```
# 主页导航
http://localhost:5000/preview

# 信用卡模块
http://localhost:5000/credit-cards/transactions
http://localhost:5000/credit-cards/receipts
http://localhost:5000/credit-cards/supplier-invoices
http://localhost:5000/credit-cards/monthly-report

# 发票系统
http://localhost:5000/invoices/preview.pdf?layout=service&lang=en
http://localhost:5000/invoices/make?layout=service&bill_to_name=TEST&amount=100

# 贷款系统
http://localhost:5000/loans/page
http://localhost:5000/loans/ranking
http://localhost:5000/loans/compare/page
http://localhost:5000/ctos/page

# 系统工具
http://localhost:5000/health
http://localhost:5000/stats
http://localhost:5000/files/pdf-to-text
```

---

### A.2 API快速参考

```bash
# 演示数据生成
curl -X POST http://localhost:5000/admin/seed/demo

# DSR计算
curl -X POST http://localhost:5000/loans/dsr/calc \
  -H "Content-Type: application/json" \
  -d '{"monthly_income":10000,"existing_loans":[],"new_loan_monthly":3000}'

# 发票生成
curl "http://localhost:5000/invoices/make?layout=service&bill_to_name=TEST&amount=100" -o test.pdf

# 健康检查
curl http://localhost:5000/health
```

---

### A.3 数据库快速查询

```bash
# 统计供应商数量
python3 -c "from accounting_app.db import get_session; from accounting_app.models import Supplier; print(get_session().__enter__().query(Supplier).count())"

# 查看最新发票
python3 -c "from accounting_app.db import get_session; from accounting_app.models import Invoice; print(get_session().__enter__().query(Invoice).order_by(Invoice.id.desc()).first().number)"

# 查看交易总额
python3 -c "from accounting_app.db import get_session; from accounting_app.models import Transaction; from sqlalchemy import func; print(get_session().__enter__().query(func.sum(Transaction.amount)).scalar())"
```

---

## 结语

恭喜！您现在已经完全掌握CreditPilot系统的所有功能。

**下一步建议**：
1. ✅ 体验所有核心功能
2. ✅ 使用真实数据测试
3. ✅ 配置可选API密钥（按需）
4. ✅ 点击"Publish"发布到生产环境

**获取帮助**：
- 查看 `SYSTEM_STATUS_REPORT.md` 了解系统状态
- 查看 `replit.md` 了解技术架构
- 有问题随时询问！

祝您使用愉快！🎉
