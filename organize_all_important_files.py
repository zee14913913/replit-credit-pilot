#!/usr/bin/env python3
"""
整理所有重要文件 - 执行方案1+2+3
"""
import os
import shutil
import json
import sqlite3
from datetime import datetime

def create_directories():
    """创建目录结构"""
    dirs = [
        'lee_e_kai_data/database_backup',
        'lee_e_kai_data/statements',
        'lee_e_kai_data/reports',
        'parser_system/extractors',
        'parser_system/parsers',
        'parser_system/config',
        'parser_system/docs',
        'parser_system/services',
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✅ 创建目录: {d}")

def backup_lee_data():
    """方案1: 备份LEE E KAI数据"""
    print("\n" + "=" * 120)
    print("方案1: 备份LEE E KAI数据")
    print("=" * 120)
    
    # 备份数据库
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_backup = f'lee_e_kai_data/database_backup/smart_loan_manager_backup_{timestamp}.db'
    shutil.copy2('db/smart_loan_manager.db', db_backup)
    print(f"✅ 数据库备份: {db_backup}")
    
    # 导出客户数据摘要
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    summary = {
        'backup_date': timestamp,
        'customer': {},
        'credit_cards': [],
        'statements': []
    }
    
    # 客户信息
    cursor.execute("SELECT id, name, customer_code, email FROM customers WHERE id = 18")
    cust = cursor.fetchone()
    if cust:
        summary['customer'] = {
            'id': cust[0],
            'name': cust[1],
            'customer_code': cust[2],
            'email': cust[3]
        }
    
    # 信用卡信息
    cursor.execute("SELECT id, bank_name, card_number_last4 FROM credit_cards WHERE customer_id = 18")
    for card in cursor.fetchall():
        summary['credit_cards'].append({
            'id': card[0],
            'bank': card[1],
            'last4': card[2]
        })
    
    # 对账单信息
    cursor.execute("""
        SELECT s.id, s.statement_date, cc.bank_name, s.file_path
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        WHERE cc.customer_id = 18
    """)
    for stmt in cursor.fetchall():
        summary['statements'].append({
            'id': stmt[0],
            'date': stmt[1],
            'bank': stmt[2],
            'file': stmt[3]
        })
    
    conn.close()
    
    # 保存摘要
    summary_file = f'lee_e_kai_data/customer_data_summary_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✅ 数据摘要: {summary_file}")
    
    # 创建README
    readme = f"""# LEE E KAI 客户数据存档

## 备份时间
{timestamp}

## 客户信息
- 姓名: {summary['customer']['name']}
- 客户编号: {summary['customer']['customer_code']}
- 邮箱: {summary['customer']['email']}

## 信用卡
- 共{len(summary['credit_cards'])}张信用卡

## 对账单
- 共{len(summary['statements'])}条对账单记录

## 目录结构
```
lee_e_kai_data/
├── database_backup/    数据库备份文件
├── statements/         PDF对账单文件
├── reports/           客户报告
└── customer_data_summary_*.json  数据摘要
```
"""
    
    with open('lee_e_kai_data/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"✅ README文档: lee_e_kai_data/README.md")

def organize_parser_system():
    """方案2: 整合Parser系统"""
    print("\n" + "=" * 120)
    print("方案2: 整合Parser系统")
    print("=" * 120)
    
    # 复制提取器
    if os.path.exists('pdf_field_extractor.py'):
        shutil.copy2('pdf_field_extractor.py', 'parser_system/extractors/pdf_field_extractor.py')
        print("✅ 复制: pdf_field_extractor.py -> parser_system/extractors/")
    
    # 复制parsers目录
    if os.path.exists('parsers'):
        for file in os.listdir('parsers'):
            src = os.path.join('parsers', file)
            dst = os.path.join('parser_system/parsers', file)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"✅ 复制: {src} -> {dst}")
    
    # 复制services中的parser文件
    if os.path.exists('services'):
        parser_services = [
            'bank_specific_parser.py',
            'bank_specific_parsers.py',
            'fallback_parser.py',
            'intelligent_parser.py',
            'ai_pdf_parser.py',
            'docparser_service.py'
        ]
        for file in parser_services:
            src = os.path.join('services', file)
            if os.path.exists(src):
                dst = os.path.join('parser_system/services', file)
                shutil.copy2(src, dst)
                print(f"✅ 复制: {src} -> {dst}")
    
    # 复制配置文件
    config_files = [
        'bank_parser_templates.json',
        'bank_parser_templates_13banks_16fields.json',
        'parser_field_keywords.json',
        'pdf_parser_config.py'
    ]
    for file in config_files:
        src = os.path.join('config', file)
        if os.path.exists(src):
            dst = os.path.join('parser_system/config', file)
            shutil.copy2(src, dst)
            print(f"✅ 复制: {src} -> {dst}")
    
    # 复制文档
    if os.path.exists('docparser_templates'):
        for file in os.listdir('docparser_templates'):
            src = os.path.join('docparser_templates', file)
            if os.path.isfile(src) and file.endswith('.md'):
                dst = os.path.join('parser_system/docs', file)
                shutil.copy2(src, dst)
                print(f"✅ 复制文档: {src} -> {dst}")
    
    # 创建Parser系统README
    readme = """# Parser System 完整备份

## 目录结构

```
parser_system/
├── extractors/          PDF字段提取器
│   └── pdf_field_extractor.py (40KB)
├── parsers/             银行特定Parser
│   ├── hsbc_parser.py
│   └── hsbc_ocr_parser.py
├── services/            Parser服务层
│   ├── bank_specific_parser.py
│   ├── bank_specific_parsers.py
│   ├── fallback_parser.py
│   ├── intelligent_parser.py
│   ├── ai_pdf_parser.py
│   └── docparser_service.py
├── config/              配置文件
│   ├── bank_parser_templates.json (34KB)
│   ├── bank_parser_templates_13banks_16fields.json
│   ├── parser_field_keywords.json
│   └── pdf_parser_config.py
└── docs/                Parser文档
    ├── PARSER_FIELD_RULES.md
    ├── CREATE_PARSERS_GUIDE.md
    └── QUICK_SETUP_5MIN.md
```

## 功能说明

### 提取器 (extractors/)
- **pdf_field_extractor.py**: 核心PDF字段提取引擎，支持13家马来西亚银行

### Parser (parsers/)
- 银行特定的解析器，处理各银行PDF格式差异

### 服务层 (services/)
- 提供统一的parser接口和智能解析策略

### 配置 (config/)
- 银行模板配置和解析规则

### 文档 (docs/)
- Parser系统使用指南和字段规则
"""
    
    with open('parser_system/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"✅ README文档: parser_system/README.md")

def clean_i18n_examples():
    """方案3: 清理i18n示例数据"""
    print("\n" + "=" * 120)
    print("方案3: 清理i18n示例客户数据")
    print("=" * 120)
    
    customer_keywords = [
        'cheok_jun_yoon', 'chang_choon_chow', 'teo_yok_chu', 
        'yeo_chee_wang', 'tan_zee_liang', 'galaxy'
    ]
    
    for lang_file in ['static/i18n/zh.json', 'static/i18n/en.json']:
        if not os.path.exists(lang_file):
            continue
        
        # 备份原文件
        backup = lang_file + '.backup'
        shutil.copy2(lang_file, backup)
        
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 删除包含客户名称的key
        keys_to_delete = []
        for key in data.keys():
            if any(keyword in key.lower() for keyword in customer_keywords):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del data[key]
        
        # 保存清理后的文件
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {lang_file}: 删除{len(keys_to_delete)}个示例客户key，备份到{backup}")

def main():
    print("=" * 120)
    print("整理所有重要文件 - 执行方案1+2+3")
    print("=" * 120)
    
    # 创建目录结构
    create_directories()
    
    # 执行三个方案
    backup_lee_data()
    organize_parser_system()
    clean_i18n_examples()
    
    print("\n" + "=" * 120)
    print("整理完成！")
    print("=" * 120)
    print("\n创建的目录:")
    print("  📁 lee_e_kai_data/        - LEE E KAI客户数据备份")
    print("  📁 parser_system/         - Parser系统完整备份")
    print("\n清理完成:")
    print("  ✅ static/i18n/zh.json    - 已删除示例客户数据")
    print("  ✅ static/i18n/en.json    - 已删除示例客户数据")
    print("=" * 120)

if __name__ == '__main__':
    main()
