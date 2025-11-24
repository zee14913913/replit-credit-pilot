# 📁 统一文件存储架构规范

## 设计原则

### 核心理念
1. **客户隔离优先** - 每个客户拥有独立文件夹
2. **类型分类清晰** - 按文件类型自动分类存储
3. **时间维度管理** - 按年月组织，易于归档
4. **路径即索引** - 文件路径本身就是最好的索引
5. **可扩展性** - 支持未来新增文件类型

---

## 标准目录结构

```
static/uploads/customers/{customer_code}/
├── credit_cards/                    # 信用卡账单
│   ├── {bank_name}/                 # 按银行分类
│   │   └── {YYYY-MM}/               # 按年月分类
│   │       ├── {BankName}_{Last4}_{YYYY-MM-DD}.pdf
│   │       └── {BankName}_{Last4}_{YYYY-MM-DD}_verified.pdf
│   └── merged/                      # 合并账单（多卡合一）
│       └── {YYYY-MM}/
│           └── {BankName}_Multi_{YYYY-MM-DD}.pdf
│
├── savings/                         # 储蓄账户月结单
│   ├── {bank_name}/                 # 按银行分类
│   │   └── {YYYY-MM}/               # 按年月分类
│   │       └── {BankName}_{AccountNum}_{YYYY-MM-DD}.pdf
│
├── receipts/                        # 收据管理
│   ├── payment_receipts/            # 付款收据
│   │   ├── {YYYY-MM}/
│   │   │   └── {YYYY-MM-DD}_{Merchant}_{Amount}_{card_last4}.{jpg|png|pdf}
│   │   └── pending/                 # 待匹配收据
│   │       └── {timestamp}_{filename}.{jpg|png}
│   │
│   └── merchant_receipts/           # 商户收据
│       └── {YYYY-MM}/
│           └── {YYYY-MM-DD}_{Merchant}_{Amount}.{jpg|png|pdf}
│
├── invoices/                        # 发票管理
│   ├── supplier/                    # 供应商发票
│   │   └── {YYYY-MM}/
│   │       └── Invoice_{SupplierName}_{InvoiceNum}_{Date}.pdf
│   │
│   └── customer/                    # 客户发票
│       └── {YYYY-MM}/
│           └── Invoice_{CustomerName}_{InvoiceNum}_{Date}.pdf
│
├── reports/                         # 生成的报告
│   ├── monthly/                     # 月度报告
│   │   └── {YYYY-MM}/
│   │       └── Monthly_Report_{YYYY-MM}.pdf
│   │
│   ├── annual/                      # 年度报告
│   │   └── {YYYY}/
│   │       └── Annual_Report_{YYYY}.pdf
│   │
│   └── custom/                      # 自定义报告
│       └── {report_type}_{timestamp}.pdf
│
├── loans/                           # 贷款相关文件
│   ├── applications/                # 贷款申请
│   │   └── {YYYY-MM}/
│   │       └── Loan_Application_{Date}.pdf
│   │
│   └── ctos_reports/                # CTOS报告
│       └── {YYYY-MM}/
│           └── CTOS_{Date}.pdf
│
└── documents/                       # 其他文档
    ├── contracts/                   # 合同协议
    ├── identification/              # 身份证明
    └── misc/                        # 杂项文件
```

---

## 命名规范

### 文件命名格式

#### 信用卡账单
```
{BankName}_{Last4Digits}_{YYYY-MM-DD}.pdf

示例:
- Maybank_5678_2025-10-15.pdf
- CIMB_1234_2025-09-20.pdf
- HongLeong_9876_2025-08-25.pdf
```

#### 储蓄账户月结单
```
{BankName}_{AccountNum}_{YYYY-MM-DD}.pdf

示例:
- GXBank_1761028205600_2025-10-01.pdf
- Maybank_1234567890_2025-09-30.pdf
```

#### 收据
```
{YYYY-MM-DD}_{Merchant}_{Amount}_{card_last4}.{ext}

示例:
- 2025-10-15_Starbucks_25.50_5678.jpg
- 2025-10-15_Shell_60.00_1234.png
```

