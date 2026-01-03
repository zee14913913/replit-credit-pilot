# 🧪 INFINITE GZ SDN BHD - 自动化测试框架 v3.0

## 📋 概述

企业级自动化测试框架，包含完整的路由测试、性能分析、风险评估功能。

## 🎯 核心功能

### 1️⃣ 路由测试覆盖
- **30个 GET 路由**：包括客户端、管理端、系统功能
- **10个 POST 路由**：表单提交、数据操作、管理操作
- **Session管理**：自动登录并保持会话状态

### 2️⃣ 性能分析
- ⏱️ 平均响应时间计算
- 🐢 最慢5个接口识别
- 📊 按HTTP方法分组统计

### 3️⃣ 风险评估
- 🚨 失败接口检测
- ❌ 错误路由识别
- 📈 成功率统计

## 📁 文件结构

```
├── test_all_routes_v3.py        # 主测试脚本
├── analyze_test_results.py      # 高级分析脚本
├── dummy_data.json              # 测试数据模板
├── .env.example                 # 环境变量示例
└── logs/                        # 测试报告目录
    ├── summary_YYYYMMDD_HHMMSS.txt
    └── detailed_YYYYMMDD_HHMMSS.txt
```

## 🚀 使用方法

### 步骤 1：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
BASE_URL=http://localhost:5000
TEST_EMAIL=testuser@example.com
TEST_PASSWORD=123456
```

### 步骤 2：运行测试

```bash
python3 test_all_routes_v3.py
```

**自动执行流程：**
1. 客户登录验证
2. 测试所有 GET 路由
3. 测试所有 POST 路由
4. 生成双报告（摘要+详细）
5. **自动运行高级分析**

### 步骤 3：查看报告

测试完成后查看 `logs/` 文件夹：

#### 摘要报告 (`summary_*.txt`)
```
========================================
INFINITE GZ SDN BHD - System Test Summary
========================================
Generated at: 2025-10-09 16:05:32
Base URL: http://localhost:5000

Total Tests: 40
✅ PASS: 35 (87.5%)
⚠️ FAIL: 3 (7.5%)
❌ ERROR: 2 (5.0%)
========================================
```

#### 详细报告 (`detailed_*.txt`)
```
[16:05:32] [PASS]     GET   /customer/login                                200   0.15s
[16:05:33] [PASS]     POST  /upload_statement                              200   0.32s
[16:05:34] [FAIL]     GET   /admin                                         403   0.12s
...
```

## 📊 高级分析输出

自动分析包含：

### 1. 整体性能摘要
```
📊 测试结果摘要：
   总测试数：40
   ✅ 通过：35 (87.5%)
   ⚠️ 失败：3 (7.5%)
   ❌ 错误：2 (5.0%)
   📉 总失败率：12.5%
```

### 2. 最慢接口排名
```
⏱️ 性能指标：
   平均响应时间：0.18s

🐢 最慢的 5 个接口：
   1. ✅ POST  /upload_statement                           0.32s
   2. ✅ GET   /generate_report/1                          0.28s
   3. ✅ POST  /batch/upload/1                             0.25s
   4. ✅ GET   /analytics/1                                0.22s
   5. ✅ GET   /banking_news                               0.19s
```

### 3. 高风险接口列表
```
🚨 高风险接口列表 (3 个)：
   ⚠️ GET   /admin                                         (FAIL)
   ❌ POST  /create_reminder                               (ERROR)
   ⚠️ POST  /budget/delete/1/1                             (FAIL)
```

### 4. HTTP方法统计
```
📈 按请求方法统计：
   GET   → ✅ 28 / ⚠️ 2 / ❌ 0
   POST  → ✅ 7 / ⚠️ 1 / ❌ 2
```

## 🛠️ 独立运行分析脚本

如果只想分析现有日志：

```bash
python3 analyze_test_results.py
```

## 📝 测试路由清单

### 客户端功能 (13个)
- `/customer/login`
- `/customer/register`
- `/customer/logout`
- `/customer-authorization`
- `/customer/<customer_id>`
- `/customer/<customer_id>/employment`
- `/customer/download/<statement_id>`
- `/customer/portal`
- `/upload_statement`
- `/validate_statement/<statement_id>`
- `/confirm_statement/<statement_id>`
- `/batch/upload/<customer_id>`
- `/search/<customer_id>`

### 数据分析与报告 (3个)
- `/analytics/<customer_id>`
- `/generate_report/<customer_id>`
- `/export/<customer_id>/<format>`

### 财务功能 (5个)
- `/loan_evaluation/<customer_id>`
- `/budget/<customer_id>`
- `/budget/delete/<budget_id>/<customer_id>`
- `/advisory/<customer_id>`
- `/consultation/request/<customer_id>`

### 交易管理 (2个)
- `/transaction/<transaction_id>/note`
- `/transaction/<transaction_id>/tag`

### 提醒系统 (3个)
- `/reminders`
- `/create_reminder`
- `/mark_paid/<reminder_id>`

### 新闻系统 (3个)
- `/banking_news`
- `/add_news`
- `/refresh_bnm_rates`

### 管理端功能 (6个)
- `/admin-login`
- `/admin`
- `/admin-logout`
- `/admin/news`
- `/admin/news/approve/<news_id>`
- `/admin/news/reject/<news_id>`
- `/admin/news/fetch`

### 系统功能 (2个)
- `/set-language/<lang>`
- `/` (首页)

## ⚙️ 自定义配置

### 修改测试参数

编辑 `test_all_routes_v3.py`：

```python
# 动态测试参数
CUSTOMER_ID = "1"
STATEMENT_ID = "1"
TRANSACTION_ID = "1"
BUDGET_ID = "1"
REMINDER_ID = "1"
NEWS_ID = "1"
```

### 修改测试数据

编辑 `dummy_data.json`：

```json
{
  "reminder": {
    "title": "自定义标题",
    "amount": 1500,
    "due_date": "2025-12-31"
  }
}
```

## 🔍 故障排查

### 登录失败
```
❌ 登录失败，测试终止。
```
**解决方案：**
1. 检查 `.env` 中的 `TEST_EMAIL` 和 `TEST_PASSWORD`
2. 确认测试账号已在系统中注册
3. 验证 `BASE_URL` 是否正确

### 路由测试失败
```
⚠️ FAIL GET /admin 403
```
**解决方案：**
1. 检查是否需要管理员权限
2. 验证 Session 是否正确维持
3. 查看详细日志获取错误信息

### 分析脚本无法运行
```
⚠️ 无法运行高级分析
```
**解决方案：**
1. 确认 `pandas` 已安装：`pip install pandas`
2. 检查 `logs/` 目录是否存在
3. 手动运行：`python3 analyze_test_results.py`

## 📦 依赖要求

```
python-dotenv
requests
pandas
```

安装依赖：
```bash
pip install python-dotenv requests pandas
```

## 🎯 最佳实践

1. **每次部署前运行测试**，确保所有路由正常
2. **定期检查性能报告**，优化慢速接口
3. **监控高风险接口**，优先修复失败路由
4. **保留历史日志**，追踪性能趋势

## 📈 持续集成

可集成到 CI/CD 流程：

```yaml
# .github/workflows/test.yml
- name: Run System Tests
  run: python3 test_all_routes_v3.py
  
- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: logs/
```

---

**INFINITE GZ SDN BHD** - Enterprise Testing Framework v3.0
