# 📄 PDF版本生成指南

## 为什么需要PDF版本？

Markdown文件适合：
- ✅ 在线查看和编辑
- ✅ 版本控制（Git）
- ✅ 快速修改

但PDF文件更适合：
- ✅ 正式签署
- ✅ 打印存档
- ✅ 客户下载
- ✅ 法律提交

---

## 🖨️ 转换为PDF的方法

### 方法1：在线转换（最简单）

**推荐工具：**
1. **Pandoc Online** - https://pandoc.org/try/
   - 上传Markdown文件
   - 选择输出格式：PDF
   - 下载

2. **Markdown to PDF** - https://www.markdowntopdf.com/
   - 拖放Markdown文件
   - 自动转换
   - 下载PDF

3. **Dillinger** - https://dillinger.io/
   - 粘贴Markdown内容
   - Export as PDF
   - 保存

### 方法2：使用软件（本地）

**选项A：Visual Studio Code + Extension**
```bash
# 1. 安装VS Code Markdown PDF插件
# 2. 打开.md文件
# 3. 右键 > Markdown PDF: Export (pdf)
```

**选项B：Typora (Windows/Mac/Linux)**
- 下载：https://typora.io/
- 打开.md文件
- File > Export > PDF
- 支持中文字体

**选项C：Pandoc (命令行)**
```bash
# 安装Pandoc
sudo apt-get install pandoc

# 转换完整协议
pandoc credit-card-management-service-agreement.md \
  -o credit-card-management-service-agreement.pdf \
  --pdf-engine=xelatex \
  -V CJKmainfont="Noto Sans CJK SC" \
  -V geometry:margin=2cm

# 转换快速协议
pandoc credit-card-management-quick-agreement.md \
  -o credit-card-management-quick-agreement.pdf \
  --pdf-engine=xelatex \
  -V CJKmainfont="Noto Sans CJK SC" \
  -V geometry:margin=2cm
```

### 方法3：Microsoft Word（推荐用于正式版本）

1. **导入Markdown：**
   - 打开Word
   - File > Open > 选择.md文件
   - Word会自动转换格式

2. **格式调整：**
   - 添加页眉页脚
   - 插入公司Logo
   - 调整字体（标题：Arial 16pt，正文：Arial 11pt）
   - 添加页码

3. **双语排版优化：**
   - 英文：Arial / Calibri
   - 中文：Microsoft YaHei / SimSun

4. **导出PDF：**
   - File > Save As > PDF
   - 设置：高质量打印（300 dpi）

---

## 📋 推荐格式设置

### 页面设置
```
纸张大小：A4 (210mm × 297mm)
边距：上下2cm，左右2.5cm
页眉：公司名称 + Logo
页脚：页码 + 版本号
字体大小：
  - 标题1：18pt（加粗）
  - 标题2：14pt（加粗）
  - 标题3：12pt（加粗）
  - 正文：11pt
  - 注释：9pt
行距：1.15
段落间距：6pt
```

### 封面页（建议添加）
```
[公司Logo]

CREDIT CARD MANAGEMENT
SERVICE AGREEMENT
信用卡管理服务协议

[完整版 / 简化版]

Version 1.0
Effective Date: 1 January 2026

INFINITE GZ SDN BHD
Company Registration No.: [待填写]

Contact: [电话] | [邮箱] | [网站]

---
CONFIDENTIAL - FOR AUTHORIZED USE ONLY
机密文件 - 仅供授权使用
```

---

## ✅ PDF版本检查清单

在分发PDF前，请确认：

**内容检查：**
- ☐ 所有占位符已填写（公司注册号、联系方式等）
- ☐ 页码连续且正确
- ☐ 目录（如有）链接有效
- ☐ 所有表格完整显示
- ☐ 中英文字体清晰可读

**格式检查：**
- ☐ 页面无截断
- ☐ 标题层级清晰
- ☐ 签名栏有足够空间
- ☐ 表格未跨页断开（如可能）
- ☐ 页眉页脚一致

**法律检查：**
- ☐ 版本号和日期正确
- ☐ 免责声明存在
- ☐ 律师审查章（如已审查）
- ☐ 公司盖章位置标记清晰

**技术检查：**
- ☐ 文件大小合理（<5MB）
- ☐ 可搜索（非扫描图片）
- ☐ 可打印（高分辨率）
- ☐ 可复制文本（非只读）
- ☐ PDF/A格式（用于存档）

---

## 🔐 PDF安全设置（可选）

### 保护敏感文档：

