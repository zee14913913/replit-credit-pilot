# ⚡ Render部署快速启动指南

## 🎯 3分钟完成部署

### 第一步：推送代码到GitHub
```bash
git add .
git commit -m "准备部署到Render"
git push origin main
```

### 第二步：Render创建服务
1. 访问 [render.com](https://render.com)
2. 点击 **"New +"** → **"Blueprint"**
3. 连接您的GitHub仓库
4. Render自动读取 `render.yaml` 配置
5. 点击 **"Apply"**

### 第三步：配置环境变量

在Render服务设置中添加：

| 变量名 | 值 |
|--------|-----|
| `ADMIN_EMAIL` | `infinitegz.reminder@gmail.com` |
| `ADMIN_PASSWORD` | `Be_rich13` |
| `FLASK_ENV` | `production` |

### 第四步：等待部署完成

⏱️ 约3-5分钟后，您会看到：
```
✅ Your service is live 🎉
```

### 第五步：测试访问

您的应用URL格式：
```
https://smart-loan-manager-xxxx.onrender.com
```

**测试链接**：
- 首页: `/`
- 管理员登录: `/admin-login`
- 客户注册: `/customer/register`

---

## 🔧 故障排除

### 部署失败？
查看Render日志获取详细错误信息

### 应用无法启动？
确认所有环境变量已正确设置

### 需要详细指南？
查看 `RENDER_DEPLOYMENT.md` 获取完整文档

---

## 📞 管理员凭据

登录 `/admin-login` 使用：
- **Email**: infinitegz.reminder@gmail.com
- **Password**: Be_rich13

---

**需要帮助？** 查看完整部署文档或联系技术支持