#### 发票
```
Invoice_{PartyName}_{InvoiceNumber}_{Date}.pdf

示例:
- Invoice_ABC_Supply_INV001_2025-10-15.pdf
- Invoice_Customer_John_Doe_INV123_2025-10-20.pdf
```

### 目录命名规范

#### 客户代码 (customer_code)
```
Be_rich_{INITIALS}

规则:
- 前缀固定为 "Be_rich_"
- 使用客户姓名的首字母缩写（大写）
- 多个单词取每个单词的首字母

示例:
- CHANG CHOON CHOW → Be_rich_CCC
- Ahmad Abdullah → Be_rich_AA
- Lee Wei Ming → Be_rich_LWM
```

#### 银行名称 (bank_name)
```
使用标准银行简称，用下划线连接多个单词

示例:
- Maybank
- CIMB_Bank
- Hong_Leong_Bank
- Alliance_Bank
- GX_Bank
```

#### 年月格式 (YYYY-MM)
```
统一使用 ISO 8601 格式

示例:
- 2025-10
- 2024-12
- 2025-01
```

---

## 路径生成规则

### 信用卡账单路径
```python
def get_credit_card_statement_path(customer_code, bank_name, card_last4, statement_date):
    """
    生成信用卡账单存储路径
    
    Args:
        customer_code: 客户代码 (例如: Be_rich_CCC)
        bank_name: 银行名称 (例如: Maybank)
        card_last4: 卡号后4位 (例如: 5678)
        statement_date: 账单日期 (datetime对象或字符串)
    
    Returns:
        完整文件路径: static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/2025-10/Maybank_5678_2025-10-15.pdf
    """
    year_month = statement_date.strftime('%Y-%m')
    date_str = statement_date.strftime('%Y-%m-%d')
    filename = f"{bank_name}_{card_last4}_{date_str}.pdf"
    
    return f"static/uploads/customers/{customer_code}/credit_cards/{bank_name}/{year_month}/{filename}"
```

### 储蓄账户月结单路径
```python
def get_savings_statement_path(customer_code, bank_name, account_num, statement_date):
    """
    生成储蓄账户月结单存储路径
    """
    year_month = statement_date.strftime('%Y-%m')
    date_str = statement_date.strftime('%Y-%m-%d')
    filename = f"{bank_name}_{account_num}_{date_str}.pdf"
    
    return f"static/uploads/customers/{customer_code}/savings/{bank_name}/{year_month}/{filename}"
```

### 收据路径
```python
def get_receipt_path(customer_code, receipt_date, merchant, amount, card_last4, file_ext):
    """
    生成收据存储路径
    """
    year_month = receipt_date.strftime('%Y-%m')
    date_str = receipt_date.strftime('%Y-%m-%d')
    # 清理商户名称（移除特殊字符）
    clean_merchant = re.sub(r'[^\w\s-]', '', merchant).replace(' ', '_')
    filename = f"{date_str}_{clean_merchant}_{amount}_{card_last4}.{file_ext}"
    
    return f"static/uploads/customers/{customer_code}/receipts/payment_receipts/{year_month}/{filename}"
```

---

## 目录创建策略

### 自动创建规则
1. **按需创建** - 只在需要保存文件时创建目录
2. **递归创建** - 使用 `os.makedirs(exist_ok=True)`
3. **权限设置** - 确保Web服务器可读写
4. **日志记录** - 记录目录创建操作

### 示例代码
```python
def ensure_directory_exists(file_path):
    """
    确保文件路径的目录存在
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    return directory
```

---

## 文件操作规范

### 上传流程
```python
1. 接收上传文件
2. 验证文件类型和大小
3. 提取关键信息（客户、银行、日期等）
4. 生成标准化文件路径
5. 确保目标目录存在
6. 保存文件到目标位置
7. 更新数据库file_path字段
8. 记录审计日志
```