**选项1：密码保护**
```
打开密码：用于查看文档
编辑密码：用于修改文档
建议：仅设置编辑密码，允许客户自由查看
```

**选项2：水印**
```
添加文字水印："DRAFT - 草稿版" 或 "SAMPLE - 样本"
位置：对角线，半透明
用于：内部审查或展示版本
```

**选项3：数字签名**
```
使用证书签名
确保文档完整性
客户可验证真实性
```

---

## 📦 文件命名规范

```
[公司缩写]_[文档类型]_[版本]_[日期]_[语言].pdf

示例：
INFINITEGZ_CreditCard_ServiceAgreement_Full_v1.0_20260101_EN-ZH.pdf
INFINITEGZ_CreditCard_ServiceAgreement_Quick_v1.0_20260101_EN-ZH.pdf

简化版：
CreditCard_Agreement_Full_v1.0.pdf
CreditCard_Agreement_Quick_v1.0.pdf
```

---

## 🌐 在线托管建议

### 选项A：公司网站
```
URL结构：
https://infinitegz.com/legal/credit-card-service-agreement.pdf
https://infinitegz.com/legal/credit-card-quick-agreement.pdf

优点：完全控制，品牌化
```

### 选项B：文档管理平台
- **DocuSign** - 电子签署 + 存储
- **Adobe Sign** - PDF签署专业工具
- **PandaDoc** - 文档管理 + 分析
- **Google Drive** - 简单共享

### 选项C：GitHub (当前)
```
https://github.com/zee14913913/replit-credit-pilot/tree/main/infinitegz-website/public/legal-documents

优点：版本控制，免费托管
缺点：需要GitHub账号查看
```

---

## 🚀 快速生成PDF（推荐工作流）

### 步骤1：准备Markdown
```bash
cd /home/user/webapp/infinitegz-website/public/legal-documents
ls -la
```

### 步骤2：在线转换
1. 访问 https://www.markdowntopdf.com/
2. 上传 `credit-card-management-service-agreement.md`
3. 等待转换（约30秒）
4. 下载PDF

### 步骤3：质量检查
- 在Adobe Reader或Chrome打开
- 检查中文字体显示
- 测试打印预览
- 验证签名栏空间

### 步骤4：最终处理（Microsoft Word）
1. Word打开PDF
2. 添加封面页
3. 插入公司Logo
4. 添加页眉页脚
5. 导出最终PDF

---

## 💡 专业提示

### 打印建议：
- **纸张：** 80gsm白色A4纸（至少）
- **打印：** 双面打印（节省纸张）
- **装订：** 左侧装订，留2.5cm边距
- **份数：** 
  - 原件：公司存档（盖章）
  - 副本：客户（盖章）
  - 副本：法务部门存档

### 存储建议：
- **物理：** 防火文件柜，按年份和客户ID分类
- **数字：** 云端备份（Google Drive/OneDrive）+ 本地备份
- **保留期：** 7年（符合马来西亚法律）

### 版本管理：
```
v1.0 - 初版（2026-01-01）
v1.1 - 律师审查后修订（待定）
v1.2 - 首次客户反馈后优化（待定）
v2.0 - 年度大修订（2027-01-01）
```

---

## ❓ 常见问题

**Q: PDF能否直接在平板上签署？**
A: 可以！使用以下App：
- Adobe Acrobat Reader（免费）
- GoodReader
- PDF Expert
- DocuSign（电子签名）

**Q: 如何确保PDF无法被篡改？**
A: 
1. 使用数字签名
2. 转换为PDF/A格式
3. 设置编辑密码
4. 添加水印

**Q: 客户说中文字体显示为方块？**
A: PDF生成时嵌入中文字体：
- Pandoc: 使用 `-V CJKmainfont`
- Word: 导出时选择"嵌入字体"
- 在线工具: 使用支持Unicode的工具

**Q: PDF文件太大（>10MB）？**
A: 压缩方法：
- Adobe Acrobat: 另存为 > 缩小文件大小
- 在线工具: https://www.ilovepdf.com/compress_pdf
- 命令行: `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf`

---

## 📞 需要帮助？

如果你在PDF转换过程中遇到问题：

1. **字体显示问题** → 使用Word转换并嵌入字体
2. **格式错乱** → 使用Typora或Pandoc命令行
3. **文件太大** → 使用压缩工具或降低图片质量
4. **需要批量转换** → 使用Pandoc脚本批处理

---

**提示：** 在正式使用PDF版本前，建议先打印一份测试版，确保所有内容清晰可读，签名栏位置合适。

**最佳实践：** 保留Markdown原始版本用于修改，只将PDF用于签署和存档。
