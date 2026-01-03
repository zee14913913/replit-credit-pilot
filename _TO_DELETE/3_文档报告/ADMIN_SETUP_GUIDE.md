# 🔐 Admin账户设置指南

## 📋 三种登录方式

### 方式 1：使用现有的默认Admin账户 ✅ **推荐**

系统已有默认管理员账户，可以直接登录：

**登录信息：**
- 👤 Username: `admin`
- 📧 Email: `admin@company.com`
- 🔑 Password: `admin123`

**登录步骤：**
1. 访问：`/admin/login`
2. 输入 Username: `admin`
3. 输入 Password: `admin123`
4. 点击 **Login** 按钮

**⚠️ 安全提示：** 首次登录后请立即修改默认密码！

---

### 方式 2：创建新的Admin账户 🆕

如果你想创建自己的管理员账户，使用注册功能：

**注册步骤：**
1. 访问：`/admin/login`
2. 点击底部的 **"Don't have an account? Register here"** 链接
3. 或直接访问：`/admin/register`
4. 填写注册表单：
   - **Company ID**: `1` (默认主公司)
   - **Username**: 你的用户名（至少3个字符）
   - **Email**: 你的邮箱地址
   - **Full Name**: 你的全名（可选）
   - **Password**: 密码（至少6个字符）
   - **Confirm Password**: 再次输入密码
5. 点击 **"Create Admin Account"** 按钮
6. 注册成功后，系统自动跳转到登录页面
7. 使用新账户登录

---

### 方式 3：使用环境变量凭据（需要先创建用户）

你的环境变量中设置了：
- 📧 Email: `infinitegz.reminder@gmail.com`
- 🔑 Password: `Be_rich13`

**创建对应账户的步骤：**
1. 访问 `/admin/register`
2. 填写以下信息：
   - **Company ID**: `1`
   - **Username**: `infinitegz`（或你喜欢的用户名）
   - **Email**: `infinitegz.reminder@gmail.com`
   - **Full Name**: `Infinite GZ Admin`
   - **Password**: `Be_rich13`
   - **Confirm Password**: `Be_rich13`
3. 注册成功后，使用这些凭据登录

---

## 🎯 快速开始（3步）

### 第一步：登录Admin账户

**最简单方式 - 使用默认账户：**
```
访问: /admin/login
Username: admin
Password: admin123
```

### 第二步：访问Evidence Archive

登录成功后：
1. 在浏览器访问：`/admin/evidence`
2. 查看证据包管理界面

### 第三步：测试Evidence Archive功能

参考 `EVIDENCE_ARCHIVE_TEST_GUIDE.md` 进行完整测试

---

## 🔐 安全最佳实践

### 1. 首次登录后立即修改密码
默认密码 `admin123` 仅用于初始设置，请立即修改。

### 2. 使用强密码
- 至少8个字符
- 包含大小写字母、数字和特殊字符
- 不使用常见密码

### 3. 定期更新密码
建议每3个月更新一次管理员密码。

### 4. 限制Admin账户数量
仅为需要完整系统访问权限的人员创建admin账户。

---

## 📊 当前系统用户

**数据库中现有用户：**

| ID | Username | Email | Role | Status |
|----|----------|-------|------|--------|
| 1 | admin | admin@company.com | admin | ✅ Active |
| 3 | testuser | test@example.com | admin | ✅ Active |
| 4 | proxy_service | proxy@internal.service | admin | ✅ Active |

---

## 🆘 常见问题

### Q1: 忘记密码怎么办？
**A:** 目前系统没有密码重置功能。有以下解决方案：
1. 使用默认账户 `admin / admin123` 登录
2. 联系系统管理员通过数据库重置密码
3. 创建新的admin账户

### Q2: 注册失败提示"用户已存在"？
**A:** 该用户名或邮箱已被使用。请尝试：
1. 使用不同的用户名
2. 使用不同的邮箱地址
3. 如果是你的账户，直接登录即可

### Q3: 登录后显示"权限不足"？
**A:** 确认你的账户角色是 `admin`。只有admin角色可以访问Evidence Archive等高级功能。

### Q4: Company ID应该填什么？
**A:** 
- 默认使用 `1`（主公司）
- 如果你的系统有多个公司，请咨询系统管理员

### Q5: 可以删除默认的admin账户吗？
**A:** 
- 不建议删除，保留作为备用账户
- 如需删除，请确保至少有另一个admin账户可用
- 删除前请先创建你自己的admin账户

---

## 🔧 技术说明

### 密码加密方式
- 使用 **SHA-256** 哈希加密
- 密码格式：`SHA256:<hash>`
- 不可逆加密，保证安全性

### RBAC权限系统
- **Admin**: 完全系统权限（`*.*`）
- **Accountant**: 财务核心权限
- **Viewer**: 只读权限
- **Data Entry**: 数据录入权限
- **Loan Officer**: 贷款业务权限

### 数据库表
- **users**: 用户基本信息
- **permissions**: 权限矩阵
- **audit_logs**: 审计日志（记录所有登录/登出操作）

---

## 🚀 下一步操作

1. ✅ **登录系统** - 使用上述任一方式
2. ✅ **访问Evidence Archive** - `/admin/evidence`
3. ✅ **测试功能** - 参考 `EVIDENCE_ARCHIVE_TEST_GUIDE.md`
4. ✅ **修改密码** - 确保账户安全
5. ✅ **创建其他用户** - 为团队成员分配适当角色

---

## 📞 需要帮助？

如果遇到问题：
1. 检查浏览器控制台错误信息
2. 查看服务器日志
3. 验证数据库连接状态
4. 确认环境变量配置

**快速测试数据库连接：**
```bash
# 检查users表
psql $DATABASE_URL -c "SELECT id, username, email, role FROM users;"
```

---

**创建时间：** 2025-11-03  
**版本：** 1.0  
**适用系统：** Smart Credit & Loan Manager

