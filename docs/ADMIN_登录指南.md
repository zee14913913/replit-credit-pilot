# 🔐 Admin 管理员登录指南

## 📋 快速访问

### **Admin 登录页面**
```
URL: http://localhost:5000/admin/login
生产环境: https://your-domain.com/admin/login
```

---

## 🔑 登录凭证

您的Admin管理员账号已经配置在**环境变量（Secrets）**中：

```
✅ ADMIN_EMAIL: 已配置
✅ ADMIN_PASSWORD: 已配置
```

### **登录步骤：**

1. **访问登录页面**
   - 开发环境：http://localhost:5000/admin/login
   - 或点击导航栏的 **"ADMIN"** 按钮

2. **输入凭证**
   - Username: 使用 `ADMIN_EMAIL` 环境变量中的值
   - Password: 使用 `ADMIN_PASSWORD` 环境变量中的值

3. **成功登录后**
   - 自动跳转到 Admin Dashboard
   - 可以访问所有管理功能

---

## 🎯 Admin Dashboard 新功能

### **导航按钮栏** (顶部)

登录后，Admin Dashboard 顶部现在有 **4个快捷导航按钮**：

```
┌────────────────────┬────────────────┬──────────────────────┬──────────────────┐
│ Back To Dashboard  │    Logout      │  Evidence Archive    │  File Management │
│   (返回主页)        │   (登出)        │   (证据归档)          │   (文件管理)      │
└────────────────────┴────────────────┴──────────────────────┴──────────────────┘
```

#### **1. Back To Dashboard** 
- 功能：返回主 Dashboard (首页)
- 颜色：深紫色渐变 + 白边
- 快捷键：无

#### **2. Logout**
- 功能：退出Admin登录
- 颜色：桃红色渐变 + 白边
- 自动记录审计日志

#### **3. Evidence Archive**
- 功能：打开证据归档管理页面
- 颜色：黑色 + 桃红边框
- 需要Admin权限

#### **4. File Management**
- 功能：打开会计文件管理系统
- 颜色：深紫色渐变 + 紫边
- 管理上传的银行账单和文件

---

## 🛡️ 安全机制

### **权限控制**
```python
@require_admin_or_accountant  # Admin和Accountant都可访问
```

所有Admin路由都有严格的权限验证：
- ✅ 需要登录才能访问
- ✅ 需要Admin或Accountant角色
- ✅ 所有操作记录审计日志

### **Session管理**
- Session存储在Flask服务器
- 自动过期时间：根据配置
- 退出登录会清除所有Session数据

---

## 📊 Admin Dashboard 功能概览

登录后可以访问以下管理功能：

### **核心统计面板**
- 📊 客户总数
- 📄 账单总数
- 💳 交易总数
- 🎫 活跃信用卡数

### **财务统计**
- 💰 Owner's Expenses (个人支出)
- 💵 Owner's Payment (个人还款)
- 📈 Owner's OS Balance (未偿余额)
- 📋 Supplier Invoices (供应商发票)

### **GZ公司财务**
- 🏢 GZ's Expenses (公司支出)
- 💼 GZ's Payment (公司还款)
- 📊 GZ's OS Balance (公司余额)
- 💰 Total Invoices Amount (总发票金额)

### **管理模块**
- 👥 Customer Management (客户管理)
- 💳 Credit Card Management (信用卡管理)
- 📊 Savings Admin (储蓄账户管理)
- 📋 Evidence Archive (证据归档)
- 📁 File Management (文件管理)
- 🔧 System Settings (系统设置)

---

## 🚨 常见问题

### **Q1: 忘记Admin密码怎么办？**
**A:** Admin密码存储在环境变量中，请联系系统管理员或查看Replit Secrets配置。

### **Q2: 登录后提示权限不足？**
**A:** 请确认您的账号角色为 `admin` 或 `accountant`。

### **Q3: Session过期怎么办？**
**A:** 重新访问 `/admin/login` 登录即可。

### **Q4: 如何查看审计日志？**
**A:** 所有Admin操作都会自动记录到PostgreSQL的 `audit_logs` 表中，包括：
- 登录/登出操作
- 文件下载/删除操作
- Evidence归档操作

---

## 🎨 设计风格

Admin Dashboard 严格遵循 **3色调色板**：

```
✅ Hot Pink #FF007F  - 主要强调色、边框、收入
✅ Dark Purple #322446 - 次要强调色、边框、支出
✅ Black #000000 - 背景色、卡片背景
```

所有按钮、卡片、边框都使用这3种颜色，保持高端专业的视觉风格。

---

## 📝 更新日志

### **2025-11-03**
- ✅ 添加4个快捷导航按钮（Back/Logout/Evidence/Files）
- ✅ 所有导航文字改为大写（UPPERCASE）
- ✅ 页脚标题转换为黑色卡片样式（白字+桃红边框）
- ✅ 严格3色调色板合规性

---

## 🔗 相关文档

- [Evidence Archive配置指南](./TASK_SECRET_TOKEN_配置指南.md)
- [系统部署文档](./replit_task_response.txt)
- [项目技术文档](../replit.md)

---

**如有任何问题，请联系系统管理员！** 🚀
