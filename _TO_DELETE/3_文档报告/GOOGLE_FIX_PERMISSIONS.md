# 修复Google Document AI权限问题

## 问题
```
403 Permission 'documentai.processors.processOnline' denied
```

## 解决方案（2分钟）

### 步骤1：访问IAM页面
👉 https://console.cloud.google.com/iam-admin/iam?project=famous-tree-468019-b9

### 步骤2：找到Service Account
1. 在列表中找到您的Service Account（以`@famous-tree-468019-b9.iam.gserviceaccount.com`结尾）
2. 点击右侧的✏️（编辑）图标

### 步骤3：添加角色
1. 点击 **"ADD ANOTHER ROLE"**
2. 搜索并选择：**Cloud Document AI API User**
3. 点击 **"SAVE"**

### 步骤4：等待生效
- 等待1-2分钟让权限生效

### 步骤5：重新测试
```bash
python3 test_google_ai_quick.py
```

---

## 如果找不到Service Account

### 创建新的Service Account：

1. 访问：https://console.cloud.google.com/iam-admin/serviceaccounts?project=famous-tree-468019-b9

2. 点击 **"CREATE SERVICE ACCOUNT"**

3. 填写信息：
   - Name: `documentai-service`
   - ID: 自动生成

4. 点击 **"CREATE AND CONTINUE"**

5. 选择角色：
   - **Cloud Document AI API User**
   
6. 点击 **"CONTINUE"** → **"DONE"**

7. 点击新创建的Service Account

8. 切换到 **"KEYS"** 标签

9. 点击 **"ADD KEY"** → **"Create new key"** → **"JSON"**

10. 下载JSON文件

11. 在Replit Secrets中更新：
    - Key: `GOOGLE_SERVICE_ACCOUNT_JSON`
    - Value: `{JSON文件的全部内容}`

12. 重新测试：
    ```bash
    python3 test_google_ai_quick.py
    ```
