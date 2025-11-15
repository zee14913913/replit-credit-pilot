# 客户文件存储位置规范

## 🚨 重要警告：客户原件仅存放在一个位置！

**所有客户上传的银行账单原件PDF文件必须且只能存放在：**

```
static/uploads/customers/
```

**❌ 禁止将客户原件存放在以下位置：**
- ❌ `attached_assets/` - 这是临时上传区，不是永久存储位置
- ❌ `archive_old/` - 这是测试文件归档区
- ❌ 项目根目录
- ❌ 任何其他位置

---

## 📁 标准文件夹结构

### 信用卡账单存储结构

```
static/uploads/customers/
└── {customer_code}/                    # 客户代码（例如：Be_rich_CJY）
    └── credit_cards/                   # 信用卡账单文件夹
        └── {bank_name}/                # 银行名称（例如：AmBank, HSBC）
            └── {YYYY-MM}/              # 账单月份（例如：2025-05）
                └── {bank}_{last4}_{date}.pdf  # 账单文件
```

**示例：**
```
static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf
static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-09/HSBC_0034_2025-09-13.pdf
```

### 储蓄账户月结单存储结构

```
static/uploads/customers/
└── {customer_code}/                    # 客户代码
    └── savings/                        # 储蓄账户文件夹
        └── {bank_name}/                # 银行名称
            └── {YYYY-MM}/              # 账单月份
                └── {customer}_{bank}_{account}_{date}.pdf
```

**示例：**
```
static/uploads/customers/CORP20251030054640/savings/Hong_Leong_Bank/2025-09/INFINITE_GZ_Hong_Leong_Bank_4645_2025-09-05.pdf
```

---

## 📝 文件命名规范

### 信用卡账单命名格式

```
{BankName}_{CardLast4}_{YYYY-MM-DD}.pdf
```

**组成部分：**
- `{BankName}`: 银行名称（大小写标准化）
  - 例如：AmBank, HSBC, HONG_LEONG, STANDARD_CHARTERED
- `{CardLast4}`: 信用卡号后四位
  - 例如：6354, 0034, 3964
- `{YYYY-MM-DD}`: 账单日期
  - 例如：2025-05-28, 2025-09-13

**示例：**
```
AmBank_6354_2025-05-28.pdf
HSBC_0034_2025-09-13.pdf
HONG_LEONG_3964_2025-09-16.pdf
STANDARD_CHARTERED_1237_2025-09-14.pdf
```

### 储蓄账户命名格式

```
{CustomerName}_{BankName}_{AccountLast4}_{YYYY-MM-DD}.pdf
```

**示例：**
```
AI_SMART_TECH_Public_Bank_9009_2025-05-31.pdf
INFINITE_GZ_Hong_Leong_Bank_4645_2025-09-05.pdf
```

---

## 🔒 文件权限要求

所有客户原件PDF文件必须设置为：
- **权限**: `rw-------` (600) - 仅所有者可读写
- **所有者**: runner
- **用户组**: runner

**设置命令：**
```bash
chmod 600 static/uploads/customers/**/*.pdf
```

---

## 🚫 严格禁止的操作

### ❌ 禁止随意移动客户原件

**错误操作示例：**
```bash
# ❌ 错误！不要将客户原件移动到attached_assets
mv static/uploads/customers/Be_rich_CJY/credit_cards/*.pdf attached_assets/

# ❌ 错误！不要将客户原件归档到archive_old
mv static/uploads/customers/*.pdf archive_old/

# ❌ 错误！不要重命名客户原件文件
mv AmBank_6354_2025-05-28.pdf old_statement.pdf
```

### ✅ 正确操作

**上传新文件：**
```bash
# 1. 上传到临时位置（系统自动处理）
# 2. 系统自动移动到标准位置
# 3. 数据库记录 file_path
```

**查看文件：**
```bash
# 使用数据库中记录的 file_path
# 通过 /view_statement_file/<statement_id> 路由访问
```

---

## 📊 文件与数据库关联

### 数据库字段：`monthly_statements.file_path`

**每个月度账单记录必须包含：**
```sql
CREATE TABLE monthly_statements (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    bank_name TEXT,
    card_last4 TEXT,
    statement_month TEXT,
    file_path TEXT,  -- 指向实际PDF文件的路径
    ...
);
```

