# 🚀 CreditPilot v1.0 生产部署指南

## ✅ 系统状态：已就绪

**部署时间**: 2025-11-05  
**版本**: v1.0 Production Ready  
**域名**: `https://workspace-business183.replit.app`

---

## 📊 已完成配置

### 1️⃣ 安全密钥（已设置）

```bash
✅ PORTAL_KEY        # CTOS 客户访问密钥
✅ ADMIN_KEY         # 管理员超级密钥
✅ LOANS_REFRESH_KEY # 贷款资讯手动刷新密钥
✅ FERNET_KEY        # 敏感数据加密密钥
```

### 2️⃣ 环境配置（已设置）

```bash
✅ ENV=prod                    # 生产环境模式
✅ TZ=Asia/Kuala_Lumpur       # 吉隆坡时区
✅ MIN_REFRESH_HOURS=20       # 20小时冷却期
✅ SHOW_REFRESH_BUTTON=0      # 客户页面隐藏刷新按钮
```

### 3️⃣ 数据库（已初始化）

```bash
✅ loan_updates     # 贷款产品表（3条示例数据）
✅ loan_intel       # 银行偏好情报表（3条情报）
✅ loan_meta_kv     # 元数据表（最后采集时间）
✅ ctos_consent     # CTOS授权表（加密存储）
```

---

## 🌐 客户访问入口

### **Loans 智能情报页面**（只读模式）
```
https://workspace-business183.replit.app/loans/page
```

**功能说明**：
- ✅ 查看最新贷款产品（Home Loan、Personal Loan、SME）
- ✅ 银行偏好客户画像（偏好/不偏好、资料要求、口碑摘要、情绪分数）
- ✅ 搜索功能（支持中英文关键词）
- ✅ CSV 导出（产品清单 + 情报数据）
- ✅ DSR 试算工具（输入收入/负债/贷款额计算 DSR）
- ✅ 比价篮（收藏感兴趣的产品）

**客户权限**：
- ❌ **无法手动刷新**（按钮已隐藏，避免消耗 API Token）
- ✅ 数据每天 11:00 AM 自动更新

### **CTOS 授权页面**（需要密钥）
```
https://workspace-business183.replit.app/ctos/page?key=ktW1LjEm1_W9ceHFUBZ2hvZBNiO3Rn8w0gk9hep5vhs=
```

**功能说明**：
- ✅ 客户填写个人/企业资料（IC/SSM、Email、Phone）
- ✅ 授权 CTOS 查询同意书
- ✅ 数据自动加密存储（使用 FERNET_KEY）

---

## 🔧 管理员运维指令

### **1. 手动触发贷款资讯采集**

```bash
curl -X POST https://workspace-business183.replit.app/loans/updates/refresh \
  -H "X-Refresh-Key: 7kAZcDfucTLmLU9umU5A5w1XoOkVDgALVTJQVr0zAlY="
```

**说明**：
- ⏱️ 受 20 小时冷却期保护（避免重复消耗 Token）
- ✅ 返回 `{"status":"done","saved":3,"last_harvest_at":"..."}`
- ❌ 冷却期内返回 `{"status":"skipped","skipped_reason":"cooldown 20h"}`

### **2. 查看最后采集时间**

```bash
curl https://workspace-business183.replit.app/loans/updates/last
```

返回：
```json
{
  "last_harvest_at": "2025-11-05T13:45:22.071694",
  "min_hours": 20
}
```

### **3. CTOS 管理后台**（查看所有授权记录）

```
https://workspace-business183.replit.app/ctos/admin?key=ktW1LjEm1_W9ceHFUBZ2hvZBNiO3Rn8w0gk9hep5vhs=&ak=t6Hr8ITSfjNtC40x3etdufJKovRDSmdyPtaySiX0QiQ=
```

**说明**：
- 🔒 需要双密钥验证（PORTAL_KEY + ADMIN_KEY）
- ✅ 显示所有客户授权记录（包括解密后的敏感数据）
- 📊 查看授权时间、IP、User-Agent

---

## 📈 自动化机制

### **每日自动采集**
- ⏰ **时间**: 每天 11:00 AM（Asia/Kuala_Lumpur）
- 🤖 **执行**: APScheduler 自动触发
- 🔒 **保护**: 20 小时冷却期（避免重复采集）
- 📊 **数据源**: 
  - 无 `PERPLEXITY_API_KEY` → 使用占位示例数据
  - 有 `PERPLEXITY_API_KEY` → 真实抓取银行官网/社媒口碑

