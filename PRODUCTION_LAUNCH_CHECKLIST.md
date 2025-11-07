# 🚀 CreditPilot Production Launch Checklist
**系统**: CreditPilot Accounting System v2.0  
**发布日期**: 2025年11月  
**环境**: Production

---

## ✅ Pre-Launch Verification | 发布前验证

### 🔐 1. API Keys & Secrets | API密钥配置

| 密钥名称 | 用途 | 必需性 | 配置状态 | 获取方式 |
|---------|------|--------|---------|---------|
| `DATABASE_URL` | PostgreSQL连接 | ✅ 必需 | ☐ | Replit自动配置 |
| `FERNET_KEY` | 数据加密 | ✅ 必需 | ☐ | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"` |
| `ADMIN_EMAIL` | 管理员邮箱 | ✅ 必需 | ☐ | 手动设置 |
| `ADMIN_PASSWORD` | 管理员密码 | ✅ 必需 | ☐ | 强密码（≥16字符） |
| `OCR_API_KEY` | 收据OCR识别 | ⚠️ 可选 | ☐ | OCR.space或Google Vision |
| `SENDGRID_API_KEY` | 邮件发送 | ⚠️ 可选 | ☐ | SendGrid Dashboard |
| `TWILIO_ACCOUNT_SID` | SMS提醒 | ⚠️ 可选 | ☐ | Twilio Console |
| `TWILIO_AUTH_TOKEN` | SMS认证 | ⚠️ 可选 | ☐ | Twilio Console |
| `TWILIO_PHONE_NUMBER` | SMS发送号码 | ⚠️ 可选 | ☐ | 购买Twilio号码 |

**验证命令**：
```bash
# 检查所有必需密钥
python3 -c "
import os
required = ['DATABASE_URL', 'FERNET_KEY', 'ADMIN_EMAIL', 'ADMIN_PASSWORD']
for key in required:
    status = '✅' if os.getenv(key) else '❌'
    print(f'{status} {key}')
"
```

**安全检查**：
- ☐ 所有密钥已添加到Replit Secrets（不在代码中）
- ☐ 密钥长度符合要求（≥32字符）
- ☐ 生产环境密钥与开发环境不同

---

### 💾 2. Database Backup | 数据库备份

**自动备份配置**：
```bash
# Replit PostgreSQL自动备份已启用
# 手动触发备份（可选）
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

**验证检查**：
- ☐ PostgreSQL实例正常运行
- ☐ 数据库表结构完整（49张表）
- ☐ 测试数据已清理（可选）
- ☐ 备份文件可访问

**回滚准备**：
```bash
# 创建当前状态快照
git tag production-$(date +%Y%m%d-%H%M%S)
git push --tags

# 备份数据库
pg_dump $DATABASE_URL | gzip > production_backup.sql.gz
```

---

### 🌐 3. Domain & SSL | 域名与SSL配置

**Replit部署配置**：
- ☐ 项目已发布（Deploy）
- ☐ HTTPS自动启用
- ☐ 自定义域名已配置（可选）

**域名配置示例**：
```
生产URL: https://creditpilot.repl.co
自定义域名: https://app.creditpilot.com (可选)
```

**SSL验证**：
```bash
# 检查SSL证书
curl -vI https://your-app-url.repl.co 2>&1 | grep "SSL certificate"

# 应返回：TLS handshake成功
```

**安全头检查**：
- ☐ HSTS已启用
- ☐ X-Frame-Options: DENY
- ☐ X-Content-Type-Options: nosniff
- ☐ Content-Security-Policy已配置

---

### ⚙️ 4. Environment Variables | 环境变量

**生产环境配置**：
```bash
# 核心配置
PORT=5000
ENV=production
DEBUG=false

# 安全配置
HTTPS_ONLY=true
SESSION_SECRET=<随机生成>
MAX_UPLOAD_SIZE=10485760  # 10MB

# 速率限制
RATE_LIMIT_ZIP=5/minute
RATE_LIMIT_OCR=20/hour

# 日志级别
LOG_LEVEL=INFO
AUDIT_LOG_ENABLED=true

