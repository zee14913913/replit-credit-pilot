# CreditPilot 文件存储规范（强制执行）

**版本**: V1.0.0  
**生效日期**: 2025-11-24  
**状态**: 强制执行

---

## 🚨 严重问题回顾

### 历史问题
1. **文件重复上传**：系统一直说文件不见，导致8个客户累积几千份重复文件
2. **文件丢失**：清理过程中误删用户上传的原件
3. **业务混乱**：个人业务和公司业务没有明确区分

### 根本原因
- ❌ 没有文件索引系统
- ❌ 文件路径没有在数据库中记录
- ❌ 没有文件完整性验证
- ❌ 缺乏个人/公司业务分离机制

---

## ✅ 新文件存储系统（强制规范）

### 1. 文件注册表（File Registry）

**所有文件必须在file_registry表中注册**

```sql
CREATE TABLE file_registry (
    id INTEGER PRIMARY KEY,
    file_uuid TEXT UNIQUE NOT NULL,  -- 唯一标识
    original_filename TEXT NOT NULL,  -- 原始文件名
    file_path TEXT NOT NULL,  -- 存储路径
    file_hash TEXT,  -- MD5哈希（防重复）
    
    -- 客户信息
    customer_id INTEGER,
    customer_code TEXT,
    business_type TEXT CHECK(business_type IN ('personal', 'company', 'mixed')),
    
    -- 文件分类
    file_category TEXT NOT NULL,  -- 文件类别
    file_subcategory TEXT,  -- 子类别
    
    -- 关联信息
    entity_type TEXT,  -- 关联实体（statement/transaction/loan）
    entity_id INTEGER,  -- 关联ID
    
    -- 状态管理
    status TEXT DEFAULT 'active',  -- active/archived/deleted
    is_original BOOLEAN DEFAULT 1,  -- 是否原件
    parent_file_id INTEGER,  -- 如果是衍生文件，指向原件
    
    -- 备份信息
    backup_path TEXT,
    last_verified DATETIME,
    verification_status TEXT,
    
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded_by TEXT
);
```

---

### 2. 业务类型严格区分

#### 个人业务（Personal）

**定义**：客户个人名义的所有财务活动

```yaml
包含内容:
  - 个人名义的信用卡
  - 个人储蓄账户
  - 个人收入证明
  - 个人贷款申请
  - 个人CTOS报告

存储路径:
  static/uploads/customers/{customer_code}/personal/
  ├── credit_cards/
  ├── savings/
  ├── income_documents/
  ├── loans/
  └── ctos_reports/

business_type: 'personal'
```

---

#### 公司业务（Company）

**定义**：客户公司名义的所有财务活动

```yaml
包含内容:
  - 公司信用卡
  - 公司银行账户
  - 公司发票
  - 公司贷款
  - 公司CTOS报告

存储路径:
  static/uploads/customers/{customer_code}/company/
  ├── credit_cards/
  ├── bank_accounts/
  ├── invoices/
  ├── loans/
  └── ctos_reports/

business_type: 'company'
```

---

#### 混合业务（Mixed）

**定义**：同一张卡片/账户包含个人和公司混合支出

```yaml
示例:
  - LEE E KAI的AmBank信用卡
    → Owner's Expenses（个人支出）
    → INFINITE GZ's Expenses（公司支出）

存储路径:
  static/uploads/customers/{customer_code}/mixed/
  └── credit_cards/
      └── AmBank/
          ├── 2025-10/
          │   ├── AmBank_2025-10-28.pdf  -- 原始PDF
          │   ├── AmBank_2025-10-28_personal.xlsx  -- 个人部分
          │   └── AmBank_2025-10-28_company.xlsx  -- 公司部分
          
business_type: 'mixed'
```

---

### 3. 标准文件路径结构

#### 完整路径格式

```
static/uploads/customers/{customer_code}/{business_type}/{category}/{subcategory}/{year_month}/{filename}
```

#### 示例

