# INFINITE GZ - VBA混合架构项目结构

## 📌 项目概述
INFINITE GZ信用卡系统 - VBA客户端 + Replit云端混合架构
- **客户端**: Windows + Excel + VBA解析器
- **云端**: Flask后端接收标准JSON数据
- **数据库**: SQLite (本地开发)

---

## 🗂️ 核心文件结构

### 1️⃣ VBA模板系统 (客户端)
```
vba_templates/
├── 1_CreditCardParser.vba          # 信用卡账单解析器 (12KB)
├── 2_BankStatementParser.vba       # 银行账单解析器 (13KB)
├── 3_PDFtoExcel_Guide.vba          # PDF转Excel指南 (7KB)
├── 4_DataValidator.vba             # 数据验证器 (10KB)
├── 5_Usage_Guide.md                # 使用指南 (6KB)
├── JSON_Format_Specification.md    # JSON格式规范 (9KB)
└── COMPLETE_INTEGRATION_GUIDE.md   # 完整集成指南 (14KB)
```
**用途**: VBA模板套件，用户下载后在Excel中运行解析账单

**发布位置**: 
- 打包文件: `static/vba_templates.tar.gz` (16KB)
- 下载页面: `/vba/upload` 页面顶部下载按钮

---

### 2️⃣ PDF转换工具 (可选客户端工具)
```
tools/pdf_converter/
├── pdf_to_excel.py                 # Python批量转换工具
└── README.md                       # 工具使用说明
```
**用途**: 批量将PDF账单转换为Excel格式，方便VBA解析

---

### 3️⃣ VBA JSON处理服务 (云端核心)
```
services/vba_json_processor.py      # 540行核心处理逻辑
```
**功能**:
- 解析VBA生成的标准JSON
- 验证数据格式
- 插入SQLite数据库 (monthly_statements, transactions表)
- 自动创建客户和信用卡记录
- 支持单文件和批量处理

---

### 4️⃣ Web上传界面 (云端前端)
```
templates/vba_upload.html           # VBA JSON上传页面
```
**访问URL**: `/vba/upload`

**功能**:
- 下载VBA模板套件
- 单文件拖放上传
- 批量文件拖放上传
- 实时上传结果显示
- 美观UI (黑色+热粉色+深紫色)

---

### 5️⃣ API端点 (云端接口)
```python
# app.py 中的API路由

@app.route('/vba/upload')                    # 上传页面
@app.route('/api/upload/vba-json')           # 单文件上传API
@app.route('/api/upload/vba-batch')          # 批量上传API
```

**完整URL**:
```
https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/vba/upload
https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/api/upload/vba-json
https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/api/upload/vba-batch
```

---

## 🗄️ 数据库结构

### SQLite数据库
**路径**: `db/smart_loan_manager.db`

**核心表**:
- `customers` - 客户信息
- `credit_cards` - 信用卡信息
- `monthly_statements` - 月度账单汇总
- `monthly_statement_cards` - 卡片关联
- `transactions` - 交易明细

---

## 📋 测试配置文档
```
VBA_TESTING_GUIDE.md                # 完整测试配置指南
```

**包含内容**:
- VBA模板下载方式 (3种)
- API访问信息 (完整URL)
- 认证方式说明
- 测试账号配置
- 端到端测试流程
- 故障排除指南

---

## 🎯 数据流程

### 完整工作流：
```
1. 用户下载VBA模板
   ↓
2. 客户端Excel运行VBA解析PDF/Excel账单
   ↓
3. VBA生成标准JSON文件
   ↓
4. 用户访问 /vba/upload 上传JSON
   ↓
5. Flask接收并调用 vba_json_processor.py
   ↓
6. 数据验证 + 插入SQLite数据库
   ↓
7. 返回上传结果 (statement_id, 银行, 月份, 交易数)
   ↓
8. 用户访问 /credit-cards 查看数据
```

---

## 🔐 认证系统

**登录方式**: Flask Session认证

**测试账号**:
```
Email:    infinitegz.reminder@gmail.com
Password: Be_rich13
权限:     Admin (完全访问)
```

**访问控制**:
- `/vba/upload` - 需要登录
- `/api/upload/vba-json` - 需要Admin或Accountant权限
- `/api/upload/vba-batch` - 需要Admin或Accountant权限

---

## 📦 发布资源

### 静态资源
```
static/vba_templates.tar.gz         # VBA模板打包文件 (16KB)
```

**生成方式**:
```bash
cd vba_templates
tar -czf ../static/vba_templates.tar.gz *
```

---

## 🔧 开发工具

### Python后端服务 (备用)
```
services/excel_parsers/
├── bank_statement_excel_parser.py  # 银行账单解析器 (备用)
├── credit_card_excel_parser.py     # 信用卡解析器 (备用)
├── bank_detector.py                # 银行格式检测
└── transaction_classifier.py       # 交易分类器 (30+类别)
```
**用途**: VBA的Python备份方案，系统韧性保障

---

## 📊 系统监控

### 日志查看
```
/admin/logs                         # 系统日志查看
/admin/audit                        # 审计日志查看
```

### 数据查看
```
/credit-cards                       # 信用卡和账单查看
/statements/<statement_id>          # 交易明细查看
/reports                            # 报表生成和导出
```

---

## 🗃️ 归档文件

### 测试文件归档
```
archive_old/
└── attached_assets/                # 旧测试PDF和图片文件
```
**说明**: 已清理的测试文件存档，不影响系统运行

---

## 🚀 快速开始

### 用户端操作：
```
1. 访问: https://.../vba/upload
2. 下载VBA模板套件
3. 在Excel中运行VBA解析账单
4. 上传生成的JSON文件
5. 查看数据入库结果
```

### 开发端操作：
```
1. 修改 vba_templates/ 中的VBA代码
2. 重新打包: tar -czf static/vba_templates.tar.gz vba_templates/*
3. 重启Flask服务器
4. 测试上传功能
```

---

## 📝 文档索引

### 用户文档
- `VBA_TESTING_GUIDE.md` - 测试配置指南
- `vba_templates/5_Usage_Guide.md` - VBA使用指南
- `vba_templates/JSON_Format_Specification.md` - JSON格式规范
- `vba_templates/COMPLETE_INTEGRATION_GUIDE.md` - 完整集成指南

### 技术文档
- `PROJECT_STRUCTURE.md` - 项目结构说明 (本文档)
- `replit.md` - 系统架构和技术决策
- `tools/pdf_converter/README.md` - PDF转换工具说明

---

## 🎯 未来开发计划

### 待开发功能
1. **GZ vs OWNER费用分摊结算系统**
   - 自动区分Owner消费和GZ消费
   - 计算月度分摊金额
   - 生成结算报表 (明细 + 汇总)

### 技术改进
- [ ] 增强VBA错误处理
- [ ] 支持更多银行格式
- [ ] 优化大文件上传性能
- [ ] 添加数据导出功能

---

## 📞 技术支持

**项目**: INFINITE GZ Smart Credit & Loan Manager  
**架构**: VBA Hybrid (Client + Replit Cloud)  
**版本**: 1.0.0  
**更新日期**: 2024-11-15

---

**系统就绪！开始使用吧！** 🚀
