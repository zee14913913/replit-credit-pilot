# CreditPilot Deployment Checklist

**INFINITE GZ SDN. BHD.**  
**Target Domain**: portal.creditpilot.digital  
**System Version**: v2.0

---

## 📋 **Pre-Deployment Checklist**

### **1. Environment Variables（环境变量验证）**

**必需环境变量（13个）**：

```bash
# 访问控制
☑ PORTAL_KEY          # Portal访问密钥
☑ ADMIN_KEY           # 管理员后台密钥
☑ LOANS_REFRESH_KEY   # 刷新权限密钥

# 数据加密
☑ FERNET_KEY          # PII数据加密密钥

# 数据库
☑ DATABASE_URL        # PostgreSQL连接字符串
☑ PGHOST              # PostgreSQL主机
☑ PGPORT              # PostgreSQL端口（5432）
☑ PGUSER              # PostgreSQL用户名
☑ PGPASSWORD          # PostgreSQL密码
☑ PGDATABASE          # PostgreSQL数据库名

# 系统配置
☑ ENV=prod            # 生产环境标识
☑ TZ=Asia/Kuala_Lumpur  # 时区设置
☑ PORT=5000           # 服务端口
```

**验证命令**：
```bash
# 检查所有环境变量是否存在
env | grep -E "(PORTAL_KEY|ADMIN_KEY|FERNET_KEY|DATABASE_URL|ENV|TZ)"
```

---

### **2. Database（数据库检查）**

**SQLite数据库（loans.db）**：
```bash
☑ 数据库文件存在：db/loans.db
☑ 表结构完整：5个表（loan_updates, loan_intel, loan_share, ctos_submissions, harvest_log）
☑ 演示数据就绪：3个产品 + 3条情报数据
```

**PostgreSQL数据库（通知/审计）**：
```bash
☑ 连接正常：curl -s http://localhost:5000/health | grep "ok"
☑ 权限正确：读写权限
```

**验证命令**：
```bash
# 检查SQLite数据
sqlite3 db/loans.db "SELECT COUNT(*) FROM loan_updates;"  # 应返回 3
sqlite3 db/loans.db "SELECT COUNT(*) FROM loan_intel;"    # 应返回 3

# 检查PostgreSQL
psql $DATABASE_URL -c "\dt"  # 列出所有表
```

---

### **3. API Endpoints（端点健康检查）**

**核心端点验证（20个）**：
```bash
☑ GET  /health                    → 200 OK
☑ GET  /loans/updates             → 200 OK (3条数据)
☑ GET  /loans/intel               → 200 OK (3条数据)
☑ GET  /loans/ranking             → 200 OK (Top-3)
☑ GET  /loans/ranking/pdf         → 200 OK (PDF文件)
☑ GET  /loans/top3/cards          → 200 OK (HTML)
☑ GET  /loans/page                → 200 OK (主页)
☑ GET  /loans/compare/page        → 200 OK (对比页)
☑ POST /loans/compare/add         → 200 OK
☑ GET  /loans/compare/json        → 200 OK
☑ POST /loans/compare/snapshot    → 200 OK
☑ GET  /ctos/page?key=***         → 200 OK
```

**自动化验证脚本**：
```bash
#!/bin/bash
BASE="https://portal.creditpilot.digital"

echo "🔍 API健康检查..."

# 基础端点
curl -sf "$BASE/health" || echo "❌ /health 失败"
curl -sf "$BASE/loans/updates" | jq -e 'length == 3' || echo "❌ /loans/updates 数据不正确"
curl -sf "$BASE/loans/intel" | jq -e 'length == 3' || echo "❌ /loans/intel 数据不正确"

# Ranking端点
curl -sf "$BASE/loans/ranking" | jq -e 'length == 3' || echo "❌ Top-3 数据不正确"
curl -sf "$BASE/loans/ranking/pdf" -o /tmp/top3.pdf && file /tmp/top3.pdf | grep PDF || echo "❌ PDF生成失败"

# 页面端点
curl -sf "$BASE/loans/page" | grep "Loans Intelligence" || echo "❌ Loans页面失败"
curl -sf "$BASE/loans/compare/page" | grep "Compare" || echo "❌ Compare页面失败"

echo "✅ 所有端点检查完成"
```

---

### **4. Security（安全检查）**

**安全头部验证**：
```bash
☑ X-Frame-Options: SAMEORIGIN
☑ X-Content-Type-Options: nosniff
☑ Referrer-Policy: no-referrer
☑ Strict-Transport-Security: max-age=31536000 (生产环境)
```

