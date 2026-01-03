# 📊 PDF批量处理系统 - 快速开始

## 🎯 系统功能

自动处理Cheok Jun Yoon的**41份信用卡账单PDF**，实现：

✅ **自动数据提取** - Google Document AI提取15个核心字段  
✅ **智能分类** - 5种交易分类（Owners/GZ/Suppliers）  
✅ **精确计算** - Outstanding Balance自动计算  
✅ **1%手续费** - 供应商交易自动计入  
✅ **Excel报告** - 一键生成完整结算报告  

---

## 📁 文件位置

```
客户PDF文件: static/uploads/customers/Be_rich_CJY/credit_cards/
           ├── AmBank/      (6份)
           ├── HSBC/        (6份)
           ├── UOB/         (6份)
           ├── OCBC/        (6份)
           ├── STANDARD_CHARTERED/ (6份)
           └── HONG_LEONG/  (5份)

输出报告: reports/Be_rich_CJY/
         ├── settlement_report_YYYYMMDD.xlsx   (Excel结算报告)
         └── processing_results_YYYYMMDD.json  (JSON详细数据)
```

---

## 🚀 快速开始

### 步骤1：测试单个PDF

```bash
python3 scripts/test_single_pdf.py
```

**输出示例：**
```
📄 测试文件: AmBank_6354_2025-05-28.pdf
✅ Document AI提取成功

基本信息:
   银行: AmBank
   卡号: 6354
   账单日期: 2025-05-28
   
交易记录: 23 笔

分类结果:
   owners_expenses (15笔)
   suppliers (5笔)
   owners_payment (3笔)

余额详情:
   Outstanding Balance: RM 5,234.56
```

### 步骤2：批量处理所有PDF

```bash
python3 scripts/process_cheok_statements.py
```

**处理流程：**
```
🚀 开始批量处理 41 个PDF文件
📊 并发数: 3

📄 处理: AmBank_6354_2025-05-28.pdf
   ├─ 提取数据...
   ├─ 提取交易: 23笔
   ├─ 分类交易...
   └─ ✅ 成功
      - 交易总数: 23
      - Outstanding Balance: RM 5,234.56

进度: 1/41 (2.4%)
...
进度: 41/41 (100.0%)

📋 处理摘要:
   总文件数: 41
   成功: 39
   失败: 2

💰 总体统计:
   交易总笔数: 856
   消费总额: RM 234,567.89
   还款总额: RM 198,765.43
   Outstanding Balance: RM 35,802.46

✅ 处理完成！

📁 报告文件:
   Excel: reports/Be_rich_CJY/settlement_report_20251117.xlsx
   JSON: reports/Be_rich_CJY/processing_results_20251117.json
```

---

## 📊 专业格式化Excel报告

打开 `CheokJunYoon_Settlement_YYYYMMDD_HHMMSS.xlsx`，包含4个专业格式化工作表：

### ✨ 13项专业格式化标准
- 🎨 **CreditPilot官方配色**: 主粉色#FFB6C1 + 深棕色#3E2723
- 📏 **优化列宽**: 18-40字符宽，自动适应内容
- 🖼️ **精美样式**: 标题行深棕色背景+白色文字，数据行交替颜色
- 💰 **专业格式**: RM 1,234.56（千位分隔符），负数红色显示
- 🎯 **分类颜色**: 5种分类专属颜色（粉色系）
- 🏪 **智能图标**: 供应商🏪和GZ💼交易自动标记
- 🖨️ **打印优化**: 横向打印、页眉页脚、冻结窗格
- 🔍 **自动筛选**: 所有标题行可筛选

📖 **详细格式化说明**: `docs/excel_formatting_guide.md`

---

### 1️⃣ 账单汇总
| 文件名 | 银行 | 卡号 | 账单日期 | Outstanding Balance |
|--------|------|------|----------|-------------------|
| AmBank_6354_2025-05.pdf | AmBank | 6354 | 2025-05-28 | RM 5,234.56 |

