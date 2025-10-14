# 系统工具脚本

此目录包含系统维护和查看工具脚本。

## 可用脚本

### 1. create_monthly_ledger_tables.py
创建月度账本相关的数据库表，包括：
- monthly_ledger（客户月度账本）
- infinite_monthly_ledger（INFINITE月度账本）
- infinite_transfers（转账记录）
- supplier_aliases（供应商别名）
- payer_aliases（付款人别名）
- transfer_recipient_aliases（转账收款人别名）

**使用方法：**
```bash
python scripts/create_monthly_ledger_tables.py
```

### 2. calculate_monthly_ledgers.py
计算所有客户的月度账本，重新计算所有财务数据。

**使用方法：**
```bash
python scripts/calculate_monthly_ledgers.py
```

### 3. view_monthly_ledger.py
查看客户的月度财务账本，包括客户账本和INFINITE账本。

**使用方法：**
```bash
# 列出所有客户
python scripts/view_monthly_ledger.py

# 查看特定客户（例如ID=5的Chang Choon Chow）
python scripts/view_monthly_ledger.py 5
```

## 注意事项

- 这些脚本直接操作数据库，请谨慎使用
- 建议在使用前备份数据库
- 所有脚本使用新的DR/CR分类逻辑和双轨财务系统
