#!/usr/bin/env python3
"""
整理API、集成、配置等重要文件到统一位置
"""
import os
import shutil

def create_system_backup_structure():
    """创建系统备份目录结构"""
    dirs = [
        'system_backup/api_docs',
        'system_backup/api_tests',
        'system_backup/config',
        'system_backup/services',
        'system_backup/integrations',
        'system_backup/accounting_api',
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✅ 创建目录: {d}")

def backup_api_files():
    """备份API相关文件"""
    print("\n" + "=" * 120)
    print("备份API文件")
    print("=" * 120)
    
    # API文档
    api_docs = [
        'API_ENDPOINTS_SUMMARY.md',
    ]
    
    for file in api_docs:
        if os.path.exists(file):
            shutil.copy2(file, f'system_backup/api_docs/{file}')
            print(f"✅ 复制API文档: {file}")
    
    # API测试文件
    test_files = [
        'tests/Card_Optimizer_API_Tests.postman_collection.json',
        'tests/README_API_TESTING.md',
        'tests/test_data_seed.json',
    ]
    
    for file in test_files:
        if os.path.exists(file):
            basename = os.path.basename(file)
            shutil.copy2(file, f'system_backup/api_tests/{basename}')
            print(f"✅ 复制API测试: {file}")

def backup_config_files():
    """备份配置文件"""
    print("\n" + "=" * 120)
    print("备份配置文件")
    print("=" * 120)
    
    # 所有config目录中的重要文件
    config_files = [
        'app_settings.json',
        'bank_templates.json',
        'business_rules.json',
        'colors.json',
        'colors.py',
        'database.json',
        'document_ai_schema.json',
        'settings.json',
        'settings_loader.py',
        'README.md',
        # Parser配置已在parser_system中备份，这里再备份一份
        'bank_parser_templates.json',
        'parser_field_keywords.json',
        'pdf_parser_config.py',
    ]
    
    for file in config_files:
        src = f'config/{file}'
        if os.path.exists(src):
            shutil.copy2(src, f'system_backup/config/{file}')
            print(f"✅ 复制配置: {file}")

def backup_service_files():
    """备份services目录所有文件"""
    print("\n" + "=" * 120)
    print("备份Services文件")
    print("=" * 120)
    
    if os.path.exists('services'):
        count = 0
        for file in os.listdir('services'):
            if file.endswith('.py'):
                src = f'services/{file}'
                dst = f'system_backup/services/{file}'
                shutil.copy2(src, dst)
                count += 1
        print(f"✅ 复制{count}个service文件")

def backup_integration_files():
    """备份集成相关文件"""
    print("\n" + "=" * 120)
    print("备份集成文件")
    print("=" * 120)
    
    # 集成测试文件
    integration_files = [
        'test_docparser_integration.py',
        'tests/test_fee_splitting_integration.py',
    ]
    
    for file in integration_files:
        if os.path.exists(file):
            basename = os.path.basename(file)
            shutil.copy2(file, f'system_backup/integrations/{basename}')
            print(f"✅ 复制集成测试: {file}")

def backup_accounting_api():
    """备份Accounting API关键文件"""
    print("\n" + "=" * 120)
    print("备份Accounting API")
    print("=" * 120)
    
    # 复制关键文件
    if os.path.exists('accounting_app'):
        key_files = [
            'accounting_app/main.py',
            'accounting_app/config_versioning.py',
        ]
        
        for file in key_files:
            if os.path.exists(file):
                basename = os.path.basename(file)
                shutil.copy2(file, f'system_backup/accounting_api/{basename}')
                print(f"✅ 复制: {file}")

def create_readme():
    """创建系统备份README"""
    readme = """# 系统备份 - API、配置、集成文件

## 目录结构

```
system_backup/
├── api_docs/           API文档
│   └── API_ENDPOINTS_SUMMARY.md
├── api_tests/          API测试文件
│   ├── Card_Optimizer_API_Tests.postman_collection.json
│   ├── README_API_TESTING.md
│   └── test_data_seed.json
├── config/             所有配置文件
│   ├── app_settings.json
│   ├── bank_templates.json
│   ├── business_rules.json
│   ├── colors.json
│   ├── colors.py
│   ├── database.json
│   ├── settings.json
│   └── settings_loader.py
├── services/           所有服务文件 (45+个)
│   ├── auto_classifier_service.py
│   ├── docparser_service.py
│   ├── google_document_ai_service.py
│   └── ... (所有service文件)
├── integrations/       集成相关文件
│   ├── test_docparser_integration.py
│   └── test_fee_splitting_integration.py
└── accounting_api/     Accounting API核心文件
    ├── main.py
    └── config_versioning.py
```

## 文件说明

### API文档 (api_docs/)
- **API_ENDPOINTS_SUMMARY.md**: API端点完整文档

### API测试 (api_tests/)
- **Postman Collection**: API测试集合
- **README_API_TESTING.md**: API测试指南
- **test_data_seed.json**: 测试数据

### 配置文件 (config/)
- **app_settings.json**: 应用设置
- **business_rules.json**: 业务规则配置
- **colors.json/colors.py**: 颜色系统配置
- **database.json**: 数据库配置
- **settings.json**: 全局设置

### Services (services/)
- 所有业务逻辑服务层文件（45+个）
- 包括分类器、解析器、AI服务等

### 集成 (integrations/)
- DocParser集成
- 费用拆分集成测试

### Accounting API (accounting_api/)
- FastAPI主程序
- 配置版本管理

## 备份时间
由 organize_api_integration_files.py 自动生成
"""
    
    with open('system_backup/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"✅ 创建README: system_backup/README.md")

def main():
    print("=" * 120)
    print("整理API、集成、配置文件到统一位置")
    print("=" * 120)
    
    create_system_backup_structure()
    backup_api_files()
    backup_config_files()
    backup_service_files()
    backup_integration_files()
    backup_accounting_api()
    create_readme()
    
    print("\n" + "=" * 120)
    print("整理完成！")
    print("=" * 120)
    print("\n创建的备份目录:")
    print("  📁 system_backup/")
    print("     ├── api_docs/         - API文档")
    print("     ├── api_tests/        - API测试文件")
    print("     ├── config/           - 所有配置文件")
    print("     ├── services/         - 所有服务文件 (45+个)")
    print("     ├── integrations/     - 集成文件")
    print("     └── accounting_api/   - Accounting API")
    print("\n✅ 所有重要文件已安全备份！")
    print("=" * 120)

if __name__ == '__main__':
    main()
