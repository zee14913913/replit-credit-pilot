# INFINITE GZ - 完整集成指南

## 📚 目录

1. [系统架构](#系统架构)
2. [快速开始](#快速开始)
3. [详细步骤](#详细步骤)
4. [API文档](#api文档)
5. [故障排除](#故障排除)
6. [附录](#附录)

---

## 🏗️ 系统架构

### 混合架构设计

```
┌─────────────────────────────────────────────────────────┐
│  客户端（Windows + Excel + VBA）                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  1. 账单文件准备                                │     │
│  │     - Excel/CSV 直接使用                        │     │
│  │     - PDF → Excel转换（Tabula/Adobe）           │     │
│  └────────────┬───────────────────────────────────┘     │
│               │                                          │
│               ▼                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  2. VBA智能解析                                 │     │
│  │     - 识别银行格式（PBB/MBB/CIMB/RHB/HLB）      │     │
│  │     - 提取账户信息                               │     │
│  │     - 逐行读取交易                               │     │
│  │     - 30+智能分类                                │     │
│  │     - DR/CR自动识别                              │     │
│  │     - 余额验证                                   │     │
│  └────────────┬───────────────────────────────────┘     │
│               │                                          │
│               ▼                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  3. 标准JSON导出                                │     │
│  │     - account_info                              │     │
│  │     - transactions[]                            │     │
│  │     - summary                                   │     │
│  └────────────┬───────────────────────────────────┘     │
└───────────────┼─────────────────────────────────────────┘
                │
                │ HTTPS Upload
                ▼
┌─────────────────────────────────────────────────────────┐
│  云端服务器（Replit Flask）                               │
│  ┌────────────────────────────────────────────────┐     │
│  │  4. API接收验证                                 │     │
│  │     POST /api/upload/vba-json                   │     │
│  │     POST /api/upload/vba-batch                  │     │
│  └────────────┬───────────────────────────────────┘     │
│               │                                          │
│               ▼                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  5. 数据入库处理                                │     │
│  │     - JSON格式验证                               │     │
│  │     - 写入SQLite数据库                           │     │
│  │     - 生成月结报表                               │     │
│  │     - AI智能分析                                 │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 技术决策

| 组件 | 技术选择 | 理由 |
|------|----------|------|
| **客户端解析** | VBA | ✅ 准确率高、成本低、团队熟悉 |
| **PDF转换** | Tabula/Adobe | ✅ 专业工具，保留表格格式 |
| **数据传输** | JSON | ✅ 标准格式，易验证 |
| **服务器** | Replit Flask | ✅ 云端部署，易扩展 |
| **数据库** | SQLite | ✅ 轻量级，无需配置 |

---

## 🚀 快速开始

### 前置要求

✅ **客户端（必需）：**
- Windows 10/11
- Microsoft Excel 2016+ （启用宏）

✅ **PDF转换（可选）：**
- Adobe Acrobat Pro（推荐）
- Tabula（免费）
- Python 3.7+（使用我们的工具）

✅ **Replit服务器（自动提供）：**
- 无需额外配置

### 3分钟快速体验

**步骤1：下载VBA模板**
```
vba_templates/
├── 1_CreditCardParser.vba
├── 2_BankStatementParser.vba
├── 4_DataValidator.vba
└── 5_Usage_Guide.md
```

**步骤2：导入VBA到Excel**
1. 打开Excel账单文件
2. 按 `Alt + F11` 打开VBA编辑器
3. 插入 → 模块
4. 复制粘贴 `1_CreditCardParser.vba` 代码

**步骤3：运行解析器**
1. 按 `Alt + F8`
2. 选择 `ParseCreditCardStatement`
3. 点击"运行"
4. 获得JSON文件

**步骤4：上传到Replit**
- 使用Replit网页界面上传JSON文件

---

## 📖 详细步骤

### 第一阶段：准备账单文件

#### 情况A：Excel/CSV账单

✅ **无需额外处理，直接进入VBA解析**

#### 情况B：PDF账单

**方案1：Adobe Acrobat Pro（最佳准确率）**

1. 打开PDF文件
2. 文件 → 导出为 → 电子表格 → Microsoft Excel工作簿
3. 选择页面范围
4. 点击"导出"
5. 得到Excel文件

**方案2：Tabula（免费开源）**

1. 下载安装Tabula：https://tabula.technology/
2. 导入PDF文件
3. 手动选择表格区域
4. Export → Excel
5. 得到Excel文件

**方案3：Python自动化工具（我们提供）**

```bash
cd tools/pdf_converter
python pdf_to_excel.py ../../pdfs/statement.pdf
```

批量转换：
```bash
python pdf_to_excel.py ../../pdfs/ -b
```

---

### 第二阶段：VBA解析

#### 步骤1：导入VBA模块

1. **打开Excel文件**
2. **启用宏（如未启用）**
   - 文件 → 选项 → 信任中心 → 宏设置
   - 选择"启用所有宏"
3. **打开VBA编辑器**
   - 按 `Alt + F11`
4. **插入新模块**
   - VBAProject右键 → 插入 → 模块
5. **复制粘贴代码**
   - 信用卡：粘贴 `1_CreditCardParser.vba`
   - 银行流水：粘贴 `2_BankStatementParser.vba`
   - 验证器（可选）：粘贴 `4_DataValidator.vba`

#### 步骤2：运行解析器

**信用卡账单：**
```vba
1. 按 Alt + F8
2. 选择 "ParseCreditCardStatement"
3. 点击"运行"
4. 等待完成（3-10秒）
5. JSON文件保存在同一文件夹
```

**银行流水：**
```vba
1. 按 Alt + F8
2. 选择 "ParseBankStatement"
3. 点击"运行"
4. 等待完成（3-10秒）
5. JSON文件保存在同一文件夹
```

#### 步骤3：验证数据质量（推荐）

```vba
1. 按 Alt + F8
2. 选择 "GenerateValidationReport"
3. 点击"运行"
4. 查看即时窗口（Ctrl + G）的验证报告
```

**验证报告示例：**
```
================================================================================
数据验证报告
================================================================================

账单类型: 信用卡账单

【余额验证】
✓ 余额验证通过
  期初余额: RM 5,000.00
  期末余额: RM 3,500.00
  计算余额: RM 3,500.00
  差异: RM 0.00

【数据完整性】
✓ 数据完整性检查通过

【综合评分】
  质量评分: 100%
  ✓ 数据质量优秀，可直接上传

================================================================================
```

---

### 第三阶段：上传到Replit

#### 方法A：网页界面上传（推荐新手）

1. **登录Replit账户**
2. **访问上传页面**
   ```
   https://your-replit-url.repl.co/upload
   ```
3. **选择JSON文件**
   - 单文件上传：点击"选择文件"
   - 批量上传：按住Ctrl选择多个JSON文件
4. **点击"上传"**
5. **查看结果**

#### 方法B：API上传（推荐高级用户）

**单文件上传：**
```bash
curl -X POST https://your-replit-url.repl.co/api/upload/vba-json \
  -F "file=@credit_card_20241115_143052.json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**批量上传：**
```bash
curl -X POST https://your-replit-url.repl.co/api/upload/vba-batch \
  -F "files=@file1.json" \
  -F "files=@file2.json" \
  -F "files=@file3.json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**PowerShell脚本（Windows批量上传）：**
```powershell
# 批量上传当前文件夹所有JSON
$files = Get-ChildItem -Filter *.json
foreach ($file in $files) {
    curl.exe -X POST https://your-replit-url.repl.co/api/upload/vba-json `
        -F "file=@$($file.Name)" `
        -H "Authorization: Bearer YOUR_TOKEN"
}
```

---

## 📡 API文档

### POST /api/upload/vba-json

接收单个VBA处理后的JSON文件

**请求：**
```
POST /api/upload/vba-json
Content-Type: multipart/form-data

file: <JSON文件>
```

**成功响应（200）：**
```json
{
  "status": "success",
  "message": "JSON数据接收成功",
  "document_type": "credit_card",
  "parsed_by": "VBA Parser v1.0",
  "parsed_at": "2024-11-15 14:30:52",
  "total_transactions": 25
}
```

**错误响应（400/500）：**
```json
{
  "status": "error",
  "message": "JSON格式错误：缺少status字段"
}
```

---

### POST /api/upload/vba-batch

批量接收多个JSON文件

**请求：**
```
POST /api/upload/vba-batch
Content-Type: multipart/form-data

files: <JSON文件1>
files: <JSON文件2>
files: <JSON文件N>
```

**成功响应（200）：**
```json
{
  "status": "success",
  "total_files": 10,
  "success_count": 9,
  "failed_count": 1,
  "results": [
    {
      "filename": "credit_card_1.json",
      "status": "success",
      "document_type": "credit_card",
      "transactions": 25
    },
    {
      "filename": "bank_statement_1.json",
      "status": "error",
      "message": "JSON格式错误"
    }
  ]
}
```

---

## 🔧 故障排除

### 问题1：VBA运行出错

**症状：**
```
编译错误：找不到函数 FindCellValue
```

**解决方法：**
1. 确保完整复制粘贴VBA代码
2. 检查是否包含所有辅助函数
3. 重新导入VBA模块

---

### 问题2：JSON文件未生成

**症状：**
VBA运行完成，但文件夹中没有JSON文件

**解决方法：**
1. 检查文件夹写入权限
2. 查看VBA即时窗口（Ctrl + G）的错误信息
3. 手动指定输出路径

---

### 问题3：余额验证失败

**症状：**
```
✗ 余额验证失败！
  差异: RM 150.00
```

**解决方法：**
1. 检查Excel数据是否完整（PDF转换可能丢失数据）
2. 人工核对账单原件
3. 调整VBA代码中的行号范围
4. 如差异小于RM 1.00，可能是四舍五入误差，可接受

---

### 问题4：上传到Replit失败

**症状：**
```
{
  "status": "error",
  "message": "JSON格式错误"
}
```

**解决方法：**
1. 用JSON验证器检查文件格式：https://jsonlint.com/
2. 确认JSON包含必填字段（参考格式规范）
3. 检查日期格式是否为 `dd-mm-yyyy`
4. 检查金额是否为数字类型（不带逗号和货币符号）

---

### 问题5：PDF转Excel格式混乱

**症状：**
表格合并错误、数据缺失

**解决方法：**
1. 使用Adobe Acrobat Pro（准确率最高）
2. 在Tabula中手动调整表格区域
3. 使用我们的Python工具：
   ```bash
   python pdf_to_excel.py statement.pdf -m tabula
   ```
4. 转换后人工检查Excel数据完整性

---

## 📊 性能参考

| 操作 | 单文件 | 批量100文件 |
|------|--------|-------------|
| **PDF→Excel** | 3-10秒 | 5-15分钟 |
| **VBA解析** | 2-5秒 | 3-8分钟 |
| **上传Replit** | 1-3秒 | 1-2分钟 |
| **总耗时** | ~10秒 | ~20分钟 |

---

## 📂 附录

### 附录A：支持的银行格式

| 银行 | 代码 | 信用卡 | 银行流水 |
|------|------|--------|----------|
| Public Bank | PBB | ✅ | ✅ |
| Maybank | MBB | ✅ | ✅ |
| CIMB | CIMB | ✅ | ✅ |
| RHB | RHB | ✅ | ✅ |
| Hong Leong Bank | HLB | ✅ | ✅ |
| HSBC | HSBC | 🔄 | 🔄 |
| Alliance Bank | ABB | 🔄 | 🔄 |

✅ = 已支持 | 🔄 = 开发中

---

### 附录B：文件结构

```
vba_templates/
├── 1_CreditCardParser.vba          # 信用卡解析器
├── 2_BankStatementParser.vba       # 银行流水解析器
├── 3_PDFtoExcel_Guide.vba          # PDF转换指南
├── 4_DataValidator.vba              # 数据验证器
├── 5_Usage_Guide.md                 # 使用指南
├── JSON_Format_Specification.md    # JSON格式规范
└── COMPLETE_INTEGRATION_GUIDE.md   # 完整集成指南（本文件）

tools/pdf_converter/
├── pdf_to_excel.py                  # Python转换工具
└── README.md                        # 工具说明
```

---

### 附录C：技术支持

**遇到问题？联系我们：**

📧 **Email：** [Your Email]  
📞 **电话：** [Your Phone]  
💬 **项目：** INFINITE GZ  
🌐 **网站：** [Your Website]  

**工作时间：** 周一至周五 9:00-18:00 (GMT+8)

---

## ✅ 检查清单

使用前请确认：

- [ ] 已安装Microsoft Excel 2016+
- [ ] 已启用Excel宏
- [ ] 已下载所有VBA模板
- [ ] 已准备账单文件（Excel或PDF）
- [ ] 已了解JSON格式规范
- [ ] 已获得Replit访问权限

---

**祝您使用愉快！如有任何问题，随时联系我们。** 🚀

**版本 1.0.0 | 2024-11-15**
