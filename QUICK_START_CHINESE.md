# 🚀 Mac快速开始（中文指南）

## 📦 第1步：下载文件（5分钟）

在Replit下载以下文件到您的Mac：

1. **CCC_89_PDF_Files.tar.gz** (32 MB)
2. **mac_excel_processor.py** (处理脚本)
3. **MAC_COMPLETE_GUIDE.md** (完整指南)

## 💻 第2步：设置环境（3分钟）

打开Mac终端，运行以下命令：

```bash
# 创建工作目录
mkdir -p ~/CCC_Processing/{PDFs,Excel_Files,JSON_Output}

# 进入下载目录
cd ~/Downloads

# 解压PDF
tar -xzf CCC_89_PDF_Files.tar.gz
mv credit_cards ~/CCC_Processing/PDFs/

# 复制脚本
cp mac_excel_processor.py ~/CCC_Processing/

# 安装Python库
pip3 install pandas openpyxl
```

## 📄 第3步：PDF转Excel（15-20分钟）

**方法A：Adobe Acrobat Pro（推荐）**
- 打开Adobe → 导出PDF → Excel工作簿
- 保存到 `~/CCC_Processing/Excel_Files/`

**方法B：在线工具**
- 访问 https://www.ilovepdf.com/pdf_to_excel
- 批量上传PDF → 转换 → 下载

**方法C：Tabula（免费）**
```bash
brew install tabula
cd ~/CCC_Processing/PDFs/credit_cards
for pdf in *.pdf; do
    tabula -o "~/CCC_Processing/Excel_Files/${pdf%.pdf}.xlsx" "$pdf"
done
```

## ▶️ 第4步：运行处理脚本（5-10分钟）

```bash
cd ~/CCC_Processing
python3 mac_excel_processor.py
```

**预期输出：**
```
✅ 成功: 89 个文件
📈 成功率: 100.0%
📁 JSON文件已保存
```

## 📤 第5步：上传JSON到Replit（5分钟）

### 方法A：手动上传
1. 打开Replit项目
2. 进入 `static/uploads/customers/Be_rich_CCC/vba_json_files/`
3. 拖拽所有JSON文件

### 方法B：打包上传
```bash
cd ~/CCC_Processing/JSON_Output
tar -czf ccc_json.tar.gz *.json
# 在Replit上传这个tar.gz文件
```

## 🎯 第6步：Replit生成报告（2分钟）

在Replit终端运行：

```bash
# 处理JSON
python3 scripts/process_uploaded_json.py

# 生成结算报告
python3 scripts/generate_ccc_settlement_report.py
```

## ✅ 完成！

您将看到：
- ✅ Owner消费/付款合计
- ✅ GZ消费/付款合计
- ✅ Supplier Fees (1%)
- ✅ **GZ Outstanding Balance**

---

## ⏱️ 总时间：30-45分钟

## 📞 需要帮助？

遇到问题立即在Replit反馈！
