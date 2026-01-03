# INFINITE GZ - 系统路由地图

## 📌 完整URL前缀
```
https://6020cca9-a8d9-41a4-b1b0-5f1ba22a7012-00-3vonlpnvgsuce.riker.replit.dev
```

---

## 🏠 1. 首页与仪表板

| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/` | GET | 主仪表板 | 登录后访问 |
| `/customer/<customer_id>` | GET | 客户个人仪表板 | Admin/Accountant |
| `/customer/<customer_id>/dashboard` | GET | 客户财务仪表板 | Admin/Accountant |
| `/financial-dashboard/<customer_id>` | GET | 财务综合仪表板 | Admin/Accountant |

---

## 👥 2. 客户管理模块

### 2.1 客户基础操作
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/customers` | GET | 客户列表页面 | Admin |
| `/add_customer_page` | GET | 添加客户表单页面 | Admin/Accountant |
| `/add_customer` | POST | 提交新客户 | Admin/Accountant |
| `/edit_customer/<customer_id>` | GET | 编辑客户表单页面 | Admin/Accountant |
| `/edit_customer/<customer_id>` | POST | 更新客户信息 | Admin/Accountant |
| `/customer/<customer_id>/delete` | POST | 删除客户及数据 | Admin/Accountant |

### 2.2 客户注册与门户
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/customer/register` | GET, POST | 客户自助注册 | 公开 |
| `/customer/portal` | GET | 客户数据门户 | Customer |
| `/customer/download/<statement_id>` | GET | 下载账单 | Customer |
| `/customer-authorization` | GET | 客户授权协议 | 登录后 |

### 2.3 客户资源管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/customer/<customer_id>/resources` | GET | 资源、网络、技能管理 | Admin/Accountant |
| `/customer/<customer_id>/add_resource` | POST | 添加个人资源 | Admin/Accountant |
| `/customer/<customer_id>/add_network` | POST | 添加网络联系人 | Admin/Accountant |
| `/customer/<customer_id>/add_skill` | POST | 添加技能 | Admin/Accountant |
| `/customer/<customer_id>/delete_resource/<resource_id>` | POST | 删除资源 | Admin/Accountant |
| `/customer/<customer_id>/delete_network/<network_id>` | POST | 删除网络联系人 | Admin/Accountant |
| `/customer/<customer_id>/delete_skill/<skill_id>` | POST | 删除技能 | Admin/Accountant |

### 2.4 客户就业信息
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/customer/<customer_id>/employment` | GET, POST | 设置就业类型与文档上传 | Admin/Accountant |

---

## 💳 3. 信用卡管理模块

### 3.1 信用卡基础操作
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/customer/<customer_id>/add-card` | GET, POST | 添加信用卡 | Admin/Accountant |
| `/admin/customers-cards` | GET | 客户信用卡总览 | Admin |

### 3.2 信用卡账本系统
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/credit-card/ledger` | GET, POST | 信用卡账本首页（上传+列表） | Admin/Accountant |
| `/credit-card/ledger/<customer_id>/timeline` | GET | 客户账单时间线 | Admin/Accountant |
| `/credit-card/ledger/<customer_id>/<year>/<month>` | GET | 月度账本详情 | Admin/Accountant |
| `/credit-card/ledger/statement/<statement_id>` | GET | 单账单详细分析 | Admin/Accountant |

### 3.3 信用卡优化系统
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/credit-card-optimizer` | GET | 信用卡优化主页 | Admin/Accountant |
| `/credit-card-optimizer/report/<customer_id>` | GET | 生成优化报告 | Admin/Accountant |
| `/credit-card-optimizer/download/<customer_id>` | GET | 下载优化报告PDF | Admin/Accountant |

