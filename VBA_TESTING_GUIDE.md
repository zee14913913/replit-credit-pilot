# INFINITE GZ - VBA混合架构测试配置指南

## 📌 完整配置信息

### 1️⃣ VBA模板文件访问

#### 📂 文件位置
```
项目路径: /home/runner/workspace/vba_templates/
包含7个文件:
├── 1_CreditCardParser.vba          (12KB)
├── 2_BankStatementParser.vba       (13KB)
├── 3_PDFtoExcel_Guide.vba          (7KB)
├── 4_DataValidator.vba              (10KB)
├── 5_Usage_Guide.md                 (6KB)
├── JSON_Format_Specification.md    (9KB)
└── COMPLETE_INTEGRATION_GUIDE.md   (14KB)
```

#### 📥 下载方式

**方式A：网页下载（推荐）**
```
访问: https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/vba/upload
点击页面顶部"下载VBA模板套件"按钮
下载文件: vba_templates.tar.gz (16KB)
```

**方式B：直接URL下载**
```
https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/static/vba_templates.tar.gz
```

**方式C：使用curl命令**
```bash
curl -O https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/static/vba_templates.tar.gz
```

#### 📦 解压文件
```bash
# Windows (7-Zip)
7z x vba_templates.tar.gz
7z x vba_templates.tar

# Linux/Mac
tar -xzf vba_templates.tar.gz
```

---

### 2️⃣ Replit项目访问信息

#### 🌐 完整URL
```
主URL: https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev
端口: 5000 (自动映射)
```

#### 🔗 API端点完整地址

**单文件上传API:**
```
POST https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/api/upload/vba-json

Content-Type: multipart/form-data
Body: file=<your_json_file.json>
```

**批量上传API:**
```
POST https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/api/upload/vba-batch

Content-Type: multipart/form-data
Body: files=<file1.json>&files=<file2.json>&files=<file3.json>
```

#### 🔐 认证方式

**登录认证：** ✅ 需要（使用Flask Session）

**获取Session Cookie:**
1. 先登录系统
2. Cookie自动保存
3. 后续API调用自动携带Cookie

---

### 3️⃣ 前端上传界面

#### ✅ 已创建专用上传页面

**网页界面URL:**
```
https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/vba/upload
```

**功能特性:**
- ✅ 下载VBA模板套件（页面顶部）
- ✅ 单文件拖放上传
- ✅ 批量文件拖放上传
- ✅ 实时上传进度
- ✅ 详细结果显示（账单ID、银行、月份、交易数）
- ✅ 美观的UI设计（黑色背景+热粉色+深紫色）

---

### 4️⃣ 数据查看和结算计算

#### 📊 查看入库数据

**月度账单查看:**
```
访问: /credit-cards 页面
查看: 所有客户的信用卡和月度账单
```

**交易明细查看:**
```
访问: /statements/<statement_id> 页面
查看: 具体账单的所有交易明细
```

#### 💰 结算计算功能

**当前状态:** 数据已入库到以下表：
- `monthly_statements` - 月度账单汇总
- `monthly_statement_cards` - 卡片关联
- `transactions` - 交易明细
- `customers` - 客户信息
- `credit_cards` - 信用卡信息

**结算报表页面:**
```
访问: /reports 页面
功能: 生成月度报表、导出Excel/PDF
```

**是否需要新界面:** 
- ❓ 请确认您需要的结算计算具体功能
- ❓ 是否需要GZ vs OWNER的费用分摊计算？
- ❓ 是否需要特定的结算报表格式？

---

### 5️⃣ 测试账号

#### 🔑 Admin账号（推荐测试用）

```
登录URL: https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/login

Email:    infinitegz.reminder@gmail.com
Password: Be_rich13
权限:     Admin（完全访问权限）
```

#### 👤 现有客户账号

如需使用现有账号，请查看数据库中的customers表。

---

## 🚀 完整测试流程

