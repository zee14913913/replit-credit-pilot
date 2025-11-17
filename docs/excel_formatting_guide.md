# 📊 CreditPilot 专业Excel格式化指南

## 概述

CreditPilot系统使用**专业级Excel格式化引擎**，确保所有生成的信用卡结算报告都符合高端商务标准，使用统一的CreditPilot官方配色方案。

---

## 🎨 CreditPilot官方配色方案

### 核心颜色
1. **主粉色**: `#FFB6C1` - 标题、重要按钮、强调内容
2. **深棕色**: `#3E2723` - 文字、边框、次要元素
3. **纯白色**: `#FFFFFF` - 背景、标题文字

### 标题行配色
- **背景色**: 深棕色 `#3E2723`
- **文字颜色**: 纯白色 `#FFFFFF`
- **字体**: Calibri 12pt 加粗

### 分类行配色
- **Owners Expenses**: 浅粉色 `#FFE4E1`
- **GZ Expenses**: 粉灰色 `#F5E6E8`
- **Suppliers**: 浅棕粉 `#F8E8E6`
- **Payments**: 浅粉紫 `#F3E5F5`
- **Outstanding Balance**: 醒目粉 `#FFB6C1` + 棕色文字 `#3E2723`

### 数据行配色
- **奇数行**: 纯白 `#FFFFFF`
- **偶数行**: 极浅棕 `#FAF8F7`

---

## ✅ 13项专业格式化标准

### 1️⃣ 列宽设置（自动适应内容）

| 字段 | 宽度（字符） | 用途 |
|------|--------------|------|
| statement_date | 18 | 账单日期 |
| due_date | 18 | 到期日期 |
| card_number | 22 | 完整显示16位卡号 |
| cardholder_name | 25 | 持卡人姓名 |
| bank_name | 20 | 银行名称 |
| amount | 15 | 金额 |
| description | 40 | 交易描述（需要更宽） |
| category | 20 | 分类 |

**对齐方式**:
- 金额列：右对齐
- 日期列：居中对齐
- 文本列：左对齐

---

### 2️⃣ 行高设置

- **标题行**: 30像素高度
- **数据行**: 25像素高度
- **垂直对齐**: 所有单元格垂直居中
- **文本换行**: 禁用（`wrapText=False`）
- **单行显示**: 所有内容必须显示在单行内，不允许折叠

---

### 3️⃣ 单元格内边距（Padding）

- **左右内边距**: 5像素
- **上下内边距**: 3像素
- **视觉距离**: 内容不紧贴边框，保持舒适阅读距离

---

### 4️⃣ 边框和网格线

- **所有单元格**: 细实线边框（thin solid border）
- **边框颜色**: 深棕色 `#3E2723`
- **标题行**: 加粗底边框（medium border）
- **透明度**: 细边框使用80%透明度

---

### 5️⃣ 颜色方案

#### 标题行
- 背景色: 深棕色 `#3E2723`
- 文字颜色: 白色 `#FFFFFF`
- 字体加粗
- 字号: 12pt

#### 数据行交替颜色
- 奇数行: 白色 `#FFFFFF`
- 偶数行: 极浅棕 `#FAF8F7`

#### 分类汇总行
- Owners Expenses: 浅粉色 `#FFE4E1`
- GZ Expenses: 粉灰色 `#F5E6E8`
- Suppliers: 浅棕粉 `#F8E8E6`
- Payments: 浅粉紫 `#F3E5F5`
- Outstanding Balance: 醒目粉 `#FFB6C1` + 加粗字体

---

### 6️⃣ 字体设置

- **字体系列**: Calibri或Arial（专业商务字体）
- **标题字号**: 12pt，加粗
- **数据字号**: 11pt
- **数字字体**: 等宽字体便于阅读

---

### 7️⃣ 数字格式化

- **金额格式**: `RM 1,234.56`（带千位分隔符，2位小数）
- **日期格式**: `DD/MM/YYYY`
- **百分比格式**: `1.00%`（2位小数）

---

### 8️⃣ 冻结窗格

- **冻结第一行**（标题行）
- **冻结第一列**（如果有索引列）
- **便于滚动**: 查看大量数据时保持标题可见

---

### 9️⃣ 列筛选器

- **所有标题行**: 添加自动筛选器
- **筛选功能**: 按分类、日期、金额等筛选
- **便于分析**: 快速查找特定交易

---

### 🔟 工作表整体设置

- **页面方向**: 横向（Landscape）
- **缩放比例**: 100%
- **打印区域**: 自动适应所有数据
- **页边距**: 上下左右各1.5cm
- **页眉**: 客户名称（Cheok Jun Yoon）+ 报告日期
- **页脚**: 页码（第X页，共Y页）

---

### 1️⃣1️⃣ 特殊格式要求

#### 负数金额
- **颜色**: 红色字体 `#D32F2F`
- **格式**: 加括号显示 `(RM 1,234.56)`

#### 到期日期已过
- **背景**: 整行浅红色提醒

#### 供应商交易
- **图标**: 在description列前添加 🏪

#### GZ代付交易
- **图标**: 在description列前添加 💼

---

### 1️⃣2️⃣ 汇总行格式

每个分类的汇总行：
- **背景色**: 对应分类的浅色调
- **字体**: 加粗
- **上边框**: 加粗（区分数据行）
- **金额**: 右对齐，加粗显示

---

### 1️⃣3️⃣ Excel文件命名

**格式**: `CheokJunYoon_Settlement_YYYYMMDD_HHMMSS.xlsx`