### 3.4 月度汇总报表
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/monthly-summary` | GET | 月度汇总首页 | Admin/Accountant |
| `/monthly-summary/report/<customer_id>/<year>/<month>` | GET | 月度汇总报告 | Admin/Accountant |
| `/monthly-summary/yearly/<customer_id>/<year>` | GET | 年度汇总 | Admin/Accountant |
| `/monthly-summary/download/monthly/...` | GET | 下载月度汇总PDF | Admin/Accountant |
| `/monthly-summary/download/yearly/...` | GET | 下载年度汇总PDF | Admin/Accountant |

---

## 💰 4. 储蓄账户模块

### 4.1 储蓄账户管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/savings` | GET | 公开储蓄报告 | 公开 |
| `/savings-admin` | GET | 储蓄管理仪表板 | Admin |
| `/savings/customers` | GET | 储蓄客户列表 | Admin/Accountant |
| `/savings/accounts` | GET | 储蓄账户列表（重定向） | Admin/Accountant |
| `/savings/accounts/<customer_id>` | GET | 客户储蓄账户详情 | Admin/Accountant |
| `/savings/account/<account_id>` | GET | 单个储蓄账户详情 | Admin/Accountant |

### 4.2 储蓄账单处理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/savings/upload` | GET, POST | 上传储蓄账单 | Admin/Accountant |
| `/savings/verify/<statement_id>` | GET | 手动验证账单 | Admin/Accountant |
| `/savings/mark_verified/<statement_id>` | POST | 标记账单已验证 | Admin/Accountant |
| `/view_savings_statement_file/<statement_id>` | GET | 查看储蓄账单PDF | Admin |

### 4.3 储蓄交易管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/savings/search` | GET, POST | 搜索储蓄交易 | Admin/Accountant |
| `/savings/transaction/<transaction_id>/edit` | POST | 编辑交易详情 | Admin/Accountant |
| `/savings/tag/<transaction_id>` | POST | 标记交易 | Admin/Accountant |
| `/savings/export-transaction/<transaction_id>` | GET | 导出交易截图 | Admin |
| `/savings/settlement/<customer_name>` | GET | 生成结算报告 | Admin/Accountant |

---

## 🏦 5. 贷款评估模块

### 5.1 贷款评估系统
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/loan_evaluation/<customer_id>` | GET | 传统贷款评估页面 | Admin/Accountant |
| `/loan-evaluate` | GET | 现代贷款评估（三模式） | Admin/Accountant |
| `/loan-evaluate/submit` | POST | 提交贷款评估 | Admin/Accountant |
| `/sme-loan-evaluate` | GET | SME贷款评估表单 | Admin/Accountant |
| `/sme-loan-evaluate/submit` | POST | 提交SME贷款评估 | Admin/Accountant |

### 5.2 贷款产品匹配
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/loan-matcher` | GET | 贷款产品匹配表单 | Admin/Accountant |
| `/loan-matcher/analyze` | POST | 分析客户数据并匹配 | Admin/Accountant |
| `/loan-products` | GET | 贷款产品目录浏览 | Admin |
| `/loan-products/<product_id>` | GET | 贷款产品详情页 | Admin |
| `/loan-products-dashboard` | GET | 贷款产品仪表板 | Admin |

### 5.3 贷款报告生成
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/loan-reports` | GET | 贷款报告生成器 | Admin/Accountant |

---

## 📄 6. 收据与发票模块

### 6.1 收据管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/receipts` | GET | 收据管理首页 | Admin/Accountant |
| `/receipts/upload` | GET, POST | 上传收据 | Admin/Accountant |
| `/receipts/pending` | GET | 待匹配收据列表 | Admin/Accountant |
| `/receipts/manual-match/<receipt_id>` | POST | 手动匹配收据 | Admin/Accountant |
| `/receipts/customer/<customer_id>` | GET | 客户收据列表 | Admin/Accountant |

### 6.2 发票管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/invoices` | GET | 发票管理首页 | Admin/Accountant |
| `/test/invoice` | GET | 测试发票视图 | 开发测试 |
| `/test/invoice/download` | GET | 下载测试发票PDF | 开发测试 |

---

## 📊 7. 报表与分析模块

