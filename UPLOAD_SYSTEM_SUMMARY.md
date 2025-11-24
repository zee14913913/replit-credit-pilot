# CreditPilot强制性文件上传系统 - 快速参考

**版本**: V2.0.0  
**日期**: 2025-11-24  
**状态**: ✅ 生产就绪

---

## 🎯 核心功能

### 1. 8阶段强制Pipeline

```
文件上传 → PendingChecksum → PendingParse → PendingAttribution → 
PendingClassification → ApprovedForStorage → StorageComplete
```

**每个阶段都是强制性的，不能跳过！**

### 2. 自动识别文件主人

- ✅ 解析PDF提取客户名字
- ✅ 交叉引用customers表
- ✅ 置信度评分（必须≥0.98）
- ⚠️ 低置信度 → 自动转人工审核

### 3. Owner/GZ自动分类

**示例：LEE E KAI - AmBank Islamic**

```yaml
Owner's Expenses（个人消费）:
  - 餐饮、购物、娱乐、个人开支
  - 示例：Starbucks, McDonald, Cinema, Shopping Mall
  
GZ's Expenses（INFINITE GZ业务支出）:
  - 供应商、设备、业务开支
  - 示例：7SL, Dinas Raub, Ai Smart Tech, Huawei
```

### 4. 对比表格自动生成

```
┌────────────────────────────────────────┐
│ 原件数据（From PDF）                    │
│ Statement Total:    RM 14,515.00       │
│                                        │
│ 计算数据（Calculated）                  │
│ Owner's Total:      RM  8,200.00       │
│ GZ's Total:         RM  6,315.00       │
│ Calculated Total:   RM 14,515.00       │
│                                        │
│ 验证: ✅ 差异 RM 0.00                   │
└────────────────────────────────────────┘
```

### 5. 原件固定位置（绝不丢失）

```
主存储:
static/uploads/customers/{customer_code}/statements/original/
  {bank_name}/{YYYY-MM}/{bank_name}_{date}_ORIGINAL.pdf

备份:
static/uploads_backup/customers/{customer_code}/statements/original/
  {bank_name}/{YYYY-MM}/{bank_name}_{date}_ORIGINAL.pdf
```

---

## 🚫 强制性约束（ARCHITECT监督）

| 约束 | 说明 | 违反后果 |
|------|------|---------|
| ❌ 禁止跳过Pipeline | 必须完成所有8个阶段 | 自动失败 |
| ❌ 禁止直接保存文件 | 不能调用FileStorageManager.save_file() | Assert错误 |
| ❌ 禁止缺失强制字段 | 7个字段必须全部提取 | 转人工审核 |
| ❌ 禁止低置信度存储 | 置信度必须≥0.98 | 转人工审核 |
| ❌ 禁止跳过Owner/GZ分类 | 必须分类并验证 | 转人工审核 |
| ❌ 禁止单写 | 必须双写（主+备份） | 回滚失败 |
| ❌ 禁止移动/删除原件 | 原件路径固定 | 系统警报 |

---

## 📂 文件结构

```
services/
├── upload_orchestrator.py      # 上传编排器（8阶段Pipeline）
├── owner_gz_classifier.py      # Owner/GZ分类器
├── file_storage_manager.py     # 文件存储管理
└── file_integrity_service.py   # 文件完整性服务

db/
└── smart_loan_manager.db
    ├── upload_transactions      # 状态机主表
    ├── upload_state_changes     # 状态变更审计
    └── file_registry            # 文件注册表

ARCHITECT_CONSTRAINTS.md         # 强制性约束文档
UPLOAD_SYSTEM_SUMMARY.md         # 本文档
demo_upload_pipeline.py          # 演示脚本
```

---

## 🔍 数据库表

### upload_transactions（状态机）