**file_path 格式：**
```
static/uploads/customers/{customer_code}/credit_cards/{bank}/{month}/{filename}.pdf
```

**示例记录：**
```sql
INSERT INTO monthly_statements (file_path) VALUES 
('static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf');
```

---

## 🔄 attached_assets 迁移规则

### 检查 attached_assets 中的客户文件

**识别规则：**
1. 文件名包含银行名称（AmBank, HSBC, Maybank, Public Bank, etc.）
2. 文件名包含客户姓名
3. 文件格式为PDF
4. 文件大小 > 50KB（真实账单）

**迁移步骤：**

```bash
# 1. 识别客户文件
find attached_assets -name "*AmBank*.pdf" -o -name "*HSBC*.pdf" -o -name "*Maybank*.pdf"

# 2. 确定客户代码和月份
# 从文件名或内容中提取信息

# 3. 创建标准目录
mkdir -p static/uploads/customers/{customer_code}/credit_cards/{bank}/{month}/

# 4. 移动文件到标准位置
mv attached_assets/original.pdf static/uploads/customers/{customer_code}/credit_cards/{bank}/{month}/{standard_name}.pdf

# 5. 更新数据库 file_path 字段
UPDATE monthly_statements SET file_path = '新路径' WHERE id = XXX;

# 6. 验证文件可访问
ls -lh static/uploads/customers/{customer_code}/credit_cards/{bank}/{month}/
```

### ⚠️ 迁移后验证

**必须检查：**
1. ✅ 文件在新位置存在
2. ✅ 数据库 file_path 已更新
3. ✅ 通过系统路由可以访问文件
4. ✅ 文件权限正确 (600)
5. ✅ 旧位置文件已删除

---

## 📋 文件管理最佳实践

### 1. 上传新账单

**系统自动处理流程：**
```python
# services/file_storage_manager.py
def store_statement_file(customer_code, bank_name, month, uploaded_file):
    # 1. 生成标准路径
    base_path = f"static/uploads/customers/{customer_code}/credit_cards/{bank_name}/{month}/"
    
    # 2. 创建目录
    os.makedirs(base_path, exist_ok=True)
    
    # 3. 生成标准文件名
    filename = f"{bank_name}_{card_last4}_{statement_date}.pdf"
    
    # 4. 保存文件
    file_path = os.path.join(base_path, filename)
    uploaded_file.save(file_path)
    
    # 5. 设置权限
    os.chmod(file_path, 0o600)
    
    # 6. 返回路径用于数据库存储
    return file_path
```

### 2. 查看账单文件

**通过路由访问：**
```python
@app.route('/view_statement_file/<int:statement_id>')
def view_statement_file(statement_id):
    # 1. 从数据库获取 file_path
    cursor.execute('SELECT file_path FROM monthly_statements WHERE id = ?', (statement_id,))
    row = cursor.fetchone()
    
    # 2. 验证文件存在
    if not os.path.exists(row['file_path']):
        return "文件不存在", 404
    
    # 3. 发送文件
    return send_file(row['file_path'], mimetype='application/pdf')
```

### 3. 删除账单

**级联删除流程：**
```python
def delete_statement(statement_id):
    # 1. 获取文件路径
    cursor.execute('SELECT file_path FROM monthly_statements WHERE id = ?', (statement_id,))
    file_path = cursor.fetchone()['file_path']
    
    # 2. 删除数据库记录
    cursor.execute('DELETE FROM monthly_statements WHERE id = ?', (statement_id,))
    cursor.execute('DELETE FROM transactions WHERE statement_id = ?', (statement_id,))
    
    # 3. 删除物理文件
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 4. 提交事务
    conn.commit()
```

---

## 🔍 文件完整性检查

### 定期检查脚本

```python
# tools/verify_file_integrity.py
import os
import sqlite3

def verify_file_integrity():
    """验证所有数据库记录都有对应的文件"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, file_path FROM monthly_statements WHERE file_path IS NOT NULL')
    
    missing_files = []
    for row in cursor.fetchall():
        if not os.path.exists(row['file_path']):
            missing_files.append({
                'id': row['id'],
                'path': row['file_path']
            })
    
    if missing_files:
        print(f"❌ 发现 {len(missing_files)} 个文件丢失！")
        for item in missing_files:
            print(f"   - ID:{item['id']}, Path:{item['path']}")
    else:
        print("✅ 所有文件完整！")
    
    return missing_files

if __name__ == '__main__':
    verify_file_integrity()
```

