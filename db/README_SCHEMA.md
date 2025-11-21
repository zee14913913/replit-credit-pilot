
# Infinite GZ 系统数据库 Schema 文档

## 📋 概述

完整的 Infinite GZ 信用卡管理系统数据库设计，包含 11 个核心表和 1 个汇总视图。

## 🗂️ 数据库文件

- **schema.sql** - 完整的 SQLite 建表脚本
- **models.py** - Python SQLAlchemy ORM 模型
- **init_infinite_gz_schema.py** - 自动初始化脚本

## 📊 核心表结构

### 1. users - 用户信息表
```sql
主要字段：
- id, name, ic_number, phone, email
- company_name, role (customer/admin/accountant/viewer)
- ctos_score, dsr, monthly_income
- password_hash, is_active
```

### 2. credit_cards - 信用卡账户表
```sql
主要字段：
- user_id (FK), bank_name, card_number_last4
- credit_limit, available_credit
- statement_cutoff_day, payment_due_day
- points_balance
```

### 3. statements - 账单主表
```sql
主要字段：
- user_id (FK), card_id (FK)
- statement_date, due_date, statement_month
- total_amount, min_payment
- parse_status, is_confirmed
- file_path, upload_filename
```

### 4. transactions - 交易明细表
```sql
主要字段：
- statement_id (FK), transaction_date, description
- debit_amount, credit_amount
- classification (Owner/GZ) ⭐
- transaction_type (Expense/Payment) ⭐
- supplier_name, supplier_fee (1%)
```

### 5. settlements - 月结算表
```sql
主要字段：
- user_id (FK), settlement_month
- owner_expenses, owner_payments, owner_outstanding_balance
- gz_expenses, gz_payments, gz_outstanding_balance
- total_supplier_fee, optimization_savings
- settlement_status
```

### 6. suppliers - 供应商列表
```sql
主要字段：
- supplier_name, supplier_aliases (JSON)
- supplier_category (7SL主要供应商/Shop/Utilities)
- fee_percentage (默认1%)
```

### 7. reminders - 提醒记录表
```sql
主要字段：
- user_id (FK), reminder_type
- scheduled_time, send_status
- send_channel (email/sms/in_app)
```

### 8. contracts - 合同签约表
```sql
主要字段：
- user_id (FK), contract_type, contract_number
- signed_at, signature_image_path
- contract_status, pdf_path
```

### 9. loan_products - 贷款产品知识库
```sql
主要字段：
- institution_name, product_name, product_type
- interest_rate_min/max, loan_amount_min/max
- min_income, min_ctos_score, max_dsr
```

### 10. tax_records - 税务记录表
```sql
主要字段：
- user_id (FK), tax_year
- total_income, total_deductions
- taxable_income, tax_payable
```

### 11. monthly_statements - 月度汇总表 (Module 4)
```sql
6个强制字段（100%准确度）：
1. total_spent - 总支出
2. total_fees - 总费用（1% supplier fee）
3. total_supplier_consumption - 供应商消费总额
4. total_customer_payment - 客户付款总额
5. total_revenue - 总收入
6. total_refunds - 退款总额
```

## 🚀 快速开始

### 方法1：使用初始化脚本（推荐）

```bash
cd db
python init_infinite_gz_schema.py
```

### 方法2：手动执行 SQL

```bash
sqlite3 db/smart_loan_manager.db < db/schema.sql
```

### 方法3：Python ORM 方式

```python
from sqlalchemy import create_engine
from db.models import Base, init_database

# 创建数据库引擎
engine = create_engine('sqlite:///db/smart_loan_manager.db')

# 初始化所有表
init_database(engine)
```

## 📝 使用示例

### 1. 创建用户

```python
from sqlalchemy.orm import sessionmaker
from db.models import User

Session = sessionmaker(bind=engine)
session = Session()

user = User(
    name="Chang Choon Chow",
    email="ccc@example.com",
    ic_number="901231-10-5678",
    role="customer",
    monthly_income=8000.00,
    ctos_score=750
)
session.add(user)
session.commit()
```

### 2. 创建信用卡

```python
from db.models import CreditCard

card = CreditCard(
    user_id=user.id,
    bank_name="Maybank",
    card_number_last4="5678",
    card_type="Visa",
    credit_limit=10000.00,
    statement_cutoff_day=25,
    payment_due_day=15
)
session.add(card)
session.commit()
```