### 步骤1：下载VBA模板
```
1. 访问: https://.../vba/upload
2. 点击"下载VBA模板套件"按钮
3. 保存 vba_templates.tar.gz
4. 解压获得7个文件
```

### 步骤2：使用VBA解析账单
```
1. 打开Excel信用卡账单文件
2. 导入VBA模块（Alt + F11）
3. 粘贴 1_CreditCardParser.vba 代码
4. 运行 ParseCreditCardStatement (Alt + F8)
5. 获得JSON文件（同一文件夹）
```

### 步骤3：登录Replit系统
```
1. 访问: https://.../login
2. 输入Email: infinitegz.reminder@gmail.com
3. 输入Password: Be_rich13
4. 点击登录
```

### 步骤4：上传JSON到Replit

**方式A：网页界面上传（推荐）**
```
1. 访问: https://.../vba/upload
2. 拖放JSON文件到上传区
3. 点击"上传到Replit"按钮
4. 查看上传结果
```

**方式B：API上传（curl）**
```bash
curl -X POST https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/api/upload/vba-json \
  -F "file=@credit_card_20241115.json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### 步骤5：验证数据入库
```
1. 查看返回的 statement_id
2. 访问: /credit-cards 页面
3. 找到对应银行和月份的账单
4. 点击查看交易明细
5. 确认数据正确
```

---

## 📋 测试检查清单

### ✅ VBA模板测试
- [ ] 成功下载VBA模板套件
- [ ] 解压获得7个文件
- [ ] 导入VBA到Excel
- [ ] 运行信用卡解析器
- [ ] 生成JSON文件
- [ ] JSON格式验证通过

### ✅ API上传测试
- [ ] 登录Replit系统成功
- [ ] 访问VBA上传页面
- [ ] 单文件上传成功
- [ ] 批量上传成功
- [ ] 收到正确的statement_id
- [ ] 返回正确的交易数量

### ✅ 数据验证测试
- [ ] 数据写入monthly_statements表
- [ ] 数据写入transactions表
- [ ] 客户信息正确创建
- [ ] 信用卡信息正确创建
- [ ] 余额数据准确
- [ ] 交易分类正确

### ✅ 批量处理测试
- [ ] 批量上传5-10个文件
- [ ] 所有文件处理成功
- [ ] 失败文件正确报告
- [ ] 数据库无重复记录

---

## 🔧 故障排除

### 问题1：无法下载VBA模板
**解决：** 
- 检查URL是否正确
- 尝试直接访问: /static/vba_templates.tar.gz
- 使用curl命令下载

### 问题2：API返回401未授权
**解决：**
- 确认已登录系统
- 检查session cookie是否有效
- 重新登录后再试

### 问题3：JSON上传失败
**解决：**
- 验证JSON格式是否正确
- 确认status字段为"success"
- 确认document_type字段存在
- 使用网页界面查看详细错误信息

### 问题4：数据未入库
**解决：**
- 检查API返回的statement_id
- 查看服务器日志
- 验证数据库连接
- 联系技术支持

---

## 📞 技术支持

**项目:** INFINITE GZ  
**系统:** Smart Credit & Loan Manager  
**架构:** VBA Hybrid (Client + Replit Cloud)  

**需要帮助？**
- 查看: vba_templates/COMPLETE_INTEGRATION_GUIDE.md
- 查看: vba_templates/5_Usage_Guide.md
- 查看: vba_templates/JSON_Format_Specification.md

---

## 🎯 快速开始命令

```bash
# 1. 下载VBA模板
curl -O https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/static/vba_templates.tar.gz

# 2. 解压
tar -xzf vba_templates.tar.gz

# 3. 测试单文件上传（替换YOUR_SESSION_COOKIE）
curl -X POST https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev/api/upload/vba-json \
  -F "file=@test.json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

---

**准备就绪！开始测试吧！** 🚀

**版本:** 1.0.0  
**更新日期:** 2024-11-15