### 删除流程
```python
1. 检查文件是否存在
2. 备份文件到backup目录
3. 从文件系统删除
4. 更新数据库状态（软删除或物理删除）
5. 记录审计日志
```

### 移动/重命名流程
```python
1. 验证源文件存在
2. 生成新的目标路径
3. 确保目标目录存在
4. 复制文件到新位置
5. 验证复制成功
6. 删除原文件
7. 更新数据库file_path字段
8. 记录审计日志
```

---

## 数据库字段规范

### file_path 字段
```sql
-- 统一使用相对路径（从项目根目录开始）
file_path TEXT

-- 示例值:
'static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/2025-10/Maybank_5678_2025-10-15.pdf'

-- 不要使用绝对路径:
'/home/runner/workspace/static/uploads/...'  ❌
```

### 路径存储原则
1. **相对路径** - 便于项目迁移
2. **正斜杠** - 跨平台兼容
3. **无空格** - 避免URL编码问题
4. **小写优先** - 除客户代码外尽量使用小写

---

## 备份策略

### 定期备份
```bash
# 每日备份整个customers目录
tar -czf backup_customers_$(date +%Y%m%d).tar.gz static/uploads/customers/

# 按客户备份
tar -czf backup_Be_rich_CCC_$(date +%Y%m%d).tar.gz static/uploads/customers/Be_rich_CCC/
```

### 备份保留策略
- **每日备份**: 保留7天
- **每周备份**: 保留4周
- **每月备份**: 保留12个月
- **年度备份**: 永久保留

---

## 性能优化

### 文件访问优化
1. **CDN加速** - 静态文件通过CDN分发
2. **延迟加载** - 大文件按需加载
3. **缓存策略** - PDF预览使用浏览器缓存
4. **索引优化** - 数据库file_path字段建索引

### 存储优化
1. **压缩存储** - PDF文件自动压缩
2. **归档策略** - 超过2年的文件归档到冷存储
3. **去重检测** - 上传前检查MD5避免重复

---

## 迁移计划

### 阶段1：准备工作（已完成）
- ✅ 设计新架构
- ✅ 创建FileStorageManager服务
- ✅ 编写迁移脚本

### 阶段2：测试迁移（建议先执行）
- 🔄 选择1-2个客户进行测试迁移
- 🔄 验证文件访问正常
- 🔄 验证数据库路径更新正确

### 阶段3：全量迁移（测试通过后）
- 🔄 备份整个数据库和文件系统
- 🔄 执行批量迁移脚本
- 🔄 验证所有文件和路径
- 🔄 删除旧目录

### 阶段4：清理工作
- 🔄 删除旧的文件目录
- 🔄 更新所有相关代码
- 🔄 文档更新

---

## 故障恢复

### 迁移失败回滚
```python
1. 停止迁移脚本
2. 从备份恢复数据库
3. 从备份恢复文件系统
4. 验证系统正常
5. 分析失败原因
6. 修复问题后重新迁移
```

### 数据一致性检查
```python
def verify_file_consistency():
    """
    验证数据库记录与文件系统的一致性
    """
    # 检查数据库中的file_path是否都对应存在的文件
    # 检查文件系统中的文件是否都有数据库记录
    # 报告不一致的情况
```

---

## 最佳实践

### ✅ DO
- 使用FileStorageManager统一管理文件路径
- 保存文件前先验证目录存在
- 更新file_path时同时更新文件位置
- 删除记录时同时删除对应文件
- 定期运行一致性检查

### ❌ DON'T
- 不要手动构建文件路径
- 不要直接修改文件系统而不更新数据库
- 不要使用绝对路径
- 不要在文件名中使用特殊字符
- 不要忘记记录审计日志

---

## 相关文件

- **服务类**: `services/file_storage_manager.py`
- **迁移脚本**: `migrate_file_storage.py`
- **测试脚本**: `test_file_storage.py`
- **配置文件**: `config/storage_config.py`

---

**文档版本**: 1.0  
**创建时间**: 2025-10-23  
**最后更新**: 2025-10-23  
**维护者**: Replit Agent
