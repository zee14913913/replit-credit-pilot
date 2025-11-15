# 🚀 MacBook快速开始指南

## 📦 第1步：下载文件（在Replit）

下载以下3个文件到您的MacBook：

1. **CCC_89_PDF_Files.tar.gz** (89个PDF文件)
2. **mac_pdf_processor.py** (Mac处理脚本)
3. **VBA_LOCAL_PROCESSING_GUIDE.md** (详细指南)

---

## 💻 第2步：在MacBook上设置（终端命令）

```bash
# 创建工作目录
mkdir -p ~/CCC_Processing/PDFs
mkdir -p ~/CCC_Processing/JSON_Output

# 进入下载目录（通常是~/Downloads）
cd ~/Downloads

# 解压PDF文件
tar -xzf CCC_89_PDF_Files.tar.gz -C ~/CCC_Processing/PDFs

# 复制处理脚本
cp mac_pdf_processor.py ~/CCC_Processing/

# 安装Python依赖
pip3 install pdfplumber openpyxl pandas

# 如果pip3不可用，使用：
# python3 -m pip install pdfplumber openpyxl pandas
```

---

## ▶️ 第3步：运行处理脚本

```bash
# 进入工作目录
cd ~/CCC_Processing

# 运行脚本（会自动处理89个PDF）
python3 mac_pdf_processor.py
```

**预计时间：20-30分钟**

处理完成后，您会看到：
```
✅ 成功: 89 个文件
📁 JSON文件已保存到: /Users/您的用户名/CCC_Processing/JSON_Output
```

---

## 📤 第4步：上传JSON回Replit

### 方法A：手动上传（简单）
1. 打开Replit项目
2. 导航到 `static/uploads/customers/Be_rich_CCC/vba_json_files/`
3. 拖拽所有JSON文件到此目录

### 方法B：使用命令行（更快）
```bash
# 在MacBook终端运行
# 需要安装Replit CLI
curl -s https://api.replit.com/install.sh | sh
replit login

# 上传JSON文件
cd ~/CCC_Processing/JSON_Output
for json in *.json; do
    replit upload "$json" static/uploads/customers/Be_rich_CCC/vba_json_files/
done
```

---

## 🎯 第5步：Replit处理（回到Replit）

上传完成后，在Replit终端运行：

```bash
python3 scripts/process_uploaded_json.py
```

这将：
1. ✅ 验证所有JSON
2. ✅ 入库处理
3. ✅ 自动生成最终结算报告
4. ✅ 显示GZ OS Balance

---

## ⏱️ 总时间估计

- 步骤1-2（设置）：5分钟
- 步骤3（处理）：20-30分钟
- 步骤4（上传）：5-10分钟
- 步骤5（结算）：2分钟

**总计：30-50分钟**

---

## ❓ 常见问题

### Q: 如果pip3安装失败？
```bash
# 使用Homebrew安装Python3
brew install python3

# 或使用系统自带Python
python3 -m ensurepip --upgrade
```

### Q: 如果pdfplumber安装失败？
```bash
# 单独安装依赖
pip3 install --upgrade pip
pip3 install pdfplumber --no-cache-dir
```

### Q: 处理过程中出错？
- 检查PDF文件是否完整解压
- 确认PDF文件在 `~/CCC_Processing/PDFs/credit_cards/` 目录下
- 查看错误信息并反馈

---

## 📞 需要帮助？

如有任何问题，立即在Replit反馈！