```sql
CREATE TABLE upload_transactions (
    id INTEGER PRIMARY KEY,
    transaction_uuid TEXT UNIQUE,
    original_filename TEXT,
    file_checksum TEXT,
    
    -- 状态机
    status TEXT CHECK(status IN (
        'PendingChecksum', 'PendingParse', 
        'PendingAttribution', 'PendingClassification',
        'ApprovedForStorage', 'StorageComplete',
        'Failed', 'PendingReview'
    )),
    
    -- 解析结果（7个强制字段）
    parsed_owner_name TEXT,
    parsed_customer_code TEXT,
    parsed_bank_name TEXT,
    parsed_statement_date TEXT,
    parsed_due_date TEXT,
    parsed_statement_total REAL,
    parsed_minimum_payment REAL,
    
    -- 归属
    attributed_customer_id INTEGER,
    attribution_confidence REAL,
    
    -- 分类
    classified_business_type TEXT,
    
    -- Owner/GZ
    owner_total REAL,
    gz_total REAL,
    calculated_total REAL,
    calculation_difference REAL,
    comparison_status TEXT,
    
    -- 存储
    final_file_path TEXT,
    backup_file_path TEXT,
    original_pdf_path TEXT,
    comparison_table_path TEXT
);
```

### upload_state_changes（审计日志）

```sql
CREATE TABLE upload_state_changes (
    id INTEGER PRIMARY KEY,
    transaction_uuid TEXT,
    from_status TEXT,
    to_status TEXT,
    changed_at DATETIME,
    reason TEXT,
    metadata TEXT  -- JSON
);
```

---

## 🚀 使用示例

### Python代码

```python
from services.upload_orchestrator import upload_orchestrator
from services.owner_gz_classifier import owner_gz_classifier

# 1. 启动上传
result = upload_orchestrator.execute_full_pipeline(
    file_path='temp/uploaded_file.pdf',
    original_filename='AmBank_Statement_Oct_2025.pdf',
    parser_service=pdf_parser,
    file_storage_manager=file_mgr,
    file_integrity_service=integrity_svc,
    business_type=None,  # 自动检测
    uploaded_by='admin'
)

# 2. 检查结果
if result['success']:
    print(f"✅ 上传成功！")
    print(f"   Customer: {result['customer']['customer_name']}")
    print(f"   Business Type: {result['business_type']}")
    print(f"   Owner Total: RM {result['parsed_data']['owner_total']:.2f}")
    print(f"   GZ Total: RM {result['parsed_data']['gz_total']:.2f}")
else:
    print(f"❌ 上传失败: {result['reason']}")
    print(f"   Transaction UUID: {result['transaction_uuid']}")
```

---

## 📊 运行演示

```bash
# 运行完整演示
python3 demo_upload_pipeline.py

# 输出：
# - 8阶段Pipeline执行过程
# - Owner/GZ自动分类结果
# - 对比表格
# - 原件路径
# - Architect约束检查
```

---

## ✅ 验收清单

上传文件后，系统必须：

- [x] 自动识别文件主人
- [x] 提取7个强制字段
- [x] 客户归属置信度≥0.98
- [x] 自动分类Owner/GZ
- [x] 生成对比表格
- [x] 验证计算准确性（差异≤RM 0.01）
- [x] 原件保存在固定路径
- [x] 备份到backup目录
- [x] 注册到file_registry
- [x] 记录所有状态变更到audit log
- [x] MD5重复检测

---

## 🛡️ 防健忘机制

### 1. 代码级别

```python
# Assert强制检查
assert status == 'PendingChecksum', "Invalid state"
assert confidence >= 0.98, "Confidence too low"
assert all_fields_present(), "Missing mandatory fields"
```

### 2. 数据库级别

```sql
-- CHECK约束
CHECK(status IN ('PendingChecksum', ...))
CHECK(attribution_confidence >= 0 AND attribution_confidence <= 1)
CHECK(status != 'StorageComplete' OR final_file_path IS NOT NULL)
```

### 3. 每日对账

```python
def daily_reconciliation():
    # 检查卡住的事务（>24小时）
    # 验证file_registry与文件系统一致性
    # 检查审计日志完整性
    pass
```

### 4. Watchdog警报

```python
def watchdog_check():
    # 检查超时事务（>2小时）
    # 发送警报
    pass
```

---

**© 2025 CreditPilot - 强制性文件上传系统**  
**再也不会丢失文件！再也不会健忘！**
