# Chang Choon Chow 结算计算 - VBA处理完整指南

## 📋 概述

本指南将帮助您使用VBA技术从89个PDF原件重新解析并计算Chang Choon Chow的最终结算金额。

---

## 🎯 目标

使用VBA确保100%准确的数据解析和计算：
- ✅ 准确识别每一笔交易
- ✅ 正确提取日期、金额、描述
- ✅ 区分消费(DR)和付款(CR)
- ✅ 识别Supplier商户
- ✅ 按照最新规则分类

---

## 📁 所需文件

### PDF原件位置（已准备）
```
static/uploads/customers/Be_rich_CCC/credit_cards/
├── Alliance_Bank/ (26个PDF)
├── HSBC/ (12个PDF)
├── Hong_Leong_Bank/ (25个PDF)
├── Maybank/ (13个PDF)
└── UOB/ (13个PDF)

总计：89个PDF文件
```

### VBA模板位置
```
vba_templates/
├── 1_CreditCardParser.vba  （信用卡解析器）
├── 2_BankStatementParser.vba （银行流水解析器）
├── 4_DataValidator.vba （数据验证器）
└── JSON_Format_Specification.md （JSON格式规范）
```

---

## 🚀 完整处理步骤

### 第1步：下载PDF文件到Windows电脑

**方法1：通过Replit界面下载**
1. 在Replit文件管理器中，右键点击文件夹
2. 选择"Download"下载整个文件夹

**方法2：使用压缩包**
```bash
# 在Replit Shell中执行
cd static/uploads/customers/Be_rich_CCC/credit_cards
zip -r ~/ccc_pdfs.zip .
```
然后下载 `ccc_pdfs.zip` 到Windows

---

### 第2步：PDF转Excel（使用Adobe/Tabula）

**推荐工具：Adobe Acrobat Pro**

对每个PDF文件：
1. 打开PDF
2. 文件 → 导出为 → 电子表格 → Microsoft Excel工作簿
3. 保存为Excel文件（保持原文件名）

**批量处理建议：**
- 建议按银行分批处理（Alliance 26个 → HSBC 12个 → 等）
- 保持文件名一致性

---

### 第3步：VBA解析Excel文件

#### 3.1 导入VBA模板

1. **打开Excel文件**
2. **按 Alt + F11** 打开VBA编辑器
3. **插入 → 模块**
4. **复制粘贴** `1_CreditCardParser.vba` 完整代码
5. **保存**工作簿（.xlsm格式）

#### 3.2 运行VBA解析器

1. **按 Alt + F8** 打开宏列表
2. **选择** `ParseCreditCardStatement`
3. **点击"运行"**
4. **等待处理完成**

#### 3.3 生成JSON文件

VBA会自动生成JSON文件，格式如下：
```
Alliance_Bank_4514_2024-09-12.json
```

JSON内容示例：
```json
{
  "status": "success",
  "document_type": "credit_card",
  "parsed_by": "VBA Parser v1.0",
  "account_info": {
    "owner_name": "CHANG CHOON CHOW",
    "bank": "Alliance Bank",
    "card_last_4": "4514",
    "statement_date": "12-09-2024",
    "previous_balance": 1296.47,
    "closing_balance": 2718.94
  },
  "transactions": [
    {
      "date": "01-09-2024",
      "description": "GRAB TRANSPORT",
      "amount": 50.00,
      "dr": 50.00,
      "cr": 0,
      "category": "Purchases"
    }
  ],
  "summary": {
    "total_transactions": 15,
    "total_purchases": 2500.00,
    "total_payments": 1000.00
  }
}
```

---

### 第4步：批量上传JSON到Replit

#### 方法1：使用Replit网页界面
1. 创建文件夹：`uploads/ccc_json/`
2. 拖拽所有JSON文件到该文件夹

#### 方法2：使用批量上传API
```bash
# 在Windows PowerShell中执行
$files = Get-ChildItem -Path "C:\CCC_JSON\*.json"
foreach ($file in $files) {
    curl -X POST https://your-replit.repl.co/api/upload/vba-json `
      -F "file=@$($file.FullName)"
}
```

---

### 第5步：服务器端处理JSON

一旦JSON文件上传，服务器会自动：

1. **验证JSON格式**
2. **提取交易数据**
3. **按最新规则分类**：
   - Owner's Expenses（非Supplier消费）
   - GZ's Expenses（7个Supplier + 1% Fee）
   - Owner's Payment（客户付款）
   - GZ's Payment Direct（GZ直接付款）
   - GZ's Payment Indirect（GZ转账给客户）

4. **计算OS Balance**：
   ```
   Owner OS = 上月余额 + Owner消费 - Owner付款
   GZ OS = 上月余额 + GZ消费 - GZ付款
   最终结算 = GZ OS Balance
   ```

5. **生成结算报告**

---

## 📊 Supplier List（重要）

VBA会识别以下7个Supplier：

1. 7SL
2. DINAS
3. RAUB SYC HAINAN
4. AI SMART TECH
5. HUAWEI
6. PASAR RAYA
7. PUCHONG HERBS

**所有Supplier消费会：**
- 计入GZ账本
- 自动计算1% Merchant Fee
- Fee计入Owner账本

---

## ⏱️ 预计时间

| 步骤 | 时间 | 备注 |
|------|------|------|
| 下载PDF | 10分钟 | 89个文件 |
| PDF转Excel | 30-60分钟 | 使用Adobe批量处理 |
| VBA解析 | 20-30分钟 | 每个文件10-20秒 |
| 上传JSON | 10分钟 | |
| 服务器处理 | 2-5分钟 | 自动 |
| **总计** | **1.5-2小时** | |

---

## ✅ 验证清单

完成后请验证：

- [ ] 所有89个PDF已转Excel
- [ ] 所有89个Excel已用VBA解析
- [ ] 所有89个JSON格式正确
- [ ] 所有89个JSON已上传
- [ ] 服务器成功处理所有JSON
- [ ] 最终结算金额已生成

---

## 🆘 常见问题

### Q1: VBA宏被禁用怎么办？
**A**: 文件 → 选项 → 信任中心 → 宏设置 → 启用所有宏

### Q2: PDF转Excel后格式混乱？
**A**: 使用Adobe Acrobat Pro，选择"保留表格结构"

### Q3: VBA解析出错？
**A**: 检查Excel格式是否完整，确保有表头行

### Q4: JSON格式验证失败？
**A**: 使用在线JSON验证工具检查格式

---

## 📞 技术支持

如有问题，请提供：
1. 错误截图
2. 问题PDF文件名
3. 银行名称
4. 错误信息

---

## 🎯 最终目标

完成后您将获得：
- ✅ 100%准确的交易数据
- ✅ 完整的分类明细
- ✅ 精确的结算金额
- ✅ 详细的计算过程

**按照此指南操作，确保数据100%准确无误！**
