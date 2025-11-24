# ARCHITECT强制性约束 - 文件上传与分类系统

**版本**: V2.0.0  
**生效日期**: 2025-11-24  
**核心要求**: 自动解析文件主人、分类Owner/GZ、生成对比表格、原件固定位置

---

## 🎯 核心功能要求

### 1. 自动识别文件主人

**强制要求**：
- ✅ 解析PDF时自动提取客户名字
- ✅ 交叉引用customers表
- ✅ 自动匹配customer_code
- ✅ 置信度≥0.98才自动存储

### 2. 自动分类Owner/GZ

**业务规则**（以LEE E KAI为例）：
```yaml
Owner's Expenses（个人支出）:
  - LEE E KAI本人的消费
  - 个人生活开支
  - 分类: business_type = 'personal'

GZ's Expenses（公司支出 - INFINITE GZ）:
  - INFINITE GZ SDN BHD的业务支出
  - 供应商付款（7SL, Dinas Raub, Ai Smart Tech等）
  - 分类: business_type = 'company'

Mixed（混合业务）:
  - 同一张卡包含Owner + GZ支出
  - 需要分开计算
  - 分类: business_type = 'mixed'
```

### 3. 生成对比表格

**强制要求**：每个账单必须生成对比表格

```yaml
对比表格内容:
  原件数据:
    - Statement Total（账单总额）
    - Minimum Payment（最低还款）
    - Due Date（到期日期）
  
  计算数据:
    - Owner's Total（个人支出总计）
    - GZ's Total（公司支出总计）
    - Calculated Total（计算总额）
  
  验证:
    - 差异 = Calculated Total - Statement Total
    - 差异 ≤ RM 0.01 → ✅ 验证通过
    - 差异 > RM 0.01 → ⚠️  需要人工审核
```

### 4. 原件固定位置

**强制存储路径**：
```
static/uploads/customers/{customer_code}/statements/original/
├── {bank_name}/
│   └── {YYYY-MM}/
│       └── {bank_name}_{YYYY-MM-DD}_ORIGINAL.pdf

示例:
static/uploads/customers/LEE_EK_009/statements/original/AmBank_Islamic/2025-10/AmBank_Islamic_2025-10-28_ORIGINAL.pdf
```

**备份路径**：
```
static/uploads_backup/customers/{customer_code}/statements/original/
└── (相同结构)
```

**绝对禁止**：
- ❌ 移动原件
- ❌ 重命名原件
- ❌ 删除原件
- ❌ 修改原件

---

## 📋 完整Pipeline（含Owner/GZ分类）

### Stage 1-3：基础Pipeline
（已实现）

### Stage 4：Owner/GZ自动分类

```python
def checkpoint_4_classify_owner_gz(transaction_uuid: str) -> Dict:
    """
    检查点4：Owner/GZ自动分类
    
    步骤：
    1. 读取解析的交易记录
    2. 根据商户名称自动分类
    3. 计算Owner Total和GZ Total
    4. 生成对比表格
    """
    
    # 1. 获取交易记录
    transactions = get_parsed_transactions(transaction_uuid)
    
    # 2. 自动分类规则
    owner_transactions = []
    gz_transactions = []
    
    for txn in transactions:
        merchant = txn['merchant_name'].upper()
        
        # GZ供应商列表（公司支出）
        GZ_SUPPLIERS = [
            '7SL', 'DINAS RAUB', 'AI SMART TECH', 
            'HUAWEI', 'TESCO', 'LOTUS', 'SHOPEE'
        ]
        
        # 判断是否GZ支出
        is_gz = any(supplier in merchant for supplier in GZ_SUPPLIERS)
        
        if is_gz:
            gz_transactions.append(txn)
        else:
            owner_transactions.append(txn)
    
    # 3. 计算总额
    owner_total = sum(t['amount'] for t in owner_transactions)
    gz_total = sum(t['amount'] for t in gz_transactions)
    calculated_total = owner_total + gz_total
    
    # 4. 对比原件
    statement_total = get_statement_total(transaction_uuid)
    difference = abs(calculated_total - statement_total)
    
    # 5. 验证
    if difference > 0.01:
        # ⚠️ 差异过大，转人工审核
        return {
            'success': False,
            'reason': f'Calculation mismatch: {difference:.2f}',
            'owner_total': owner_total,
            'gz_total': gz_total,
            'calculated_total': calculated_total,
            'statement_total': statement_total
        }
    
    # ✅ 分类成功
    return {
        'success': True,
        'owner_total': owner_total,
        'gz_total': gz_total,
        'calculated_total': calculated_total,
        'statement_total': statement_total,
        'difference': difference,
        'owner_count': len(owner_transactions),
        'gz_count': len(gz_transactions)
    }
```

### Stage 5：生成对比表格

```python
def generate_comparison_table(transaction_uuid: str) -> str:
    """
    生成对比表格（Excel格式）
    
    格式：
    ┌────────────────────────────────────────┐
    │   LEE E KAI - AmBank Islamic          │
    │   Statement Date: 2025-10-28          │
    ├────────────────────────────────────────┤
    │                                        │
    │   原件数据（From PDF）                  │
    │   Statement Total:    RM 14,515.00    │
    │   Minimum Payment:    RM    450.00    │
    │   Due Date:           2025-11-15      │
    │                                        │
    │   计算数据（Calculated）                │
    │   Owner's Total:      RM  8,200.00    │
    │   GZ's Total:         RM  6,315.00    │
    │   Calculated Total:   RM 14,515.00    │
    │                                        │
    │   验证结果                              │
    │   差异:               RM      0.00    │
    │   状态:               ✅ 验证通过       │
    │                                        │
    └────────────────────────────────────────┘
    """
    pass
```

---

## 🔒 强制性约束（新增）

