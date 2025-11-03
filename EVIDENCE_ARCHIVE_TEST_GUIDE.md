# 🔐 Evidence Archive System - 完整测试指南

## 📋 系统概述

Evidence Archive System 是一个企业级证据归档管理系统，提供：
- ✅ **安全存储**：证据包存放在私有目录 `evidence_bundles/`，无法通过URL直接访问
- ✅ **完整审计**：所有下载/删除/轮转操作都记录到audit_logs
- ✅ **RBAC权限**：仅admin可访问归档管理页面和执行轮转
- ✅ **自动轮转**：支持30天保留+每月首个包长期留存策略
- ✅ **SHA256验证**：每个证据包都有完整性校验哈希

---

## 🎯 测试计划

### ✅ 已完成状态检查

**当前系统状态：**
- 📦 证据包目录：`evidence_bundles/` ✓ 已创建
- 📄 现有证据包：`evidence_bundle_20251103_093641.zip` (6.1 KB) ✓ 已存在
- 🔧 API端点：6个端点全部实现 ✓
- 🎨 前端页面：`templates/evidence_archive.html` ✓
- 💻 JavaScript：`static/js/evidence-archive.js` ✓
- 🔑 i18n键：18个翻译键已添加 ✓

---

## 🧪 测试步骤

### 测试 1：访问 Evidence Archive 管理页面

#### 步骤：
1. 以 **Admin** 身份登录系统
2. 访问 `/admin/evidence` 页面

#### 预期结果：
✅ 显示Evidence Archive管理界面
✅ 顶部有3个按钮：
   - "Download Latest" (下载最新证据包)
   - "Run Rotation Now" (执行自动轮转) - 仅admin可见
   - "Back to Files" (返回文件列表)
✅ 表格显示所有证据包，包含以下列：
   - 文件名 (File Name)
   - 创建时间 (Created At)
   - 文件大小 (Size)
   - SHA256哈希
   - 来源 (Source)
   - 操作 (Actions: 下载/删除按钮)

#### 当前数据：
- 应显示 1 条记录：`evidence_bundle_20251103_093641.zip`

---

### 测试 2：下载证据包

#### 方法 A：下载最新证据包
1. 点击顶部 **"Download Latest"** 按钮
2. 浏览器应自动下载最新的证据包ZIP文件

#### 方法 B：下载特定证据包
1. 在表格中找到目标证据包
2. 点击该行的 **下载图标** (download icon)
3. 浏览器应下载对应的ZIP文件

#### 预期结果：
✅ ZIP文件成功下载
✅ 审计日志记录下载操作（包含IP地址、User Agent）
✅ 文件大小约 6.1 KB

#### 技术细节：
- API端点：`GET /downloads/evidence/latest` 或 `GET /downloads/evidence/file/<filename>`
- 响应头：`Content-Disposition: attachment; filename="evidence_bundle_xxx.zip"`
- RBAC检查：需要admin角色

---

### 测试 3：上传文件触发证据打包

#### 背景说明：
证据打包通常在以下场景自动触发：
- 批量上传文件
- 处理重要财务文档
- 定期归档任务

#### 手动触发方法：
由于系统已有1个证据包，说明打包功能已正常工作。

#### 验证现有证据包：
```bash
# 查看证据包列表
ls -lh evidence_bundles/

# 查看证据包内容（需要unzip工具）
# unzip -l evidence_bundles/evidence_bundle_20251103_093641.zip
```

#### 预期结果：
✅ 证据包包含处理过的文件快照
✅ SHA256哈希值正确
✅ 文件名格式：`evidence_bundle_YYYYMMDD_HHMMSS.zip`

---

### 测试 4：执行自动轮转（Rotation）

#### 前置条件：
- ✅ 以Admin身份登录
- ✅ 访问 `/admin/evidence` 页面
- ⚠️ 需要 `TASK_SECRET_TOKEN` 环境变量

#### 步骤：
1. 点击 **"Run Rotation Now"** 按钮
2. 系统弹出确认对话框：`确认执行证据包轮转策略？`
3. 点击 **确定**
4. 系统弹出输入框：`请输入TASK_SECRET_TOKEN:`
5. 输入token（默认：`dev-default-token`）
6. 点击 **确定**

#### 轮转策略规则：
- **保留最近30天**的所有证据包
- **保留每月第一个包**作为长期留存
- **删除其他过期包**

#### 预期结果：
✅ 显示成功消息：`轮转完成！保留X个，删除Y个`
✅ 表格自动刷新，显示最新列表
✅ 审计日志记录轮转操作
✅ 返回JSON：
```json
{
  "success": true,
  "kept": ["evidence_bundle_20251103_093641.zip"],
  "deleted": [],
  "reason": "Rotation policy applied: keep 30 days + monthly first"
}
```

#### 环境变量配置：
- `EVIDENCE_ROTATION_DAYS=30` （保留天数，默认30天）
- `EVIDENCE_KEEP_MONTHLY=1` （每月保留首个包，1=启用）
- `TASK_SECRET_TOKEN=dev-default-token` （轮转认证令牌）

---

### 测试 5：删除证据包

#### 步骤：
1. 在表格中找到要删除的证据包
2. 点击该行的 **垃圾桶图标** (trash icon)
3. 系统弹出确认对话框：`确认删除: evidence_bundle_xxx.zip?`
4. 点击 **确定**