**个人信用卡账单**:
```
static/uploads/customers/LEE_EK_009/personal/credit_cards/Maybank/2025-10/Maybank_2025-10-28.pdf
```

**公司供应商发票**:
```
static/uploads/customers/LEE_EK_009/company/invoices/supplier/7SL/2025-10/Invoice_7SL_INV001_2025-10-15.pdf
```

**混合业务信用卡**:
```
static/uploads/customers/LEE_EK_009/mixed/credit_cards/AmBank/2025-10/AmBank_2025-10-28.pdf
```

---

### 4. 文件上传流程（强制执行）

```yaml
Step 1: 文件验证
  - 检查文件类型（PDF/Excel/图片）
  - 检查文件大小（<10MB）
  - 计算文件MD5哈希

Step 2: 重复检测
  - 查询file_registry表
  - 如果file_hash已存在 → 提示"文件已存在，无需重复上传"
  - 显示已存在文件的位置和上传时间

Step 3: 生成文件UUID
  - 使用UUID4生成唯一标识
  - 格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Step 4: 确定业务类型
  - 询问用户：个人（Personal）/ 公司（Company）/ 混合（Mixed）
  - 根据业务类型选择存储路径

Step 5: 生成标准路径
  - 使用FileStorageManager生成路径
  - 包含业务类型前缀

Step 6: 保存文件
  - 复制文件到标准路径
  - 同时备份到backup目录

Step 7: 注册到file_registry
  - 插入完整元数据
  - 记录file_uuid、file_path、file_hash等

Step 8: 验证成功
  - 检查文件是否成功保存
  - 检查数据库记录是否创建
  - 返回file_uuid给用户

Step 9: 自动备份
  - 复制到backup_path
  - 记录备份时间
```

---

### 5. 文件完整性检查（每日自动执行）

```python
def daily_file_integrity_check():
    """每日文件完整性检查"""
    
    # 1. 检查所有file_registry记录
    files = db.query(FileRegistry).filter(
        FileRegistry.status == 'active'
    ).all()
    
    for file_record in files:
        # 2. 验证文件是否存在
        if not os.path.exists(file_record.file_path):
            # ❌ 文件丢失！
            log_critical_error(f"文件丢失：{file_record.file_path}")
            
            # 尝试从备份恢复
            if file_record.backup_path and os.path.exists(file_record.backup_path):
                shutil.copy2(file_record.backup_path, file_record.file_path)
                log_info(f"从备份恢复：{file_record.file_path}")
            else:
                # 发送紧急通知给Admin
                send_critical_alert(
                    f"文件丢失且无备份：{file_record.original_filename}"
                )
        
        # 3. 验证文件哈希
        current_hash = calculate_md5(file_record.file_path)
        if current_hash != file_record.file_hash:
            # ❌ 文件被修改！
            log_warning(f"文件哈希不匹配：{file_record.file_path}")
        
        # 4. 更新验证状态
        file_record.last_verified = datetime.now()
        file_record.verification_status = 'verified'
        db.commit()
```

---

### 6. 禁止操作清单

**绝对禁止的操作**:

```yaml
❌ 禁止项:
  1. 删除file_registry中status='active'的记录
  2. 删除is_original=1的原始文件
  3. 直接删除文件而不更新file_registry
  4. 修改已上传文件的内容
  5. 重命名已注册的文件
  6. 移动文件而不更新file_registry.file_path
  7. 清空customers目录
  8. 删除backup目录

⚠️  高风险操作（需Admin批准）:
  1. 归档文件（status='active' → 'archived'）
  2. 软删除文件（status='active' → 'deleted'）
  3. 批量文件操作（>10个文件）
```

---

### 7. 文件查询API

#### 查询客户所有文件
```python
GET /api/files/customer/{customer_code}?business_type=personal

返回:
[
    {
        "file_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "original_filename": "AmBank_Oct_2025.pdf",
        "file_path": "static/uploads/customers/LEE_EK_009/personal/credit_cards/AmBank/2025-10/AmBank_2025-10-28.pdf",
        "business_type": "personal",
        "file_category": "credit_card_statement",
        "upload_date": "2025-11-24T10:30:00Z",
        "status": "active",
        "is_original": true,
        "file_size": 524288,
        "verification_status": "verified"
    }
]
```