### 2️⃣ 交易明细
| 银行 | 分类 | 交易日期 | 交易描述 | 金额 | 供应商手续费 |
|------|------|----------|----------|------|------------|
| AmBank | owners_expenses | 15 MAY | MCDONALD'S | 36.60 | 0.00 |
| AmBank | suppliers | 16 MAY | 7SL TRADING | 1,000.00 | 10.00 |

### 3️⃣ 分类汇总
| 银行 | 分类 | 金额 |
|------|------|------|
| AmBank | owners_expenses | RM 1,234.56 |
| AmBank | gz_expenses | RM 567.89 |
| AmBank | suppliers | RM 2,345.67 |

### 4️⃣ 错误记录
| 文件名 | 错误信息 |
|--------|----------|
| HSBC_0034_2025-06.pdf | 缺少必需字段: ['card_number'] |

---

## 🏷️ 分类规则

### EXPENSES (支出)

| 分类 | 规则 | 示例 |
|------|------|------|
| **Owners Expenses** | 默认分类 | 个人日常消费 |
| **GZ Expenses** | Payment备注包含关键词 | "on behalf", "for client" |
| **Suppliers** | 匹配7个供应商 + 1%手续费 | 7SL, DINAS, HUAWEI |

### PAYMENTS (还款)

| 分类 | 规则 |
|------|------|
| **Owners Payment** | 默认分类 |
| **GZ Payment** | Payment备注包含GZ关键词 |

---

## ⚙️ 配置修改

### 修改GZ关键词

编辑 `config/business_rules.json`:

```json
{
  "classification_rules": {
    "categories": {
      "gz": {
        "keywords": [
          "on behalf",
          "behalf of",
          "for client",
          "新增关键词"  ← 添加这里
        ]
      }
    }
  }
}
```

### 修改供应商列表

```json
{
  "classification_rules": {
    "categories": {
      "suppliers": {
        "supplier_list": [
          "7SL",
          "DINAS",
          "新供应商"  ← 添加这里
        ]
      }
    }
  }
}
```

### 修改手续费比例

```json
{
  "calculation_rules": {
    "supplier_fee": {
      "enabled": true,
      "rate": 0.01  ← 1% = 0.01, 2% = 0.02
    }
  }
}
```

---

## 💡 使用技巧

### 单个文件测试

```bash
# 测试指定PDF
python3 scripts/test_single_pdf.py "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf"
```

### 调整并发数

编辑 `scripts/process_cheok_statements.py`，修改第309行：

```python
results = processor.process_batch(pdf_files, max_workers=5)  # 改为5个并发
```

### 查看处理进度

处理过程中实时显示：
- 当前处理的文件
- 提取的交易数量
- Outstanding Balance
- 进度百分比

---

## 🔧 故障排查

### ❌ Document AI提取失败

**原因**: API配额不足或凭证问题

**解决**:
1. 检查环境变量 `GOOGLE_SERVICE_ACCOUNT_JSON`
2. 确认Google Cloud账单已启用
3. 查看 `错误记录` 工作表

### ❌ 余额不匹配

**原因**: 交易分类错误或PDF数据不完整

**解决**:
1. 使用 `test_single_pdf.py` 测试该文件
2. 检查 `余额验证` 部分的差异
3. 人工核对交易记录

### ❌ 无法找到PDF文件

**原因**: 文件路径不正确

**解决**:
```bash
# 检查文件是否存在
ls -la static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/
```

---

## 📚 详细文档

- **完整使用指南**: `docs/batch_processing_guide.md`
- **Document AI Schema**: `docs/document_ai_schema.md`
- **业务规则配置**: `config/business_rules.json`

---

## 🎯 下一步

1. ✅ **测试系统** - 运行 `test_single_pdf.py`
2. ✅ **批量处理** - 运行 `process_cheok_statements.py`
3. ✅ **检查报告** - 打开Excel查看结算结果
4. ✅ **验证准确度** - 对比银行账单

---

**系统状态**: ✅ 就绪  
**支持银行**: 7家  
**处理能力**: 41份PDF  
**预计耗时**: 约5-10分钟（取决于API速度）
