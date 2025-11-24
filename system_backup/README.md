# 系统备份 - API、配置、集成文件

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
