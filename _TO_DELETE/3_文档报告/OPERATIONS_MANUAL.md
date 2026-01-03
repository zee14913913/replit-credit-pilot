# CreditPilot 后端运维手册 (Operations Manual)

## 📘 总则
作为**CreditPilot金融SaaS平台后端维护者**，本手册定义了所有日常运维、监控、数据完整性验证和故障处理的标准操作流程（SOP）。

**核心原则**：
- ✅ **100%数据准确性** - 所有API必须返回真实非零数据
- ✅ **实时监控** - 关键服务24/7健康检查
- ✅ **完整日志** - 所有异常必须追溯到详细trace
- ✅ **零停机** - 前端和MiniMax集成无缝对接

---

## 🔄 每日必须执行的检查清单

### 1️⃣ 自动化API测试 (Daily)
**频率**: 每天至少1次  
**命令**:
```bash
bash test_api_endpoints.sh
```

**预期结果**:
```
通过: 8
失败: 0
🎉 所有测试通过！系统就绪！
```

**异常处理**:
- ❌ 如有失败 → 立即记录到 `logs/error.log`
- ❌ 失败原因分析 → 查看 `/tmp/logs/Server_*.log`
- ❌ 修复后重新验证 → 再次运行测试

---

### 2️⃣ 健康监控 (Real-time)
**端点**: `/api/health`  
**命令**:
```bash
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  http://localhost:5000/api/health
```

**正常响应**:
```json
{
  "status": "healthy"
}
```
**响应时间**: < 500ms  
**状态码**: 200

**异常阈值**:
- ⚠️ 响应时间 > 500ms → 检查服务器负载
- ❌ 状态码 500/502/503 → 检查服务日志
- ❌ 超时 > 5秒 → 重启服务

---

### 3️⃣ API端点数据验证 (Daily)
**验证所有API返回真实非零数据**:

```bash
# 客户列表
curl -s http://localhost:5000/api/customers | jq '.count'
# 期望: > 0

# 仪表板汇总
curl -s http://localhost:5000/api/dashboard/summary | jq '.summary.customers'
# 期望: > 0

# OCR状态
curl -s http://localhost:5000/api/bill/ocr-status | jq '.status'
# 期望: "ready"
```

**当前基线**:
- 客户: 8
- 账单: 281
- 交易: 1,960
- 信用卡: 31
- 总费用: RM 6,904,032.73

---

### 4️⃣ 数据完整性校验 (After Imports)
**每次批量导入/初始化后必须执行**:

```bash
python3 scripts/verify_data_integrity.py
```

**预期输出**:
```
✅ 客户记录: 8
✅ 账单记录: 281
✅ 交易记录: 1,960
✅ 信用卡记录: 31
✅ 总费用: RM 6,904,032.73
✅ 总还款: RM 1,056,562.75
✅ 净余额: RM 5,847,469.98
🎯 数据完整性验证: PASS
```

**验证项目**:
- [x] 客户记录数 > 0
- [x] 账单记录数 > 0
- [x] 交易记录数 > 0
- [x] 信用卡记录数 > 0
- [x] 财务余额一致性

---

### 5️⃣ 环境变量备份 (Weekly)
**频率**: 每周一次  
**命令**:
```bash
python3 scripts/backup_env_vars.py
```

**输出**:
```
✅ GOOGLE_PROJECT_ID: 已配置 (21 字符)
✅ GOOGLE_PROCESSOR_ID: 已配置 (16 字符)
✅ GOOGLE_LOCATION: 已配置 (2 字符)
✅ GOOGLE_SERVICE_ACCOUNT_JSON: 已配置 (2404 字符)
✅ DOCPARSER_API_KEY: 已配置 (40 字符)
✅ DOCPARSER_PARSER_ID: 已配置 (12 字符)
✅ DATABASE_URL: 已配置 (119 字符)
📄 备份文件: logs/env_backup_YYYYMMDD_HHMMSS.json
```

**备份位置**: `logs/env_backup_*.json`

---

### 6️⃣ 日报生成 (Daily)
**频率**: 每天自动  
**命令**:
```bash
python3 scripts/generate_daily_report.py
```

**生成文件**:
- `logs/daily_report_YYYYMMDD.md`
- `api_validation_report.md` (主报告更新)

**内容包含**:
- API健康检查
- 数据库统计
- API端点测试结果
- 异常清单
- 环境配置状态

---

## 🛠️ 系统服务管理

### 服务列表
| 服务 | 端口 | 类型 | 自动重启 |
|------|------|------|----------|
| Flask Server | 5000 | Web应用 | ✅ (watch mode) |
| Accounting API | 8000 | FastAPI后端 | ✅ (--reload) |
| MCP Server | 8080 | MCP协议 | ✅ |

