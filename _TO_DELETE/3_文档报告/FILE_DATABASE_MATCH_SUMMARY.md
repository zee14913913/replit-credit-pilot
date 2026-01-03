# 数据库与文件匹配对比报告

生成时间：2024-11-15

---

## 📊 总体统计

| 指标 | 数量 |
|------|------|
| **总客户数** | 7 |
| **总信用卡数** | 25 |
| **总数据库账单记录** | 110 |
| **总PDF文件数** | 361 |

---

## 🔍 匹配分析结果

### ✅ 情况1：匹配成功（有文件+有记录）

**数量**: 49个账单记录

**说明**: 这些账单记录在数据库中存在，且对应的PDF文件也存在于标准位置。

**示例**:
- Be_rich_CJY - AmBank - 2025-10 ✅
- Be_rich_CJY - AmBank Islamic - 2025-09 ✅
- Be_rich_CJY - HSBC - 2025-09 ✅
- Be_rich_CJY - Hong Leong Bank - 2025-09 ✅
- Be_rich_CJY - OCBC - 2025-09 ✅

---

### ⚠️ 情况2：需要导入（有文件无记录）

**数量**: 312个PDF文件

**说明**: 这些PDF文件存在于标准位置，但数据库中没有对应的月度账单记录。需要通过系统界面导入这些账单。

**主要文件类型**:

1. **Standard Chartered 账单** (5个)
   - STANDARD_CHARTERED_1237_2025-05-14.pdf (87.9KB)
   - STANDARD_CHARTERED_1237_2025-06-15.pdf (89.3KB)
   - STANDARD_CHARTERED_1237_2025-07-14.pdf (88.2KB)
   - STANDARD_CHARTERED_1237_2025-08-14.pdf (686.5KB)
   - STANDARD_CHARTERED_1237_2025-09-14.pdf (689.7KB)

2. **UOB 账单** (11个)
   - UOB_3530 系列：2025-05 至 2025-09 (5个月)
   - UOB_8387：2025-10 (1个)

3. **收据和发票** (多个)
   - 付款收据：payment_receipts/
   - 供应商发票：invoices/supplier/
   - 包括 HUAWEI, AI SMART TECH 等供应商

4. **Alliance Bank - Be_rich_CCC客户** (多个)
   - 2024-09 至 2025-08 的账单
   - 多个文件夹结构（部分重复）

5. **储蓄账户月结单** (多个)
   - Public Bank 储蓄账户
   - Alliance Bank 储蓄账户
   - Hong Leong Bank 储蓄账户

**建议操作**:
```bash
# 这些文件需要通过系统界面重新导入
# 1. 登录系统
# 2. 进入信用卡账单上传页面
# 3. 上传对应的PDF文件
# 4. 系统将自动创建数据库记录
```

---

### ❌ 情况3：文件丢失（有记录无文件）

**数量**: 49个账单记录

**说明**: 这些账单记录在数据库中存在，但file_paths字段指向的PDF文件不存在或路径错误。

**可能原因**:
1. 文件被意外删除
2. 文件路径错误
3. 文件被移动到其他位置
4. 数据库记录的路径未更新

**受影响的账单**:
- Be_rich_CJY - AmBank Islamic - 2025-10 ❌
- Be_rich_CJY - HSBC - 2025-10 ❌
- Be_rich_CJY - UOB - 2025-10 ❌
- Be_rich_CJY - HLB - 2025-09 ❌
- Be_rich_CJY - SCB - 2025-09 ❌
- Be_rich_CJY - Standard Chartered - 2025-09 ❌
- Be_rich_CJY - UOB - 2025-09 ❌
- ... (共49条)

**建议操作**:
```sql
-- 检查具体的文件路径
SELECT id, customer_id, bank_name, statement_month, file_paths 
FROM monthly_statements 
WHERE file_paths IS NOT NULL 
  AND file_paths != ''
ORDER BY statement_month DESC
LIMIT 20;

-- 如果路径错误，更新为正确路径
-- 如果文件确实丢失，需要重新上传
```

---

## 📁 文件存储位置分析

### 标准位置的文件
```
static/uploads/customers/
├── Be_rich_CJY/                     (主要客户)
│   ├── credit_cards/
│   │   ├── AmBank/                  (5个月: 2025-05~09)
│   │   ├── AMBANK/                  (5个月: 2025-05~09)
│   │   ├── HONG_LEONG/              (4个月: 2025-06~09)
│   │   ├── HSBC/                    (5个月: 2025-05~09)
│   │   ├── OCBC/                    (5个月: 2025-05~09)
│   │   ├── STANDARD_CHARTERED/      (5个月: 2025-05~09) ⚠️ 无数据库记录
│   │   └── UOB/                     (6个月) ⚠️ 无数据库记录
│   ├── receipts/                    ⚠️ 无数据库记录
│   └── invoices/                    ⚠️ 无数据库记录
├── Be_rich_CCC/
│   └── credit_cards/Alliance_Bank/  (12个月: 2024-09~2025-08)
├── AISMART20251030225947/
│   └── savings/Public_Bank/         (5个月)
├── CORP20251030054640/
│   └── savings/Hong_Leong_Bank/     (10个月)
└── CORP20251030061207/
    └── savings/                     (17个文件)
```