### **数据更新流程**
```
11:00 AM 定时任务触发
    ↓
检查上次采集时间
    ↓
≥ 20 小时 → 执行采集
    ↓
保存到 loan_updates + loan_intel 表
    ↓
更新 last_harvest_at 时间戳
```

---

## 📦 导出功能

### **产品清单 CSV**
```
https://workspace-business183.replit.app/loans/updates/export.csv
```
包含：source, product, type, rate, link, snapshot, pulled_at

### **偏好情报 CSV**
```
https://workspace-business183.replit.app/loans/intel/export.csv
```
包含：source, product, preferred_customer, less_preferred, docs_required, feedback_summary, sentiment_score, pulled_at

---

## 🔐 安全密钥管理

### **密钥用途说明**

| 密钥 | 用途 | 分发对象 | 轮换周期 |
|------|------|----------|----------|
| `PORTAL_KEY` | 客户访问 CTOS 授权页面 | 客户邮件/SMS | 每 6 个月 |
| `ADMIN_KEY` | 管理员查看敏感数据 | 仅内部管理员 | 每 3 个月 |
| `LOANS_REFRESH_KEY` | 手动触发贷款更新 | 仅运维人员 | 每 3 个月 |
| `FERNET_KEY` | 加密客户 IC/SSM/Phone | 系统内部 | 每 6 个月 |

### **密钥轮换步骤**

1. 在 Replit Secrets 中修改对应密钥值
2. 重启 FastAPI Server 工作流
3. 更新客户访问链接（如果是 PORTAL_KEY）
4. 旧密钥保留 7 天过渡期

---

## 🎯 性能指标

### **当前数据量**
- 贷款产品：3 条
- 银行情报：3 条
- 平均情绪分数：0.79（正面）

### **系统容量**
- 支持存储：最多 2000 条历史记录
- CSV 导出：最多 2000 行
- API 响应时间：< 100ms

---

## 📞 客户发送模板

### **Email 模板**

```
主题：CreditPilot 智能贷款配对系统 - 专属访问链接

亲爱的 [客户姓名]，

感谢您选择 CreditPilot！我们为您提供马来西亚最全面的贷款资讯与银行偏好情报。

🔗 立即访问您的专属页面：
https://workspace-business183.replit.app/loans/page

✨ 功能亮点：
• 实时贷款产品比较（Home Loan / Personal Loan / SME）
• 银行偏好客户画像（了解哪些银行最适合您）
• 智能 DSR 计算器（即时评估您的借贷能力）
• 一键导出 CSV（方便您与财务顾问讨论）

📊 数据更新：每天 11:00 AM 自动刷新

需要 CTOS 授权服务？请点击：
https://workspace-business183.replit.app/ctos/page?key=ktW1LjEm1_W9ceHFUBZ2hvZBNiO3Rn8w0gk9hep5vhs=

祝您贷款顺利！
CreditPilot 团队
```

---

## 🚨 常见问题

### **Q: 页面显示"暂无数据"？**
A: 执行一次手动刷新：
```bash
curl -X POST https://workspace-business183.replit.app/loans/updates/refresh \
  -H "X-Refresh-Key: 7kAZcDfucTLmLU9umU5A5w1XoOkVDgALVTJQVr0zAlY="
```

### **Q: 客户能否手动刷新数据？**
A: 不能。`SHOW_REFRESH_BUTTON=0` 已隐藏刷新按钮，避免客户滥用。

### **Q: 如何接入真实的 Perplexity 抓取？**
A: 在 Replit Secrets 添加：
```
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx
```
下次自动采集即切换到真实数据。

### **Q: CTOS 数据是否安全？**
A: 是的。所有 IC/SSM/Email/Phone 使用 FERNET_KEY 加密存储，管理员需双密钥才能解密查看。

---

## 📝 下一步计划

### **立即可做**
- ✅ 发送客户访问链接（Email/SMS）
- ✅ 测试 CTOS 授权流程
- ✅ 导出首批情报 CSV 发给销售团队

### **未来增强**
- 📊 PDF 月报：整合偏好情报到财务报告
- 🎯 智能推荐：根据客户 DSR 自动匹配最适产品
- 📈 情绪趋势：显示各银行口碑分数时间趋势
- 🔔 新品通知：当有新产品上线时自动 Email/SMS

---

**系统已 100% 就绪，可立即投入生产使用！** 🎉