# 缓存配置（可选）
MONTH_SUMMARY_CACHE_TTL=60
```

**验证命令**：
```bash
# 检查环境变量
env | grep -E "PORT|ENV|DEBUG|HTTPS"
```

---

### 👥 5. Test Accounts | 测试账号

**管理员账号**：
```
Email: ${ADMIN_EMAIL}
Password: ${ADMIN_PASSWORD}
Role: ADMIN
```

**测试客户账号**（演示用）：
```
Customer Code: DEMO001
Customer Name: Demo Restaurant Sdn Bhd
Created: Setup时自动创建
```

**验证流程**：
- ☐ 管理员可以登录
- ☐ 可以创建新客户
- ☐ 可以上传信用卡账单
- ☐ 可以生成发票
- ☐ 可以导出报告

---

### 🔒 6. RBAC Permissions | 权限配置

**角色定义**：
| 角色 | 权限 | 数量限制 |
|------|------|---------|
| `ADMIN` | 全部功能 | 无限制 |
| `ACCOUNTANT` | 查看、上传、生成报告 | 100客户 |
| `VIEWER` | 仅查看 | 50客户 |

**权限矩阵**：
```
功能                 ADMIN  ACCOUNTANT  VIEWER
上传账单               ✅      ✅         ❌
生成发票               ✅      ✅         ❌
导出报告               ✅      ✅         ✅
用户管理               ✅      ❌         ❌
系统配置               ✅      ❌         ❌
审计日志               ✅      ✅         ✅
```

**验证步骤**：
- ☐ 不同角色访问正确的功能
- ☐ 越权访问被拦截
- ☐ 审计日志记录操作

---

### 🏥 7. Health Check Endpoints | 健康检查

**关键端点**：
```bash
# 1. 系统健康检查
curl https://your-app.repl.co/health
# 期望: {"status": "ok", "db": "connected"}

# 2. 数据库连接
curl https://your-app.repl.co/api/db/status
# 期望: {"connected": true, "tables": 49}

# 3. Portal加载
curl -I https://your-app.repl.co/portal
# 期望: HTTP/1.1 200 OK

# 4. 月末统计API
curl https://your-app.repl.co/credit-cards/month-summary
# 期望: {"ok": true, "pending": N, "suppliers": M}

# 5. 批量ZIP生成
curl -I https://your-app.repl.co/credit-cards/supplier-invoices/batch.zip
# 期望: HTTP/1.1 200 OK, Content-Type: application/zip
```

**性能基准**：
| 端点 | 期望响应时间 | SLA |
|------|-------------|-----|
| `/portal` | < 200ms | 99.5% |
| `/month-summary` | < 500ms | 99.0% |
| `/batch.zip` | < 2s | 95.0% |
| `/export.csv` | < 100ms | 99.9% |

**监控设置**：
```bash
# 使用Replit监控或外部服务（Uptime Robot）
# 每5分钟ping /health
# 失败时发送告警到${ADMIN_EMAIL}
```

---

### 🧪 8. Functional Testing | 功能测试

**完整工作流测试**（6分钟月末闭环）：

#### **第1步: Portal查看待办**（30秒）
```bash
# 访问Portal
open https://your-app.repl.co/portal

# 验证月末待办卡显示数据
✓ 待匹配收据显示数字
✓ 本月供应商显示数字
✓ 预计服务费显示金额
```

#### **第2步: 上传收据**（2分钟）
```bash
# 访问收据页面
open https://your-app.repl.co/credit-cards/receipts

# 上传收据图片
✓ 支持JPG/PNG格式
✓ OCR自动识别（如已配置）
✓ 显示识别结果
```

#### **第3步: 批量匹配**（30秒）
```bash
# 点击 [Match All ≥ 0.90]
✓ 自动匹配高相似度交易
✓ 更新覆盖率评分
✓ 刷新统计数据
```

#### **第4步: 生成发票ZIP**（1分钟）
```bash
# 访问供应商发票页面
open https://your-app.repl.co/credit-cards/supplier-invoices

# 点击 [Generate All (ZIP)]
✓ 下载invoices_YYYY-MM.zip
✓ 解压包含N个PDF文件
✓ 文件名安全（无路径遍历）
```

#### **第5步: 导出月度报告**（30秒）
```bash
# 访问月度报告页面
open https://your-app.repl.co/credit-cards/monthly-report

# 点击 [导出 CSV]
✓ 下载monthly_YYYY-MM_X.csv
✓ Excel可正常打开
✓ 数据格式正确
```

#### **第6步: 验证完整性**（1分钟）
```bash
# 检查数据完整性
✓ 覆盖率评级正确（A/B/C/D）
✓ 供应商总数匹配
✓ 服务费计算准确（1%）
```

**自动化测试脚本**：
```python
# tests/e2e_workflow_test.py
import requests
import time

BASE_URL = "https://your-app.repl.co"