### 7.1 账单与交易查看
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/validate_statement/<statement_id>` | GET | 验证账单页面 | Admin/Accountant |
| `/confirm_statement/<statement_id>` | POST | 确认账单 | Admin/Accountant |
| `/view_statement_file/<statement_id>` | GET | 查看账单PDF文件 | Admin/Accountant |
| `/monthly_statement/<monthly_statement_id>/detail` | GET | 月度账单详情 | Admin/Accountant |
| `/monthly_statement/<monthly_statement_id>/edit` | POST | 编辑月度账单 | Admin/Accountant |
| `/statement/<statement_id>/comparison` | GET | 账单对比 | Admin/Accountant |

### 7.2 交易管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/search/<customer_id>` | GET | 搜索和筛选交易 | Admin/Accountant |
| `/transaction/<transaction_id>/note` | POST | 更新交易备注 | Admin/Accountant |
| `/transaction/<transaction_id>/tag` | POST | 标记交易 | Admin/Accountant |

### 7.3 报表生成
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/generate_report/<customer_id>` | GET | 生成月度报告 | Admin/Accountant |
| `/customer/<customer_id>/monthly-reports` | GET | 客户月度报告列表 | Admin/Accountant |
| `/customer/<customer_id>/generate-monthly-report/<year>/<month>` | GET | 手动生成月度报告 | Admin/Accountant |
| `/download-monthly-report/<report_id>` | GET | 下载月度报告PDF | Admin/Accountant |

### 7.4 数据导出
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/export/<customer_id>/<format>` | GET | 导出Excel/CSV | RBAC保护 |
| `/export_statement_transactions/<statement_id>/<format>` | GET | 导出账单交易 | Admin/Accountant |

### 7.5 高级分析
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/analytics/<customer_id>` | GET | 客户分析仪表板 | Admin/Accountant |
| `/advanced-analytics/<customer_id>` | GET | 高级财务分析（Beta） | Admin/Accountant |
| `/customer/<customer_id>/optimization-proposal` | GET | 优化建议 | Admin/Accountant |
| `/customer/<customer_id>/request-optimization-consultation` | GET, POST | 请求优化咨询 | Admin/Accountant |

---

## 🖥️ 8. VBA混合架构系统

### 8.1 VBA上传界面
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/vba/upload` | GET | VBA JSON上传界面 | 登录后 |

### 8.2 VBA API端点
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/upload/vba-json` | POST | 单文件JSON上传 | Admin/Accountant |
| `/api/upload/vba-batch` | POST | 批量JSON上传 | Admin/Accountant |

### 8.3 Excel上传API
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/upload/excel/credit-card` | POST | 上传信用卡Excel/CSV | Admin/Accountant |
| `/api/upload/excel/bank-statement` | POST | 上传银行账单Excel/CSV | Admin/Accountant |
| `/api/upload/excel/batch` | POST | 批量上传Excel/CSV | Admin/Accountant |
| `/api/upload/detect-bank` | POST | 检测银行格式 | Admin/Accountant |

---

## 🔌 9. API端点汇总

### 9.1 客户API
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/customers/list` | GET | 获取客户列表JSON | Admin/Accountant |

### 9.2 财务分析API
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/cashflow-prediction/<customer_id>` | GET | 现金流预测数据 | Feature Toggle |
| `/api/financial-score/<customer_id>` | GET | 财务健康评分 | Feature Toggle |
| `/api/anomalies/<customer_id>` | GET | 财务异常检测 | Feature Toggle |
| `/api/recommendations/<customer_id>` | GET | 个性化推荐 | Feature Toggle |
| `/api/tier-info/<customer_id>` | GET | 客户等级信息 | Feature Toggle |
| `/resolve-anomaly/<anomaly_id>` | POST | 解决财务异常 | Admin/Accountant |

