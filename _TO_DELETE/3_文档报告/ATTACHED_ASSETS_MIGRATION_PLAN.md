# attached_assets 客户文件迁移计划

## 🎯 目标

将 `attached_assets/` 中发现的客户原件PDF迁移到标准存储位置：
```
static/uploads/customers/{customer_code}/credit_cards/{bank}/{month}/
```

---

## 📋 已发现的客户文件清单

### 1. HSBC 账单（CHEOK JUN YOON客户）

#### 文件1：HSBC 13:10:2025 3_1761889944083.pdf
- **当前位置**: `attached_assets/HSBC 13:10:2025 3_1761889944083.pdf`
- **文件大小**: 693.3 KB
- **页数**: 5页
- **客户**: CHEOK JUN YOON
- **地址**: 124 JLN 4 TMN DUYUNG, 70200 SEREMBAN
- **账单日期**: 2025年10月13日（从文件名推断）
- **账户号**: 000575-003163-003163

**迁移目标位置**:
```
static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf
```

**迁移命令**:
```bash
# 1. 创建目录
mkdir -p static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/

# 2. 复制并重命名文件
cp "attached_assets/HSBC 13:10:2025 3_1761889944083.pdf" \
   static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf

# 3. 设置权限
chmod 600 static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf

# 4. 验证文件
ls -lh static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/

# 5. 删除原文件
rm "attached_assets/HSBC 13:10:2025 3_1761889944083.pdf"
```

**数据库更新**:
```sql
-- 如果已有2025-10的HSBC记录，更新file_paths
UPDATE monthly_statements 
SET file_paths = json_array_append(
    COALESCE(file_paths, '[]'),
    '$',
    'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf'
)
WHERE customer_id = 6 
  AND bank_name = 'HSBC' 
  AND statement_month = '2025-10';

-- 如果没有记录，需要先导入该账单
```

---

#### 文件2：HSBC 13:10:2025 2_1761889721698.pdf
- **当前位置**: `attached_assets/HSBC 13:10:2025 2_1761889721698.pdf`
- **文件大小**: 258.4 KB
- **页数**: 5页
- **状态**: ⚠️ 无法提取文本（可能是扫描版或加密PDF）
- **客户**: 推测为 CHEOK JUN YOON（相同时间上传）
- **账单日期**: 2025年10月13日

**处理方案**:
```bash
# 选项A：如果是同一账单的不同版本，保留文本版
# 选项B：如果是不同卡号，需要确认后迁移
# 选项C：如果文件损坏，删除

# 建议：先尝试用其他PDF工具打开验证
pdfinfo "attached_assets/HSBC 13:10:2025 2_1761889721698.pdf"

# 如果确认是重复文件，删除
rm "attached_assets/HSBC 13:10:2025 2_1761889721698.pdf"
```

---

### 2. OCBC 账单（TEO YOK CHU & YEO CHEE WANG客户）

#### 文件：Teo 30:09:2025 ocbc_1761832561552.pdf
- **当前位置**: `attached_assets/Teo 30:09:2025 ocbc_1761832561552.pdf`
- **文件大小**: 112.4 KB
- **页数**: 1页
- **账户类型**: OCBC EASI-SAVE SAVINGS ACCOUNT (储蓄账户)
- **客户**: MS TEO YOK CHU, MR YEO CHEE WANG
- **地址**: 35 JALAN BUKIT FLORA 2/7, TAMAN BUKIT FLORA 2, 83000 BATU PAHAT JOHOR
- **账户号**: 712-261489-2
- **账单期间**: 2025年9月1日 - 9月30日

**客户代码识别**:
- 数据库客户：ID:8, 代码:Be_rich_TYC&YCW, 姓名:TEO YOK CHU
- ✅ 匹配成功！

**迁移目标位置**:
```
static/uploads/customers/Be_rich_TYC&YCW/savings/OCBC/2025-09/TEO_YOK_CHU_OCBC_1489_2025-09-30.pdf
```

**迁移命令**:
```bash
# 1. 创建目录
mkdir -p static/uploads/customers/Be_rich_TYC\&YCW/savings/OCBC/2025-09/

# 2. 复制并重命名文件
cp "attached_assets/Teo 30:09:2025 ocbc_1761832561552.pdf" \
   static/uploads/customers/Be_rich_TYC\&YCW/savings/OCBC/2025-09/TEO_YOK_CHU_OCBC_1489_2025-09-30.pdf

# 3. 设置权限
chmod 600 static/uploads/customers/Be_rich_TYC\&YCW/savings/OCBC/2025-09/TEO_YOK_CHU_OCBC_1489_2025-09-30.pdf

# 4. 验证文件
ls -lh static/uploads/customers/Be_rich_TYC\&YCW/savings/OCBC/2025-09/

# 5. 删除原文件
rm "attached_assets/Teo 30:09:2025 ocbc_1761832561552.pdf"
```

**数据库导入**:
```bash
# 这是储蓄账户月结单，需要使用储蓄系统导入
# 通过 /savings 路由上传
```

