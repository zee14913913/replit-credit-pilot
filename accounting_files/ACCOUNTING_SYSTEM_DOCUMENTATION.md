# 📁 专业会计文件组织系统文档

## 系统概述

本系统按照**专业会计审计标准**和**客户保密要求**，为每个客户创建完全独立的会计文件夹。

---

## 🏗️ 文件夹架构

### 顶层结构

```
accounting_files/
├── CHANG CHOON CHOW/          # 客户独立文件夹
├── CHEOK JUN YOON/
├── AI SMART TECH SDN. BHD./
├── INFINITE GZ SDN. BHD./
├── Tan Zee Liang/
├── TEO YOK CHU/
└── YEO CHEE WANG/
```

### 客户文件夹详细结构

每个客户文件夹包含以下标准子目录：

```
[CUSTOMER_NAME]/
├── monthly_statements/        # 月结单（按银行+月份分离）
│   ├── 2024-09_Alliance_Bank_Statement.xlsx
│   ├── 2024-09_HSBC_Statement.xlsx
│   ├── 2024-09_Hong_Leong_Bank_Statement.xlsx
│   ├── 2024-09_Maybank_Statement.xlsx
│   ├── 2024-09_UOB_Statement.xlsx
│   └── 2024-09_Summary.xlsx   # 月度汇总（所有银行）
│
├── transaction_details/       # 交易明细
│   ├── 2024-09_All_Transactions.xlsx
│   ├── 2024-10_All_Transactions.xlsx
│   └── ...
│
├── transfer_records/         # 转账记录
│   └── Transfer_Log.xlsx
│
├── reports/                  # 汇总报告
│   ├── Annual_Summary_2024.xlsx
│   └── GZ_Settlement_Report.xlsx
│
└── source_pdfs/              # 原始PDF文件
    ├── 2024-09/
    │   ├── Alliance_Bank_4514_2024-09-12.pdf
    │   ├── HSBC_2058_2024-09-10.pdf
    │   └── ...
    └── 2024-10/
        └── ...
```

---

## 📊 CHANG CHOON CHOW 文件清单

### 基本信息
- **客户代码**: Be_rich_CCC
- **处理周期**: 2024-09 至 2025-11
- **总Excel文件**: 99个
- **总PDF文件**: 89个
- **银行数量**: 5家（Alliance Bank, HSBC, Hong Leong Bank, Maybank, UOB）

### 文件分布

#### 月结单文件 (69个)
按月份 × 银行组合，每个月每家银行一个独立Excel文件：

**2024-09** (5家银行)
- `2024-09_Alliance_Bank_Statement.xlsx`
- `2024-09_HSBC_Statement.xlsx`
- `2024-09_Hong_Leong_Bank_Statement.xlsx`
- `2024-09_Maybank_Statement.xlsx`
- `2024-09_UOB_Statement.xlsx`

**2024-10** (5家银行)
**2024-11** (5家银行)
**2024-12** (5家银行)
**2025-01** (5家银行)
**2025-02** (5家银行)
**2025-03** (5家银行)
**2025-04** (5家银行)
**2025-05** (5家银行)
**2025-06** (5家银行)
**2025-07** (5家银行)
**2025-08** (5家银行)
**2025-09** (2家银行: HLB, UOB)
**2025-10** (1家银行: Maybank)
**2025-11** (6家银行: Alliance, Alliance Bank, HLB, Hong Leong Bank, Maybank, UOB)

#### 月度汇总文件 (15个)
每月一个汇总文件，包含所有银行的综合统计：

- `2024-09_Summary.xlsx`
- `2024-10_Summary.xlsx`
- `2024-11_Summary.xlsx`
- ... (共15个月份)
- `2025-11_Summary.xlsx`

#### 交易明细文件 (15个)
每月所有银行的完整交易记录：

- `2024-09_All_Transactions.xlsx` (48笔交易)
- `2024-10_All_Transactions.xlsx` (54笔交易)
- `2024-11_All_Transactions.xlsx` (49笔交易)
- ... 
- `2025-11_All_Transactions.xlsx` (234笔交易)

**总交易数**: 809笔

---

## 📋 Excel文件内容规范

### 1. 单银行月结单 (xxx_Bank_Statement.xlsx)

包含字段：
- ✅ 期初余额 (Previous Balance)
- ✅ 期末余额 (Closing Balance)
- ✅ OWNER 余额
- ✅ GZ 余额
- ✅ OWNER 费用 (Expenses)
- ✅ OWNER 付款 (Payments)
- ✅ GZ 费用 (Expenses)
- ✅ GZ 付款 (Payments)
- ✅ **GZ 1% 管理费** (自动计算)
- ✅ 交易笔数

### 2. 月度汇总表 (YYYY-MM_Summary.xlsx)

包含所有银行的汇总统计：
- 按银行列出OWNER和GZ的费用/付款
- 自动计算每家银行的1%管理费
- 显示月度总计
- 支持审计追踪