#### 预期结果：
✅ 显示成功消息：`已删除: evidence_bundle_xxx.zip`
✅ 表格自动刷新，该记录消失
✅ 实际文件从 `evidence_bundles/` 目录删除
✅ 审计日志记录删除操作（user_id, IP, User Agent）

#### 权限检查：
⚠️ 删除按钮仅对 **admin角色** 可见
⚠️ API端点 `/downloads/evidence/delete` 验证admin权限

---

## 🔐 安全特性验证

### 1. 无认证访问防护
```bash
# 测试未登录访问（应返回302重定向到登录页）
curl -I http://127.0.0.1:5000/admin/evidence
# 预期：Location: /admin/login
```

### 2. 非admin角色访问防护
- 以 **Customer** 或其他角色登录
- 访问 `/admin/evidence`
- **预期**：显示 `权限不足：仅admin可访问证据归档` 并重定向

### 3. 证据包目录隔离
```bash
# 尝试直接访问证据包（应失败）
curl -I http://127.0.0.1:5000/evidence_bundles/evidence_bundle_20251103_093641.zip
# 预期：404 Not Found（无法通过URL直接访问）
```

### 4. X-TASK-TOKEN验证
```bash
# 无token执行轮转（应失败）
curl -X POST http://127.0.0.1:5000/tasks/evidence/rotate
# 预期：401 Unauthorized

# 错误token执行轮转（应失败）
curl -X POST http://127.0.0.1:5000/tasks/evidence/rotate \
  -H "X-TASK-TOKEN: wrong-token"
# 预期：401 Unauthorized
```

---

## 📊 API端点总览

| 端点 | 方法 | 权限 | 功能 |
|------|------|------|------|
| `/admin/evidence` | GET | Admin | 管理页面 |
| `/downloads/evidence/list` | GET | Admin | 列出所有证据包 |
| `/downloads/evidence/latest` | GET | Admin | 下载最新证据包 |
| `/downloads/evidence/file/<filename>` | GET | Admin | 下载指定证据包 |
| `/downloads/evidence/delete` | POST | Admin | 删除证据包 |
| `/tasks/evidence/rotate` | POST | Admin + Token | 执行轮转策略 |

---

## 🌐 i18n翻译键（18个）

### Evidence Archive页面翻译键：
```json
{
  "evidence_archive_title": "EVIDENCE ARCHIVE",
  "download_latest": "Download Latest",
  "rotation_run_now": "Run Rotation Now",
  "back_to_files": "Back to Files",
  "file_name": "File Name",
  "created_at": "Created At",
  "size": "Size",
  "sha256": "SHA256",
  "source": "Source",
  "actions": "Actions",
  "no_records": "No Evidence Bundles Found",
  "failed_to_load": "Failed to Load Evidence Bundles",
  "confirm_delete": "Confirm Delete: {filename}?",
  "confirm_rotation": "Confirm Executing Evidence Bundle Rotation Policy?",
  "rotation_running": "Running Rotation...",
  "rotation_done": "Rotation Complete! Kept {kept} Files, Deleted {deleted} Files",
  "evidence_archive_subtitle": "Secure Evidence Bundle Management System",
  "retention_policy": "Retention Policy: Keep 30 Days + Monthly First Bundle"
}
```

---

## 🧹 清理建议

测试完成后，如需清理：

```bash
# 删除所有证据包（谨慎操作！）
rm -rf evidence_bundles/*.zip

# 查看审计日志
# 使用系统的审计日志查询功能查看所有操作记录
```

---

## ✅ 测试检查清单

- [ ] Admin可访问 `/admin/evidence` 页面
- [ ] 非admin角色被拒绝访问
- [ ] 证据包列表正确显示（文件名、大小、SHA256、时间）
- [ ] 可成功下载最新证据包
- [ ] 可成功下载指定证据包
- [ ] 删除功能正常工作（仅admin可见/执行）
- [ ] 轮转功能正常工作（需TASK_SECRET_TOKEN）
- [ ] 审计日志记录所有操作
- [ ] 证据包无法通过URL直接访问
- [ ] i18n语言切换正常工作（中文/英文）

---

## 🎯 架构师审查状态

✅ **PASS** - 经过6次安全迭代优化
- ✅ 证据包从 `/static/downloads/` 迁移到私有 `evidence_bundles/` 目录
- ✅ 所有端点强制admin RBAC验证
- ✅ 完整审计日志（IP + User Agent）
- ✅ X-TASK-TOKEN双重验证
- ✅ SHA256完整性校验
- ✅ 18个i18n键完整覆盖

---

## 📝 注意事项

1. **TASK_SECRET_TOKEN**：生产环境必须设置强随机token
2. **保留策略**：根据业务需求调整 `EVIDENCE_ROTATION_DAYS`
3. **存储空间**：定期监控 `evidence_bundles/` 目录大小
4. **审计合规**：所有操作都记录到PostgreSQL audit_logs表

---

## 🚀 下一步优化建议

1. **自动化轮转**：配置定时任务（cron）每月自动执行轮转
2. **容量监控**：添加存储空间告警机制
3. **批量操作**：支持批量下载/删除证据包
4. **版本对比**：实现证据包差异比较功能
5. **云端备份**：集成S3/云存储备份证据包

---

**测试开始时间：** ___________  
**测试完成时间：** ___________  
**测试人员：** ___________  
**测试结果：** ✅ PASS / ❌ FAIL  
**备注：** ___________