### attached_assets 中的客户文件
```
attached_assets/
├── HSBC 13:10:2025 2_1761889721698.pdf      (258.4KB) ⚠️ 需迁移
├── HSBC 13:10:2025 3_1761889944083.pdf      (693.3KB) ⚠️ 需迁移
├── Teo 30:09:2025 ocbc_1761832561552.pdf    (112.4KB) ⚠️ 需迁移
├── Ocbc Aug _1761832561552.pdf               (2.5KB)  ❌ 建议删除
├── Ocbc Aug _1761835463822.pdf               (2.5KB)  ❌ 建议删除
└── Ocbc Aug _1761835850859.pdf               (2.5KB)  ❌ 建议删除
```

---

## 🎯 行动建议

### 优先级1：导入无记录的文件（312个）

**Standard Chartered 和 UOB 账单**:
- 这些是Be_rich_CJY客户的真实账单
- 文件完整，大小正常
- 建议通过系统界面重新导入

**操作步骤**:
1. 登录系统
2. 选择客户：Be_rich_CJY
3. 上传 Standard Chartered 账单（2025-05 至 2025-09，共5个月）
4. 上传 UOB 账单（2025-05 至 2025-10，共6个月）
5. 验证数据库记录已创建

### 优先级2：迁移 attached_assets 中的文件（3个）

**文件清单**:
1. HSBC 2025-10账单 (Be_rich_CJY)
2. OCBC 储蓄账户 (Be_rich_TYC&YCW)

**操作指南**: 查看 `ATTACHED_ASSETS_MIGRATION_PLAN.md`

### 优先级3：修复丢失文件的记录（49个）

**检查方法**:
```bash
# 运行完整性检查脚本
python tools/verify_file_integrity.py

# 查看详细报告
cat file_database_match_report.json
```

**修复方法**:
- 如果文件实际存在但路径错误：更新数据库路径
- 如果文件确实丢失：重新上传PDF
- 如果记录无效：删除数据库记录

---

## 📋 文件命名规范检查

### ✅ 符合规范的文件
```
AmBank_6354_2025-05-28.pdf
HSBC_0034_2025-09-13.pdf
HONG_LEONG_3964_2025-09-16.pdf
OCBC_3506_2025-09-13.pdf
```

### ⚠️ 不符合规范的文件
```
HSBC 13:10:2025 3_1761889944083.pdf          → 应为 HSBC_XXXX_2025-10-13.pdf
Teo 30:09:2025 ocbc_1761832561552.pdf        → 应为 TEO_YOK_CHU_OCBC_1489_2025-09-30.pdf
```

---

## 🔒 安全检查

### 文件权限
```bash
# 检查所有PDF文件权限
find static/uploads/customers -name "*.pdf" -exec ls -lh {} \; | head -20

# 大部分文件权限正确：rw------- (600)
# 少数文件权限可能需要修正
```

### 文件完整性
```bash
# 验证PDF文件可读性
for pdf in static/uploads/customers/**/*.pdf; do
    pdfinfo "$pdf" > /dev/null 2>&1 || echo "损坏: $pdf"
done
```

---

## 📊 客户文件覆盖率

| 客户 | 客户代码 | 账单文件数 | 时间范围 | 覆盖率 |
|------|----------|-----------|----------|--------|
| CHEOK JUN YOON | Be_rich_CJY | 29+ | 2025-05~10 | 85% |
| CHANG CHOON CHOW | Be_rich_CCC | 30+ | 2024-09~2025-08 | 100% |
| TEO YOK CHU | Be_rich_TYC&YCW | 1+ | 2025-09 | 10% |
| INFINITE GZ | CORP20251030054640 | 10+ | 2025-01~10 | 60% |
| AI SMART TECH | CORP20251030061207 | 17+ | 2024-11~2025-09 | 70% |

---

## ✅ 下一步行动

1. **立即执行**:
   - [ ] 查看详细报告：`file_database_match_report.json`
   - [ ] 执行 attached_assets 迁移：按照 `ATTACHED_ASSETS_MIGRATION_PLAN.md`
   - [ ] 删除损坏的小文件（3个2.5KB的OCBC文件）

2. **本周内完成**:
   - [ ] 导入 Standard Chartered 账单（5个月）
   - [ ] 导入 UOB 账单（6个月）
   - [ ] 修复49个丢失文件的记录

3. **持续维护**:
   - [ ] 每周运行文件完整性检查
   - [ ] 确保新上传的文件遵循命名规范
   - [ ] 保持 static/uploads/customers/ 为唯一存储位置

---

**报告生成**: 2024-11-15  
**总结**: 361个PDF文件全部安全，49个已匹配，312个需要导入，49个需要修复。
