# 专业发票系统使用指南

---

## 系统概述

CreditPilot现已集成**企业级专业发票生成系统**，支持三种正式商务发票格式，采用黑白正式公文风格（非品牌色），适用于对外正式文件。

---

## 三种发票类型

### 1. Service Invoice（专业服务发票）

**适用场景**：会计、审计、税务、咨询等专业服务

**包含元素**：
- 公司抬头与联系信息
- Bill To（受票方）信息
- 发票编号、日期、付款条款
- 明细表格（描述、数量、单价、金额）
- 小计、税额（可配置税率）、合计
- 付款信息（银行账号）
- 备注条款
- 授权签名区

**示例数据**：
```python
{
  "company": {
    "name": "INFINITE GZ SDN. BHD.",
    "address": "No. 28, Jalan Ipoh, 51200 Kuala Lumpur",
    "contact": "Tel: +60-12-345-6789"
  },
  "title": "INVOICE",
  "bill_to": {
    "name": "VK Premium Auto Detailing",
    "address": "Seri Kembangan, Selangor",
    "email": "billing@vk.com"
  },
  "meta": {
    "number": "INV-2025-0001",
    "date": "2025-11-07",
    "terms": "14 days"
  },
  "items": [
    {"desc": "Statutory Audit Services", "qty": 1, "unit_price": 12000},
    {"desc": "Corporate Tax Submission", "qty": 1, "unit_price": 6000}
  ],
  "tax_rate": 0.06,
  "payment": "Bank: HLB 160-0000-9191",
  "notes": [
    "Please settle within 14 days.",
    "10% p.a. interest for overdue balances."
  ]
}
```

---

### 2. Debit Note（借记单）

**适用场景**：逾期利息、费用调整、补充计费

**包含元素**：
- 公司抬头
- "DEBIT NOTE"居中标题
- TO（受票方）完整信息
- 发票编号、日期、付款条款、页码
- 序号化描述列表
- 金额总计
- "Computer Generated Billing"标识

**示例数据**：
```python
{
  "company": DEMO_COMPANY,
  "bill_to": {
    "name": "VK Premium Auto Detailing",
    "address": "Seri Kembangan",
    "tel": "+60-12-345-6789",
    "email": "billing@vk.com"
  },
  "meta": {
    "number": "DN-2504001",
    "date": "2025-04-01",
    "terms": "CASH"
  },
  "items": [
    {"desc": "Late Payment Interest - March 2025", "amount": 28.00}
  ]
}
```

---

### 3. Itemised Tax Invoice（明细税务发票）

**适用场景**：航空、酒店、复杂费用拆分

**包含元素**：
- 公司抬头
- "TAX INVOICE"标题
- 发票编号、日期、税率标识
- 分段明细表（FARE、FEES等）
- 每段包含小计
- Grand Total汇总

**示例数据**：
```python
{
  "company": DEMO_COMPANY,
  "title": "TAX INVOICE",
  "meta": {
    "number": "TI-0001",
    "date": "2025-03-18"
  },
  "st_rate": 0.06,
  "sections": [
    {
      "title": "FARE",
      "rows": [
        ["No.", "Description", "Total Excl. ST", "ST @ 6%"],
        ["1", "1x Guest (IPH-SIN)", "85.00", "0.00"],
        ["2", "1x Fuel Surcharge", "40.00", "0.00"]
      ]
    },
    {
      "title": "FEES",
      "rows": [
        ["No.", "Description", "MYR", "MYR"],
        ["1", "1x Checked baggage 20kg", "70.00", "0.00"]
      ]
    }
  ],
  "grand_total": 299.00
}
```

---

## API端点使用

### 预览三种格式

```bash
# 1. 专业服务发票
GET /invoices/preview.pdf?layout=service

# 2. 借记单
GET /invoices/preview.pdf?layout=debit

# 3. 明细税务发票
GET /invoices/preview.pdf?layout=itemised
```

### 快速生成发票（POST）

```bash
# 生成借记单并下载
POST /invoices/make?layout=debit&number=DN-2504001&bill_to_name=VK%20Premium&amount=28

# 生成服务发票
POST /invoices/make?layout=service&number=INV-2025-0002&bill_to_name=Sin%20Hiap%20Lee&amount=19080
```

### 供应商发票（兼容旧端点）

```bash
GET /invoices/supplier.pdf?supplier=Dinas&month=2025-11
```

---

## 技术实现

### 文件结构

```
accounting_app/
├── services/
│   └── invoice_service.py     # 核心PDF生成引擎
└── routers/
    └── invoices.py            # API端点定义
```

### 核心函数

```python
# 主函数
def build_invoice_pdf(layout: str, payload: dict) -> bytes:
    """
    layout: 'service' | 'debit' | 'itemised'
    payload: 数据字典
    返回: PDF字节流
    """
```

### 设计规范