**运行检查：**
```bash
python tools/verify_file_integrity.py
```

---

## 📦 备份策略

### 1. 每日备份

```bash
# backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="backups/$DATE"

# 备份客户文件
mkdir -p $BACKUP_DIR
cp -r static/uploads/customers $BACKUP_DIR/

# 备份数据库
sqlite3 db/smart_loan_manager.db ".backup $BACKUP_DIR/smart_loan_manager.db"

echo "✅ 备份完成: $BACKUP_DIR"
```

### 2. 云存储同步（可选）

```bash
# 同步到云存储（AWS S3、Google Cloud Storage等）
aws s3 sync static/uploads/customers/ s3://your-bucket/customers/ --exclude "*.tmp"
```

---

## 🎯 快速参考

### 关键路径

| 用途 | 路径 | 说明 |
|------|------|------|
| **信用卡账单** | `static/uploads/customers/{code}/credit_cards/{bank}/{month}/` | ✅ 标准位置 |
| **储蓄月结单** | `static/uploads/customers/{code}/savings/{bank}/{month}/` | ✅ 标准位置 |
| **临时上传** | `attached_assets/` | ⚠️ 临时，需迁移 |
| **测试归档** | `archive_old/` | ❌ 仅测试文件 |

### 关键命令

```bash
# 查看所有客户文件
find static/uploads/customers -name "*.pdf" | wc -l

# 检查文件权限
ls -lh static/uploads/customers/**/*.pdf

# 验证数据库记录
sqlite3 db/smart_loan_manager.db "SELECT COUNT(*) FROM monthly_statements WHERE file_path IS NOT NULL;"

# 查找孤立文件（有文件无记录）
python tools/verify_file_integrity.py
```

---

## ⚠️ 常见错误和解决方案

### 错误1：文件上传到了错误位置

**症状：**
```
文件在 attached_assets/ 而不是 static/uploads/customers/
```

**解决：**
```bash
# 1. 识别客户和月份
# 2. 移动到标准位置
mv attached_assets/statement.pdf static/uploads/customers/{code}/credit_cards/{bank}/{month}/
# 3. 更新数据库
UPDATE monthly_statements SET file_path = '新路径' WHERE id = XXX;
```

### 错误2：数据库记录指向错误路径

**症状：**
```
数据库中 file_path = 'attached_assets/xxx.pdf'
```

**解决：**
```sql
-- 批量更新路径
UPDATE monthly_statements 
SET file_path = REPLACE(file_path, 'attached_assets/', 'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/')
WHERE file_path LIKE 'attached_assets/%';
```

### 错误3：文件权限错误

**症状：**
```
-rw-r--r-- 1 runner runner 264K AmBank_6354_2025-05-28.pdf
```

**解决：**
```bash
# 批量修复权限
find static/uploads/customers -name "*.pdf" -exec chmod 600 {} \;
```

---

## 📚 相关文档

- **系统架构**: `replit.md`
- **文件路由**: `app.py` → `/view_statement_file/<statement_id>`
- **存储管理**: `services/file_storage_manager.py`
- **数据库模式**: `db/schema.sql`

---

## 🔐 安全要求

1. **文件权限**: 600 (仅所有者可读写)
2. **访问控制**: 需要Admin/Accountant权限
3. **路径验证**: 防止路径遍历攻击
4. **HTTPS**: 生产环境必须使用HTTPS
5. **审计日志**: 记录所有文件访问操作

---

## ✅ 检查清单

在操作客户文件前，请确认：

- [ ] 文件存储在 `static/uploads/customers/` 目录
- [ ] 文件夹结构符合标准：`{code}/credit_cards/{bank}/{month}/`
- [ ] 文件命名符合规范：`{Bank}_{Last4}_{Date}.pdf`
- [ ] 文件权限设置为 600
- [ ] 数据库 `file_path` 字段已更新
- [ ] 可通过系统路由访问文件
- [ ] 已删除临时位置的副本
- [ ] 已记录操作日志

---

**最后更新**: 2024-11-15  
**版本**: 1.0.0  
**维护者**: INFINITE GZ Team

**记住：客户原件只能存放在一个位置！** 🔒