### 服务状态检查
```bash
# 检查所有服务
curl http://localhost:5000/api/health   # Flask
curl http://localhost:8000/docs         # FastAPI
curl http://localhost:8080/health       # MCP
```

### 查看服务日志
```bash
# Flask日志
tail -f /tmp/logs/Server_*.log

# FastAPI日志
tail -f /tmp/logs/Accounting_API_*.log

# MCP日志
tail -f /tmp/logs/MCP_Server_*.log

# 查看错误
tail -100 /tmp/logs/Server_*.log | grep ERROR
```

### 重启服务（如需要）
```bash
# Flask和FastAPI会自动重启（watch模式）
# 如需手动重启，修改文件即可触发：
touch app.py  # 触发Flask重启
```

---

## 🌐 CORS与权限管理

### CORS域名清单（10个）
```python
# cors_config.py
ALLOWED_ORIGINS = [
    "https://ynqoo4ipbuar.space.minimax.io",  # MiniMax - 当前
    "https://iz6ki2qe01mh.space.minimax.io",  # MiniMax - 旧版
    "https://finance-pilot-businessgz.replit.app",
    "https://creditpilot.digital",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:5678",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000"
]
```

### CORS验证
```bash
# 测试MiniMax域名
curl -I -H "Origin: https://ynqoo4ipbuar.space.minimax.io" \
  http://localhost:5000/api/customers

# 期望响应头:
# Access-Control-Allow-Origin: https://ynqoo4ipbuar.space.minimax.io
# Access-Control-Allow-Credentials: true
```

### 权限验证
**需要认证的端点**:
- `/api/bill/upload` - Admin/Accountant
- `/api/customer/create` - Admin/Accountant

**认证方式**:
- Flask: Session Cookie
- FastAPI: JWT Token

---

## 📊 数据库管理

### 数据库信息
- **类型**: SQLite
- **文件**: `db/smart_loan_manager.db`
- **大小**: 4.2 MB
- **表数**: 20+

### 数据库查询
```bash
# 使用Python查询（sqlite3命令不可用）
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('db/smart_loan_manager.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM customers")
print(f"客户数: {cursor.fetchone()[0]}")
conn.close()
EOF
```

### 数据库备份
```bash
# 手动备份
cp db/smart_loan_manager.db db/smart_loan_manager_backup_$(date +%Y%m%d).db

# 验证备份
ls -lh db/*.db
```

---

## 🚨 异常处理流程

### 异常类型与响应

#### 1. API超时
**症状**: 响应时间 > 500ms  
**诊断**:
```bash
# 检查服务器负载
top -bn1 | head -20

# 查看慢查询
tail -100 /tmp/logs/Server_*.log | grep "slow"
```
**修复**: 优化查询 / 增加缓存 / 扩展资源

#### 2. 数据丢失
**症状**: API返回空数据或零值  
**诊断**:
```bash
python3 scripts/verify_data_integrity.py
```
**修复**: 从备份恢复 / 重新导入数据

#### 3. 集成报错
**症状**: 前端调用API失败  
**诊断**:
```bash
# 检查CORS配置
grep "ynqoo4ipbuar" cors_config.py

# 检查API密钥
python3 scripts/backup_env_vars.py
```
**修复**: 更新配置 / 刷新API密钥 / 重启服务

#### 4. CORS失败
**症状**: 跨域请求被拒绝  
**诊断**:
```bash
curl -I -H "Origin: https://ynqoo4ipbuar.space.minimax.io" \
  http://localhost:5000/api/customers | grep -i "access-control"
```
**修复**: 更新 `cors_config.py` 添加新域名

#### 5. 认证失效
**症状**: 401 Unauthorized  
**诊断**:
```bash
# 检查Session/Token
tail -50 /tmp/logs/Server_*.log | grep "401"
```
**修复**: 重新登录 / 刷新Token

---

## 📝 日志管理

### 日志位置
```
/tmp/logs/
├── Server_*.log           # Flask应用日志
├── Accounting_API_*.log   # FastAPI后端日志
├── MCP_Server_*.log       # MCP服务器日志
└── browser_console_*.log  # 浏览器控制台日志

logs/
├── daily_report_*.md      # 每日运维报告
├── env_backup_*.json      # 环境变量备份
└── error.log              # 持久化错误日志（待创建）
```

### 查看错误日志
```bash
# 查看最新错误
tail -100 /tmp/logs/Server_*.log | grep ERROR

# 实时监控
tail -f /tmp/logs/Server_*.log | grep -E "ERROR|WARNING"

# 查看特定时间段
grep "2025-11-22 09:" /tmp/logs/Server_*.log
```

### 日志持久化（推荐）
**创建持久化错误日志**:
```bash
mkdir -p logs
touch logs/error.log
```