**示例**: `CheokJunYoon_Settlement_20251118_001530.xlsx`

---

## 📁 系统架构

### 核心文件

1. **`config/colors.json`**
   - CreditPilot官方配色方案
   - 所有颜色定义和用途说明
   - Web UI和Excel颜色统一配置

2. **`utils/excel_formatter.py`**
   - 专业Excel格式化工具类
   - 实现所有13项格式化标准
   - 可复用的格式化方法

3. **`scripts/process_cheok_statements.py`**
   - 批量处理脚本
   - 集成Excel格式化功能
   - 自动生成专业报告

---

## 🚀 使用方法

### 方法1: 批量处理（推荐）

```bash
python3 scripts/process_cheok_statements.py
```

自动处理所有PDF并生成专业格式化Excel报告。

### 方法2: 独立使用格式化工具

```python
from utils.excel_formatter import ExcelFormatter
from openpyxl import Workbook

# 创建工作簿
wb = Workbook()
ws = wb.create_sheet("账单汇总")

# 添加数据
ws.append(['银行', '卡号', '金额'])
ws.append(['AmBank', '6354', 1234.56])

# 应用格式化
formatter = ExcelFormatter()
formatter.format_worksheet(ws, 'summary', 'Cheok Jun Yoon')

# 保存
wb.save('formatted_report.xlsx')
```

### 方法3: 测试格式化效果

```bash
python3 scripts/test_excel_formatting.py
```

生成测试Excel文件，验证所有格式化标准。

---

## 📊 工作表类型

### 1. 账单汇总（Summary）

**列**: 银行、卡号、账单日期、到期日期、上期余额、本期消费、本期还款、Outstanding Balance、最低还款、Owners余额

**格式**: 
- 列宽优化显示所有字段
- 金额右对齐，日期居中
- 交替行颜色提高可读性

### 2. 交易明细（Transactions）

**列**: 银行、卡号、交易日期、描述、金额、分类、供应商手续费、账单日期

**特色**:
- 描述列宽40字符
- 供应商交易显示 🏪 图标
- GZ代付交易显示 💼 图标
- 负数金额红色显示

### 3. 分类汇总（Categories）

**列**: 分类、交易数量、总金额、占比%、说明

**特色**:
- 每个分类使用专属颜色
- Outstanding Balance使用醒目粉色
- 所有汇总行加粗字体

### 4. 错误记录（Errors）

**列**: 银行、卡号、账单日期、错误信息、详情

**用途**: 记录处理失败的PDF文件及原因

---

## 🎨 配色设计理念

### 为什么选择粉色+棕色？

1. **专业高端**: 深棕色传递稳重、专业的商务形象
2. **醒目突出**: 主粉色作为点缀，吸引注意力
3. **易于识别**: 分类颜色柔和不刺眼，长时间查看不疲劳
4. **品牌统一**: 与CreditPilot Web UI配色一致

### 颜色心理学

- **深棕色 #3E2723**: 稳重、可靠、专业
- **主粉色 #FFB6C1**: 温和、友好、醒目
- **浅粉系列**: 柔和、舒适、易于区分

---

## 📝 最佳实践

### ✅ 推荐做法

1. **使用统一配色**: 所有报告使用`config/colors.json`定义的颜色
2. **保持简洁**: 不添加额外的装饰性元素
3. **测试打印**: 确保打印效果与屏幕显示一致
4. **验证格式**: 使用`test_excel_formatting.py`验证格式化效果

### ❌ 避免做法

1. 不要修改`config/colors.json`中的核心颜色
2. 不要使用自定义字体（保持Calibri）
3. 不要添加图片或图表（影响文件大小）
4. 不要修改列宽（已优化为最佳宽度）

---

## 🔧 故障排查

### 问题1: 格式化不生效

**原因**: openpyxl未安装

**解决**:
```bash
pip install openpyxl
```

### 问题2: 颜色显示不正确

**原因**: `config/colors.json`文件缺失或损坏

**解决**: 检查文件是否存在，重新创建配置文件

### 问题3: 中文显示乱码

**原因**: Excel编码问题

**解决**: 确保使用UTF-8编码，openpyxl会自动处理

---

## 📊 性能指标

- **格式化速度**: <1秒/工作表
- **文件大小**: 约10KB/工作表
- **兼容性**: Excel 2007及以上版本
- **跨平台**: Windows, macOS, Linux

---

## 🎓 技术细节

### 实现方式

使用**openpyxl**库实现专业格式化：

```python
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

# 标题行格式
header_font = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
header_fill = PatternFill(start_color='3E2723', end_color='3E2723', fill_type='solid')

# 应用到单元格
cell.font = header_font
cell.fill = header_fill
```

### 配色管理

所有颜色从`config/colors.json`加载，便于：
- 全局颜色统一修改
- 主题切换（未来功能）
- 品牌颜色管理

---

## 📖 相关文档

- **快速开始**: `README_BATCH_PROCESSING.md`
- **完整指南**: `docs/batch_processing_guide.md`
- **配色方案**: `config/colors.json`
- **测试脚本**: `scripts/test_excel_formatting.py`

---

## ✅ 验证清单

在使用Excel格式化前，请确认：

- [ ] 已安装openpyxl包
- [ ] `config/colors.json`文件存在
- [ ] 测试脚本运行成功
- [ ] Excel文件可以正常打开
- [ ] 所有格式化效果符合预期

---

**最后更新**: 2025-11-17  
**版本**: 1.0.0  
**维护者**: CreditPilot开发团队