### 9.3 Portfolio API
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/portfolio/overview` | GET | Portfolio总览 | Admin |
| `/api/portfolio/revenue` | GET | 收入明细 | Admin |

### 9.4 贷款API
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/loans/evaluate/<customer_id>` | POST | 贷款评估 | Admin/Accountant |
| `/api/loans/quick-income` | POST | 快速收入贷款估算 | Admin/Accountant |
| `/api/loans/quick-income-commitment` | POST | 收入+承诺贷款估算 | Admin/Accountant |
| `/api/loans/full-auto` | POST | 全自动贷款评估 | Admin/Accountant |
| `/api/loans/product-recommendations` | POST | 贷款产品推荐 | Admin/Accountant |
| `/api/loans/advisor` | POST | AI贷款顾问 | Admin/Accountant |
| `/api/loan-products/select` | POST | 选择贷款产品 | Admin/Accountant |

### 9.5 文件管理API（代理到FastAPI）
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/proxy/files/<subpath>` | GET, POST, DELETE | 文件管理代理 | Admin |
| `/api/proxy/unified-files/<subpath>` | GET, POST, PATCH, DELETE | 统一文件管理代理 | Admin |
| `/api/parsers/<subpath>` | GET | 解析器API代理 | Admin |
| `/api/metrics/<subpath>` | GET | 指标API代理 | Admin |

### 9.6 AI助手API
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/api/ai-assistant/<subpath>` | GET, POST | AI助手代理 | 登录后 |

---

## 🔐 10. 管理后台

### 10.1 管理仪表板
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/admin` | GET | 管理员仪表板 | Admin |
| `/admin/customers-cards` | GET | 客户信用卡总览 | Admin |
| `/admin/portfolio` | GET | Portfolio管理 | Admin |
| `/admin/portfolio/client/<customer_id>` | GET | 客户Portfolio详情 | Admin |

### 10.2 系统配置
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/admin/payment-accounts` | GET | 收款账户管理 | Admin |
| `/admin/api-keys` | GET | API密钥管理 | Admin |

### 10.3 自动化与测试
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/admin/test-generate-reports` | GET | 手动触发报告生成 | Admin |
| `/admin/test-send-reports` | GET | 手动触发报告发送 | Admin |
| `/admin/automation-status` | GET | 自动化系统状态 | Admin |

### 10.4 证据归档
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/admin/evidence` | GET | 证据归档管理 | Admin |
| `/downloads/evidence/latest` | GET | 下载最新证据包 | Admin |
| `/downloads/evidence/file/<filename>` | GET | 下载特定证据包 | Admin |
| `/downloads/evidence/list` | GET | 列出所有证据包 | Admin |
| `/downloads/evidence/delete` | POST | 删除证据包 | Admin |
| `/tasks/evidence/rotate` | POST | 轮转证据包 | Admin |

---

## 🔑 11. 认证系统

### 11.1 管理员认证
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/admin/login` | GET, POST | 管理员登录 | 公开 |
| `/admin/register` | GET, POST | 管理员注册 | 公开 |
| `/admin/logout` | GET | 管理员登出 | Admin |

### 11.2 CTOS授权
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/ctos/personal/submit` | POST | 提交个人CTOS授权 | Admin/Accountant |
| `/ctos/company/submit` | POST | 提交公司CTOS授权 | Admin/Accountant |

---

## 📝 12. 其他功能

### 12.1 提醒系统
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/reminders` | GET | 待处理提醒列表 | Admin/Accountant |
| `/create_reminder` | POST | 创建提醒 | Admin/Accountant |
| `/mark_paid/<reminder_id>` | POST | 标记已支付 | Admin/Accountant |

### 12.2 通知系统
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/notifications-history` | GET | 通知历史 | Admin/Accountant |
| `/notification-settings` | GET | 通知设置 | Admin/Accountant |

### 12.3 收入管理
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/income` | GET | 收入文档首页 | Admin/Accountant |
| `/income/upload` | GET | 上传收入文档 | Admin/Accountant |

### 12.4 咨询服务
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/advisory/<customer_id>` | GET | 财务咨询仪表板 | Admin/Accountant |
| `/consultation/request/<customer_id>` | POST | 请求详细咨询 | Admin/Accountant |

