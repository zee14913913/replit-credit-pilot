# PDF转Excel自动化工具

## 🎯 功能

将PDF格式的信用卡账单和银行流水自动转换为Excel格式，方便VBA解析。

## 📦 安装

### 前置要求

1. **Python 3.7+**
2. **Java Runtime Environment (JRE)** - Tabula需要Java环境

### 安装Python依赖

```bash
pip install tabula-py openpyxl pdfplumber pandas
```

如果安装失败，可以分别安装：

```bash
pip install tabula-py
pip install openpyxl
pip install pdfplumber
pip install pandas
```

## 🚀 使用方法

### 方法1：单文件转换

```bash
python pdf_to_excel.py statement.pdf
```

输出：`statement.xlsx`（同一文件夹）

指定输出路径：

```bash
python pdf_to_excel.py statement.pdf -o output/statement.xlsx
```

### 方法2：批量转换

```bash
python pdf_to_excel.py pdf_folder/ -b
```

或

```bash
python pdf_to_excel.py pdf_folder/ -o excel_folder/ -b
```

### 方法3：指定转换方法

```bash
# 使用Tabula（推荐，准确率高）
python pdf_to_excel.py statement.pdf -m tabula

# 使用PDFPlumber（备用）
python pdf_to_excel.py statement.pdf -m pdfplumber

# 自动选择（默认）
python pdf_to_excel.py statement.pdf -m auto
```

## 📋 示例

### 示例1：转换单个PDF

```bash
cd tools/pdf_converter
python pdf_to_excel.py ../../static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/2024-09/Maybank_5943_2024-09-03.pdf
```

### 示例2：批量转换整个文件夹

```bash
python pdf_to_excel.py ../../static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/ -b
```

### 示例3：转换后保存到指定文件夹

```bash
python pdf_to_excel.py input_pdfs/ -o output_excel/ -b
```

## 🔧 转换方法对比

| 方法 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **Tabula** | 专门提取表格，准确率高 | 需要Java环境 | 银行账单（表格规整） |
| **PDFPlumber** | 无需Java，文本提取强 | 表格识别较弱 | 简单格式账单 |
| **Auto** | 自动选择最佳方法 | - | 混合格式（推荐） |

## ⚠️ 常见问题

### Q1: 提示"Java未安装"？

**A1:** 安装Java Runtime Environment (JRE)

**Windows:**
1. 下载：https://www.java.com/download/
2. 安装后重启命令行

**Mac:**
```bash
brew install java
```

**Linux:**
```bash
sudo apt-get install default-jre
```

### Q2: 转换后Excel格式混乱？

**A2:** 尝试以下方法：
1. 使用 `-m tabula` 强制Tabula方法
2. 检查PDF文件是否为扫描件（需要OCR）
3. 手动用Adobe Acrobat Pro导出

### Q3: 批量转换时部分文件失败？

**A3:** 正常现象，可能原因：
- PDF格式特殊
- 扫描件无法识别
- PDF加密保护

失败的文件可以手动用Adobe或Tabula GUI处理。

### Q4: 转换速度慢？

**A4:** 优化方法：
- 减小PDF文件大小
- 使用SSD硬盘
- 单独处理大文件

## 📊 性能参考

- **单文件转换：** 3-10秒
- **批量100文件：** 5-15分钟
- **准确率：** 85-95%（取决于PDF质量）

## 🔗 推荐工作流

```
1. PDF账单收集
   ↓
2. Python批量转换 (本工具)
   ↓
3. Excel文件生成
   ↓
4. VBA解析处理
   ↓
5. JSON导出
   ↓
6. 上传到Replit
```

## 📞 技术支持

如遇问题，请联系：
- **项目：** INFINITE GZ
- **Email：** [Your Email]

---

**开始转换您的PDF账单吧！** 🚀