**颜色体系**（正式黑白）：
- `LINE_GREY`: #444444（边框线）
- `TEXT_GREY`: #111111（正文黑）
- `MUTED_GREY`: #666666（次要文字）

**字体**：
- 标题：Helvetica-Bold 14-18pt
- 正文：Helvetica 10-10.5pt
- 备注：Helvetica 9pt

**线条**：
- HAIRLINE = 0.4（细线）

---

## 实际应用场景

### 场景1：月度服务费账单

```python
# 向7家供应商开具月度服务费发票
for supplier in ['Dinas', 'Huawei', '7SL', ...]:
    payload = {
        "company": COMPANY_INFO,
        "bill_to": {"name": supplier},
        "meta": {"number": f"INV-{month}-{supplier[:3].upper()}"},
        "items": [{"desc": "Monthly Service Fee (1%)", "qty": 1, "unit_price": fee}],
        "tax_rate": 0.00
    }
    pdf = build_invoice_pdf("service", payload)
    # 发送邮件或保存
```

### 场景2：逾期利息借记单

```python
# 自动生成逾期利息借记单
if days_overdue > 14:
    interest = calculate_late_interest(overdue_amount, days_overdue)
    payload = {
        "company": COMPANY_INFO,
        "bill_to": client_info,
        "meta": {"number": f"DN-{today}-{client_id}", "terms": "CASH"},
        "items": [{"desc": f"Late Payment Interest ({days_overdue} days)", "amount": interest}]
    }
    pdf = build_invoice_pdf("debit", payload)
```

### 场景3：航空票务明细

```python
# 仿AirAsia格式的税费拆分
payload = {
    "title": "TAX INVOICE",
    "st_rate": 0.06,
    "sections": [
        {"title": "FARE", "rows": [...]},
        {"title": "FEES", "rows": [...]},
        {"title": "SURCHARGES", "rows": [...]}
    ],
    "grand_total": total_amount
}
pdf = build_invoice_pdf("itemised", payload)
```

---

## 与UI集成

### 在Supplier Invoices页面调用

```html
<!-- accounting_app/templates/credit_cards_supplier_invoices.html -->
<script>
  function generatePDF() {
    const supplier = document.getElementById('selSupplier').value;
    const month = document.getElementById('selMonth').value;
    window.open(`/invoices/supplier.pdf?supplier=${supplier}&month=${month}`);
  }
</script>
```

---

## 测试验证

### 快速测试（命令行）

```bash
# 下载三种格式预览
curl http://localhost:5000/invoices/preview.pdf?layout=service -o service.pdf
curl http://localhost:5000/invoices/preview.pdf?layout=debit -o debit.pdf
curl http://localhost:5000/invoices/preview.pdf?layout=itemised -o itemised.pdf

# 检查文件
ls -lh *.pdf
# 预期输出：
# -rw-r--r-- 1 user user 2.8K service.pdf
# -rw-r--r-- 1 user user 2.4K debit.pdf
# -rw-r--r-- 1 user user 2.7K itemised.pdf
```

### 浏览器测试

直接访问URL，PDF会在浏览器内打开：
```
http://your-app-url/invoices/preview.pdf?layout=service
```

---

## 常见问题

### Q1: 如何自定义公司信息？

修改 `accounting_app/routers/invoices.py` 中的 `DEMO_COMPANY` 字典：

```python
DEMO_COMPANY = {
    "name": "YOUR COMPANY SDN. BHD.",
    "address": "Your Address",
    "contact": "Tel: +60-XX-XXX-XXXX • email@company.com"
}
```

### Q2: 如何调整税率？

在payload中设置 `tax_rate` 字段：
```python
"tax_rate": 0.06  # 6% SST
"tax_rate": 0.08  # 8% GST
"tax_rate": 0.00  # 无税
```

### Q3: 如何添加中文支持？

取消注释字体注册代码（需安装NotoSansCJK字体）：
```python
pdfmetrics.registerFont(TTFont("NotoSans", "/path/to/NotoSansCJK-Regular.ttc"))
BASE_FONT = "NotoSans"
```

### Q4: 如何批量生成发票？

```python
from accounting_app.services.invoice_service import build_invoice_pdf

invoice_list = [...]  # 发票数据列表
for inv_data in invoice_list:
    pdf_bytes = build_invoice_pdf("service", inv_data)
    with open(f"invoices/{inv_data['meta']['number']}.pdf", "wb") as f:
        f.write(pdf_bytes)
```

---

## 下一步扩展

1. **数据库集成**：将发票记录存入PostgreSQL
2. **邮件自动发送**：结合SendGrid API自动发送给客户
3. **发票编号自增**：实现自动序号生成逻辑
4. **多语言版本**：EN/CN双语切换
5. **电子签名**：集成数字签名功能
6. **支付链接**：嵌入在线支付QR码

---

**系统已就绪，立即开始使用！** 🚀
