# 📚 系统文档索引 - 快速查找指南

## ⭐ 最重要的文档（必读）

### 1️⃣ 信用卡账单系统设置标准文档 - 最终版
**文件位置**：`docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`

**内容**：
- ✅ 7个固定供应商列表（7SL, HUAWEI, PASAR RAYA, DINAS, RAUB SYC HAINAN, AI SMART TECH, PUCHONG HERBS）
- ✅ ONE BANK + ONE MONTH = ONE RECORD 规则
- ✅ OWNER vs INFINITE 分类系统完整规则
- ✅ 手动验证流程（100%准确，零容差）
- ✅ 第一个月 Previous Balance = 100% Own's 余额规则
- ✅ 文件命名标准：`BankName_YYYY-MM-DD.pdf`（无卡号后4位）
- ✅ 完整上传流程（14步，含提醒系统）
- ✅ 月度报表生成规则（30/31号生成，1号发送）
- ✅ 3色严格限制（Black #000000, Hot Pink #FF007F, Dark Purple #322446）

**用途**：信用卡系统的"操作圣经"，所有录入、验证、分类都按照这个文档执行

---

### 2️⃣ 储蓄账户月结单系统设置标准文档
**文件位置**：`docs/SAVINGS_ACCOUNT_STATEMENT_STANDARDS.md`

**内容**：
- ✅ 8家支持银行（Maybank, GX Bank, HLB, CIMB, UOB, OCBC, Public Bank, Maybank Islamic）
- ✅ Balance-Change算法（核心数据提取逻辑）
- ✅ 双重人工验证系统（Mandatory）
- ✅ 文件存储标准（按客户/银行/月份分类）
- ✅ 完整14步上传流程
- ✅ 100%准确性验证标准

**用途**：储蓄账户系统的"操作圣经"，确保100%数据准确性

---

### 3️⃣ 双重人工验证工作流程
**文件位置**：`docs/MANUAL_VERIFICATION_WORKFLOW.md`

**内容**：
- ✅ 零容差、100%准确性核心原则
- ✅ 完整双重验证工作流程（第一遍 + 第二遍）
- ✅ 验证检查清单（Checklist）
- ✅ 质量标准（9项100%准确性要求）
- ✅ 验证脚本使用说明
- ✅ 时间估算和安全性规范

**用途**：储蓄账户月结单的双重人工验证标准操作流程

---

### 4️⃣ 项目状态和架构记录
**文件位置**：`replit.md`

**内容**：
- 系统最新变更记录（按时间倒序）
- 用户偏好设置
- 系统架构概览
- 技术实现细节
- 数据库设计
- 文件存储架构

**用途**：系统"记忆"，记录所有重要决策和变更历史

---

## 📁 其他重要文档

### 核心技术文档（docs/core/）
| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 系统架构 | `docs/core/SYSTEM_ARCHITECTURE.md` | 完整技术架构说明 |
| 快速启动 | `docs/core/QUICK_START.md` | 新用户快速上手指南 |
| 功能清单 | `docs/core/系统功能完整清单.md` | 所有功能详细列表 |
| 双重验证系统 | `docs/core/账单双重验证系统详解.md` | 数据验证机制详解 |

### 业务文档（docs/business/）
| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 客户演示PPT | `docs/business/客户演示PPT.md` | 产品演示材料 |
| 用户使用指南 | `docs/business/用户使用指南.md` | 用户操作手册 |
| 销售邮件模板 | `docs/business/销售邮件模板库.md` | 营销材料 |

### 功能文档（docs/features/）
| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 分类规则 | `docs/features/CREDIT_CARD_CLASSIFICATION_RULES.md` | OWNER/INFINITE分类详解 |
| 收据系统 | `docs/features/RECEIPT_SYSTEM.md` | OCR收据处理系统 |
| 高级功能报告 | `docs/features/高级功能实施报告.md` | AI分析功能说明 |

### 部署文档（docs/deployment/）
| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 部署指南 | `docs/deployment/DEPLOYMENT_GUIDE.md` | 完整部署流程 |
| 检查清单 | `docs/deployment/deployment_checklist.md` | 部署前检查项 |
| Render部署 | `docs/deployment/RENDER_DEPLOYMENT.md` | Render平台部署 |

### 文件存储架构
| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 存储架构 | `docs/FILE_STORAGE_ARCHITECTURE.md` | 文件夹结构和命名规范 |

---

## 📦 归档文档（docs/archived/）

历史文档和旧版分析资料都存放在这里，已不再使用：
- `docs/archived/cleanup_reports/` - 历史清理报告
- `docs/archived/migration_reports/` - 数据迁移报告
- `docs/archived/old_audits/` - 旧版审计报告
- `docs/archived/old_features/` - 旧版功能文档

---

## 🔍 快速查找规则

### 想要查找...

**信用卡相关**：
- **如何录入信用卡账单？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **7个供应商是哪些？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
- **OWNER vs INFINITE怎么分？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`

**储蓄账户相关**：
- **如何录入储蓄账户月结单？** → `docs/SAVINGS_ACCOUNT_STATEMENT_STANDARDS.md`
- **如何进行双重人工验证？** → `docs/MANUAL_VERIFICATION_WORKFLOW.md`
- **Balance-Change算法是什么？** → `docs/SAVINGS_ACCOUNT_STATEMENT_STANDARDS.md`
- **支持哪些银行？** → `docs/SAVINGS_ACCOUNT_STATEMENT_STANDARDS.md`

**系统相关**：
- **文件命名规则？** → `docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md` 或 `docs/SAVINGS_ACCOUNT_STATEMENT_STANDARDS.md`
- **系统有什么功能？** → `docs/core/系统功能完整清单.md`
- **如何部署系统？** → `docs/deployment/DEPLOYMENT_GUIDE.md`
- **最新变更记录？** → `replit.md`
- **文件存放在哪里？** → `docs/FILE_STORAGE_ARCHITECTURE.md`

---

## 🎯 核心原则（必须记住）

1. **信用卡标准文档**：`docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`
2. **储蓄账户标准文档**：`docs/SAVINGS_ACCOUNT_STATEMENT_STANDARDS.md`
3. **双重验证工作流程**：`docs/MANUAL_VERIFICATION_WORKFLOW.md`
4. **系统记忆**：`replit.md`
5. **文档索引**：`DOCUMENTATION_INDEX.md`（本文件）

**这5个文件是整个系统的"导航中心"，永远不会移动或删除！**

---

## 📊 清理历史

**最近一次清理**：2025-10-26
- ❌ 删除：旧版标准文档（`docs/CREDIT_CARD_STATEMENT_STANDARDS.md`）
- ❌ 删除：临时备份文件（`alliance_bank_backup_before_cleanup.json`）
- ❌ 删除：专用批量导入脚本（`batch_scripts/batch_import_alliance_chang_choon_chow.py`）
- ✅ 保留：最终版标准文档（`docs/CREDIT_CARD_STATEMENT_STANDARDS_FINAL.md`）

**详细报告**：`docs/CLEANUP_SUMMARY_2025-10-26.md`

---

## 🚀 最后更新

**日期**：2024年10月29日  
**更新内容**：
- ✅ 新增储蓄账户月结单系统设置标准文档
- ✅ 新增双重人工验证工作流程文档
- ✅ 更新文档索引，添加储蓄账户相关内容

**状态**：✅ 文档系统已完整建立，所有文件位置固定  
**下次更新**：有新增或删除文档时更新此索引
