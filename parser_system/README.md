# Parser System 完整备份

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
