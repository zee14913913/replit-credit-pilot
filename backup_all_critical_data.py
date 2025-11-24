#!/usr/bin/env python3
"""
备份所有关键数据：贷款产品、信用卡产品、功能设置
"""
import os
import shutil
import json
import sqlite3
from datetime import datetime

def create_product_backup():
    """备份产品数据到专门目录"""
    print("=" * 120)
    print("备份产品数据库")
    print("=" * 120)
    
    # 创建目录
    os.makedirs('product_data_backup', exist_ok=True)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 导出loan_products
    cursor.execute("SELECT * FROM loan_products")
    columns = [desc[0] for desc in cursor.description]
    loan_products = []
    for row in cursor.fetchall():
        loan_products.append(dict(zip(columns, row)))
    
    loan_file = f'product_data_backup/loan_products_{timestamp}.json'
    with open(loan_file, 'w', encoding='utf-8') as f:
        json.dump(loan_products, f, indent=2, ensure_ascii=False)
    print(f"✅ 导出贷款产品: {len(loan_products)}个 -> {loan_file}")
    
    # 导出credit_card_products
    cursor.execute("SELECT * FROM credit_card_products")
    columns = [desc[0] for desc in cursor.description]
    card_products = []
    for row in cursor.fetchall():
        card_products.append(dict(zip(columns, row)))
    
    card_file = f'product_data_backup/credit_card_products_{timestamp}.json'
    with open(card_file, 'w', encoding='utf-8') as f:
        json.dump(card_products, f, indent=2, ensure_ascii=False)
    print(f"✅ 导出信用卡产品: {len(card_products)}个 -> {card_file}")
    
    conn.close()
    
    # 创建产品数据README
    readme = f"""# 产品数据备份

## 备份时间
{timestamp}

## 数据统计
- **贷款产品**: {len(loan_products)}个
- **信用卡产品**: {len(card_products)}个

## 文件说明
- `loan_products_{timestamp}.json`: 所有贷款产品数据（800-900个）
- `credit_card_products_{timestamp}.json`: 所有信用卡产品数据

## 恢复方法
使用这些JSON文件可以完整恢复所有产品数据到数据库

## 重要性
⚠️ **这些产品数据是系统核心资产，切勿删除！**
"""
    
    with open('product_data_backup/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"✅ 创建README: product_data_backup/README.md")

def backup_feature_docs():
    """备份功能设置文档"""
    print("\n" + "=" * 120)
    print("备份功能设置文档")
    print("=" * 120)
    
    # 创建目录
    os.makedirs('feature_settings_backup/docs', exist_ok=True)
    os.makedirs('feature_settings_backup/config', exist_ok=True)
    
    # 功能文档
    feature_docs = [
        'docs/features/8项月度计算已添加到界面.md',
        'docs/features/BANK_PRODUCTS_STATUS_REPORT.md',
        'docs/features/CREDIT_CARD_CLASSIFICATION_RULES.md',
        'docs/features/CREDIT_CARD_OPTIMIZATION_SYSTEM_DESIGN.md',
        'docs/features/RECEIPT_SYSTEM.md',
        'docs/features/高级功能实施报告.md',
        'docs/core/系统功能完整清单.md',
        'docs/core/账单双重验证系统详解.md',
        'docs/core/SYSTEM_ARCHITECTURE.md',
        'docs/core/QUICK_START.md',
        '文件查看功能使用指南.md',
        '智能上传功能说明.md',
    ]
    
    count = 0
    for doc in feature_docs:
        if os.path.exists(doc):
            basename = os.path.basename(doc)
            shutil.copy2(doc, f'feature_settings_backup/docs/{basename}')
            count += 1
    print(f"✅ 复制{count}个功能文档")
    
    # 配置文件
    config_files = [
        'config/app_settings.json',
        'config/business_rules.json',
        'config/settings.json',
    ]
    
    for cfg in config_files:
        if os.path.exists(cfg):
            basename = os.path.basename(cfg)
            shutil.copy2(cfg, f'feature_settings_backup/config/{basename}')
    print(f"✅ 复制配置文件")
    
    # 创建README
    readme = """# 功能设置完整备份

## 包含内容

### 功能文档
- 8项月度计算功能
- 银行产品状态报告
- 信用卡分类规则
- 信用卡优化系统设计
- 收据系统
- 高级功能实施报告
- 系统功能完整清单
- 账单双重验证系统
- 文件查看功能
- 智能上传功能

### 配置文件
- app_settings.json: 应用设置
- business_rules.json: 业务规则
- settings.json: 全局设置

## 目录结构
```
feature_settings_backup/
├── docs/       功能文档
└── config/     配置文件
```
"""
    
    with open('feature_settings_backup/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"✅ 创建README: feature_settings_backup/README.md")

def main():
    print("=" * 120)
    print("备份所有关键数据")
    print("=" * 120)
    
    create_product_backup()
    backup_feature_docs()
    
    print("\n" + "=" * 120)
    print("备份完成！")
    print("=" * 120)
    print("\n创建的备份:")
    print("  📁 product_data_backup/")
    print("     ├── loan_products_*.json           (800-900个贷款产品)")
    print("     ├── credit_card_products_*.json    (信用卡产品)")
    print("     └── README.md")
    print("\n  📁 feature_settings_backup/")
    print("     ├── docs/                          (功能文档)")
    print("     ├── config/                        (配置文件)")
    print("     └── README.md")
    print("\n✅ 所有关键数据已安全备份！")
    print("=" * 120)

if __name__ == '__main__':
    main()