### 3. 交易明细表 (YYYY-MM_All_Transactions.xlsx)

包含字段：
- ✅ 日期 (Transaction Date)
- ✅ 银行 (Bank Name)
- ✅ 描述 (Description)
- ✅ 借记 (DR - Debit)
- ✅ 贷记 (CR - Credit)
- ✅ 分类 (Category)
- ✅ **归属** (OWNER / GZ)

---

## 🎨 Excel样式规范

### 颜色编码

1. **表头**: 
   - 月结单: Hot Pink (#FF007F) - 白色字体
   - 汇总表: Dark Purple (#322446) - 白色字体

2. **数据行**:
   - OWNER数据: 浅粉色背景 (#FFE0F0)
   - GZ数据: 浅紫色背景 (#E8D8F0)
   - 合计行: 深色高亮 + 粗体

3. **金额格式**: #,##0.00 (千位分隔符 + 2位小数)

---

## 🔍 数据分类说明

### Owner/GZ 归属判断

**GZ归属** (公司费用):
- 描述包含关键词: GZ, INFINITE, KENG CHOW
- owner_flag = 'INFINITE'

**OWNER归属** (个人费用):
- 其他所有交易
- owner_flag = 'OWNER'

### Supplier List识别

系统自动识别7家供应商公司：
1. 7SL
2. DINAS
3. RAUB SYC HAINAN
4. AI SMART TECH
5. HUAWEI
6. PASAR RAYA
7. PUCHONG HERBS

### 1%管理费计算

```
GZ 1% 管理费 = GZ费用总额 × 0.01
```

每个月结单和汇总表都自动计算并显示此费用。

---

## 📊 统计数据汇总

### CHANG CHOON CHOW 财务概况 (2024-09 至 2025-11)

| 银行 | 月数 | GZ总费用 | OWNER总费用 |
|------|------|----------|-------------|
| Alliance Bank | 13个月 | RM 29,298.00 | RM 25,362.83 |
| HSBC | 12个月 | RM 0.00 | RM 79,518.94 |
| Hong Leong Bank | 14个月 | RM 246,104.00 | RM 68,309.21 |
| Maybank | 14个月 | RM 261,527.00 | RM 73,727.01 |
| UOB | 14个月 | RM 0.00 | RM 87,375.13 |

**GZ总费用**: RM 536,929.00  
**OWNER总费用**: RM 334,293.12  
**GZ 1%管理费总计**: RM 5,369.29

---

## ✅ 审计合规性

### 符合专业会计标准

1. **客户独立性** ✅
   - 每个客户完全独立的文件夹
   - 跨客户数据完全隔离

2. **数据可追溯性** ✅
   - 从原始PDF到最终报表的完整链条
   - 所有交易明细可查

3. **分类透明度** ✅
   - Owner/GZ清晰分类
   - Supplier识别准确
   - 1%费用自动计算

4. **文件命名规范** ✅
   - 统一命名格式: YYYY-MM_Bank_Type.xlsx
   - 易于排序和查找

5. **备份与存档** ✅
   - 原始PDF保存在source_pdfs/
   - 处理后Excel独立存储

---

## 🔐 数据安全与保密

### 客户保密措施

1. **文件夹隔离**: 每个客户独立文件夹，防止数据混淆
2. **访问控制**: 仅授权会计人员可访问
3. **审计日志**: 所有操作记录在数据库audit_logs表

### 数据完整性

- ✅ 数据库主记录保留
- ✅ Excel报表自动生成（非手工编辑）
- ✅ 余额自动验证
- ✅ 交易数量自动统计

---

## 📝 使用指南

### 查找特定月份的账单

```
路径: accounting_files/[客户名]/monthly_statements/
文件名格式: YYYY-MM_[银行名]_Statement.xlsx
```

例如：`accounting_files/CHANG CHOON CHOW/monthly_statements/2024-09_Alliance_Bank_Statement.xlsx`

### 查看月度汇总

```
路径: accounting_files/[客户名]/monthly_statements/
文件名格式: YYYY-MM_Summary.xlsx
```

### 查看完整交易明细

```
路径: accounting_files/[客户名]/transaction_details/
文件名格式: YYYY-MM_All_Transactions.xlsx
```

### 访问原始PDF

```
路径: accounting_files/[客户名]/source_pdfs/
组织方式: 按月份分组
```

---

## 🛠️ 系统维护

### 添加新月份数据

1. 上传新的PDF到系统
2. 处理并入库到数据库
3. 运行脚本自动生成新月份的Excel文件：
   ```bash
   python3 scripts/create_customer_accounting_folders.py
   ```

### 更新现有数据

系统会自动覆盖同名文件，确保数据始终是最新的。

---

## 📞 技术支持

如需技术支持，请提供：
1. 客户名称
2. 月份
3. 银行名称
4. 问题描述

---

**生成时间**: 2025-11-16  
**系统版本**: 1.0  
**维护单位**: INFINITE GZ Smart Loan Manager