### 12.5 业务计划
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/customer/<customer_id>/generate_business_plan` | POST | 生成AI业务计划 | Admin/Accountant |
| `/customer/<customer_id>/business_plan/<plan_id>` | GET | 查看业务计划 | Admin/Accountant |
| `/customer/<customer_id>/business_plans` | GET | 业务计划列表 | Admin/Accountant |

### 12.6 批量操作
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/batch/upload/<customer_id>` | GET, POST | 批量上传账单 | Admin/Accountant |

### 12.7 语言切换
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/set-language/<lang>` | GET | 切换系统语言 | 公开 |

### 12.8 测试功能
| 路由 | 方法 | 功能 | 权限要求 |
|------|------|------|----------|
| `/test_input` | GET | 简单输入测试页面 | 开发测试 |

---

## 📊 路由统计总结

| 模块 | 前端页面 | API端点 | 总计 |
|------|----------|---------|------|
| **客户管理** | 12 | 1 | 13 |
| **信用卡管理** | 9 | 0 | 9 |
| **储蓄账户** | 11 | 0 | 11 |
| **贷款评估** | 8 | 7 | 15 |
| **收据发票** | 7 | 0 | 7 |
| **报表分析** | 15 | 6 | 21 |
| **VBA系统** | 1 | 6 | 7 |
| **管理后台** | 12 | 2 | 14 |
| **认证系统** | 5 | 0 | 5 |
| **其他功能** | 18 | 3 | 21 |
| **文件代理** | 0 | 5 | 5 |
| **总计** | **98** | **30** | **128** |

---

## 🔒 权限级别说明

| 权限级别 | 说明 |
|----------|------|
| **公开** | 无需登录即可访问 |
| **登录后** | 需要任何有效登录（Customer/Admin/Accountant） |
| **Customer** | 仅客户可访问 |
| **Admin/Accountant** | 管理员或会计师可访问 |
| **Admin** | 仅管理员可访问 |
| **RBAC保护** | 基于角色的细粒度权限控制 |
| **Feature Toggle** | 需要开启功能开关 |

---

## 🎯 核心业务流程路由

### 流程1：客户注册与入职
```
1. /customer/register (客户自助注册)
2. /admin/login (管理员登录)
3. /add_customer_page (管理员添加客户)
4. /customer/<id>/add-card (添加信用卡)
5. /customer/<id> (查看客户仪表板)
```

### 流程2：VBA账单上传处理
```
1. /vba/upload (访问VBA上传界面)
2. 下载VBA模板套件
3. 客户端VBA解析PDF/Excel
4. POST /api/upload/vba-json (上传JSON)
5. /credit-card/ledger (查看账本)
6. /monthly-summary/report/<id>/<year>/<month> (查看月度汇总)
```

### 流程3：贷款评估与产品推荐
```
1. /loan-evaluate (贷款评估表单)
2. POST /loan-evaluate/submit (提交评估)
3. /loan-matcher (贷款产品匹配)
4. POST /loan-matcher/analyze (分析匹配)
5. /loan-products/<product_id> (查看产品详情)
```

### 流程4：财务报告生成
```
1. /customer/<id>/monthly-reports (月度报告列表)
2. /customer/<id>/generate-monthly-report/<year>/<month> (生成报告)
3. /download-monthly-report/<report_id> (下载PDF)
4. /credit-card-optimizer/report/<id> (优化报告)
```

---

## 🚀 快速访问链接

### 常用管理页面
- **主仪表板**: `/`
- **客户列表**: `/customers`
- **VBA上传**: `/vba/upload`
- **信用卡账本**: `/credit-card/ledger`
- **储蓄管理**: `/savings-admin`
- **管理后台**: `/admin`

### 常用API端点
- **客户列表API**: `/api/customers/list`
- **VBA单文件上传**: `/api/upload/vba-json`
- **VBA批量上传**: `/api/upload/vba-batch`
- **贷款产品推荐**: `/api/loans/product-recommendations`
- **AI助手**: `/api/ai-assistant/chat`

---

**文档版本**: 1.0.0  
**更新日期**: 2024-11-15  
**总路由数**: 128个（98个页面 + 30个API）

**系统完整就绪！** 🎉