---

### 3. 损坏的小文件（建议删除）

以下文件太小（2.5KB），可能是上传失败或文件损坏：

```bash
# 这些文件应该删除
rm "attached_assets/Ocbc Aug _1761832561552.pdf"           # 2.5KB
rm "attached_assets/Ocbc Aug _1761835463822.pdf"           # 2.5KB
rm "attached_assets/Ocbc Aug _1761835850859.pdf"           # 2.5KB
```

**原因**:
- 正常的银行账单PDF至少应该有50KB+
- 2.5KB的PDF可能只包含错误信息或部分数据
- 已有完整的112.4KB OCBC账单文件

---

## 🔄 完整迁移流程

### 步骤1：备份
```bash
# 备份整个 attached_assets 文件夹
cp -r attached_assets attached_assets_backup_$(date +%Y%m%d)
```

### 步骤2：执行迁移
```bash
# 执行上述迁移命令
# 建议逐个文件处理，确保每个文件都正确迁移
```

### 步骤3：更新数据库
```bash
# 使用系统界面重新导入迁移的文件
# 或者手动更新 monthly_statements 表的 file_paths 字段
```

### 步骤4：验证
```bash
# 1. 验证文件在新位置存在
find static/uploads/customers -name "HSBC_0034_2025-10-13.pdf"
find static/uploads/customers -name "TEO_YOK_CHU_OCBC_1489_2025-09-30.pdf"

# 2. 验证文件可读
pdfinfo static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf

# 3. 验证数据库记录
sqlite3 db/smart_loan_manager.db "SELECT * FROM monthly_statements WHERE file_paths LIKE '%HSBC_0034_2025-10-13.pdf%';"
```

### 步骤5：清理
```bash
# 确认所有文件已正确迁移后，删除原文件
rm "attached_assets/HSBC 13:10:2025 3_1761889944083.pdf"
rm "attached_assets/HSBC 13:10:2025 2_1761889721698.pdf"
rm "attached_assets/Teo 30:09:2025 ocbc_1761832561552.pdf"
rm "attached_assets/Ocbc Aug _1761832561552.pdf"
rm "attached_assets/Ocbc Aug _1761835463822.pdf"
rm "attached_assets/Ocbc Aug _1761835850859.pdf"
```

---

## 📊 迁移总结

| 文件 | 大小 | 客户 | 目标位置 | 状态 |
|------|------|------|----------|------|
| HSBC 13:10:2025 3 | 693.3KB | Be_rich_CJY | .../HSBC/2025-10/ | 待迁移 |
| HSBC 13:10:2025 2 | 258.4KB | Be_rich_CJY | 待确认 | 需验证 |
| Teo 30:09:2025 ocbc | 112.4KB | Be_rich_TYC&YCW | .../OCBC/2025-09/ | 待迁移 |
| Ocbc Aug (3个) | 2.5KB | - | - | 建议删除 |

**总计**:
- ✅ 可迁移：2个文件
- ⚠️ 需验证：1个文件
- ❌ 建议删除：3个小文件

---

## ⚠️ 注意事项

1. **文件名中包含特殊字符**
   - 文件名中有空格、冒号等特殊字符
   - 迁移时需要用引号包裹
   - 标准化后使用下划线代替空格

2. **客户代码包含特殊字符**
   - `Be_rich_TYC&YCW` 中的 `&` 需要转义
   - 在bash中使用 `\&` 或引号

3. **数据库字段是 file_paths（复数）**
   - 使用JSON数组存储多个文件路径
   - 更新时需要使用 `json_array_append`

4. **储蓄账户 vs 信用卡账单**
   - 储蓄账户放在 `/savings/` 目录
   - 信用卡账单放在 `/credit_cards/` 目录
   - 使用不同的命名规范

---

## ✅ 验证清单

迁移完成后，请检查：

- [ ] 文件在新位置存在
- [ ] 文件大小与原文件一致
- [ ] 文件权限设置为 600
- [ ] 文件可以通过PDF阅读器打开
- [ ] 数据库 file_paths 字段已更新
- [ ] 通过系统界面可以查看文件
- [ ] 原文件已删除
- [ ] 备份已保存

---

## 🔧 故障排除

### 问题1：文件名包含特殊字符无法操作
```bash
# 解决：使用引号或转义
mv "attached_assets/HSBC 13:10:2025 3_1761889944083.pdf" new_location/
```

### 问题2：客户代码包含 & 符号
```bash
# 解决：转义或使用引号
mkdir -p static/uploads/customers/Be_rich_TYC\&YCW/
# 或
mkdir -p "static/uploads/customers/Be_rich_TYC&YCW/"
```

### 问题3：数据库更新失败
```sql
-- 检查是否已有记录
SELECT * FROM monthly_statements 
WHERE customer_id = 6 AND bank_name = 'HSBC' AND statement_month = '2025-10';

-- 如果没有记录，需要先通过系统导入账单
```

---

**最后更新**: 2024-11-15  
**执行人**: 系统管理员  
**状态**: 待执行