def test_6min_workflow():
    start = time.time()
    
    # 1. Portal加载
    r = requests.get(f"{BASE_URL}/portal")
    assert r.status_code == 200
    
    # 2. 月末统计
    r = requests.get(f"{BASE_URL}/credit-cards/month-summary")
    data = r.json()
    assert data["ok"] == True
    
    # 3. 批量ZIP
    r = requests.get(f"{BASE_URL}/credit-cards/supplier-invoices/batch.zip")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/zip"
    
    # 4. CSV导出
    r = requests.get(f"{BASE_URL}/credit-cards/monthly-report/export.csv")
    assert r.status_code == 200
    assert "Category,Expenses,Payments" in r.text
    
    elapsed = time.time() - start
    assert elapsed < 360, f"Workflow took {elapsed}s, expected < 360s"
    print(f"✅ 6-minute workflow completed in {elapsed:.1f}s")

if __name__ == "__main__":
    test_6min_workflow()
```

---

### 📊 9. Performance Testing | 性能测试

**负载测试**（使用Apache Bench）：
```bash
# 测试Portal并发加载
ab -n 100 -c 10 https://your-app.repl.co/portal

# 期望结果：
# - 100% requests successful
# - Mean response time < 500ms
# - No failed requests

# 测试month-summary API
ab -n 200 -c 20 https://your-app.repl.co/credit-cards/month-summary

# 期望结果：
# - 95th percentile < 800ms
# - Database connections stable
```

**压力测试场景**：
```
场景1: 10个用户同时生成ZIP
场景2: 50个并发Portal访问
场景3: 100次/分钟month-summary调用
```

**性能指标**：
- ☐ CPU使用率 < 70%
- ☐ 内存使用 < 512MB
- ☐ 数据库连接池 < 20
- ☐ 响应时间P95 < 1s

---

### 🔒 10. Security Audit | 安全审计

**漏洞扫描**：
- ☐ Zip Slip防护已验证
- ☐ SQL注入测试通过（ORM保护）
- ☐ XSS防护已启用（Jinja2转义）
- ☐ CSRF令牌已配置
- ☐ 文件上传限制已设置（10MB）

**渗透测试检查清单**：
```bash
# 1. 路径遍历攻击
curl "https://app.repl.co/credit-cards/supplier-invoices/batch.zip" \
  -H "X-Malicious-Supplier: ../../evil"
# 期望: 文件名被安全化

# 2. SQL注入测试
curl "https://app.repl.co/credit-cards/transactions?supplier='; DROP TABLE--"
# 期望: 参数化查询，无影响

# 3. XSS测试
curl "https://app.repl.co/portal" \
  -d "name=<script>alert(1)</script>"
# 期望: HTML实体转义
```

**合规检查**：
- ☐ GDPR数据保护（如适用）
- ☐ PCI DSS（如处理支付）
- ☐ 审计日志保留 ≥ 90天
- ☐ 数据加密（传输+静态）

---

### 📝 11. Documentation | 文档完整性

**必需文档**：
- ☐ `用户使用手册_CREDITPILOT完整功能指南.md`（150页）
- ☐ `UI_UPGRADE_SUMMARY.md`（升级说明）
- ☐ `SECURITY_FIXES_REPORT.md`（安全修复报告）
- ☐ `PRODUCTION_LAUNCH_CHECKLIST.md`（本文档）
- ☐ `replit.md`（系统架构）

**API文档**：
```bash
# FastAPI自动生成文档
open https://your-app.repl.co/docs
# 验证所有端点已记录
```

**运维手册**：
- ☐ 故障排查指南
- ☐ 日志查看命令
- ☐ 数据库维护步骤
- ☐ 回滚操作流程

---

### 🔄 12. Rollback Plan | 回滚计划

**快速回滚步骤**（<5分钟）：

#### **场景1: 代码回滚**
```bash
# 1. 查看最近发布tag
git tag -l "production-*"

# 2. 回滚到上一版本
git checkout production-20251107-1200
git push --force

# 3. 重启服务
# Replit会自动重新部署
```

#### **场景2: 数据库回滚**
```bash
# 1. 停止应用（避免写入）
# 在Replit Dashboard停止Deployment

# 2. 恢复数据库
gunzip < production_backup.sql.gz | psql $DATABASE_URL

# 3. 验证数据完整性
psql $DATABASE_URL -c "SELECT COUNT(*) FROM suppliers;"

