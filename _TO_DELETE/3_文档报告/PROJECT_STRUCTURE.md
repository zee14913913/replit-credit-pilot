# 项目完整文件和目录结构

## 一、主要目录结构

### 核心应用目录
- **accounting_app/** - 主要会计应用模块
  - db/ - 数据库相关
  - middleware/ - 中间件
  - migrations/ - 数据库迁移文件
  - parsers/ - 解析器
  - routes/ - 路由
  - schemas/ - 数据模式
  - services/ - 服务层
  - static/ - 静态资源
  - templates/ - 模板文件
  - tests/ - 测试文件
  - tasks/ - 任务
  - utils/ - 工具函数

### 功能模块目录
- **admin/** - 管理员功能
- **advisory/** - 咨询服务
- **analytics/** - 分析功能
- **api/** - API接口
- **auth/** - 认证授权
- **batch/** - 批处理
- **email_service/** - 邮件服务
- **export/** - 导出功能
- **ingest/** - 数据导入
- **loan/** - 贷款相关
- **report/** - 报表生成
- **search/** - 搜索功能
- **services/** - 服务层
- **validate/** - 验证功能

### 数据存储目录
- **accounting_data/** - 会计数据
  - companies/ - 公司数据
  - reports/ - 报表
  - statements/ - 对账单
  
- **accounting_files/** - 会计文件
- **credit_card_files/** - 信用卡文件（按客户分类）
  - AI SMART TECH SDN. BHD.
  - CHANG CHOON CHOW
  - CHEOK JUN YOON
  - INFINITE GZ SDN. BHD.
  - Tan Zee Liang
  - TEO YOK CHU
  - YEO CHEE WANG

- **evidence_bundles/** - 证据包
- **logs/** - 日志文件

### 数据库目录
- **db/** - 数据库相关
  - migrations/ - 数据库迁移
    - 011_supplier_fee_split.sql

- **data/banks/** - 银行数据

## 二、templates/ 目录详细内容

### 模板组件
- **components/** - 组件模板
  - card_timeline_12months.html

- **partials/** - 部分模板
  - chatbot.html

### 功能模板目录
- **credit_card/** - 信用卡模板
  - ledger_detail.html
  - ledger_index.html
  - ledger_monthly.html
  - ledger_timeline.html

- **ctos/** - CTOS相关
  - ctos_company.html
  - ctos_personal.html

- **income/** - 收入相关
  - index.html
  - upload.html

- **invoices/** - 发票
  - home.html

- **monthly_summary/** - 月度总结
  - index.html
  - report.html
  - yearly.html

- **receipts/** - 收据
  - customer_receipts.html
  - home.html
  - pending.html
  - upload.html
  - upload_results.html

- **savings/** - 储蓄
  - account_detail.html
  - accounts.html
  - customers.html
  - search.html
  - settlement.html
  - upload.html
  - verify.html

### 主要模板文件（根目录）
- accounting_files.html
- add_credit_card.html
- add_customer.html
- admin_client_detail.html
- admin_customers_cards.html
- admin_dashboard.html
- admin_login.html
- admin_payment_accounts.html
- admin_portfolio.html
- admin_register.html
- advanced_analytics.html
- analytics.html
- api_keys_management.html
- banking_news.html
- base.html
- batch_upload.html
- business_plan.html
- cheok_jun_yoon_report.html
- credit_card_excel_browser.html
- credit_card_month_detail.html
- credit_card_optimizer.html
- credit_card_optimizer_report.html
- customer_dashboard.html
- customer_portal.html
- customer_register.html
- customer_resources.html
- customers_list.html
- edit_customer.html
- evidence_archive.html
- file_detail.html
- files_list.html
- financial_advisory.html
- financial_dashboard.html
- index.html
- layout.html
- loan_evaluate.html
- loan_matcher_result.html
- loan_modern_evaluate.html
- loan_products.html
- loan_products_dashboard.html
- loan_reports.html
- monthly_reports.html
- monthly_statement_detail.html
- notification_settings.html
- notifications_history.html
- optimization_proposal.html
- reminders.html
- request_consultation.html
- savings_admin_dashboard.html
- savings_report.html
- sme_loan_evaluate.html
- statement_comparison.html
- test_invoice.html
- validate_statement.html
- vba_upload.html

## 三、static/ 目录详细内容

### CSS样式文件
- **css/**
  - galaxy-theme.css
  - loan_evaluate.css
  - loan_marketplace_dashboard.css
  - loan_products_catalog.css
  - loan_result.css
  - matrix.css

### JavaScript文件
- **js/**
  - ai_predict.js
  - bank-support.js
  - evidence-archive.js
  - i18n.js
  - loan_evaluate.js
  - loan_products_catalog.js
  - loan_result_renderer.js
  - next-actions.js
  - status-badge.js
  - toast.js
  - unified-ui-enhancements.js

### 国际化文件
- **i18n/**
  - en.json
  - zh.json

### 静态资源目录
- **downloads/** - 下载文件
- **exports/** - 导出文件
- **invoices/** - 发票（包含多个PDF文件）
- **templates/** - 模板文件
  - bank_statement_template.csv

### 上传文件目录
- **uploads/** - 上传文件（按客户组织）
  - Chang_Choon_Chow/
    - credit_cards/ - 信用卡（按银行和月份）
      - Alliance_Bank/
      - Hong_Leong_Bank/
  - Be_rich_CCC/
    - bank_statements/
    - credit_cards/ - 信用卡（多家银行）
      - Alliance Bank/
      - Alliance_Bank/
      - Hong Leong Bank/
      - Hong_Leong_Bank/
      - HSBC/
      - Maybank/
      - UOB/
    - invoices/
      - supplier/ - 供应商发票（按月份）
    - savings/
      - Public_Bank/
    - vba_json_files/ - VBA JSON文件
  - customers/
    - AISMART20251030225947/
      - savings/
        - Public_Bank/
    - Be_rich_CCC/ (如上)

### 报表目录
- **reports/monthly/** - 月度报表
  - Galaxy_Report_CHEOK JUN YOON_2025_09.pdf

### 其他静态文件
- LOAN_PRODUCTS_完整产品目录.xlsx
- LOAN_PRODUCTS_对比排名表.xlsx
- logo.png
- sample_invoice.pdf
- vba_templates.tar.gz

## 四、migrations/ 目录详细内容

### 根目录 migrations/
- **archived/** - 归档的迁移
  - migrate_to_monthly_statements.py
  - README.md
- create_monthly_statements.py
- fix_owner_gz_balances.py

### accounting_app/migrations/
- 001_add_new_tables_and_fields.py
- 001_add_raw_document_protection.sql
- 002_extend_file_index.sql
- 003_create_audit_logs.sql
- 004_create_users_rbac.sql
- 005_user_company_roles.sql
- 006_export_level_permissions.sql
- 007_create_api_keys.sql
- 008_add_validation_fields.sql
- 009_fix_status_constraint.sql
- 010_extend_file_status.sql
- create_notification_tables.py

### db/migrations/
- 011_supplier_fee_split.sql

## 五、其他重要目录

### 工具和脚本
- **scripts/** - 脚本文件
  - archived/ - 归档脚本
- **batch_scripts/** - 批处理脚本
- **tools/** - 工具
  - pdf_converter/ - PDF转换器

### 模块和解析器
- **modules/** - 模块
  - parsers/ - 解析器
  - recommendations/ - 推荐系统
- **parsers/** - 解析器

### 测试和文档
- **tests/** - 测试
  - unit/ - 单元测试
- **docs/** - 文档
  - archived/ - 归档文档
  - business/ - 业务文档
  - core/ - 核心文档
  - deployment/ - 部署文档
  - features/ - 功能文档

### 测试数据
- **test_csvs/** - CSV测试文件
- **test_pdfs/** - PDF测试文件
- **vba_templates/** - VBA模板

### 国际化和配置
- **i18n/** - 国际化
- **lang/** - 语言文件
- **config/** - 配置文件
- **.config/** - 系统配置

### 附件资源
- **attached_assets/** - 附件资源（包含大量PDF、图片等文件）
- **archive_old/** - 旧归档
  - attached_assets/

### 报表和导出
- **reports/** - 报表
  - CCC_Detailed_Reports/
  - monthly/
- **export/** - 导出

### 验证和搜索
- **verification/** - 验证
- **search/** - 搜索

## 六、配置和系统文件

- .git/ - Git版本控制
- .cache/ - 缓存
- .pythonlibs/ - Python库
- .local/ - 本地配置
- __pycache__/ - Python缓存（多处）

## 总结

这是一个大型的财务/会计管理系统，包含：
1. 信用卡管理
2. 储蓄账户管理
3. 发票和收据管理
4. 贷款评估
5. 财务报表和分析
6. 客户管理
7. RBAC权限系统
8. API接口
9. 多语言支持（中英文）
10. 文档管理和验证

系统支持多家马来西亚银行（Alliance Bank, Hong Leong Bank, HSBC, Maybank, UOB, Public Bank等）的数据处理。