### 3. 添加交易记录

```python
from db.models import Transaction

transaction = Transaction(
    statement_id=1,
    transaction_date="2025-11-15",
    description="7SL TECH SDN BHD",
    debit_amount=1500.00,
    classification="GZ",  # GZ's Expense
    transaction_type="Expense",
    supplier_name="7SL",
    supplier_fee=15.00  # 1% of 1500
)
session.add(transaction)
session.commit()
```

### 4. 查询月度汇总

```python
from db.models import MonthlyStatement

monthly = session.query(MonthlyStatement).filter_by(
    user_id=user.id,
    statement_month="2025-11"
).first()

print(f"总支出: {monthly.total_spent}")
print(f"总费用: {monthly.total_fees}")
print(f"总收入: {monthly.total_revenue}")
```

## 🔍 重要业务规则

### Module 4: 交易分类规则

1. **Owner's Expenses** - Owner 自己的消费
   - 非7个供应商的消费
   - Shop (Shopee/Lazada)
   - Utilities (TNB)

2. **GZ's Expenses** - GZ 公司的消费
   - 7个主要供应商：7SL, Dinas Raub, SYC Hainan, Ai Smart Tech, HUAWEI, Pasar Raya, Puchong Herbs
   - 产生 1% supplier fee

3. **Owner's Payment** - Owner 还款
   - Owner 名字出现在交易描述中

4. **GZ's Payment** - GZ 公司还款
   - GZ 银行账户转账

### 月结算计算公式

```
Owner's OS Bal = Previous Bal + Owner's Expenses - Owner's Payment
GZ's OS Bal = Previous Bal + GZ's Expenses + Supplier Fee - GZ's Payment
Total Revenue = Total Fees + Total Supplier Consumption
```

## 🔐 数据完整性

- ✅ 所有外键关系已设置 `ON DELETE CASCADE`
- ✅ 关键字段设置 `NOT NULL` 约束
- ✅ 枚举字段使用 `CHECK` 约束
- ✅ 唯一性约束：email, ic_number, contract_number
- ✅ 组合唯一约束：(card_id, statement_month)
- ✅ 31 个索引优化查询性能

## 📦 预置数据

### 供应商（10条）

1. 7SL (7SL主要供应商, 1% fee)
2. Dinas Raub (7SL主要供应商, 1% fee)
3. SYC Hainan (7SL主要供应商, 1% fee)
4. Ai Smart Tech (7SL主要供应商, 1% fee)
5. HUAWEI (7SL主要供应商, 1% fee)
6. Pasar Raya (7SL主要供应商, 1% fee)
7. Puchong Herbs (7SL主要供应商, 1% fee)
8. Shopee (Shop, 0% fee)
9. Lazada (Shop, 0% fee)
10. TNB (Utilities, 0% fee)

### 管理员账户（1个）

- Email: admin@infinitegz.com
- Role: admin
- 注意：首次使用需要设置密码

## 🛠️ 维护操作

### 备份数据库

```bash
sqlite3 db/smart_loan_manager.db ".backup db/backup_$(date +%Y%m%d).db"
```

### 查看表结构

```bash
sqlite3 db/smart_loan_manager.db ".schema transactions"
```

### 查看所有索引

```bash
sqlite3 db/smart_loan_manager.db "SELECT name FROM sqlite_master WHERE type='index'"
```

## ❓ 常见问题

### Q: 为什么使用 SQLite 而不是 PostgreSQL？
A: 轻量级、无需配置、适合单用户/小团队场景。如需扩展可迁移到 PostgreSQL。

### Q: 如何修改现有表结构？
A: 使用 SQLite 的 ALTER TABLE 或创建迁移脚本。

### Q: 外键约束如何启用？
A: 每次连接需执行 `PRAGMA foreign_keys = ON;`

## 📞 技术支持

如有问题请查看：
- `docs/` 文件夹中的详细文档
- `services/transaction_classifier.py` 交易分类逻辑
- `services/monthly_report_generator.py` 月度报表生成

---

**版本**: 1.0  
**创建日期**: 2025-11-21  
**作者**: Infinite GZ 开发团队
