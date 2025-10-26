# Smart Credit & Loan Manager

## 🚀 快速开始

### 📚 重要文档位置（永久固定）

#### ⭐ 3个核心文档（永不移动）

1. **系统操作圣经**  
   📄 `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`  
   包含所有录入、验证、分类规则

2. **系统记忆**  
   📄 `replit.md`  
   记录所有变更历史和架构决策

3. **文档索引**  
   📄 `DOCUMENTATION_INDEX.md`  
   快速查找所有文档的位置

---

## 🔍 想要查找...

- **如何录入账单？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **7个供应商是哪些？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **OWNER vs INFINITE怎么分？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **文件命名规则？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **系统有什么功能？** → `docs/core/系统功能完整清单.md`
- **最新变更记录？** → `replit.md`
- **所有文档位置？** → `DOCUMENTATION_INDEX.md`

---

## 🎯 核心规则速查

### 1️⃣ 一家银行一个月 = 一条记录
- 同一客户，同一银行，同一月份，无论有几张卡，都合并成一条记录

### 2️⃣ 7个固定供应商（GZ's Expenses）
1. 7SL
2. HUAWEI
3. PASAR RAYA
4. DINAS
5. RAUB SYC HAINAN
6. AI SMART TECH
7. PUCHONG HERBS

### 3️⃣ 文件命名标准
- 格式：`BankName_YYYY-MM-DD.pdf`
- 例如：`AllianceBank_2024-09-12.pdf`
- ❌ 不要加卡号后4位

### 4️⃣ 3色严格限制
- **Black** (#000000): 背景
- **Hot Pink** (#FF007F): 收入、付款、CR
- **Dark Purple** (#322446): 支出、消费、DR

### 5️⃣ 100%准确性要求
- 手动逐笔验证，零容差
- 系统必须1:1复刻PDF内容
- 所有负数保持负号显示

---

## 🖥️ 启动系统

```bash
python app.py
```

访问：http://localhost:5000

---

## 📁 项目结构

```
项目根目录/
├── README.md                      ⭐ 本文件（快速访问入口）
├── DOCUMENTATION_INDEX.md         ⭐ 文档索引（永久固定）
├── replit.md                      ⭐ 系统记忆（永久固定）
├── docs/
│   ├── CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md  ⭐ 标准文档（永久固定）
│   ├── FILE_STORAGE_ARCHITECTURE.md
│   ├── CLEANUP_SUMMARY_2025-10-26.md
│   ├── business/      （业务文档）
│   ├── core/          （核心技术文档）
│   ├── deployment/    （部署文档）
│   ├── features/      （功能文档）
│   └── archived/      （归档文件）
├── app.py             （主程序）
├── db/                （数据库）
├── templates/         （HTML模板）
├── static/            （静态文件和上传文件）
├── services/          （业务逻辑）
├── ingest/            （PDF解析）
├── validate/          （数据验证）
├── scripts/           （工具脚本）
└── batch_scripts/     （批量操作脚本）
```

---

## 🎉 最新成就

✅ **Chang Choon Chow - Alliance Bank**  
12个月账单（2024年9月 - 2025年8月）已100%录入完成  
- 87笔交易全部验证通过
- INFINITE消费：RM 29,298.00
- Own's Balance: -RM 19,293.54
- GZ Balance: RM 29,298.00
- 最终余额：RM 10,004.46

---

**最后更新**：2025年10月26日