# 4. 重启应用
```

#### **场景3: 部分回滚（热修复）**
```bash
# 仅回滚特定功能（通过feature flag）
# 在代码中添加：
if os.getenv("DISABLE_NEW_ZIP_FEATURE") == "true":
    # 使用旧逻辑
    pass
```

**回滚决策矩阵**：
| 问题严重程度 | 响应时间 | 操作 |
|------------|---------|------|
| P0 - 系统不可用 | < 5分钟 | 立即完全回滚 |
| P1 - 功能损坏 | < 30分钟 | 部分回滚或热修复 |
| P2 - 性能下降 | < 2小时 | 监控+计划修复 |
| P3 - UI问题 | < 1天 | 计划修复 |

---

### 📞 13. Support & Monitoring | 支持与监控

**告警配置**：
```yaml
# 使用Replit监控或外部服务
alerts:
  - name: "Server Down"
    condition: "health_check_failed"
    notify: ${ADMIN_EMAIL}
    
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    notify: ${ADMIN_EMAIL}
    
  - name: "Slow Response"
    condition: "p95_latency > 2s"
    notify: ${ADMIN_EMAIL}
```

**日志聚合**：
```bash
# 查看实时日志
# Replit Dashboard → Logs

# 搜索错误
grep -r "ERROR" /tmp/logs/

# 审计日志查询
psql $DATABASE_URL -c "
  SELECT * FROM audit_logs 
  WHERE created_at > NOW() - INTERVAL '1 hour'
  ORDER BY created_at DESC
  LIMIT 50;
"
```

**支持团队联系**：
```
技术负责人: ${ADMIN_EMAIL}
紧急热线: ${TWILIO_PHONE_NUMBER} (可选)
工作时间: 周一至周五 9:00-18:00 MYT
响应SLA: P0=1h, P1=4h, P2=1d, P3=3d
```

---

## 🎯 Launch Day Checklist | 发布日核对表

### T-24小时
- [ ] 所有代码已合并到main分支
- [ ] 所有测试通过（功能+性能+安全）
- [ ] 生产环境变量已配置
- [ ] 数据库备份已创建
- [ ] 团队已收到发布通知

### T-2小时
- [ ] 最终健康检查通过
- [ ] 回滚计划已确认
- [ ] 支持团队待命
- [ ] 文档已更新到最新版

### T-0（发布时刻）
- [ ] 点击Replit "Deploy"按钮
- [ ] 等待部署完成（~5分钟）
- [ ] 验证生产URL可访问
- [ ] 运行冒烟测试（6分钟工作流）
- [ ] 监控错误日志（前30分钟）

### T+30分钟
- [ ] 检查健康指标
- [ ] 验证用户可正常访问
- [ ] 确认没有重大错误
- [ ] 发送"发布成功"通知

### T+2小时
- [ ] 性能指标稳定
- [ ] 用户反馈收集
- [ ] 可以安全下班 🎉

---

## 📋 Post-Launch Tasks | 发布后任务

### 第1天
- [ ] 监控用户活跃度
- [ ] 收集首日反馈
- [ ] 修复紧急bug（如有）

### 第1周
- [ ] 性能优化调整
- [ ] 用户培训/演示
- [ ] 完善文档（基于反馈）

### 第1月
- [ ] 功能使用统计分析
- [ ] 计划下一版本功能
- [ ] 安全审计回顾

---

## 🔍 Quick Reference | 快速参考

### 常用命令
```bash
# 查看服务状态
curl https://your-app.repl.co/health

# 重启服务（Replit）
# Dashboard → Stop → Start

# 查看日志
tail -f /tmp/logs/FastAPI_Server_*.log

# 数据库连接
psql $DATABASE_URL

# 创建备份
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 关键URL
```
Production: https://your-app.repl.co
Portal: /portal
Health: /health
API Docs: /docs
Admin: /admin (需登录)
```

### 紧急联系
```
技术支持: ${ADMIN_EMAIL}
Replit Support: https://replit.com/support
数据库问题: Replit Database团队
```

---

## ✅ Sign-Off | 最终签字

**系统检查**：
- [ ] 所有P0项目已完成
- [ ] 所有测试通过
- [ ] 文档齐全
- [ ] 团队已培训

**发布批准**：
```
技术负责人: ________________  日期: ____/____/____
产品负责人: ________________  日期: ____/____/____
安全审查员: ________________  日期: ____/____/____
```

---

**版本**: 1.0  
**最后更新**: 2025年11月7日  
**下次审查**: 发布后30天  

🚀 **准备好了吗？Let's Launch!** 🚀
