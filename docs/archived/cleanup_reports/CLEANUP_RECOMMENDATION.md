# 🧹 系统清理建议

## 📊 当前状态分析

根目录发现 **70+ 个文件**，包括：
- 📜 **35+ 文档文件** (.md)
- 🐍 **15+ Python脚本** (.py)
- 📋 **5+ 配置文件** (.json, .yaml, .toml)

---

## 🎯 清理建议（按优先级）

### 🔴 **高优先级：可以删除的临时文件**

#### 导入脚本（已完成任务）
- `demo_upload_ambank.py` - 演示上传脚本
- `import_chang_choon_chow_statements.py` - 已完成导入
- `import_new_gx_statements.py` - 已完成导入
- `import_tan_zee_liang_statements.py` - 已完成导入
- `reimport_gx_statements.py` - 重新导入脚本

#### 清理脚本（已完成任务）
- `cleanup_duplicates.py` - 清理重复项
- `cleanup_orphaned_files.py` - 清理孤立文件
- `cleanup_report_duplicates.txt` - 清理报告
- `cleanup_report_orphaned_files.txt` - 清理报告

#### 检查脚本（一次性使用）
- `check_db_schema.py` - 数据库检查
- `check_statements.py` - 账单检查
- `final_check.py` - 最终检查
- `system_audit.py` - 系统审计

#### 测试文件
- `test_file_storage.py` - 文件存储测试
- `test_theme.html` - 主题测试页面

---

### 🟡 **中优先级：可以归档的文档**

#### 迁移报告（已完成）
- `migration_report_20251023_190414.json`
- `migration_report_20251023_190630.json`
- `migration_final_summary.json`
- `MIGRATION_SUCCESS_REPORT.md`

#### 旧的清理/审计报告
- `CLEANUP_PLAN.md`
- `FINAL_CLEANUP_REPORT.md`
- `PAGE_AUDIT_RECOMMENDATIONS.md`
- `SECURITY_AUDIT_CUSTOMER_ROUTES.md` - 刚生成的
- `SYSTEM_IMPROVEMENTS_SUMMARY.md` - 刚生成的
- `ROLE_SEPARATION_IMPLEMENTATION_SUMMARY.md`

#### 功能清单（可合并）
- `SYSTEM_FEATURES_COMPLETE_ANALYSIS.md`
- `SYSTEM_FEATURES_GUIDE.md`
- `系统功能完整清单.md`
- `INFINITE_GZ_功能清单.md`

#### 演示/使用记录
- `LIVE_演示记录_2025-10-22.md`
- `实际操作演示指南.md`
- `实际操作演示记录.md`

---

### 🟢 **低优先级：建议保留的核心文件**

#### 核心配置
- ✅ `app.py` - 主应用
- ✅ `requirements.txt` - 依赖
- ✅ `pyproject.toml` - 项目配置
- ✅ `uv.lock` - 依赖锁定
- ✅ `replit.md` - 项目文档

#### 核心脚本
- ✅ `init_db.py` - 数据库初始化
- ✅ `migrate_file_storage.py` - 文件迁移工具

#### 核心文档
- ✅ `QUICK_START.md` - 快速开始
- ✅ `DEPLOYMENT_GUIDE.md` - 部署指南
- ✅ `SYSTEM_ARCHITECTURE.md` - 系统架构
- ✅ `COMPLETE_SECURITY_FIX_REPORT.md` - 最新安全报告

#### 业务文档
- ✅ `客户演示PPT.md` - 客户演示
- ✅ `用户使用指南.md` - 用户指南
- ✅ `销售邮件模板库.md` - 销售模板

---

## 📂 建议的文件组织结构

```
根目录/
├── app.py                          # 主应用
├── requirements.txt                # Python依赖
├── pyproject.toml                  # 项目配置
├── replit.md                       # 项目文档
│
├── scripts/                        # 管理脚本
│   ├── init_db.py
│   ├── migrate_file_storage.py
│   └── (移动其他脚本到这里)
│
├── docs/                          # 文档（已存在）
│   ├── core/                      # 核心文档
│   │   ├── QUICK_START.md
│   │   ├── DEPLOYMENT_GUIDE.md
│   │   └── SYSTEM_ARCHITECTURE.md
│   ├── business/                  # 业务文档
│   │   ├── 客户演示PPT.md
│   │   ├── 用户使用指南.md
│   │   └── 销售邮件模板库.md
│   ├── features/                  # 功能文档
│   └── archived/                  # 已完成项目归档
│       ├── migration_reports/
│       ├── cleanup_reports/
│       └── old_audits/
│
├── data/                          # 数据文件（已存在）
└── (其他现有文件夹...)
```

---

## 🎯 建议的清理操作

### 步骤1：创建归档文件夹
```bash
mkdir -p docs/archived/{migration_reports,cleanup_reports,old_audits,temp_scripts}
```

### 步骤2：移动文件到归档
```bash
# 迁移报告
mv migration_*.json docs/archived/migration_reports/
mv MIGRATION_SUCCESS_REPORT.md docs/archived/migration_reports/

# 清理报告
mv cleanup_*.txt docs/archived/cleanup_reports/
mv CLEANUP_PLAN.md FINAL_CLEANUP_REPORT.md docs/archived/cleanup_reports/

# 临时脚本
mv demo_upload_ambank.py docs/archived/temp_scripts/
mv import_*.py reimport_*.py docs/archived/temp_scripts/
mv cleanup_*.py check_*.py final_check.py system_audit.py docs/archived/temp_scripts/
```

### 步骤3：删除测试文件
```bash
rm test_file_storage.py test_theme.html
```

### 步骤4：组织核心文档
```bash
mkdir -p docs/core docs/business docs/features
# 移动相应文档...
```

---

## 📊 预计效果

**清理前**: 70+ 个文件在根目录  
**清理后**: ~10 个核心文件在根目录  

**好处**:
- ✅ 根目录整洁，易于维护
- ✅ 文档分类清晰，易于查找
- ✅ 归档历史记录，便于回溯
- ✅ 专业的项目结构

---

## ❓ 需要您确认

1️⃣ **是否执行上述清理计划？**
2️⃣ **哪些文档您希望保留在根目录？**
3️⃣ **是否需要合并重复的功能清单文档？**

请告诉我，我将立即执行清理！