**配置日志格式**:
```
[YYYY-MM-DD HH:MM:SS] [ERROR] <详细trace> <context>
```

---

## 🔧 自动化工具清单

### 已创建的脚本
| 脚本 | 功能 | 频率 |
|------|------|------|
| `test_api_endpoints.sh` | API端点自动化测试 | 每天 |
| `scripts/verify_data_integrity.py` | 数据完整性验证 | 每次导入后 |
| `scripts/backup_env_vars.py` | 环境变量备份 | 每周 |
| `scripts/generate_daily_report.py` | 生成每日报告 | 每天 |

### 快速命令参考
```bash
# 1. 完整系统健康检查
bash test_api_endpoints.sh

# 2. 数据完整性验证
python3 scripts/verify_data_integrity.py

# 3. 环境变量备份
python3 scripts/backup_env_vars.py

# 4. 生成日报
python3 scripts/generate_daily_report.py

# 5. 查看所有日志
ls -lh logs/

# 6. 检查服务状态
curl http://localhost:5000/api/health
```

---

## 📈 性能监控与告警（推荐集成）

### 推荐工具
1. **Sentry** - 实时错误追踪
   - 自动捕获异常
   - 堆栈追踪
   - 用户上下文
   
2. **Prometheus** - 性能指标监控
   - API响应时间
   - 请求量统计
   - 资源使用率

3. **Grafana** - 可视化仪表板
   - 实时图表
   - 告警配置
   - 趋势分析

### 集成状态
- [ ] **Sentry**: 未配置（高优先级）
- [ ] **Prometheus**: 未配置（高优先级）
- [ ] **Grafana**: 未配置（中优先级）

---

## 🎯 运维检查表（每日执行）

### 早上检查（09:00 UTC）
- [ ] 运行 `bash test_api_endpoints.sh`
- [ ] 执行 `python3 scripts/generate_daily_report.py`
- [ ] 检查 `/api/health` 响应时间
- [ ] 查看 `logs/daily_report_*.md`
- [ ] 确认无CRITICAL告警

### 下午检查（15:00 UTC）
- [ ] 再次运行API测试
- [ ] 检查服务日志是否有异常
- [ ] 验证CORS配置正常
- [ ] 确认前端集成无报错

### 晚上检查（21:00 UTC）
- [ ] 最后一次API测试
- [ ] 备份关键数据（如有更新）
- [ ] 记录今日incident（如有）
- [ ] 准备明日优化计划

---

## 📞 故障升级流程

### 级别定义
| 级别 | 定义 | 响应时间 | 通知方式 |
|------|------|----------|----------|
| P0 - CRITICAL | 系统完全不可用 | 立即 | 电话+邮件+SMS |
| P1 - HIGH | 核心功能受损 | 15分钟内 | 邮件+SMS |
| P2 - MEDIUM | 部分功能异常 | 1小时内 | 邮件 |
| P3 - LOW | 性能下降 | 4小时内 | 记录到日志 |

### 升级路径
1. **自动诊断** - 运行健康检查脚本
2. **本地修复** - 应用标准修复流程
3. **团队通知** - 如15分钟内无法解决
4. **升级管理** - 如涉及数据丢失或安全问题

---

## 📚 附录

### A. 重要文件清单
```
项目根目录/
├── app.py                          # Flask主应用
├── cors_config.py                  # CORS配置
├── test_api_endpoints.sh           # API测试脚本
├── api_validation_report.md        # API验证报告
├── daily_operations_log.md         # 运维日志
├── OPERATIONS_MANUAL.md            # 本手册
├── db/
│   └── smart_loan_manager.db       # SQLite数据库
├── config/
│   └── bank_parser_templates.json  # 银行解析器配置
├── logs/
│   ├── daily_report_*.md           # 每日报告
│   ├── env_backup_*.json           # 环境变量备份
│   └── error.log                   # 错误日志（待创建）
└── scripts/
    ├── verify_data_integrity.py    # 数据完整性验证
    ├── backup_env_vars.py          # 环境变量备份
    └── generate_daily_report.py    # 日报生成
```

### B. 联系方式
- **运维团队**: operations@creditpilot.com
- **紧急热线**: (待配置)
- **Slack频道**: #creditpilot-ops

### C. 变更日志
| 日期 | 变更内容 | 操作者 |
|------|----------|--------|
| 2025-11-22 | 创建完整运维手册 | Backend Team |
| 2025-11-22 | 部署4个新API端点 | Backend Team |
| 2025-11-22 | 配置CORS支持10个域名 | Backend Team |

---

**文档版本**: v1.0  
**最后更新**: 2025-11-22 09:36 UTC  
**维护者**: CreditPilot Backend Operations Team  
**下次审核**: 2025-11-29
