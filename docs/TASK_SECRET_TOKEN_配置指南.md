# 🔐 TASK_SECRET_TOKEN 配置详细操作指南

## 📌 配置目标
为 Evidence Archive System 配置安全令牌，启用证据包自动轮转功能。

---

## ✅ 您的专属安全令牌

```
sk_rotate_4p2djUMb4KRaiJhy
```

**⚠️ 重要提醒：**
- 此令牌仅显示一次，请立即复制保存
- 不要与他人分享此令牌
- 配置完成后会用它来触发证据轮转

---

## 📋 配置步骤（共 5 步）

### **步骤 1：进入 Replit Secrets 配置页面**

1. 在当前 Replit 项目界面，找到左侧工具栏
2. 点击 **🔒 Tools** 按钮（或 **Secrets** 图标）
3. 如果看不到 Secrets，点击 **Show hidden files**，然后找到 **Secrets** 面板

**位置参考：**
```
左侧工具栏 → Tools → Secrets
或
左侧工具栏 → 🔒 Secrets (锁图标)
```

---

### **步骤 2：添加 TASK_SECRET_TOKEN**

1. 在 Secrets 面板中，点击 **"+ New Secret"** 按钮
2. 在弹出的对话框中填写：

   **Key (键名)：**
   ```
   TASK_SECRET_TOKEN
   ```

   **Value (值)：**
   ```
   sk_rotate_4p2djUMb4KRaiJhy
   ```

3. 点击 **"Add new secret"** 或 **"Save"** 按钮确认

**✅ 检查点：**
- 确认 Key 名称完全一致（区分大小写）
- 确认 Value 包含完整的 `sk_rotate_` 前缀
- 看到 Secrets 列表中新增了 `TASK_SECRET_TOKEN` 条目

---

### **步骤 3：添加轮转策略配置（可选但推荐）**

如果 Secrets 中没有以下两项，建议一并添加：

#### 3.1 添加 EVIDENCE_ROTATION_DAYS

1. 点击 **"+ New Secret"**
2. 填写：
   - **Key:** `EVIDENCE_ROTATION_DAYS`
   - **Value:** `30`
3. 点击保存

#### 3.2 添加 EVIDENCE_KEEP_MONTHLY

1. 点击 **"+ New Secret"**
2. 填写：
   - **Key:** `EVIDENCE_KEEP_MONTHLY`
   - **Value:** `1`
3. 点击保存

**配置说明：**
- `EVIDENCE_ROTATION_DAYS=30`：保留最近 30 天的证据包
- `EVIDENCE_KEEP_MONTHLY=1`：每月第一个证据包永久保留（长期存档）

---

### **步骤 4：重启服务使配置生效**

配置完 Secrets 后，需要重启两个服务：

#### 4.1 重启 Flask 服务（主应用）

1. 在 Replit 界面找到 **Shell** 标签页（或底部终端）
2. 输入以下命令并按回车：
   ```bash
   # 如果是通过 Run 按钮启动的，直接点击 Stop 然后 Run
   # 或者在 Shell 中手动重启
   pkill -f "python app.py"
   ```
3. 等待服务自动重启（Replit 会自动重新运行 workflow）

#### 4.2 重启 FastAPI 服务（端口 8000）

1. 在 Shell 中输入：
   ```bash
   pkill -f "uvicorn accounting_app.main"
   ```
2. 等待服务自动重启

**✅ 检查点：**
- 看到 Console 输出 "Flask server starting..." 或类似日志
- 没有红色错误提示
- 网页预览正常显示

---

### **步骤 5：验证配置是否成功**

在 Shell 中运行以下命令验证：

```bash
python3 -c "import os; print('✅ TASK_SECRET_TOKEN 已配置') if os.getenv('TASK_SECRET_TOKEN') else print('❌ 未检测到配置')"
```

**预期输出：**
```
✅ TASK_SECRET_TOKEN 已配置
```

如果看到 ❌，请返回步骤 2 检查 Key 名称是否正确。

---

## 🧪 功能测试（可选）

配置完成后，可以测试轮转功能是否正常：

### 方法 1：通过 Admin 后台测试

1. 以 Admin 身份登录系统
2. 访问：`/admin/evidence`
3. 点击页面上的 **"自动轮转"** 按钮
4. 如果配置正确，会看到成功提示

### 方法 2：使用 cURL 测试（高级）

在 Shell 中运行：

```bash
curl -X POST "https://$(env | grep REPL_SLUG | cut -d'=' -f2).$(env | grep REPL_OWNER | cut -d'=' -f2).repl.co/tasks/evidence/rotate" \
  -H "X-TASK-TOKEN: sk_rotate_4p2djUMb4KRaiJhy" \
  -H "Cookie: session=<你的会话Cookie>"
```

**预期返回：**
```json
{
  "success": true,
  "kept": [...],
  "deleted": [...]
}
```

---

## ❓ 常见问题

### Q1: 找不到 Secrets 面板？
**A:** 点击左侧工具栏最下方的 **Tools** (工具箱图标)，在弹出菜单中选择 **Secrets**。

### Q2: 配置后没生效？
**A:** 确保：
1. Key 名称完全一致（`TASK_SECRET_TOKEN`，全大写，有下划线）
2. 已重启服务（Flask + FastAPI 都要重启）
3. 等待 10-15 秒让服务完全启动

### Q3: 重启后网站打不开？
**A:** 
1. 查看 Console 是否有红色错误
2. 确认端口 5000 的服务已启动
3. 尝试点击顶部的 **Run** 按钮重新启动

### Q4: 如何修改令牌？
**A:** 
1. 在 Secrets 面板找到 `TASK_SECRET_TOKEN`
2. 点击右侧的编辑图标 ✏️
3. 输入新的 Value
4. 保存后重启服务

---

## 📊 配置完成检查清单

配置完成后，请逐项核对：

- [ ] **步骤 1**：已进入 Secrets 配置页面
- [ ] **步骤 2**：已添加 `TASK_SECRET_TOKEN`，值为 `sk_rotate_4p2djUMb4KRaiJhy`
- [ ] **步骤 3**：已添加 `EVIDENCE_ROTATION_DAYS=30` 和 `EVIDENCE_KEEP_MONTHLY=1`
- [ ] **步骤 4**：已重启 Flask 和 FastAPI 服务
- [ ] **步骤 5**：验证命令返回 ✅ 已配置

**全部打勾？恭喜您配置成功！** 🎉

---

## 🆘 需要帮助？

如果遇到问题，请截图以下信息并联系技术支持：

1. Secrets 面板的截图（遮住 Value 值）
2. Console 中的错误日志（如果有红色文字）
3. 验证命令的输出结果

---

**生成时间：** 2025-11-03  
**适用版本：** Smart Credit & Loan Manager v2.0  
**安全级别：** 🔒 机密文档，仅供内部使用