### 约束11：原件路径固定

```python
# 强制路径格式
ORIGINAL_PATH_TEMPLATE = (
    "static/uploads/customers/{customer_code}/"
    "statements/original/{bank_name}/{year_month}/"
    "{bank_name}_{date}_ORIGINAL.pdf"
)

# 生成路径时强制使用模板
def get_original_statement_path(customer_code, bank_name, statement_date):
    year_month = statement_date.strftime('%Y-%m')
    date_str = statement_date.strftime('%Y-%m-%d')
    
    return ORIGINAL_PATH_TEMPLATE.format(
        customer_code=customer_code,
        bank_name=bank_name,
        year_month=year_month,
        date=date_str
    )
```

### 约束12：Owner/GZ分类强制执行

```python
# 强制分类检查
MANDATORY_CLASSIFICATION = {
    'owner_total': float,    # 必须有Owner总额
    'gz_total': float,       # 必须有GZ总额
    'calculated_total': float, # 必须有计算总额
    'statement_total': float,  # 必须有原件总额
    'difference': float        # 必须有差异值
}

# 验证
def validate_classification(result: Dict) -> bool:
    for key, expected_type in MANDATORY_CLASSIFICATION.items():
        if key not in result:
            raise ValueError(f"Missing mandatory field: {key}")
        if not isinstance(result[key], expected_type):
            raise TypeError(f"Invalid type for {key}")
    
    return True
```

### 约束13：对比表格强制生成

```python
# 每个账单必须生成对比表格
def finalize_upload(transaction_uuid: str):
    # 1. 分类Owner/GZ
    classification_result = checkpoint_4_classify_owner_gz(transaction_uuid)
    
    if not classification_result['success']:
        # 转人工审核
        status = 'PendingReview'
        return
    
    # 2. 强制生成对比表格
    comparison_table_path = generate_comparison_table(transaction_uuid)
    
    # 3. 验证表格已生成
    assert os.path.exists(comparison_table_path), \
        "Comparison table generation failed"
    
    # 4. 保存路径到数据库
    save_comparison_table_path(transaction_uuid, comparison_table_path)
```

---

## 📊 数据库扩展

### 新增字段（upload_transactions表）

```sql
ALTER TABLE upload_transactions ADD COLUMN IF NOT EXISTS
    -- Owner/GZ分类结果
    owner_total REAL,
    gz_total REAL,
    calculated_total REAL,
    statement_total_original REAL,
    calculation_difference REAL,
    
    -- 对比表格
    comparison_table_path TEXT,
    comparison_status TEXT CHECK(comparison_status IN ('match', 'mismatch', 'pending_review')),
    
    -- 原件路径（固定不变）
    original_pdf_path TEXT UNIQUE  -- 强制唯一，防止重复
```

---

## 🎯 LEE E KAI示例

### 完整流程

```yaml
Step 1: 上传AmBank Islamic 10月账单
  文件: AmBank_E-Statement_Oct_2025.pdf

Step 2: 自动解析
  Owner Name: LEE E KAI
  Customer Code: LEE_EK_009
  Bank: AmBank Islamic
  Statement Date: 2025-10-28
  Statement Total: RM 14,515.00
  Minimum Payment: RM 450.00

Step 3: 客户匹配
  匹配结果: LEE E KAI (LEE_EK_009)
  置信度: 1.0 ✅

Step 4: Owner/GZ自动分类
  交易总数: 156条
  
  Owner's Expenses（个人）:
    - 餐饮: RM 1,200.00
    - 购物: RM 3,500.00
    - 交通: RM 800.00
    - 其他: RM 2,700.00
    Owner Total: RM 8,200.00（95条）
  
  GZ's Expenses（公司 - INFINITE GZ）:
    - 7SL: RM 2,500.00
    - Dinas Raub: RM 1,800.00
    - Ai Smart Tech: RM 1,200.00
    - 其他供应商: RM 815.00
    GZ Total: RM 6,315.00（61条）
  
  Calculated Total: RM 14,515.00
  
Step 5: 对比验证
  原件总额: RM 14,515.00
  计算总额: RM 14,515.00
  差异: RM 0.00 ✅ 验证通过

Step 6: 存储原件
  路径: static/uploads/customers/LEE_EK_009/statements/original/AmBank_Islamic/2025-10/AmBank_Islamic_2025-10-28_ORIGINAL.pdf
  备份: static/uploads_backup/customers/LEE_EK_009/statements/original/AmBank_Islamic/2025-10/AmBank_Islamic_2025-10-28_ORIGINAL.pdf

Step 7: 生成对比表格
  Excel: static/uploads/customers/LEE_EK_009/statements/comparison/AmBank_Islamic/2025-10/AmBank_Islamic_2025-10-28_COMPARISON.xlsx

Step 8: 注册file_registry
  file_uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  business_type: mixed（包含Owner+GZ）
  status: active
```

---

## ✅ 验收标准

**上传文件后，系统必须**：

1. ✅ 自动识别文件主人（LEE E KAI）
2. ✅ 自动分类Owner/GZ支出
3. ✅ 计算Owner Total和GZ Total
4. ✅ 生成对比表格（计算 vs 原件）
5. ✅ 验证差异≤RM 0.01
6. ✅ 原件保存在固定路径
7. ✅ 备份到backup目录
8. ✅ 注册到file_registry
9. ✅ 记录所有状态变更
10. ✅ 生成可查看的对比表格Excel

**禁止**：
- ❌ 移动或重命名原件
- ❌ 删除任何原始文件
- ❌ 跳过Owner/GZ分类
- ❌ 跳过对比验证
- ❌ 手动指定文件路径

---

**© 2025 CreditPilot - ARCHITECT强制性约束V2.0**  
**包含自动Owner/GZ分类和对比表格生成**