**访问控制测试**：
```bash
# 测试PORTAL_KEY保护
curl -I "https://portal.creditpilot.digital/portal" | grep "401"  # 无密钥应返回401
curl -I "https://portal.creditpilot.digital/portal?key=WRONG" | grep "401"  # 错误密钥应返回401
curl -I "https://portal.creditpilot.digital/portal?key=$PORTAL_KEY" | grep "200"  # 正确密钥应返回200

# 测试ADMIN_KEY保护
curl -I "https://portal.creditpilot.digital/ctos/admin?key=$PORTAL_KEY" | grep "401"  # 无ADMIN_KEY应返回401
```

**PII加密验证**：
```bash
# 检查CTOS提交数据已加密
sqlite3 db/loans.db "SELECT nric_encrypted, phone_encrypted FROM ctos_submissions LIMIT 1;" | grep "gAAAAA"  # Fernet前缀
```

---

### **5. File Storage（文件存储检查）**

**目录结构验证**：
```bash
☑ static/uploads/           # 上传文件根目录
☑ static/uploads/customers/ # 客户文件夹（动态创建）
☑ db/                       # 数据库目录
☑ logs/                     # 日志目录（可选）
```

**权限检查**：
```bash
# 确保写权限
touch static/uploads/test.txt && rm static/uploads/test.txt || echo "❌ 写权限不足"
```

---

### **6. Performance（性能基准测试）**

**响应时间验证**：
```bash
☑ DSR计算：< 50ms
☑ Top-3评分：< 10ms
☑ API响应：< 100ms
☑ PDF生成：< 500ms
```

**负载测试**（可选）：
```bash
# 使用ab（Apache Bench）进行简单负载测试
ab -n 100 -c 10 https://portal.creditpilot.digital/loans/updates
# 预期：100%成功率，平均响应 < 100ms
```

---

### **7. Frontend（前端功能验证）**

**浏览器兼容性测试**：
```bash
☑ Chrome（最新版）   → 全功能正常
☑ Edge（最新版）     → 全功能正常
☑ Safari（iOS）      → 基础功能正常
☑ Firefox（最新版）  → 全功能正常
```

**核心交互测试**：
```bash
☑ Top-3卡片显示      → iframe加载正常
☑ "加入比价"按钮     → 徽标+1，400ms延迟
☑ Compare Basket徽标 → 15秒自动刷新
☑ 一键重算功能       → 前端计算 < 50ms
☑ 保存快照功能       → 生成10字符短码
☑ 复制分享链接       → Clipboard API正常
☑ 导出PDF功能        → 文件下载正常
☑ 可排序表格         → 7列全部可排序
```

**移动端响应式测试**：
```bash
☑ 手机屏幕（< 768px）  → Grid 1列布局
☑ 平板屏幕（768-1024px）→ Grid 2列布局
☑ 桌面屏幕（> 1024px） → Grid 3列布局
```

---

### **8. Scheduled Tasks（定时任务验证）**

**Cron任务检查**：
```bash
☑ 每日数据采集：11:00 AM Asia/Kuala_Lumpur
☑ 20小时冷却机制：防止重复调用
☑ 日志记录：harvest_log表自动更新
```

**手动触发测试**（仅测试环境）：
```bash
# 使用刷新密钥手动触发
curl -X POST "https://portal.creditpilot.digital/loans/updates/refresh" \
  -H "X-Refresh-Key: $LOANS_REFRESH_KEY"
```

---

### **9. Monitoring & Logging（监控与日志）**

**日志系统验证**：
```bash
☑ 访问日志：记录所有HTTP请求
☑ 错误日志：记录500错误和异常
☑ 审计日志：记录管理员操作（PostgreSQL）
```

**监控端点**：
```bash
☑ /health              → 系统健康状态
☑ /loans/updates/last  → 最后数据更新时间
☑ /stats               → 存储使用情况（可选）
```

---

### **10. Documentation（文档完整性）**

**必需文档**：
```bash
☑ API_REFERENCE.md         # API规范文档
☑ USER_GUIDE.md            # 客户使用手册
☑ OPERATIONS_MANUAL.md     # 运维操作手册
☑ SYSTEM_INVENTORY.md      # 系统功能清单
☑ DEPLOYMENT_CHECKLIST.md  # 部署检查清单（本文件）
☑ README.md                # 项目说明
```

