# 文件存储路径标准化规范

## 📋 概述

本文档定义了系统的文件存储路径标准，确保新功能遵循统一的文件管理规范。

**适用范围**: 
- ✅ **新功能开发**: 所有新功能必须遵循此标准
- ⚠️ **历史数据**: 旧文件保持原路径（只读，不迁移）

---

## 🎯 设计原则

### 1. 路径标准化
- **新功能**: 使用`FILES_BASE_DIR`环境变量
- **旧功能**: 继续使用`static/uploads/`（向后兼容）

### 2. 多租户隔离
- 每个客户/公司的文件独立存储
- 路径包含customer_code或company_id

### 3. 文件可追溯
- 文件名包含时间戳
- 路径体现业务类型和归属

---

## 📂 路径命名规范

### Flask系统（5000端口）- 客户侧

#### 当前实现（保留）
```
static/uploads/
├── {timestamp}_{original_filename}  # 信用卡账单
├── temp_{timestamp}_{original_filename}  # 临时文件
└── receipts/
    └── pending/
        └── {unique_filename}  # 待确认收据
```

**特点**:
- ✅ 简单直接，适合客户侧快速上传
- ✅ 已稳定运行，无需迁移
- ⚠️ 缺乏客户隔离（历史遗留）

#### 新功能建议标准
如果未来新增Flask上传功能，应遵循以下标准：

```
${FILES_BASE_DIR}/customers/{customer_code}/
├── credit_cards/
│   ├── {bank_name}/
│   │   └── {yyyy-mm}_{card_last4}_{timestamp}.pdf
├── savings/
│   └── {bank_name}_{yyyy-mm}_{timestamp}.pdf
├── receipts/
│   └── {yyyy-mm-dd}_{timestamp}_{category}.jpg
└── documents/
    └── {document_type}_{timestamp}.pdf
```

**示例**:
```
/files/customers/Be_rich_KP/credit_cards/Maybank/2025-01_1234_20250102_143022.pdf
/files/customers/Be_rich_KP/savings/CIMB_2025-01_20250103_091500.pdf
```

---

### FastAPI系统（8000端口）- 会计侧

#### 当前实现（标准）
使用`AccountingFileStorageManager`管理，已遵循标准化路径：

```
files/companies/{company_id}/
├── bank_statements/
│   ├── {bank_name}/
│   │   └── {account_number}/
│   │       └── {yyyy-mm}_{timestamp}.csv
├── supplier_invoices/
│   └── {supplier_name}/
│       └── {yyyy-mm}_{invoice_number}.pdf
├── pos_reports/
│   └── {merchant_name}/
│       └── {yyyy-mm}_{timestamp}.csv
└── raw_documents/
    └── {category}/
        └── {hash}_{timestamp}.{ext}
```

**特点**:
- ✅ 完全隔离（公司级）
- ✅ 自动hash校验
- ✅ 原件封存保护

**示例**:
```
files/companies/1/bank_statements/Maybank/1234567890/2025-01_statement.csv
files/companies/1/raw_documents/bank/a1b2c3d4e5f6_20250102_143022.csv
```

---

## 🔄 迁移策略

### Phase 1（当前）: 双轨运行
- ✅ 旧路径（`static/uploads/`）：只读，保持不变
- ✅ 新功能：使用`FILES_BASE_DIR`标准
- ✅ 两者独立，互不干扰

### Phase 2（未来）: 渐进式迁移
**仅当客户量增长、需要多租户收费时考虑**：

1. **停机维护窗口**: 预留2-4小时
2. **数据迁移脚本**: 
   - 按customer_code重组文件
   - 更新数据库file_path字段
   - 保留原文件作为备份
3. **验证测试**: 确保所有文件可访问
4. **回滚方案**: 迁移失败时恢复原状

**时机判断**:
- ❌ **不需要**: 当前客户 < 50个
- ⚠️ **可考虑**: 客户 50-100个
- ✅ **建议执行**: 客户 > 100个或开始收费

---

## 📝 环境变量配置

### Flask（5000端口）
```bash
# 当前配置（保留）
UPLOAD_FOLDER=static/uploads

# 未来新功能使用
FILES_BASE_DIR=/files
```

### FastAPI（8000端口）
```bash
# 已配置
FILES_BASE_DIR=/files  # AccountingFileStorageManager自动使用
```

---

## 🚀 开发指南

### 新功能开发checklist

**Flask新上传功能**:
```python
# ✅ 推荐：使用标准化路径
from pathlib import Path
files_base = os.getenv('FILES_BASE_DIR', 'files')
customer_dir = Path(files_base) / 'customers' / customer_code / 'credit_cards'
customer_dir.mkdir(parents=True, exist_ok=True)
file_path = customer_dir / f"{timestamp}_{filename}"

# ❌ 避免：直接使用旧路径（除非维护现有功能）
file_path = os.path.join('static/uploads', filename)
```

**FastAPI新上传功能**:
```python
# ✅ 使用AccountingFileStorageManager
from accounting_app.services.file_storage import AccountingFileStorageManager

file_path = AccountingFileStorageManager.generate_bank_statement_path(
    company_id=1,
    bank_name="Maybank",
    account_number="1234567890",
    statement_month="2025-01",
    file_extension="csv"
)
AccountingFileStorageManager.save_text_content(file_path, content)
```

---

## 🔒 安全考虑

### 1. 路径注入防护
```python
# ✅ 安全：使用Path标准化
from pathlib import Path
safe_path = Path(base_dir) / customer_code / filename
safe_path = safe_path.resolve()  # 防止../等路径穿越

# ❌ 危险：直接拼接
file_path = f"{base_dir}/{customer_code}/{filename}"
```

### 2. 文件权限
- 上传目录: `755` (drwxr-xr-x)
- 文件权限: `644` (-rw-r--r--)

### 3. 访问控制
- Flask: 通过customer_id验证归属
- FastAPI: 通过company_id和user角色验证

---

## 📊 当前状态总结

| 系统 | 路径标准 | 状态 | 迁移计划 |
|------|---------|------|---------|
| Flask (5000) | `static/uploads/` | ✅ 稳定运行 | 保留（Phase 2考虑） |
| FastAPI (8000) | `files/companies/{id}/` | ✅ 已标准化 | 无需迁移 |
| 新功能开发 | `FILES_BASE_DIR/*` | 📋 推荐遵循 | N/A |

---

## 🎯 下一步行动

### 短期（保持现状）
1. ✅ 新功能遵循此文档标准
2. ✅ 旧路径保持不变（只读）
3. ✅ 定期备份`static/uploads/`目录

### 长期（Phase 2考虑）
1. ⏳ 监控客户数量增长
2. ⏳ 评估多租户收费需求
3. ⏳ 制定详细迁移计划
4. ⏳ 预留停机维护窗口

---

**版本**: v1.0  
**更新日期**: 2025-01-02  
**负责人**: 系统架构团队