#### 检查文件是否存在
```python
GET /api/files/check?filename=AmBank_Oct_2025.pdf&customer_code=LEE_EK_009

返回:
{
    "exists": true,
    "file_uuid": "123e4567-e89b-12d3-a456-426614174000",
    "file_path": "static/uploads/customers/LEE_EK_009/personal/credit_cards/AmBank/2025-10/AmBank_2025-10-28.pdf",
    "upload_date": "2025-11-24T10:30:00Z",
    "message": "文件已存在，无需重复上传"
}
```

---

### 8. 恢复丢失文件流程

```yaml
如果用户报告文件丢失:

Step 1: 查询file_registry
  - 查找file_uuid或original_filename
  - 确认文件曾经存在

Step 2: 检查备份目录
  - 检查backup_path
  - 检查lee_e_kai_data/备份

Step 3: 从备份恢复
  - 复制备份文件到原始路径
  - 验证文件哈希
  - 更新last_verified

Step 4: 如果备份也丢失
  - 标记为 verification_status='missing'
  - 通知用户重新上传
  - 记录到审计日志
```

---

### 9. LEE E KAI客户文件结构示例

```
static/uploads/customers/LEE_EK_009/
├── personal/  -- 个人业务
│   ├── credit_cards/
│   │   ├── Maybank/
│   │   └── CIMB/
│   ├── savings/
│   ├── income_documents/
│   └── loans/
│
├── company/  -- 公司业务（INFINITE GZ）
│   ├── credit_cards/
│   ├── bank_accounts/
│   ├── invoices/
│   │   ├── supplier/  -- 供应商发票
│   │   │   ├── 7SL/
│   │   │   ├── Dinas/
│   │   │   └── Ai_Smart_Tech/
│   │   └── customer/  -- 客户发票
│   └── loans/
│
└── mixed/  -- 混合业务（同一张卡包含个人+公司）
    └── credit_cards/
        └── AmBank_Islamic/
            └── 2025-10/
                ├── AmBank_Islamic_2025-10-28.pdf  -- 原始PDF
                ├── AmBank_Islamic_2025-10-28_personal.xlsx
                └── AmBank_Islamic_2025-10-28_company.xlsx
```

---

### 10. 监控和告警

**自动监控项**:

```yaml
1. 文件完整性检查（每日）
   - 验证所有active文件存在
   - 验证文件哈希
   
2. 重复文件检测（每周）
   - 查找相同file_hash的文件
   - 合并重复记录

3. 存储空间监控（实时）
   - 监控磁盘使用率
   - 超过80%发送警告

4. 备份状态检查（每日）
   - 验证backup_path有效
   - 检查备份文件完整性

告警渠道:
  - 系统日志
  - 邮件通知（Admin）
  - SMS通知（紧急情况）
```

---

## 📋 实施检查清单

### 上线前必须完成

- [ ] file_registry表创建完成
- [ ] FileStorageManager更新支持business_type
- [ ] 文件上传API更新支持重复检测
- [ ] 文件完整性检查脚本部署
- [ ] 备份恢复流程测试
- [ ] 所有现有文件注册到file_registry
- [ ] Admin文件管理界面上线
- [ ] 文档培训完成

---

## ⚠️ 违规惩罚

**如果发现以下违规操作**:

1. **删除原始文件** → 系统回滚 + 从备份恢复
2. **未注册直接上传** → 文件移动到quarantine目录
3. **重复上传检测失败** → Bug修复优先级P0
4. **文件完整性检查失败** → 立即告警 + 人工介入

---

**© 2025 CreditPilot - 文件存储规范（强制执行）**  
**任何违反此规范的操作都将被视为严重系统故障**