---

## 🚀 **Deployment Steps（部署步骤）**

### **Step 1: 环境准备**
```bash
# 1. 确认所有环境变量已配置
env | grep -E "(PORTAL_KEY|ADMIN_KEY|FERNET_KEY|DATABASE_URL|ENV)"

# 2. 检查依赖包
pip list | grep -E "(fastapi|uvicorn|reportlab|pdfplumber)"

# 3. 验证数据库连接
curl -s http://localhost:5000/health
```

### **Step 2: 本地验证**
```bash
# 1. 启动本地服务器
uvicorn accounting_app.main:app --host 0.0.0.0 --port 5000

# 2. 运行健康检查脚本
bash health_check.sh

# 3. 浏览器测试
open http://localhost:5000/loans/page
```

### **Step 3: 域名配置**
```bash
# 1. 在Replit中配置自定义域名
# Settings → Domains → portal.creditpilot.digital

# 2. 验证DNS解析
nslookup portal.creditpilot.digital

# 3. SSL证书验证
curl -I https://portal.creditpilot.digital | grep "HTTP/2 200"
```

### **Step 4: 生产部署**
```bash
# 1. 标记当前版本
git tag -a v2.0 -m "Production release - Loans Intelligence System"

# 2. 部署到production
# （Replit自动部署，无需手动操作）

# 3. 验证生产环境
curl -s https://portal.creditpilot.digital/health | jq .
```

### **Step 5: 最终验证**
```bash
# 运行完整端点测试
bash deployment_verification.sh

# 检查监控指标
curl https://portal.creditpilot.digital/loans/updates/last
```

---

## ✅ **Post-Deployment（部署后验证）**

### **立即验证（部署后5分钟内）**
- [ ] 访问 https://portal.creditpilot.digital/loans/page
- [ ] 查看Top-3卡片显示正常
- [ ] 测试"加入比价"功能
- [ ] 导出Top-3 PDF
- [ ] 测试Compare页面所有功能
- [ ] 测试快照保存与分享
- [ ] 验证CTOS表单提交

### **24小时内验证**
- [ ] 检查定时采集任务运行（11:00 AM次日）
- [ ] 查看日志无异常错误
- [ ] 验证所有PDF导出正常
- [ ] 测试分享链接可访问

### **一周内验证**
- [ ] 监控系统性能（响应时间、错误率）
- [ ] 检查数据库增长（SQLite大小）
- [ ] 验证PII加密存储正常
- [ ] 审计日志完整性

---

## 🔧 **Rollback Plan（回滚计划）**

**如果部署出现问题**：

### **方案A：Replit历史回滚**
```bash
1. 打开Replit History
2. 选择最后一个稳定版本（标记为"prod-stable"）
3. 点击"Restore"恢复
4. 重启workflow
```

### **方案B：数据库回滚**
```bash
# 恢复SQLite备份
cp /home/runner/pgdump_YYYYMMDD.sql.backup db/loans.db

# 恢复PostgreSQL
psql $DATABASE_URL < /home/runner/pgdump_YYYYMMDD.sql
```

### **方案C：紧急维护模式**
```bash
# 临时关闭服务
pkill -f uvicorn

# 显示维护页面（可选）
# 修改main.py添加维护模式检查
```

---

## 📞 **Support Contacts（技术支持）**

**生产问题联系**：
- Email: support@infinitegz.com
- Emergency: （预留紧急联系方式）

**系统管理员**：
- 访问：https://portal.creditpilot.digital/ctos/admin?key=***&ak=***

---

## 📝 **Deployment Log Template（部署日志模板）**

```
=== CreditPilot Deployment Log ===
Date: YYYY-MM-DD HH:MM
Version: v2.0
Deployed by: [Your Name]
Environment: Production

Pre-Deployment Checks:
☑ Environment variables verified
☑ Database connection OK
☑ API endpoints healthy (20/20)
☑ Security headers configured
☑ Performance benchmarks met

Deployment Steps:
☑ Local verification passed
☑ Domain DNS configured
☑ SSL certificate valid
☑ Production deployment successful
☑ Post-deployment tests passed

Issues Found: None / [List any issues]
Resolution: N/A / [Describe fixes]

System Status: ✅ READY FOR PRODUCTION
```

---

**版本**: v2.0  
**最后更新**: 2025-11-05  
**状态**: ✅ Production Ready

© INFINITE GZ SDN. BHD. All rights reserved.
